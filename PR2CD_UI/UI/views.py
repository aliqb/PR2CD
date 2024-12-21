import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from Extractors import HazmExtractor
from Requirement import Requirement
from ClassDiagramExtractor import ClassDiagramExtractor, ExtractorEvaluator
from Diagram import ClassDiagram
from hazm.dependency_parser import SpacyDependencyParser
from hazm import POSTagger, Lemmatizer, DependencyParser, word_tokenize
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
model_path = os.path.join(BASE_DIR, 'pos_tagger.model')
# Path to the model file
spacy_parser_path = os.path.join(BASE_DIR, 'spacy_dependency_parser')
lemmatizer = Lemmatizer()
tagger = POSTagger(model=model_path)
spacy_parser = SpacyDependencyParser(tagger=tagger, lemmatizer=lemmatizer,
                                     model_file=spacy_parser_path,
                                     working_dir=spacy_parser_path)
hazm_extractor = HazmExtractor(spacy_parser, lemmatizer, with_ezafe_tag=True)


def index(request):
    req_text = ''
    old_req = request.session.get('req')
    if old_req is not None:
        req_text = old_req['text']
    return render(request, 'UI/index.html', {'req': req_text})


def submit_req(request):
    req_text = request.POST['req']
    if req_text is None or req_text == "":
        return render(request, 'UI/index.html', {
            "error": "متنی وارد نکرده‌اید."
        })

    requirement = Requirement(req_text, hazm_extractor.extract)
    extractor = ClassDiagramExtractor(requirement)
    extractor.extract_diagram()
    request.session['result'] = {
        'classes': [{'text': element.text, 'attributes': [attr.text for attr in element.attributes],
                     'operations': [operation.text for operation in element.operations]} for element in
                    extractor.diagram.classes],
        'relations': [
            {'source': relation.source.text, 'relation_type': relation.relation_type, 'target': relation.target.text,
             'label': relation.label} for relation in extractor.diagram.relations]
    }
    request.session['mermaid'] = extractor.diagram.to_mermaid()
    request.session['req'] = requirement.serialize()
    return HttpResponseRedirect(reverse('UI:diagram'))


def diagram(request):
    result = request.session.get('result')
    requirement = request.session.get('req')
    result_json = json.dumps(result, ensure_ascii=False)
    requirement_json = json.dumps(requirement, ensure_ascii=False)
    warning_nodes_addresses = []
    for sentence in requirement['sentences']:
        for node in sentence['nlp_nodes']:
            if (node['tag'] == 'VERB' and 'شد' in node['lemma']) or node['tag'] == 'PRON':
                warning_nodes_addresses.append([sentence['index'], node['address']])
    return render(request, 'UI/diagram.html',
                  {'result': result_json, 'req': requirement_json, 'req_text': requirement['text'],
                   'warning_nodes': warning_nodes_addresses, 'mermaid': request.session.get('mermaid')})


def about(request):
    return render(request, 'UI/about.html')


def contact(request):
    return render(request, 'UI/contact.html')

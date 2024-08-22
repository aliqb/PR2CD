import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from PNLP import HazmExtractor
from Requirement import Requirement
from ClassDiagramExtractor import ClassDiagramExtractor, ClassDiagram, ExtractorEvaluator
from hazm.dependency_parser import SpacyDependencyParser
from hazm import POSTagger, Lemmatizer, DependencyParser, word_tokenize


# Create your views here.

def index(request):
    req = ''
    old_req = request.session.get('req')
    if old_req is not None:
        req = old_req
    print('reg:', request.session.get('req'))
    return render(request, 'UI/index.html', {'req': req})


def submit_req(request):
    req_text = request.POST['req']
    print(req_text)
    if req_text is None or req_text == "":
        return render(request, 'UI/index.html', {
            "error": "متنی وارد نکرده‌اید."
        })

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
    requirement = Requirement(req_text, hazm_extractor.extract)
    extractor = ClassDiagramExtractor(requirement)
    extractor.extract_class_names()
    for element in extractor.diagram.classes:
        print(element.text, element.node.rel)
    request.session['result'] = {
        'classes': [element.text for element in extractor.diagram.classes]
    }
    request.session['req'] = requirement.text
    return HttpResponseRedirect(reverse('UI:result'))


def result_view(request):
    result = request.session.get('result')
    return render(request, 'UI/result.html', {'result': result})




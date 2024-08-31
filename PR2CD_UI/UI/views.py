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
import re


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
    extractor.extract_attributes()
    for element in extractor.diagram.classes:
        print(element.text, element.node.rel)
        print('attrs:')
        for attr in element.attributes:
            print(attr.text, attr.node.rel)
        print('---------------------------')
    request.session['result'] = {
        'classes': [{'text': element.text, 'attributes': [attr.text for attr in element.attributes]} for element in
                    extractor.diagram.classes]
    }
    request.session['req'] = requirement.text
    return HttpResponseRedirect(reverse('UI:result'))


def result_view(request):
    result = request.session.get('result')
    print(result)
    return render(request, 'UI/result.html', {'result': result})


def evaluation_view(request):
    result = request.session.get('result')
    print(request.method)
    if request.method == 'POST':
        # Get lists of all submitted standard_classes and standard_attributes
        form_standard_classes = request.POST.getlist('standard_classes')
        form_standard_attributes = request.POST.getlist('standard_attributes')

        # Example: Processing the data
        for class_name, attributes in zip(form_standard_classes, form_standard_attributes):
            print(f"Class: {class_name}, Attributes: {attributes}")

        result_diagram = ClassDiagram([item for item in result['classes']])
        standard_classes = [{'text': class_name.strip(),
                             'attributes': [key.strip() for key in re.split(r'[\-–]', attributes) if key != '']} for
                            class_name, attributes in zip(form_standard_classes, form_standard_attributes) if class_name !='']
        # standard_classes = [key.strip() for key in re.split(r'[\-–]', standard_classes_string)]
        print(repr(standard_classes))

        # print(standard_classes)
        standard_diagram = ClassDiagram(standard_classes)
        evaluator = ExtractorEvaluator(result_diagram, standard_diagram)
        class_result = evaluator.evaluate_classes()
        attribute_result = evaluator.evaluate_attributes()
        # print(class_result)
        return render(request, 'UI/evaluation.html', {'classes': class_result, 'attributes': attribute_result})
    else:
        return HttpResponseRedirect(reverse('UI:result'))

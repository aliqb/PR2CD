# Press the green button in the gutter to run the script.
from hazm.dependency_parser import SpacyDependencyParser
from hazm import POSTagger, Lemmatizer, DependencyParser, word_tokenize
from Requirement import Requirement
from ClassDiagramExtractor import ClassDiagramExtractor, ClassDiagram, ExtractorEvaluator
from PNLP import HazmExtractor, StanzaExtractor
import json

def printGraph(dg):
    for node in dg.nodes.values():
        print(node)
        # print('({h[0]}, {h[1]}), {r}, ({d[0]}, {d[1]})'.format(h=head, r=rel, d=dep))

        # print(f'head:{head[0]}, {head[1]}')
        # print(rel)
        # print(f'dep:{dep[0]}, {dep[1]}')
        # print('-----------------------------------')


def print_for_debug(extractor):
    extractor.extract_class_names()
    extractor.extract_attributes()
    for element in extractor.diagram.classes:
        print(element.text, element.node.rel)
        print('attrs:')
        for attr in element.attributes:
            print(attr.text, attr.node.rel)
        print('---------------------------')


if __name__ == '__main__':
    lemmatizer = Lemmatizer()
    tagger = POSTagger(model='pos_tagger.model')
    parser = DependencyParser(tagger=tagger, lemmatizer=lemmatizer)
    spacy_parser = SpacyDependencyParser(tagger=tagger, lemmatizer=lemmatizer,
                                         model_file='./spacy_dependency_parser',
                                         working_dir='./spacy_dependency_parser')
    hazm_extractor = HazmExtractor(spacy_parser, lemmatizer, with_ezafe_tag=True)
    # stanza_extractor = StanzaExtractor()
    name = 'Fitness center'
    try:
        with open(f'./dataset/requirements/{name}.txt', 'r', encoding='utf-8') as file:
            text = file.read()
        with open(f'./dataset/design-elements/{name}.json','r',encoding='utf-8') as json_file:
            elements = json.load(json_file)

        # test = 'هر پرسنل دارای اطلاعاتی مانند نام، سن و جنسیت است.'
        # test = 'کاربر وارد می‌شود. کاربر نام و سن دارد. ماشین راه می‌رومد. ماشین دارای ترمز است.'
        test_req = Requirement(text, hazm_extractor.extract)
        test_extractor = ClassDiagramExtractor(test_req)
        print_for_debug(test_extractor)
        #
        standard_diagram = ClassDiagram(elements)
        evaluator = ExtractorEvaluator(test_extractor.diagram, standard_diagram)
        print(evaluator.evaluate_classes())
        print(evaluator.evaluate_attributes())
    except FileNotFoundError:
        print("File not Found")
    except json.JSONDecodeError:
        print("Error decoding JSON")


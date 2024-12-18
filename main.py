# Press the green button in the gutter to run the script.
from hazm.dependency_parser import SpacyDependencyParser
from hazm import POSTagger, Lemmatizer, DependencyParser, word_tokenize
from Requirement import Requirement
from ClassDiagramExtractor import ClassDiagramExtractor, ExtractorEvaluator
from Diagram import ClassDiagram
from Extractors import HazmExtractor, StanzaExtractor
import json
from hazm.utils import verbs_list
import subprocess
import os

def printGraph(dg):
    for node in dg.nodes.values():
        print(node)
        # print('({h[0]}, {h[1]}), {r}, ({d[0]}, {d[1]})'.format(h=head, r=rel, d=dep))

        # print(f'head:{head[0]}, {head[1]}')
        # print(rel)
        # print(f'dep:{dep[0]}, {dep[1]}')
        # print('-----------------------------------')


def save_diagram_svg(diagram, name):
    # Save the mermaid markdown to a temporary file
    with open('temp.mmd', 'w', encoding='utf-8') as f:
        f.write(diagram.to_mermaid())

    # Run mermaid-cli to generate the SVG
    subprocess.run(['mmdc', '-i', 'temp.mmd', '-o', f'./dataset/output/{name}.svg'],shell=True)

    # Remove the temporary markdown file
    # subprocess.run(['rm', 'temp.mmd'],shell=True)
    os.remove('temp.mmd')
    print(f"SVG file saved as {name}.svg")


def print_for_debug(extractor):
    classes = sorted(extractor.diagram.classes, key=lambda x: x.text)
    for element in classes:
        print(element.text, element.node.meta_rel if element.node else '', element.count, element.frequency)
        print('attrs:')
        for attr in element.attributes:
            print(attr.text, attr.node.meta_rel)
        print('operations:')
        for operation in element.operations:
            print(operation.text)
        print('---------------------------')
    # print('\n\nBase Relations:')
    # for relation in extractor.diagram.base_relations:
    #     print(relation.sentence.text)
    #     print(
    #         f"{relation.source.text},{relation.relation_title.text},{relation.target.text if relation.target else 'None'} {relation.target_node.text if relation.target_node else 'None'}")
    #     print('----------------')

    print('\n\nRelations:')
    for relation in extractor.diagram.relations:
        # print(relation.sentence.text)
        print(
            f"{relation.source.text},{relation.relation_type},{relation.target.text},{relation.label if relation.label else 'None'}")
        print('----------------')


def extract_and_evaluate_from_file(name, extractor, print_elements, save_diagram):
    try:
        with open(f'./dataset/refined-requirements-1/{name}.txt', 'r', encoding='utf-8') as file:
            text = file.read()

        # text = "بازیکن‌ها اطلاعاتی مانند نام، ژانر، جنسیت، سطح و سلاح مورد استفاده خود دارند."
        test_req = Requirement(text, extractor.extract)
        test_extractor = ClassDiagramExtractor(test_req)
        test_extractor.extract_diagram()
        print(name)
        print("\n")
        if print_elements:
            print_for_debug(test_extractor)
        if save_diagram:
            save_diagram_svg(test_extractor.diagram,name)

    # except FileNotFoundError:
    #     print("File not Found")
    except json.JSONDecodeError:
        print("Error decoding JSON")
    try:
        with open(f'./dataset/design-elements/{name}.json', 'r', encoding='utf-8') as json_file:
            elements = json.load(json_file)
        standard_diagram = ClassDiagram(elements)
        evaluator = ExtractorEvaluator(test_extractor.diagram, standard_diagram)
        print(evaluator.evaluate_classes())
        print(evaluator.evaluate_attributes())
    except FileNotFoundError:
        print("File not Found")
    except json.JSONDecodeError:
        print("Error decoding JSON")
    print("//////////////////////////////////////////////////////")


def print_requirement_data(name, extractor):
    try:
        with open(f'./dataset/refined-requirements-1/{name}.txt', 'r', encoding='utf-8') as file:
            text = file.read()

        # text = "بازیکن‌ها اطلاعاتی مانند نام، ژانر، جنسیت، سطح و سلاح مورد استفاده خود دارند."
        test_req = Requirement(text, extractor.extract)
        print(name)
        print(f"sentences: {test_req.get_sentences_count()} tokens: {test_req.get_tokens_count()}")

    except FileNotFoundError:
        print("File not Found")
    except json.JSONDecodeError:
        print("Error decoding JSON")


if __name__ == '__main__':
    lemmatizer = Lemmatizer()
    tagger = POSTagger(model='pos_tagger.model')
    parser = DependencyParser(tagger=tagger, lemmatizer=lemmatizer)
    spacy_parser = SpacyDependencyParser(tagger=tagger, lemmatizer=lemmatizer,
                                         model_file='./spacy_dependency_parser',
                                         working_dir='./spacy_dependency_parser')
    file_names = [
        "ATM",
        "Course enrollment",
        "Restaurant",
        "Game",
        "Rented-car gallery",
        "File manager",
        # "Video rental",
        "Football team",
        "Music band",
        "Musical store",
        "Cinema",
        "Company",
        "Fitness center",

    ]
    new_file_names = [
        "Academic program",
        # "Monitoring Pressure",
        # "Airport",
        "Timbered house",
        "Dental clinic",
        "Circe",
        "Online shopping",
        "Police system",
        "Hospital",
        "Library"
    ]
    hazm_extractor = HazmExtractor(spacy_parser, lemmatizer, with_ezafe_tag=True)

    # stanza_extractor = StanzaExtractor()

    for file in ['test']:
        extract_and_evaluate_from_file(file, hazm_extractor, True, False)
        # print_requirement_data(file, hazm_extractor)

    # text = "کاربر ماشین می‌خرد. جرخ از قسمت‌های ماشین است. چرخ برند و سایز دارد."
    # test_req = Requirement(text, hazm_extractor.extract)
    # test_extractor = ClassDiagramExtractor(test_req)
    # test_extractor.extract_class_names()
    # test_extractor.extract_attributes()
    # test_extractor.extract_relations()
    # test_extractor.extract_operations()
    # print_for_debug(test_extractor)

    # standard_diagram = ClassDiagram(elements)
    # evaluator = ExtractorEvaluator(test_extractor.diagram, standard_diagram)
    # print(evaluator.evaluate_classes())
    # print(evaluator.evaluate_attributes())

from Requirement import Requirement


class ClassElement:
    def __init__(self, text, node=None):
        self.text = text
        self.node = node


class ClassDiagram:
    def __init__(self, classes=None):
        self.classes = []
        if classes is None:
            return
        for element in classes:
            if isinstance(element, str):
                self.add_class(element)
            else:
                self.add_class(element.text, element.node)

    def add_class(self, text, node=None):
        self.classes.append(ClassElement(text, node))


class ClassDiagramExtractor:
    def __init__(self, requirement: Requirement):
        self.requirement = requirement
        self.diagram = ClassDiagram()

    def extract_class_names(self):
        # rules = {
        #     0:def
        # }
        sentences = self.requirement.sentences
        for sentence in sentences:
            nodes = sentence.nlp_nodes
            for node in nodes:
                rel = node.rel
                tag = node.tag
                if node.address == 0 or not (tag.startswith('NOUN') or tag.startswith('PROPN')):
                    continue
                if rel == 'conj':
                    address = node.head
                    rel = sentence.find_node_by_address(address).rel
                if 'subj' in rel or rel.endswith('obj'):
                    name = sentence.find_seq_name(node)
                    same_class = self.find_class_by_name(name)
                    if same_class is None:
                        self.diagram.add_class(name, node)
                    else:
                        if same_class.node.rel != 'subj' and rel == 'subj':
                            same_class.node = node

    def find_class_by_name(self, text):
        filtered = [element for element in self.diagram.classes if element.text == text]
        return filtered[0] if len(filtered) > 0 else None


class ExtractorEvaluator:
    def __init__(self, result_diagram, standard_diagram):
        self.resul_diagram = result_diagram
        self.standard_diagram = standard_diagram

    def evaluate_metrics(self, key_elements, result_elements):
        standard_set = set([element.text for element in key_elements])
        solution_set = set([element.text for element in result_elements])
        intersection = list(standard_set & solution_set)
        n_correct = len(intersection)
        extras = list(solution_set - standard_set)
        missing = list(standard_set - solution_set)
        n_missing = len(missing)
        n_incorrect = len(extras)
        n_key = len(key_elements)
        recall = n_correct / n_key
        precision = n_correct / (n_correct + n_incorrect)
        over_specification = n_incorrect / n_key
        return {
            'recall': recall,
            'precision': precision,
            'over_specification': over_specification,
            'n_key': n_key,
            'n_correct': n_correct,
            'n_incorrect': n_incorrect,
            'n_missing': n_missing
        }

    def evaluate_classes(self):
        return self.evaluate_metrics(self.standard_diagram.classes, self.resul_diagram.classes)

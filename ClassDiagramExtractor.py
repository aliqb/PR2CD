from Requirement import Requirement


class ClassDiagramExtractor:
    def __init__(self, requirement: Requirement):
        self.requirement = requirement
        self.class_names = []

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
                if rel.endswith('subj') or rel.endswith('obj') or rel.startswith('obl'):
                    name = sentence.find_seq_name(node)
                    if not self.node_exist(self.class_names, name):
                        self.class_names.append({'text': name, 'node': node})

    def node_exist(self, diagram_list, text):
        filtered = [element for element in diagram_list if element['text'] == text]
        return len(filtered) > 0



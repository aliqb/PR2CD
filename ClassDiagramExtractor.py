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
                if 'subj' in rel or rel.endswith('obj'):
                    name = sentence.find_seq_name(node)
                    same_class = self.find_class_by_name(self.class_names, name)
                    if same_class is None:
                        self.class_names.append({'text': name, 'node': node})
                    else:
                        if same_class['node'].rel != 'subj' and rel == 'subj':
                            same_class['node'] = node

    def find_class_by_name(self, diagram_list, text):
        filtered = [element for element in diagram_list if element['text'] == text]
        return filtered[0] if len(filtered) > 0 else None

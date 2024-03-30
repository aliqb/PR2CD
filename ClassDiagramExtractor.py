from Requirement import Requirement


class ClassDiagramExtractor:
    def __init__(self, requirement: Requirement):
        self.requirement = requirement
        self.class_names = []

    def extract_class_names(self):
        # rules = {
        #     0:def
        # }
        dependency_graphs = self.requirement.dependency_graphs
        for dg in dependency_graphs:
            for node in dg.nodes.values():
                rel = node['rel']
                tag = node['tag']
                if node['address'] == 0 or not tag.startswith('NOUN'):
                    continue
                if rel == 'conj':
                    address = node['head']
                    rel = dg.nodes[address]['rel']
                if rel.endswith('subj') or rel.endswith('obj') or rel.endswith('obl'):

                    # name = self.find_seq_dependency_name(dg, node)
                    name = self.find_ezafe_name(dg, node)
                    if not self.node_exist(self.class_names, name):
                        self.class_names.append({'text':name, 'node':node})

    def node_exist(self, diagram_list, text):
        filtered = [node for node in diagram_list if node['text'] == text]
        return len(filtered) > 0

    def find_seq_dependency_name(self,dg,node):
        seq_dependencies = ['amod', 'nmod']
        addresses = []
        for dep in seq_dependencies:
            if dep in node['deps']:
                addresses += node['deps'][dep]
        name = node['lemma']
        for address in addresses:
            name += ' ' + dg.nodes[address]['word']
        return name

    def find_ezafe_name(self, dg, node):
        ezafe = node['tag'].endswith('EZ')
        # if name.endswith('ه') and ezafe:
        #     name += "‌ی"
        name = node['lemma']
        address = node['address']
        while ezafe:
            next_address = address + 1
            next_node = dg.nodes[next_address]
            name += ' ' + next_node['word']
            ezafe = next_node['tag'].endswith('EZ')
            address = next_node['address']
        return name

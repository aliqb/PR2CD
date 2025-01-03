from typing import List, Literal
from hazm.utils import words_list, verbs_list


class NLPNode:
    def __init__(self, address: int, text: str, tag: str, rel: str, lemma: str, head: int, deps: dict):
        self.deps = deps
        self.head = head
        self.lemma = lemma
        self.rel = rel
        self.tag = tag
        self.text = text
        self.address = address
        self.meta_rel = rel

    def __str__(self):
        return f"{self.address}, {self.text}, rel:{self.rel}, head:{self.head}, tag:{self.tag}"

    def serialize(self):
        return {
            'address': self.address,
            'text': self.text,
            'tag': self.tag,
            'rel': self.rel,
            'lemma': self.lemma,
            'head': self.head
        }

    def find_in_word_list(self):
        lines = words_list()
        for line in lines:
            if line[0] == self.lemma:
                return line
        if self.lemma.endswith('ی'):
            root = self.lemma[:-1]
            for line in lines:
                if line[0] == root:
                    return line
        return None

    def is_pure_adj(self):
        word_list_line = self.find_in_word_list()
        try:
            return word_list_line is not None and 'AJ' in word_list_line[2]
        except TypeError:
            return False

    def is_subject(self):
        if self.meta_rel is None:
            return False
        return 'subj' in self.meta_rel

    def is_obj(self):
        if self.meta_rel is None:
            return False
        result = self.meta_rel.endswith('obj')
        return result

    def is_infinitive(self):
        if self.text[-1] != 'ن':
            return False
        past_root = self.text[:-1]
        verbs = verbs_list()
        pasts = [verb.split('#')[0] for verb in verbs]
        return past_root in pasts

    def is_esndai_verb(self):
        if self.rel == 'cop':
            return True
        if self.rel == 'aux' and self.text in ['است']:
            return True
        return False

    def is_determiner(self):
        return self.tag.startswith('DET')


class Sentence:
    def __init__(self, index, text, nlp_nodes: List[NLPNode], find_seq_method: Literal['dep', 'ezafe'] = 'dep',
                 with_ezafe_tag: bool = False):
        self.index = index
        self.with_ezafe_tag = with_ezafe_tag
        self.text = text
        self.nlp_nodes = sorted(nlp_nodes, key=lambda x: x.address)
        self.find_seq_method = find_seq_method

    def serialize(self):
        return {
            'index': self.index,
            'text': self.text,
            'nlp_nodes': [node.serialize() for node in self.nlp_nodes]
        }

    def find_root(self):
        for node in self.nlp_nodes:
            if node.rel and node.rel.lower() == 'root':
                return node

    def find_with_tag(self, tag):
        return [node for node in self.nlp_nodes if node.tag == tag]

    def find_next_noun(self, source_node):
        nouns = [node for node in self.nlp_nodes if node.address > source_node.address and 'NOUN' in node.tag]
        if nouns:
            return nouns[0]
        return None

    def find_conjuncts(self, node):
        conj_addresses = node.deps.get('conj', [])
        conjs = [self.find_node_by_address(address) for address in conj_addresses]
        temp_conjs = conjs
        for conj in temp_conjs:
            conj.meta_rel = node.rel
            conjs += self.find_conjuncts(conj)
        return conjs

    def find_seq_first_head(self, node):
        head_node = self.find_node_by_address(node.head)
        while head_node.rel == 'nmod':
            prev_head = self.find_node_by_address(head_node.head)
            if 'NOUN' not in prev_head.tag or 'سیستم' in prev_head.text:  ######
                break
            head_node = prev_head
        return head_node

    def are_together(self, node1, node2, ignore_determiners=False, ):
        if node1.address + 1 == node2.address:
            return True
        middle_nodes = [self.find_node_by_address(index) for index in range(node1.address + 1, node2.address)]

        return all(node.tag.startswith('ADJ') or (node.tag == 'DET' and ignore_determiners) for node in middle_nodes)

    def is_esnadi(self):
        return any(node.rel == 'cop' for node in self.nlp_nodes)

    def is_hastan_masdar(self):
        root = self.find_root()
        return root.tag == 'VERB' and 'هست' in root.lemma

    def find_objects(self, verb=None):
        root = self.find_root()
        if verb is not None:
            root = verb
        sentence_objects = [node for node in self.nlp_nodes if
                            node.rel is not None and node.rel.endswith('obj') and node.head == root.address]
        objects_conjs = []
        for obj in sentence_objects:
            objects_conjs += self.find_conjuncts(obj)
        return sentence_objects + objects_conjs

    def find_obliques(self, oblique_type=None, head=None):
        rel = 'obl'
        if oblique_type is not None:
            rel += f":{oblique_type}"
        sentence_obliques = [node for node in self.nlp_nodes if node.rel is not None and node.rel.startswith(rel)]
        if head:
            sentence_obliques = [node for node in sentence_obliques if node.head == head.address]
        oblique_conjs = []
        for obl in sentence_obliques:
            oblique_conjs += self.find_conjuncts(obl)
        return sentence_obliques + oblique_conjs

    def find_compounds(self, compound_type=None):
        rel = 'compound'
        if compound_type is not None:
            rel += f":{compound_type}"
        sentence_compound = [node for node in self.nlp_nodes if node.rel is not None and node.rel.startswith(rel)]
        conjs = []
        for conj in sentence_compound:
            conjs += self.find_conjuncts(conj)
        return sentence_compound + conjs

    def find_noun_modifiers(self, node):
        noun_modifiers_addresses = node.deps.get('nmod', None)
        noun_modifiers = []
        if noun_modifiers_addresses is not None:
            for address in noun_modifiers_addresses:
                node = self.find_node_by_address(address)
                noun_modifiers.append(node)
                noun_modifiers += self.find_conjuncts(node)
        return noun_modifiers

    def find_adj_modifiers(self, node):
        noun_modifiers_addresses = node.deps.get('amod', None)
        noun_modifiers = []
        if noun_modifiers_addresses is not None:
            for address in noun_modifiers_addresses:
                node = self.find_node_by_address(address)
                noun_modifiers.append(node)
                noun_modifiers += self.find_conjuncts(node)
        return noun_modifiers

    def find_subjects(self, verb=None):
        root = self.find_root()
        if verb is not None:
            root = verb
        subjects = [node for node in self.nlp_nodes if node.rel is not None and node.is_subject()]
        sentence_subjects = [node for node in subjects if node.head == root.address]
        if len(sentence_subjects) == 0:
            advance_subject = []
            for subject in subjects:
                deb_verbs = [node for node in self.find_dependent_nodes(subject) if node.address == root.address]
                if deb_verbs:
                    advance_subject.append(subject)
            sentence_subjects += advance_subject
        subject_conjs = []
        for subj in sentence_subjects:
            subject_conjs += self.find_conjuncts(subj)

        return sentence_subjects + subject_conjs

    def find_recursive_subject(self, verb):
        temp_verb = verb
        subjects = self.find_subjects(verb)
        while len(subjects) == 0:
            if temp_verb.rel in ['conj', 'xcomp', 'ccomp']:  # probably advcl and acl should be added
                temp_verb = self.find_node_by_address(temp_verb.head)
                if temp_verb.tag == 'VERB':
                    subjects = self.find_subjects(temp_verb)
                else:
                    break
            else:
                break
        return subjects

    def find_recursive_objects(self, verb):
        temp_verb = verb
        objects = self.find_objects(verb)
        while len(objects) == 0:
            if temp_verb.rel in ['conj']:
                temp_verb = self.find_node_by_address(temp_verb.head)
                if temp_verb.tag == 'VERB':
                    between_nodes = [node for node in self.find_between_nodes(temp_verb.address, verb.address)]
                    if all(node.tag in ['SCONJ', 'CCONJ', 'PUNCT',
                                        'VERB'] or 'compound' in node.rel or node.rel == 'xcomp' for node in
                           between_nodes):
                        objects = self.find_objects(temp_verb)
                else:
                    break
            else:
                break
        return objects

    def find_xcomps(self, verb):
        xcomps = [node for node in self.nlp_nodes if
                  node.rel is not None and node.rel == 'xcomp' and node.head == verb.address]
        conjs = []
        for xcomp in xcomps:
            conjs += self.find_conjuncts(xcomp)
        return xcomps + conjs

    def find_ccomps(self, verb):
        ccomps = [node for node in self.nlp_nodes if
                  node.rel is not None and node.rel == 'ccomp' and node.head == verb.address]
        conjs = []
        for ccomp in ccomps:
            conjs += self.find_conjuncts(ccomp)
        return ccomps + conjs

    def find_node_by_address(self, address):
        filtered = [node for node in self.nlp_nodes if node.address == address]
        if len(filtered) > 0:
            return filtered[0]
        return None

    def find_node_by_text(self, text):
        return [node for node in self.nlp_nodes if node.text == text]

    def find_seq_names(self, node, skip_adj=True):
        if self.find_seq_method == 'dep':
            return self.find_seq_dependency_names(node, skip_adj)
        if not self.with_ezafe_tag:
            raise Exception('with_ezafe_tag is false')
        return self.find_ezafe_names(node)

    def find_dependent_nodes(self, node):
        nodes = []
        for dep in node.deps.keys():
            nodes += [self.find_node_by_address(address) for address in node.deps[dep]]
        return nodes

    def find_seq_dependent_nodes(self, node):
        seq_dependencies = ['amod', 'nmod', 'flat']
        # addresses = []
        nodes = []
        deps_with_main_tag = {dep.split(':')[0]: dep for dep in node.deps}
        for dep in seq_dependencies:
            if dep in deps_with_main_tag:
                addresses = node.deps[deps_with_main_tag[dep]]
                dep_nodes = [self.find_node_by_address(address) for address in addresses]
                nodes += dep_nodes
        all_nodes = nodes.copy()
        for node in nodes:
            all_nodes += self.find_seq_dependent_nodes(node)
        return all_nodes

    def find_seq_dependency_names(self, node, skip_adj=True):
        name = node.lemma if node.tag != 'VERB' else node.text
        names = []
        dep_nodes = [node for node in self.find_seq_dependent_nodes(node) if node.tag != 'PRON']
        dep_nodes.sort(key=lambda n: n.address)
        is_seq_root = (
                len(dep_nodes) and self.are_together(node, dep_nodes[0]))
        if self.with_ezafe_tag:
            is_seq_root = node.tag.endswith('EZ') and is_seq_root
        if is_seq_root and len(dep_nodes) > 0:
            dep_node = dep_nodes[0]
            old_name = name
            nodes = [node]
            for index in range(len(dep_nodes)):
                dep_node = dep_nodes[index]

                middle_ezafe = dep_node.tag.endswith('EZ')
                must_break = not middle_ezafe if self.with_ezafe_tag else (
                        index < len(dep_nodes) - 1 and self.are_together(dep_node, dep_nodes[index + 1]))
                if not skip_adj or dep_node.rel != 'amod' or not dep_node.is_pure_adj():
                    old_name = name
                    text = dep_node.text if (index < len(
                        dep_nodes) - 1 and not must_break) or dep_node.tag == 'VERB' else dep_node.lemma
                    name += ' ' + text
                    nodes.append(dep_node)
                else:
                    words = name.split(" ")
                    if words[-1] != nodes[-1].lemma and nodes[-1].tag != 'VERB':
                        words[-1] = nodes[-1].lemma
                        name = " ".join(words)
                if must_break:
                    break
            names.append((name, nodes))
            end_conjuncts = self.find_conjuncts(dep_node)
            for conjunct in end_conjuncts:
                conjunct_names = self.find_seq_dependency_names(conjunct)
                for conjunct_name, conj_nodes in conjunct_names:
                    names.append((old_name + " " + conjunct_name, nodes[0:-1] + conj_nodes))
            # start_conjuncts = self.find_conjuncts(node)
            # for conjunct in start_conjuncts:
            #     conjunct_names = self.find_seq_dependency_names(conjunct)
            #     for conjunct_name, conj_nodes in conjunct_names:
            #         no_start_name = " ".join(name[1:])
            #         names.append((conjunct_name + " " + no_start_name, nodes[1:] + conj_nodes))
        else:
            names.append((name, [node]))
        return names

    def find_ezafe_names(self, node):
        ezafe = node.tag.endswith('EZ')
        # if name.endswith('ه') and ezafe:
        #     name += "‌ی"
        name = node.lemma
        old_name = name
        names = []
        address = node.address
        next_node = None
        while ezafe:
            next_address = address + 1
            next_node = self.find_node_by_address(next_address)
            old_name = name
            name += ' ' + next_node.text
            ezafe = next_node.tag.endswith('EZ')
            address = next_node.address
        names.append(name)
        conjuncts = self.find_conjuncts(next_node)
        for conjunct in conjuncts:
            conjunct_names = self.find_seq_dependency_names(conjunct)
            for conjunct_name in conjunct_names:
                names.append(old_name + " " + conjunct_name)
        return [name]

    def find_full_infinitive(self, node):
        if node.tag != 'VERB':
            return ''
        roots = node.lemma.split('#')
        past_root = roots[0]
        if past_root == '':
            return []
        infinitive = past_root + 'ن'
        infinitives = []
        # compounds = []
        compound = ''
        xcomp = ''
        for dep in node.deps:
            if 'compound' in dep:
                address = node.deps[dep][0]
                compound = self.find_node_by_address(address)
            if 'xcomp' in dep and infinitive in ['کردن', 'شدن', 'گرفتن']:
                address = node.deps[dep][0]
                xcomp = self.find_node_by_address(address)
        if compound != '':
            infinitives.append(compound.text + " " + infinitive)
            conjs = self.find_conjuncts(compound)
            for conj in conjs:
                infinitives.append(conj.text + " " + infinitive)
        if xcomp != '':
            infinitives.append(xcomp.text + " " + infinitive)
            conjs = self.find_conjuncts(xcomp)
            for conj in conjs:
                infinitives.append(conj.text + " " + infinitive)
        if len(infinitives) > 0:
            return infinitives
        return [infinitive]

    def find_case(self, node):
        if 'case' not in node.deps:
            return None
        address = node.deps['case'][0]
        case = self.find_node_by_address(address)
        return case

    def find_between_nodes(self, start_address, end_address):
        return [node for node in self.nlp_nodes if start_address < node.address < end_address]

    @staticmethod
    def nodes_to_text(nodes):
        word = ''
        for index in range(len(nodes)):
            node = nodes[index]
            if index == 0:
                word += node.lemma
            elif index == len(nodes) - 1:
                word += " " + node.lemma
            else:
                word += " " + node.text
        return word
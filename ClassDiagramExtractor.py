from Requirement import Requirement


class DesignElement:
    def __init__(self, text, node=None):
        self.text = text
        self.node = node


class ClassElement(DesignElement):
    def __init__(self, text, node=None):
        super().__init__(text, node)
        self.attributes = []

    def add_attribute(self, text, node=None):
        if not  any(attr.text == text for attr in self.attributes):
            self.attributes.append(DesignElement(text, node))


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
        self.attr_terms = ['اطلاعات', 'فیلد', 'ویژگی', 'اطلاعاتی']
        self.attr_verb_particles = ['تعریف', 'تعیین', 'متمایز', 'مشخص']


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

    def extract_attributes(self):
        sentences = self.requirement.sentences
        for sentence in sentences:
            self.extract_attr_have_rule(sentence)
            self.extract_attr_noun_noun_rule(sentence)
            self.extract_attr_verb_particle_rule(sentence)

    def extract_attr_have_rule(self, sentence):
        root = sentence.find_root()
        subjects = sentence.find_subjects()
        subject_names = [sentence.find_seq_name(subject) for subject in subjects]
        class_elements = [element for element in self.diagram.classes if element.text in subject_names]
        if root.lemma == 'داشت#دار':
            self.extract_attr_have_verb_rule(sentence, class_elements)
        if root.lemma.startswith('دارا'):
            self.extract_attr_have_noun_rule(sentence, class_elements)

    def extract_attr_have_verb_rule(self, sentence, class_elements):
        sentence_objects = sentence.find_objects()

        for obj in sentence_objects:
            if obj.lemma in self.attr_terms:
                self.add_attr_terms_modifiers(sentence, obj, class_elements)
                continue
            name = sentence.find_seq_name(obj)
            for element in class_elements:
                element.add_attribute(name, obj)

    def extract_attr_have_noun_rule(self, sentence, class_elements):
        sentence_obliques = sentence.find_obliques('arg')
        for obl in sentence_obliques:
            if obl.lemma in self.attr_terms:
                self.add_attr_terms_modifiers(sentence, obl, class_elements)
                continue
            name = sentence.find_seq_name(obl)
            for element in class_elements:
                element.add_attribute(name, obl)

    def add_attr_terms_modifiers(self, sentence, node, class_elements):
        noun_modifiers = sentence.find_noun_modifiers(node)
        for noun in noun_modifiers:
            name = sentence.find_seq_name(noun)
            for element in class_elements:
                if name != element.text:
                    element.add_attribute(name, noun)

    def extract_attr_noun_noun_rule(self, sentence):
        nodes = sentence.nlp_nodes
        for node in nodes:
            if node.rel == 'nmod':
                head_node = sentence.find_node_by_address(node.head)
                if 'NOUN' not in head_node.tag:
                    return
                node_name = sentence.find_seq_name(node)
                class_element = self.find_class_by_name(node_name)#############

                if class_element is not None:
                    if head_node.lemma in self.attr_terms:
                        self.add_attr_terms_modifiers(sentence, head_node, [class_element])
                        if sentence.is_esnadi():
                            self.add_attr_esnadi_roots(sentence, class_element)
                        # if sentence.is_hastan_masdar():
                        #     self.add_attr_hastan_xcomp(sentence, node, class_element)
                        return
                    class_element.add_attribute(head_node.lemma, head_node)

    def extract_attr_verb_particle_rule(self, sentence):
        compounds = sentence.find_compounds()
        attr_compounds = list(set([node.text for node in compounds]) & set(self.attr_verb_particles))
        if len(attr_compounds) > 0:
            subjects = sentence.find_subjects()
            subject_names = [sentence.find_seq_name(subject) for subject in subjects]
            class_elements = [element for element in self.diagram.classes if element.text in subject_names]
            sentence_obliques = sentence.find_obliques()
            for obl in sentence_obliques:
                name = sentence.find_seq_name(obl)
                for element in class_elements:
                    element.add_attribute(name, obl)



    def add_attr_hastan_xcomp(self, sentence,node, class_element ):
        xcomps = sentence.find_xcomps()
        for xcomp in xcomps:
            if xcomp.text != node.text:
                class_element.add_attribute(xcomp.text, xcomp)

    def add_attr_esnadi_roots(self, sentence, class_element):
        root = sentence.find_root()
        conjuncts = sentence.find_conjuncts(root)
        conjuncts = [root] + conjuncts
        for conjunct in conjuncts:
            class_element.add_attribute(conjunct.text, conjunct)

    def find_class_by_name(self, text):
        filtered = [element for element in self.diagram.classes if element.text == text]
        return filtered[0] if len(filtered) > 0 else None

    def find_class_by_node_text(self, text):
        filtered = [element for element in self.diagram.classes if element.node.text == text]
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

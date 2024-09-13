from Requirement import Requirement


class DesignElement:
    def __init__(self, text, node=None):
        self.text = text
        self.node = node

    def __str__(self):
        return self.text

    def __eq__(self, other):
        if isinstance(other, DesignElement):
            return self.text == other.text
        return False


class RelationBase:
    def __init__(self, source, relation_title, target, sentence):
        self.source = source
        self.relation_title = relation_title
        self.target = target
        self.sentence = sentence


class ClassElement(DesignElement):
    def __init__(self, text, node=None, attributes=None):
        super().__init__(text, node)
        self.attributes = []
        if attributes is None:
            return
        for element in attributes:
            if isinstance(element, str):
                self.add_attribute(element)
            else:
                self.attributes(element.text, element.node)

    def add_attribute(self, text, node=None):
        if not any(attr.text == text for attr in self.attributes):
            self.attributes.append(DesignElement(text, node))


class ClassDiagram:
    def __init__(self, classes=None):
        self.classes = []
        self.base_relations = []
        if classes is None:
            return
        for element in classes:
            if isinstance(element, str):
                self.add_class(ClassElement(element))
            elif isinstance(element, dict):
                attributes = element.get('attributes', [])
                class_element = ClassElement(element['text'], None, attributes)
                self.add_class(class_element)
            else:
                self.add_class(element)

    def add_class(self, class_element):
        self.classes.append(class_element)

    def add_base_relation(self, relation):
        if not self.base_relation_exist(relation):
            self.base_relations.append(relation)

    def base_relation_exist(self, input_relation):
        return any(
            input_relation.source == relation.source and input_relation.relation_title == relation.relation_title and input_relation.target == relation.target
            for relation in self.base_relations)


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
                    names = sentence.find_seq_names(node)
                    for name in names:
                        same_class = self.find_class_by_name(name)
                        if same_class is None:
                            self.diagram.add_class(ClassElement(name, node))
                        else:
                            if same_class.node.rel != 'subj' and rel == 'subj':
                                same_class.node = node

    def extract_attributes(self):
        sentences = self.requirement.sentences
        for sentence in sentences:
            self.extract_attr_have_rule(sentence)
            self.extract_attr_noun_noun_rule(sentence)
            self.extract_attr_verb_particle_rule(sentence)
            self.attr_term_related_to_rule(sentence)

    def extract_relations(self):
        self.extract_relation_bases()

    def extract_relation_bases(self):
        sentences = self.requirement.sentences
        for sentence in sentences:
            verbs = sentence.find_with_tag('VERB')
            for verb in verbs:
                self.find_relation_base_from_verb(sentence, verb)

    def find_relation_base_from_verb(self, sentence, verb):
        if verb.lemma != 'داشت#دار':
            infinitives = sentence.find_full_infinitive(verb)
            infinitive_nodes = [DesignElement(infinitive, verb) for infinitive in infinitives if
                                infinitive not in ['توانستن', 'خواستن']]
            subjects = sentence.find_subjects(verb)
            temp_verb = verb
            while len(subjects) == 0:
                if temp_verb.rel in ['conj', 'xcomp', 'ccomp']:  # probably advcl and acl should be added
                    temp_verb = sentence.find_node_by_address(temp_verb.head)
                    if temp_verb.tag == 'VERB':
                        subjects = sentence.find_subjects(temp_verb)
                    else:
                        break
                else:
                    break
            subject_names = [name for subject in subjects for name in sentence.find_seq_names(subject)]
            objects = sentence.find_objects(verb)
            object_names = [name for obj in objects for name in sentence.find_seq_names(obj)]
            subject_classes = [element for element in self.diagram.classes if element.text in subject_names]
            object_classes = [element for element in self.diagram.classes if element.text in object_names]
            if len(object_classes) == 0:
                for subject_class in subject_classes:
                    for infinitive_node in infinitive_nodes:
                        self.diagram.add_base_relation(RelationBase(subject_class, infinitive_node, None, sentence))
            else:
                for subject_class in subject_classes:
                    for object_class in object_classes:
                        for infinitive_node in infinitive_nodes:
                            self.diagram.add_base_relation(
                                RelationBase(subject_class, infinitive_node, object_class, sentence))

    def extract_attr_have_rule(self, sentence):
        root = sentence.find_root()
        subjects = sentence.find_subjects()
        subject_names = [name for subject in subjects for name in sentence.find_seq_names(subject)]
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
            names = sentence.find_seq_names(obj)
            for name in names:
                for element in class_elements:
                    element.add_attribute(name, obj)

    def extract_attr_have_noun_rule(self, sentence, class_elements):
        sentence_obliques = sentence.find_obliques('arg')
        for obl in sentence_obliques:
            if obl.lemma in self.attr_terms:
                self.add_attr_terms_modifiers(sentence, obl, class_elements)
                continue
            names = sentence.find_seq_names(obl)
            for name in names:
                for element in class_elements:
                    element.add_attribute(name, obl)

    def add_attr_terms_modifiers(self, sentence, node, class_elements):
        noun_modifiers = sentence.find_noun_modifiers(node)
        for noun in noun_modifiers:
            names = sentence.find_seq_names(noun)
            for element in class_elements:
                for name in names:
                    if name != element.text:
                        name = name.replace('مورد', '')
                        element.add_attribute(name.strip(), noun)

    def extract_attr_noun_noun_rule(self, sentence):
        nodes = sentence.nlp_nodes
        for node in nodes:
            if node.rel == 'nmod':
                head_node = sentence.find_node_by_address(node.head)
                if 'NOUN' not in head_node.tag:
                    continue
                if not sentence.are_together(head_node, node, True):
                    continue
                nearest_head = head_node
                while head_node.rel == 'nmod':
                    prev_head = sentence.find_node_by_address(head_node.head)
                    if 'NOUN' not in prev_head.tag or 'سیستم' in prev_head.text:  ######
                        break
                    head_node = prev_head

                node_names = sentence.find_seq_names(node)
                class_elements = [self.find_class_by_name(node_name) for node_name in node_names]  #############
                for class_element in class_elements:
                    if class_element is not None:
                        if head_node.lemma in self.attr_terms:
                            self.add_attr_terms_modifiers(sentence, head_node, [class_element])
                            if sentence.is_esnadi():
                                self.add_attr_esnadi_roots(sentence, class_element)
                            # if sentence.is_hastan_masdar():
                            #     self.add_attr_hastan_xcomp(sentence, node, class_element)
                            return
                        if head_node.address == nearest_head.address:
                            class_element.add_attribute(nearest_head.lemma, head_node)
                        else:
                            names = sentence.find_seq_names(head_node)
                            names = [name for name in names if nearest_head.text in name]
                            if len(names) > 0:
                                for name in names:
                                    modifier_name = name.replace(node.text, '')
                                    class_element.add_attribute(modifier_name.strip(), head_node)
                            else:
                                class_element.add_attribute(nearest_head.lemma, head_node)

    def extract_attr_verb_particle_rule(self, sentence):
        compounds = sentence.find_compounds()
        attr_compounds = list(set([node.text for node in compounds]) & set(self.attr_verb_particles))
        if len(attr_compounds) > 0:
            subjects = sentence.find_subjects()
            subject_names = [name for subject in subjects for name in sentence.find_seq_names(subject)]
            class_elements = [element for element in self.diagram.classes if element.text in subject_names]
            sentence_obliques = sentence.find_obliques()
            for obl in sentence_obliques:
                names = sentence.find_seq_names(obl)
                for name in names:
                    for element in class_elements:
                        element.add_attribute(name, obl)

    def add_attr_hastan_xcomp(self, sentence, node, class_element):
        xcomps = sentence.find_xcomps()
        for xcomp in xcomps:
            if xcomp.text != node.text:
                class_element.add_attribute(xcomp.text, xcomp)

    def add_attr_esnadi_roots(self, sentence, class_element):
        root = sentence.find_root()
        if root.lemma.startswith('دارا'):
            return
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

    def attr_term_related_to_rule(self, sentence):
        related_term_nodes = sentence.find_node_by_text('مربوط') + sentence.find_node_by_text('مرتبط')
        related_term_nodes = [node for node in related_term_nodes if
                              node.rel == 'amod' and sentence.find_node_by_address(node.head).lemma in self.attr_terms]
        for node in related_term_nodes:
            obl_address = node.deps.get('obl:arg', None)
            if obl_address is not None:
                obl = sentence.find_node_by_address(obl_address[0])
                names = sentence.find_seq_names(obl)
                class_elements = [self.find_class_by_name(name) for name in names]
                for class_element in class_elements:
                    if class_element is not None:
                        modifiers = sentence.find_noun_modifiers(obl)
                        for modifier in modifiers:
                            attr_names = sentence.find_seq_names(modifier)
                            for attr_name in attr_names:
                                class_element.add_attribute(attr_name, modifier)


class ExtractorEvaluator:
    def __init__(self, result_diagram, standard_diagram):
        self.resul_diagram = result_diagram
        self.standard_diagram = standard_diagram

    def evaluate_metrics(self, key_texts, result_texts):
        standard_set = set(key_texts)
        solution_set = set(result_texts)
        intersection = list(standard_set & solution_set)
        n_correct = len(intersection)
        extras = list(solution_set - standard_set)
        missing = list(standard_set - solution_set)
        n_missing = len(missing)
        n_incorrect = len(extras)
        n_key = len(key_texts)
        recall = n_correct / n_key
        precision = n_correct / (n_correct + n_incorrect) if n_incorrect + n_correct > 0 else 0
        over_specification = n_incorrect / n_key
        return {
            'recall': recall,
            'precision': precision,
            'over_specification': over_specification,
            'n_correct': n_correct,
            'n_incorrect': n_incorrect,
            'n_missing': n_missing,
            'n_key': n_key
        }

    def evaluate_classes(self):
        return self.evaluate_metrics([element.text for element in self.standard_diagram.classes],
                                     [element.text for element in self.resul_diagram.classes])

    def evaluate_attributes(self):
        standard_attribute_texts = self.get_attributes_texts(self.standard_diagram)
        result_attribute_text = self.get_attributes_texts(self.resul_diagram)
        return self.evaluate_metrics(standard_attribute_texts, result_attribute_text)

    def get_attributes_texts(self, diagram):
        attribute_texts = []
        for element in diagram.classes:
            texts = [f"{element.text},{attr.text}" for attr in element.attributes]
            attribute_texts += texts

        return attribute_texts

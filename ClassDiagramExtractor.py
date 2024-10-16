from Requirement import Requirement
import re


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
    def __init__(self, source, relation_title, target, sentence, target_node=None):
        self.source = source
        self.relation_title = relation_title
        self.target = target
        self.sentence = sentence
        self.target_node = target_node
        if target is not None:
            self.target_node = self.target.node

    def __eq__(self, other):
        if self.source != other.source or self.relation_title != other.relation_title:
            return False
        if self.target == other.target:
            # If both 'target' and 'target_node' are None
            if self.target is None and self.target_node is None and other.target_node is None:
                return True

            # If 'target' is None but 'target_node' is not None, compare 'target_node.text'
            if self.target is None:
                if self.target_node is None or other.target_node is None:
                    return False  # One of the target_nodes is None while the other isn't
                return self.target_node.text == other.target_node.text and self.target_node.address == other.target_node.address

            # If 'target' is not None, return True since the 'target' comparison passed
            return True
        return False


class Relation:
    def __init__(self, source, relation_type, target, base, label=None):
        self.source = source
        self.relation_type = relation_type
        self.target = target
        self.label = label
        self.base = base

    def __eq__(self, other):
        return self.source == other.source and self.target == other.target and self.relation_type == other.relation_type and self.label == other.label


class ClassElement(DesignElement):
    def __init__(self, text, node=None, attributes=None, operations=None):
        super().__init__(text, node)
        self.attributes = []
        self.operations = []
        self._count = 0
        if attributes is None:
            return
        for element in attributes:
            if isinstance(element, str):
                self.add_attribute(element)
            else:
                self.add_attribute(element.text, element.node)
        if operations is None:
            return
        for element in operations:
            if isinstance(element, str):
                self.add_attribute(element)
            else:
                self.add_operation(element.text, element.node)

    def add_attribute(self, text, node=None):
        if not any(attr.text == text for attr in self.attributes):
            self.attributes.append(DesignElement(text, node))

    def remove_attribute(self, name):
        self.attributes = [attr for attr in self.attributes if attr.text != name]

    def add_operation(self, text, node=None):
        if not any(attr.text == text for attr in self.operations):
            self.operations.append(DesignElement(text, node))

    def is_weak(self):
        if self.node is None:
            return True
        return not self.node.is_subject()

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, new_count):
        self._count = new_count


class ClassDiagram:
    def __init__(self, classes=None):
        self.classes = []
        self.base_relations = []
        self.relations = []
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

    def remove_class(self, class_element):
        self.classes = [element for element in self.classes if element.text != class_element.text]
        self.relations = [relation for relation in self.relations if
                          relation.source.text != class_element.text and relation.target.text != class_element.text]

    def add_base_relation(self, relation):
        if not self.base_relation_exist(relation):
            self.base_relations.append(relation)

    def base_relation_exist(self, input_relation):
        return any(input_relation == relation for relation in self.base_relations)

    def relation_exist(self, input_relation):
        return any(input_relation == relation for relation in self.relations)

    def relation_with_base_exist(self, base_relation):
        return any(base_relation == relation.base for relation in self.relations)

    def add_generalization(self, child, parent, base):
        relation = Relation(child, 'GENERALIZATION', parent, base)
        if not self.relation_exist(relation):
            self.relations.append(relation)

    def add_aggregation(self, child, parent, base):
        relation = Relation(child, 'AGGREGATION', parent, base)
        if not self.relation_exist(relation):
            self.relations.append(relation)

    def add_composition(self, child, parent, base):
        relation = Relation(child, 'COMPOSITION', parent, base)
        if not self.relation_exist(relation):
            self.relations.append(relation)

    def add_association(self, source, target, base):
        relation = Relation(source, 'ASSOCIATION', target, base, base.relation_title.text)
        if not self.relation_exist(relation):
            self.relations.append(relation)


class ClassDiagramExtractor:
    def __init__(self, requirement: Requirement):
        self.requirement = requirement
        self.diagram = ClassDiagram()
        self.attr_terms = ['اطلاعات', 'فیلد', 'ویژگی', 'اطلاعاتی']
        self.attr_verb_particles = ['تعریف', 'تعیین', 'متمایز', 'مشخص']
        self.category_words = [
            'دسته',
            'گروه',
            'طبقه',
            'نوع',
            'انواع'
        ]
        self.categorizing_words = [
            'دسته‌بندی',
            'تفکیک',
            'تقسیم',
            'تفکیک',
            'بخش‌بندی'
        ]
        self.complex_categorizing_words = [
            'قرار گرفتن',
            'جای گرفتن'
        ]
        self.contain_word = 'شامل'
        self.composition_verb_particles = [
            'ساختن',
            'تشکیل'
        ]
        self.composition_nouns = [
            'قسمت',
            'جزئی',
            'بخش',
        ]

        self.composition_parent_words = [
            'ساختار',
            'اجزا'
        ]

    def extract_diagram(self):
        self.extract_class_names()
        self.extract_attributes()
        self.extract_relation_bases()
        self.extract_operations()
        self.extract_relations()
        self.post_process()

    # classes
    def extract_class_names(self):
        # rules = {
        #     0:def
        # }
        sentences = self.requirement.sentences
        for sentence in sentences:
            self.extract_subject_object_class_name(sentence)
            if sentence.is_esnadi():
                self.extract_esnadi_class_names(sentence)
            if sentence.is_hastan_masdar():
                self.extract_hastan_class_names(sentence)
        self.count_classes()

    def extract_subject_object_class_name(self, sentence):
        subjects = [node for node in sentence.nlp_nodes if node.is_subject()]
        sentence_objects = [node for node in sentence.nlp_nodes if node.is_obj()]
        all_subjects = subjects.copy()
        all_objects = sentence_objects.copy()
        for subject in subjects:
            all_subjects += sentence.find_conjuncts(subject)
        for obj in sentence_objects:
            all_objects += sentence.find_conjuncts(obj)
        nodes = all_subjects + all_objects
        for node in nodes:
            tag = node.tag
            if not (tag.startswith('NOUN') or tag.startswith('PROPN')):
                continue
            names = sentence.find_seq_names(node)
            for name in names:
                same_class = self.find_class_by_name(name)
                if same_class is None:
                    self.diagram.add_class(ClassElement(name, node))
                else:
                    if not same_class.node.is_subject() and node.is_subject():
                        same_class.node = node

    def extract_esnadi_class_names(self, sentence):
        root = sentence.find_root()
        roots = [root] + sentence.find_conjuncts(root)
        for node in roots:
            tag = node.tag
            if not (tag.startswith('NOUN') or tag.startswith('PROPN')):
                continue
            names = sentence.find_seq_names(node)
            for name in names:
                same_class = self.find_class_by_name(name)
                if same_class is None:
                    self.diagram.add_class(ClassElement(name, node))

    def extract_hastan_class_names(self, sentence):
        root = sentence.find_root()
        xcomps = sentence.find_xcomps(root)
        for node in xcomps:
            tag = node.tag
            if not (tag.startswith('NOUN') or tag.startswith('PROPN')):
                continue
            names = sentence.find_seq_names(node)
            for name in names:
                same_class = self.find_class_by_name(name)
                if same_class is None:
                    self.diagram.add_class(ClassElement(name, node))

    # attributes
    def extract_attributes(self):
        sentences = self.requirement.sentences
        for sentence in sentences:
            self.extract_attr_have_rule(sentence)
            self.extract_attr_noun_noun_rule(sentence)
            self.extract_attr_verb_particle_rule(sentence)
            self.attr_term_related_to_rule(sentence)

    def extract_attr_have_rule(self, sentence):
        root = sentence.find_root()
        subjects = sentence.find_subjects()
        subject_names = [name for subject in subjects for name in sentence.find_seq_names(subject)]
        class_elements = [element for element in self.diagram.classes if element.text in subject_names]
        if root.lemma == 'داشت#دار':
            self.extract_attr_have_verb_rule(sentence, class_elements)
        if root.lemma.startswith('دارا'):
            self.extract_attr_have_noun_rule(sentence, class_elements)

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
                                    modifier_name = re.sub(rf'\b{re.escape(node.text)}\b', '', name).strip()
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

    # relations
    def extract_relations(self):
        # self.extract_relation_bases()
        self.extract_generalizations()
        self.extract_aggregations()
        self.extract_composition()
        self.extract_associations()

    # relation bases
    def extract_relation_bases(self):
        sentences = self.requirement.sentences
        for sentence in sentences:
            verbs = sentence.find_with_tag('VERB')
            for verb in verbs:
                if verb.rel == 'cop':
                    self.find_relation_base_from_esnadi_verbs(sentence)

                elif 'هست' in verb.lemma:
                    self.find_relation_base_from_hastan(sentence, verb)
                else:
                    self.find_relation_base_from_normal_verb(sentence, verb)
            if ':' in sentence.text:
                self.find_list_relation_base(sentence)
            if self.contain_word in sentence.text:
                self.find_contain_relation_base(sentence)

    def find_relation_base_from_esnadi_verbs(self, sentence):
        root = sentence.find_root()
        subjects = sentence.find_subjects(root)
        roots = [root] + sentence.find_conjuncts(root)
        self.add_relation_triples(subjects, [DesignElement('ESNADI')], roots, sentence)

    def find_relation_base_from_hastan(self, sentence, verb):
        subjects = sentence.find_subjects(verb)
        xcomps = sentence.find_xcomps(verb)
        self.add_relation_triples(subjects, [DesignElement('ESNADI')], xcomps, sentence)

    def find_relation_base_from_normal_verb(self, sentence, verb):
        if verb.lemma != 'داشت#دار':
            infinitives = sentence.find_full_infinitive(verb)
            infinitive_elements = [DesignElement(infinitive, verb) for infinitive in infinitives if
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
            objects = sentence.find_objects(verb)
            self.add_relation_triples(subjects, infinitive_elements, objects, sentence)

    def find_list_relation_base(self, sentence):
        if "«" in sentence.text or "»" in sentence.text:
            return

        colon_nodes = sentence.find_node_by_text(':')
        if len(colon_nodes) == 0:
            return
        colon_node = colon_nodes[0]
        after_colon_nodes = [node for node in sentence.nlp_nodes if node.address > colon_node.address]
        if any(node.tag == 'VERB' for node in after_colon_nodes):
            return
        if not any(node.text in {'،', 'و', ','} for node in after_colon_nodes):
            return
        main_nodes = [node for node in after_colon_nodes if node.rel not in ['nmod', 'amod', 'punct', 'cc']]
        subjects = sentence.find_subjects()
        self.add_relation_triples(subjects, [DesignElement('LIST')], main_nodes, sentence)

    def find_contain_relation_base(self, sentence):
        contain_word_nodes = sentence.find_node_by_text(self.contain_word)
        if len(contain_word_nodes) == 0:
            return
        contain_word_node = contain_word_nodes[0]
        next_address = contain_word_node.address + 1
        obl_addresses = contain_word_node.deps.get('obl:arg', None)
        obl_node = sentence.find_node_by_address(
            obl_addresses[0]) if obl_addresses is not None else sentence.find_node_by_address(next_address)
        subjects = sentence.find_subjects()
        nodes = [obl_node] + sentence.find_conjuncts(obl_node)
        self.add_relation_triples(subjects, [DesignElement('CONTAIN')], nodes, sentence)

    def add_relation_triples(self, source_nodes, infinitive_elements, target_nodes, sentence):
        source_names = [name for source in source_nodes for name in sentence.find_seq_names(source)]
        source_classes = [element for element in self.diagram.classes if element.text in source_names]
        if len(target_nodes) == 0:
            for subject_class in source_classes:
                for infinitive_node in infinitive_elements:
                    self.diagram.add_base_relation(RelationBase(subject_class, infinitive_node, None, sentence))
        else:
            for subject_class in source_classes:
                for node in target_nodes:
                    names = sentence.find_seq_names(node)
                    for name in names:
                        target_class = self.find_class_by_name(name)
                        for infinitive_node in infinitive_elements:
                            self.diagram.add_base_relation(
                                RelationBase(subject_class, infinitive_node, target_class, sentence, node))

    # generalizations
    def extract_generalizations(self):
        for relation in self.diagram.base_relations:
            if relation.relation_title.text == 'ESNADI':
                self.extract_generalizations_from_esnadi(relation)
            if relation.relation_title.text == 'LIST':
                self.extract_generalization_from_list(relation)
            if any(term in relation.relation_title.text for term in self.categorizing_words):
                self.extract_generalization_categorization(relation)
            if any(term == relation.relation_title.text for term in self.complex_categorizing_words) and any(
                    term in relation.sentence.text for term in self.category_words):
                self.extract_generalization_categorization(relation)

    def extract_generalizations_from_esnadi(self, relation):
        base_source = relation.source
        base_target = relation.target
        sentence = relation.sentence
        if relation.target_node is not None and any(
                term in relation.target_node.text for term in self.composition_nouns):
            return
        if base_target is not None:
            self.diagram.add_generalization(base_target, base_source, relation)

    def extract_generalization_from_list(self, relation):
        parent = relation.source
        child = relation.target
        if child is None:
            node = relation.target_node
            names = relation.sentence.find_seq_names(node, False)
            for name in names:
                child = ClassElement(name, node)
                self.diagram.add_class(child)
                self.diagram.add_generalization(child, parent, relation)
        else:
            self.diagram.add_generalization(child, parent, relation)

    def extract_generalization_categorization(self, relation):
        obls = [node for node in relation.sentence.find_obliques() if node.head == relation.relation_title.node.address]
        xcomps = relation.sentence.find_xcomps(relation.relation_title.node)
        nodes = obls + xcomps
        main_nodes = []
        for node in nodes:
            if node.lemma in self.category_words + self.categorizing_words:
                main_nodes += relation.sentence.find_noun_modifiers(node)
            else:
                main_nodes.append(node)
        for node in main_nodes:
            names = relation.sentence.find_seq_names(node, False)
            for name in names:
                class_element = self.find_class_by_name(name)
                if class_element is None:
                    class_element = ClassElement(name, node)
                    self.diagram.add_class(class_element)
                self.diagram.add_generalization(class_element, relation.source, relation)

    # aggregations
    def extract_aggregations(self):
        for relation in self.diagram.base_relations:
            if relation.relation_title.text == 'CONTAIN':
                self.extract_aggregations_from_contain_relation(relation)
        # self.convert_attributes_to_aggregation()

    def extract_aggregations_from_contain_relation(self, relation):
        parent = relation.source
        child = relation.target
        if child is not None:
            self.diagram.add_aggregation(child, parent, relation)
        else:
            target_node = relation.target_node
            names = relation.sentence.find_seq_names(target_node)
            for name in names:
                attr_name = re.sub(rf'\b{re.escape(parent.text)}\b', '', name).strip()
                parent.add_attribute(attr_name, target_node)

    def convert_attributes_to_aggregation(self):
        for class_element in self.diagram.classes:
            for attribute in class_element.attributes:
                name = attribute.text
                attr_class = self.find_class_by_name(name)
                if attr_class is not None:
                    self.diagram.add_aggregation(attr_class, class_element, None)
                    class_element.remove_attribute(name)

    # composition
    def extract_composition(self):
        for relation in self.diagram.base_relations:
            if any(term in relation.relation_title.text for term in self.composition_verb_particles):
                self.extract_composition_from_composition_verbs(relation)
            if relation.relation_title.text == 'ESNADI':
                self.extract_composition_from_esnadi(relation)

    def extract_composition_from_composition_verbs(self, relation):
        if relation.target is None:
            self.find_composition_from_passive_composition_verb(relation)
        else:
            self.find_composition_from_active_composition_verb(relation)

    def find_composition_from_passive_composition_verb(self, relation):
        preposition_nodes = relation.sentence.find_node_by_text('از')
        if len(preposition_nodes) == 0:
            return
        preposition_node = preposition_nodes[0]
        next_node = relation.sentence.find_node_by_address(preposition_node.address + 1)
        nodes = [next_node] + relation.sentence.find_conjuncts(next_node)
        for node in nodes:
            names = relation.sentence.find_seq_names(node)
            for name in names:
                child = self.find_class_by_name(name)
                if child is not None:
                    self.diagram.add_composition(child, relation.source, relation)
                else:
                    relation.source.add_attribute(name, node)

    def find_composition_from_active_composition_verb(self, relation):
        parent = relation.target
        if parent is None:
            return
        child = relation.source
        self.diagram.add_composition(child, parent, relation)

    def extract_composition_from_esnadi(self, relation):
        nlp_nodes = [node for node in relation.sentence.nlp_nodes if node.text is not None]
        composition_nodes = [node for node in nlp_nodes if
                             any(term in node.text for term in self.composition_nouns)]
        preposition_nodes = relation.sentence.find_node_by_text('از')
        if len(preposition_nodes) == 0 or len(composition_nodes) == 0:
            return
        composition_node = composition_nodes[0]
        preposition_node = preposition_nodes[0]
        if composition_node.address < preposition_node.address:
            base_address = preposition_node.address

        else:
            base_address = composition_node.address
        next_node = relation.sentence.find_node_by_address(base_address + 1)
        if any(term in next_node.text for term in self.composition_parent_words):
            next_node = relation.sentence.find_node_by_address(next_node.address + 1)
        nodes = [next_node] + relation.sentence.find_conjuncts(next_node)
        for node in nodes:
            names = relation.sentence.find_seq_names(node)
            for name in names:
                parent = self.find_class_by_name(name)
                if parent is not None:
                    self.diagram.add_composition(relation.source, parent, relation)

    # ASSOCIATION
    def extract_associations(self):
        for relation in self.diagram.base_relations:
            if self.diagram.relation_with_base_exist(relation) or relation.target is None or relation.target.is_weak():
                continue
            self.diagram.add_association(relation.source, relation.target, relation)

    # operations
    def extract_operations(self):
        relations = [relation for relation in self.diagram.base_relations if
                     relation.relation_title.text not in ['ESNADI', 'LIST', 'CONTAIN']]
        for relation in relations:
            target = relation.target
            source = relation.source
            title = relation.relation_title
            if target is None:
                source.add_operation(title.text, title.node)
                continue
            if target.is_weak():
                source.add_operation(f"{title.text} {target.text}", title.node)

    # post
    def post_process(self):
        self.remove_info_words()

    def remove_info_words(self):
        info_contain_terms = self.attr_terms  + self.categorizing_words + [self.contain_word] + self.composition_nouns[0:2] + self.composition_parent_words
        info_exact_terms = self.category_words
        for class_element in self.diagram.classes:
            for term in info_contain_terms:
                if term in class_element.text :
                    self.diagram.remove_class(class_element)
            for term in info_exact_terms:
                if class_element.text == term:
                    self.diagram.remove_class(class_element)

    def find_class_by_name(self, text):
        filtered = [element for element in self.diagram.classes if element.text == text]
        return filtered[0] if len(filtered) > 0 else None

    def find_class_by_node_text(self, text):
        filtered = [element for element in self.diagram.classes if element.node.text == text]
        return filtered[0] if len(filtered) > 0 else None

    def count_classes(self):
        for element in self.diagram.classes:
            count = self.requirement.text.count(element.text)
            element.count = count


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

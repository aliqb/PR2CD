from Diagram import DesignElement, RelationBase, ClassElement, ClassDiagram
from Requirement import Requirement
import re


class ClassDiagramExtractor:
    def __init__(self, requirement: Requirement):
        self.requirement = requirement
        self.diagram = ClassDiagram()
        self.attr_terms = ['اطلاعات', 'فیلد', 'ویژگی', 'اطلاعاتی']
        self.countable_dets = ['تعداد', 'چند', 'شمار', 'عدد']
        self.uncountable_dets = ['مقدار', 'میزان']
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

        self.modal_infinitives = ['توانستن', 'خواستن']

        self.frequency_threshold_precentage = 5

        self.info_contain_terms = self.attr_terms + [
            self.contain_word] + self.composition_nouns[
                                 0:2] + self.composition_parent_words
        self.info_exact_terms = self.category_words

    def extract_diagram(self):
        self.extract_class_names()
        self.extract_attributes()
        self.extract_relation_bases()
        self.extract_relations()
        self.extract_operations()
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
        self.remove_info_words()
        self.replace_category_words()
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
        self.add_nodes_to_classes(sentence, nodes)

    def extract_esnadi_class_names(self, sentence):
        root = sentence.find_root()
        verb = [node for node in sentence.nlp_nodes if node.is_esndai_verb()][0]
        if verb.text == 'است':
            return
        if root.tag == 'VERB':
            infinitive = sentence.find_full_infinitive(root)[0]
            if infinitive in self.modal_infinitives:
                roots = sentence.find_ccomps(root) + sentence.find_xcomps(root)
            else:
                return
        else:
            roots = [root] + sentence.find_conjuncts(root)
        self.add_nodes_to_classes(sentence, roots, False)

    def extract_hastan_class_names(self, sentence):
        root = sentence.find_root()
        if root.text == 'هست':
            return
        xcomps = sentence.find_xcomps(root)
        self.add_nodes_to_classes(sentence, xcomps, False)

    def add_nodes_to_classes(self, sentence, nodes, skip_adj=True):
        for node in nodes:
            tag = node.tag
            if not (tag.startswith('NOUN') or tag.startswith('PROPN')):
                continue
            names = sentence.find_seq_names(node, skip_adj)
            for name, name_nodes in names:

                same_class = self.find_class_by_name(name)
                if same_class is None:
                    # if self.word_compound_exist(name_nodes):
                    #     continue
                    self.diagram.add_class(ClassElement(name, node, sentence=sentence))
                else:
                    if not same_class.node.is_subject() and node.is_subject():
                        same_class.node = node

    # attributes
    def extract_attributes(self):
        sentences = self.requirement.sentences
        for sentence in sentences:
            self.extract_attr_have_rule(sentence)
            self.extract_attr_noun_noun_rule(sentence)
            self.extract_attr_verb_particle_rule(sentence)
            self.attr_term_related_to_rule(sentence)
            self.extract_info_subject_attr_rule(sentence)

    def extract_attr_have_rule(self, sentence):
        verbs = sentence.find_with_tag('VERB')
        have_verbs = [verb for verb in verbs if verb.lemma == 'داشت#دار']
        if have_verbs:
            for verb in have_verbs:
                self.extract_attr_have_verb_rule(sentence, verb)
        if 'دارا' in sentence.text:
            self.extract_attr_have_noun_rule(sentence)

    def extract_attr_have_verb_rule(self, sentence, verb):
        subjects = sentence.find_recursive_subject(verb)
        subject_result = [item for subject in subjects for item in sentence.find_seq_names(subject)]
        class_elements = []
        sentence_objects = sentence.find_objects(verb)
        for item in subject_result:
            name, name_nodes = item
            element = self.find_class_by_name(name)
            if element:
                class_elements.append(element)
            else:
                for term in self.attr_terms:
                    if name.endswith(term):
                        main_name = name[:-len(term)].strip()
                        element = self.find_class_by_name(main_name)
                        if element:
                            class_elements.append(element)
                            sentence_objects.append(name_nodes[-1])

        for obj in sentence_objects:
            if obj.lemma in self.attr_terms:
                self.add_attr_terms_modifiers(sentence, obj, class_elements)
                continue
            names = [name for name, linked_nodes in sentence.find_seq_names(obj)]
            for name in names:
                for element in class_elements:
                    self.add_attribute_to_class(element, name, obj)

    def extract_attr_have_noun_rule(self, sentence):
        subjects = sentence.find_subjects()
        subject_names = [name for subject in subjects for name, name_nodes in sentence.find_seq_names(subject)]
        class_elements = [element for element in self.diagram.classes if element.text in subject_names]
        have_noun_nodes = [node for node in sentence.nlp_nodes if
                           node.lemma is not None and node.lemma.startswith('دارا')]
        for node in have_noun_nodes:
            next_node = sentence.find_next_noun(node)
            nodes = [next_node] + sentence.find_conjuncts(next_node)
            for attr_node in nodes:
                if attr_node.lemma in self.attr_terms:
                    self.add_attr_terms_modifiers(sentence, attr_node, class_elements)
                    continue
                if any(term in attr_node.lemma for term in self.countable_dets):
                    self.add_attr_terms_modifiers(sentence, attr_node, class_elements, self.countable_dets[0])
                    continue
                if any(term in attr_node.lemma for term in self.uncountable_dets):
                    self.add_attr_terms_modifiers(sentence, attr_node, class_elements, self.uncountable_dets[0])
                    continue
                names = [name for name, attr_node in sentence.find_seq_names(attr_node)]
                for name in names:
                    for element in class_elements:
                        # if name == 'تعداد'
                        self.add_attribute_to_class(element, name, attr_node)

    def extract_attr_noun_noun_rule(self, sentence):
        nodes = sentence.nlp_nodes
        for node in nodes:
            if node.rel == 'nmod':
                head_node = sentence.find_node_by_address(node.head)
                if 'NOUN' not in head_node.tag or not sentence.are_together(head_node, node,
                                                                            True) or head_node.lemma in self.info_exact_terms:
                    continue
                nearest_head = head_node
                head_node = sentence.find_seq_first_head(node)
                node_names = sentence.find_seq_names(node)
                class_elements = [self.find_class_by_name(node_name) for node_name, linked_nodes in
                                  node_names]  #############
                for class_element in class_elements:
                    if class_element is not None:
                        if head_node.lemma in self.attr_terms:
                            if sentence.is_esnadi():
                                self.add_attr_esnadi_roots(sentence, class_element)
                                continue
                            # if sentence.is_hastan_masdar():
                            #     self.add_attr_hastan_xcomp(sentence, node, class_element)
                            self.add_attr_terms_modifiers(sentence, head_node, [class_element])
                            continue
                        if head_node.address != nearest_head.address:
                            names_result = [result for result in sentence.find_seq_names(head_node)]
                            names_result = [result for result in names_result if nearest_head.text in result[0]]
                            if len(names_result) > 0:
                                for item in names_result:
                                    if any(name_node.is_infinitive() for name_node in item[1]):
                                        continue
                                    name = item[0]
                                    # modifier_name = re.sub(rf'\b{re.escape(node.lemma)}\b', '', name).strip()
                                    self.add_attribute_to_class(class_element, name, head_node)
                                continue
                        self.add_attribute_to_class(class_element, nearest_head.lemma, head_node)
                        # new_head = head_node
                        # while new_head.rel == 'conj':
                        #     new_head = sentence.find_node_by_address(new_head.head)
                        #     self.add_attribute_to_class(class_element, new_head.lemma, new_head)

    def extract_attr_verb_particle_rule(self, sentence):
        compounds = sentence.find_compounds()
        root = sentence.find_root()
        compounds += sentence.find_xcomps(root) + sentence.find_ccomps(root)
        attr_compounds = list(set([node.text for node in compounds]) & set(self.attr_verb_particles))
        if len(attr_compounds) > 0:
            subjects = sentence.find_subjects()
            subject_names = [name for subject in subjects for name, name_nodes in sentence.find_seq_names(subject)]
            class_elements = [element for element in self.diagram.classes if element.text in subject_names]
            sentence_obliques = sentence.find_obliques()
            for obl in sentence_obliques:
                names = [name for name, linked_nodes in sentence.find_seq_names(obl)]
                for name in names:
                    for element in class_elements:
                        self.add_attribute_to_class(element, name, obl)

    def extract_info_subject_attr_rule(self, sentence):
        subjects = sentence.find_subjects()
        for subject in subjects:
            if any(term in subject.text for term in self.attr_terms):
                modifiers = sentence.find_noun_modifiers(subject)
                for node in modifiers:
                    names = [name for name, linked_nodes in sentence.find_seq_names(node)]
                    class_elements = [self.find_class_by_name(name) for name in names]
                    for element in class_elements:
                        if element is None:
                            continue
                        next_noun = sentence.find_next_noun(node)
                        attrs = [next_noun] + sentence.find_conjuncts(next_noun)
                        for attr in attrs:
                            attr_names = [name for name, linked_nodes in sentence.find_seq_names(attr)]

                            for attr_name in attr_names:
                                self.add_attribute_to_class(element, attr_name, attr)

    def attr_term_related_to_rule(self, sentence):
        related_term_nodes = sentence.find_node_by_text('مربوط') + sentence.find_node_by_text('مرتبط')
        related_term_nodes = [node for node in related_term_nodes if
                              node.rel == 'amod' and sentence.find_node_by_address(node.head).lemma in self.attr_terms]
        for node in related_term_nodes:
            obl_address = node.deps.get('obl:arg', None)
            if obl_address is not None:
                obl = sentence.find_node_by_address(obl_address[0])
                names = [name for name, linked_nodes in sentence.find_seq_names(obl)]
                class_elements = [self.find_class_by_name(name) for name in names]
                for class_element in class_elements:
                    if class_element is not None:
                        modifiers = sentence.find_noun_modifiers(obl)
                        for modifier in modifiers:
                            attr_names = [name for name, linked_nodes in sentence.find_seq_names(modifier)]

                            for attr_name in attr_names:
                                self.add_attribute_to_class(class_element, attr_name, modifier)

    def add_attr_terms_modifiers(self, sentence, node, class_elements, prefix=None):
        noun_modifiers = sentence.find_noun_modifiers(node)
        for noun in noun_modifiers:
            names = [name for name, linked_nodes in sentence.find_seq_names(noun)]
            for element in class_elements:
                for name in names:
                    if name != element.text:
                        if prefix:
                            name = f"{prefix} {name}"
                        self.add_attribute_to_class(element, name.strip(), noun)

    def add_attr_hastan_xcomp(self, sentence, node, class_element):
        xcomps = sentence.find_xcomps()
        for xcomp in xcomps:
            if xcomp.text != node.text:
                self.add_attribute_to_class(class_element, xcomp.text, xcomp)

    def add_attr_esnadi_roots(self, sentence, class_element):
        root = sentence.find_root()
        if root.lemma.startswith('دارا'):
            return
        conjuncts = sentence.find_conjuncts(root)
        conjuncts = [root] + conjuncts
        for conjunct in conjuncts:
            self.add_attribute_to_class(class_element, conjunct.text, conjunct)

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
                if verb.is_esndai_verb():
                    self.find_relation_base_from_esnadi_verbs(sentence, verb)

                elif 'هست' in verb.lemma:
                    self.find_relation_base_from_hastan(sentence, verb)
                else:
                    self.find_relation_base_from_normal_verb(sentence, verb)
            if ':' in sentence.text:
                self.find_list_relation_base(sentence)
            if self.contain_word in sentence.text:
                self.find_contain_relation_base(sentence)

    def find_relation_base_from_esnadi_verbs(self, sentence, verb):
        root = sentence.find_root()
        subjects = sentence.find_subjects(root)
        if root.tag == 'VERB':
            infinitives = sentence.find_full_infinitive(root)
            if any(infinitive in self.modal_infinitives for infinitive in infinitives):
                roots = sentence.find_ccomps(root) + sentence.find_xcomps(root)
            else:
                roots = [root] + sentence.find_conjuncts(root)
        else:
            roots = [root] + sentence.find_conjuncts(root)
        tag = 'ESNADI SINGLE' if verb.text == 'است' else 'ESNADI'
        self.add_relation_triples(subjects, [DesignElement(tag)], roots, sentence)

    def find_relation_base_from_hastan(self, sentence, verb):
        subjects = sentence.find_subjects(verb)
        xcomps = sentence.find_xcomps(verb)
        tag = 'ESNADI SINGLE' if verb.text == 'است' else 'ESNADI'

        self.add_relation_triples(subjects, [DesignElement(tag)], xcomps, sentence)

    def find_relation_base_from_normal_verb(self, sentence, verb):
        if verb.lemma != 'داشت#دار':
            infinitives = sentence.find_full_infinitive(verb)
            infinitive_elements = [DesignElement(infinitive, verb) for infinitive in infinitives if
                                   infinitive not in self.modal_infinitives]
            subjects = sentence.find_recursive_subject(verb)
            targets = sentence.find_recursive_objects(verb)
            if len(targets) == 0:
                targets = [obl for obl in sentence.find_obliques('arg') if obl.head == verb.address]
                if len(targets) == 0:
                    infinitive_related_part = [node for node in sentence.find_compounds() + sentence.find_xcomps(verb)
                                               if node.head == verb.address]
                    if len(infinitive_related_part) > 0:
                        for part in infinitive_related_part:
                            targets += [obl for obl in sentence.find_obliques('arg') if obl.head == part.address]

            self.add_relation_triples(subjects, infinitive_elements, targets, sentence)

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
        self.add_relation_triples(subjects, [DesignElement('LIST')], main_nodes, sentence, False)

    def find_contain_relation_base(self, sentence):
        contain_word_nodes = sentence.find_node_by_text(self.contain_word)
        if len(contain_word_nodes) == 0:
            return
        contain_word_node = contain_word_nodes[0]
        obl_addresses = contain_word_node.deps.get('obl:arg', None)
        obl_node = sentence.find_node_by_address(
            obl_addresses[0]) if obl_addresses is not None else sentence.find_next_noun(contain_word_node)
        if not obl_node:
            return
        subjects = sentence.find_subjects()
        nodes = [obl_node] + sentence.find_conjuncts(obl_node)
        self.add_relation_triples(subjects, [DesignElement('CONTAIN')], nodes, sentence)

    def add_relation_triples(self, source_nodes, infinitive_elements, target_nodes, sentence, skip_adj=True):
        source_classes = []
        for node in source_nodes:
            names = [name for name, name_nodes in sentence.find_seq_names(node)]
            for name in names:
                class_element = self.find_class_by_name(name)
                if not class_element:
                    if any(term in name for term in self.category_words):
                        pattern = r'\b(' + '|'.join(map(re.escape, self.category_words)) + r')\b'
                        raw_name = re.sub(pattern, '', name).strip()
                        if raw_name == '':
                            next_node = sentence.find_next_noun(node)
                            raw_name, next_nodes = sentence.find_seq_names(next_node)[0]
                        class_element = self.find_class_by_name(raw_name)
                if not class_element:
                    continue
                source_classes.append(class_element)

        # source_names = [name for source in source_nodes for name, name_nodes in sentence.find_seq_names(source)]
        # source_classes = [element for element in self.diagram.classes if element.text in source_names]
        # if len(source_classes) == 0:
        #     for name in source_names:
        #         raw_name = ''
        #         for term in self.category_words:
        #             if term in name:
        #                 raw_name = re.sub(rf'\b{re.escape(term)}\b', '', name).strip()
        #         if raw_name:
        #             source_class = self.find_class_by_name(raw_name)
        #             if not source_class:
        #                 return
        #             source_classes.append(source_class)
        if len(target_nodes) == 0:
            for subject_class in source_classes:
                for infinitive_node in infinitive_elements:
                    self.diagram.add_base_relation(RelationBase(subject_class, infinitive_node, None, sentence))
        else:
            for subject_class in source_classes:
                for node in target_nodes:
                    names = [name for name, linked_nodes in sentence.find_seq_names(node, skip_adj)]
                    for name in names:
                        target_class = self.find_class_by_name(name)

                        for infinitive_node in infinitive_elements:
                            self.diagram.add_base_relation(
                                RelationBase(subject_class, infinitive_node, target_class, sentence, node))

    # generalizations
    def extract_generalizations(self):
        for relation in self.diagram.base_relations:
            if relation.is_esnadi():
                self.extract_generalizations_from_esnadi(relation)
            if relation.relation_title.text == 'LIST':
                self.extract_generalization_from_list(relation)
            if any(term in relation.relation_title.text for term in self.categorizing_words):
                self.extract_generalization_categorization(relation)
            if any(term == relation.relation_title.text for term in self.complex_categorizing_words) and any(
                    term in relation.sentence.text for term in self.category_words):
                self.extract_generalization_categorization(relation)

    def extract_generalizations_from_esnadi(self, relation):
        if relation.is_single_esnadi():
            base_source = relation.target
            base_target = relation.source
        else:
            base_source = relation.source
            base_target = relation.target
        if relation.target_node is not None and any(
                term in relation.target_node.text for term in self.composition_nouns):
            return
        if base_target is not None and base_source is not None:
            self.diagram.add_generalization(base_target, base_source, relation)

    def extract_generalization_from_list(self, relation):
        parent = relation.source
        child = relation.target
        if child is None:
            node = relation.target_node
            names = [name for name, linked_nodes in relation.sentence.find_seq_names(node, False)]
            for name in names:
                child = ClassElement(name, node, sentence=relation.sentence)
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
            names = [name for name, linked_nodes in relation.sentence.find_seq_names(node, False)]
            for name in names:
                class_element = self.find_class_by_name(name)
                if class_element is None:
                    class_element = ClassElement(name, node, sentence=relation.sentence)
                    self.diagram.add_class(class_element)
                self.diagram.add_generalization(class_element, relation.source, relation)

    # aggregations
    def extract_aggregations(self):
        for relation in self.diagram.base_relations:
            if relation.relation_title.text == 'CONTAIN' or self.contain_word in relation.relation_title.text:
                self.extract_aggregations_from_contain(relation)

    def extract_aggregations_from_contain(self, relation):
        whole = relation.source
        part = relation.target
        if part is not None:
            self.diagram.add_aggregation(part, whole, relation)
        else:
            target_node = relation.target_node
            if target_node.lemma in self.attr_terms:
                self.add_attr_terms_modifiers(relation.sentence, target_node, [whole])
                return
            names = [name for name, linked_nodes in relation.sentence.find_seq_names(target_node)]
            for name in names:
                attr_name = re.sub(rf'\b{re.escape(whole.text)}\b', '', name).strip()
                self.add_attribute_to_class(whole, attr_name, target_node)

    # composition
    def extract_composition(self):
        for relation in self.diagram.base_relations:
            if any(term in relation.relation_title.text for term in self.composition_verb_particles):
                self.extract_composition_from_composition_verbs(relation)
            if relation.is_esnadi():
                if any(term in relation.target_node.text for term in self.composition_verb_particles):
                    self.extract_composition_from_composition_verbs(relation)
                else:
                    self.extract_composition_from_esnadi(relation)

    def extract_composition_from_composition_verbs(self, relation):
        if relation.target is None or (relation.target_node and not relation.target_node.is_obj()):
            self.find_composition_from_passive_composition_verb(relation)
        else:
            self.find_composition_from_active_composition_verb(relation)

    def find_composition_from_passive_composition_verb(self, relation):
        preposition_nodes = relation.sentence.find_node_by_text('از')
        if len(preposition_nodes) == 0:
            return
        preposition_node = preposition_nodes[0]
        next_node = relation.sentence.find_next_noun(preposition_node)
        nodes = [next_node] + relation.sentence.find_conjuncts(next_node)
        for node in nodes:
            names = [name for name, linked_nodes in relation.sentence.find_seq_names(node)]

            for name in names:
                child = self.find_class_by_name(name)

                if child is None:
                    child = ClassElement(name, node, sentence=relation.sentence)
                    self.diagram.add_class(child)
                self.diagram.add_composition(child, relation.source, relation)
                # self.add_attribute_to_class(relation.source, name, node)

    def find_composition_from_active_composition_verb(self, relation):
        # if 'ساختن' in relation.relation_title.text:
        #     return
        subjects = relation.sentence.find_subjects(relation.relation_title.node)
        if len(subjects) <= 1:
            return
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
            base_node = preposition_node

        else:
            base_node = composition_node
        next_node = relation.sentence.find_next_noun(base_node)
        if any(term in next_node.text for term in self.composition_parent_words):
            next_node = relation.sentence.find_node_by_address(next_node.address + 1)
        nodes = [next_node] + relation.sentence.find_conjuncts(next_node)
        for node in nodes:
            names = [name for name, linked_nodes in relation.sentence.find_seq_names(node)]

            for name in names:
                parent = self.find_class_by_name(name)
                if parent is not None:
                    self.diagram.add_composition(relation.source, parent, relation)

    # ASSOCIATION
    def extract_associations(self):
        for relation in self.diagram.base_relations:
            if self.diagram.relation_with_base_exist(relation) or relation.target is None or self.is_weak_class(
                    relation.target):
                continue
            self.diagram.add_association(relation.source, relation.target, relation, relation.relation_title.text)

    # operations
    def extract_operations(self):
        relations = [relation for relation in self.diagram.base_relations if
                     relation.relation_title.text not in ['ESNADI', 'ESNADI SINGLE', 'LIST', 'CONTAIN']]
        terms = self.categorizing_words + self.complex_categorizing_words + self.composition_verb_particles + self.attr_verb_particles
        for relation in relations:
            title = relation.relation_title
            if any(term in title.text for term in terms):
                continue
            target = relation.target
            source = relation.source

            target_node = relation.target_node
            sentence = relation.sentence
            if target is None:
                if target_node:
                    result = sentence.find_seq_names(target_node)
                    if target_node.is_obj():
                        for item in result:
                            name, name_nodes = item

                            names = [node.text for node in name_nodes]
                            ending_target = self.add_ending_target_association(source, relation, names)
                            if not ending_target:
                                source.add_operation(f"{title} {name}", relation.target_node)
                    else:
                        case = sentence.find_case(target_node)
                        if case:
                            for item in result:
                                name, name_nodes = item
                                source.add_operation(f"{title.text} {case.text} {name}", target_node)
                else:
                    source.add_operation(title.text, title.node)
                continue
            if self.is_weak_class(target):
                names = target.text.split(" ")
                ending_target = self.add_ending_target_association(source, relation, names)
                if not ending_target:
                    source.add_operation(f"{title.text} {target.text}", title.node)
                # self.add_operation_or_association(source, relation)

    def add_ending_target_association(self, class_element, relation, names):
        target_name = ''
        for index in range(len(names) - 1, -1, -1):
            end_name = names[index]
            target_name = end_name if target_name == '' else f"{end_name} {target_name}"
            target = self.find_class_by_name(target_name)
            if target and not self.is_weak_class(target):
                text = f"{relation.relation_title.text} {''.join(names[:index])}"
                self.diagram.add_association(class_element, target, relation, text)
                return target
        return None

    # post
    def post_process(self):
        self.post_process_classes()
        self.post_process_attributes()
        self.post_process_relations()
        self.post_process_operations()

    def post_process_classes(self):
        # self.remove_info_words()
        # self.replace_category_words()
        self.remove_bigger_classes()
        # self.merge_classes()
        self.remove_weak_classes()

    def post_process_attributes(self):
        self.convert_same_start_attributes_to_class()
        # self.remove_generalized_attribute()
        self.convert_whole_part_attributes()

    def post_process_operations(self):
        self.remove_passive_operations()
        self.merge_same_start_operations()
        # self.remove_generalized_operations()

    def post_process_relations(self):
        self.same_end_to_composition()
        self.remove_generalized_items()

    def remove_info_words(self):
        for class_element in self.diagram.classes:
            for term in self.info_contain_terms:
                text = class_element.text
                if term in text:
                    if term == text:
                        self.diagram.remove_class(class_element)
                    elif text.endswith(term) and term != text:
                        short_text = re.sub(rf'\b{re.escape(term)}\b', '', text).strip()
                        short_class = self.find_class_by_name(short_text)
                        if short_class:
                            self.diagram.remove_class(class_element)
                    elif text.startswith(term):
                        self.diagram.remove_class(class_element)

            # for term in info_exact_terms:
            #     if class_element.text == term:
            #         self.diagram.remove_class(class_element)

    def replace_category_words(self):
        for class_element in self.diagram.classes:
            for term in self.category_words:
                if class_element.text == term:
                    node = class_element.node
                    next_node = class_element.sentence.find_next_noun(node)
                    if next_node:
                        name, name_nodes = class_element.sentence.find_seq_names(next_node)[0]
                        main_class = self.find_class_by_name(name)
                        if main_class:
                            self.diagram.merge_classes([main_class, class_element], main_class.text)
                        else:
                            class_element.text = name
                            class_element.node = next_node
                elif term in class_element.text:
                    text = re.sub(rf'\b{re.escape(term)}\b', '', class_element.text).strip()
                    main_class = self.find_class_by_name(text)
                    if main_class:
                        self.diagram.merge_classes([main_class, class_element], main_class.text)

    def remove_bigger_classes(self):
        for element in self.diagram.classes:
            if self.shorter_class_exist_before(element):
                if len(element.attributes) == 0 and len(element.operations) == 0:
                    self.diagram.remove_class(element)

    def shorter_class_exist_before(self, class_element):
        class_sorted_sentence = list(sorted(self.diagram.classes, key=lambda x: x.sentence.index))
        words = class_element.text.split(' ')
        compound = ''
        for word in reversed(words):
            if compound == '':
                compound = word
            else:
                compound = f"{word} {compound}"
            found_class = self.find_class_by_name(compound)
            if found_class:
                if found_class.sentence.index < class_element.sentence.index:
                    return True
                elif found_class.sentence.index == class_element.sentence.index:
                    if found_class.node.address < class_element.node.address:
                        return True
        return False
        # for element in class_sorted_sentence:
        #     if element.sentence.index >= class_element.index:
        #         return False

    def remove_weak_classes(self):
        for element in self.diagram.classes:
            if self.is_weak_class(element):
                self.diagram.remove_class(element)

    def remove_generalized_attribute(self, relation):
        source = relation.source
        target = relation.target
        target_attributes = target.attributes
        if not target_attributes:
            return
        for attribute in source.attributes:
            if attribute.text == target.text:
                source.remove_attribute(attribute.text)
                return
            if any(attribute.text == target_attribute.text for target_attribute in target_attributes):
                source.remove_attribute(attribute.text)

    def convert_whole_part_attributes(self):
        for element in self.diagram.classes:
            for attribute in element.attributes:
                part_class = self.find_class_by_name(attribute.text)
                if part_class:
                    compound_name = f"{attribute.text} {element.text}"
                    bigger_class = self.find_class_by_name(compound_name)
                    if not bigger_class and not self.diagram.relation_between_exist(element, part_class, True):
                        self.diagram.add_aggregation(part_class, element, None)
                    element.remove_attribute(attribute.text)

    def convert_same_start_attributes_to_class(self):
        for element in self.diagram.classes:
            same_starts = self.find_items_with_same_start(element.attributes, 1)

            for start, attributes in same_starts.items():
                parent_class = self.find_class_by_name(start)
                if not parent_class:
                    continue
                for attribute in attributes:
                    part_class_name = re.sub(rf'\b{re.escape(start)}\b', '', attribute.text).strip()
                    part_class = self.find_class_by_name(part_class_name)
                    if not part_class:
                        part_class = ClassElement(part_class_name, attribute.node)
                        self.diagram.add_class(part_class)
                    element.remove_attribute(attribute)
                    self.diagram.add_generalization(part_class, parent_class, None)
                self.diagram.add_aggregation(parent_class, element, None)

    def remove_passive_operations(self):
        for element in self.diagram.classes:
            for operation in element.operations:
                if operation.text.endswith('شدن'):
                    element.remove_operation(operation.text)

    def merge_same_start_operations(self):
        for element in self.diagram.classes:
            same_starts = self.find_items_with_same_start(element.operations, 1)
            for start, operations in same_starts.items():
                sorted_operations = sorted(operations, key=lambda x: x.text)
                shortest_operation = sorted_operations[0]
                for operation in operations:
                    if operation.text != shortest_operation.text and operation.text.startswith(shortest_operation.text):
                        element.remove_operation(operation.text)

    def remove_generalized_operations(self, relation):
        source = relation.source
        target = relation.target
        target_operations = target.operations
        if not target_operations:
            return
        for operation in source.operations:
            if any(operation.text == target_operation.text for target_operation in target_operations):
                source.remove_operation(operation.text)

    def find_class_by_name(self, text):
        filtered = [element for element in self.diagram.classes if element.text == text]
        return filtered[0] if len(filtered) > 0 else None

    def word_compound_exist(self, nodes):
        compound = ''
        for node in reversed(nodes):
            if compound == '':
                class_element = self.find_class_by_name(node.lemma)
                compound = node.text
            else:
                compound = f"{node.text}{' ' if compound != '' else ''}{compound}"
                class_element = self.find_class_by_name(compound)
            if class_element is not None:
                return True
        return False

    def find_class_by_node_text(self, text):
        filtered = [element for element in self.diagram.classes if element.node.text == text]
        return filtered[0] if len(filtered) > 0 else None

    def merge_classes(self):
        same_endings = self.find_class_with_same_ending(1)
        while len(same_endings.items()):
            for ending, classes in same_endings.items():
                self.diagram.merge_classes(classes, ending)
            same_endings = self.find_class_with_same_ending(1)

    def find_class_with_same_ending(self, num_words):
        # Create a dictionary to store strings with the same ending words
        endings_dict = {}
        for class_element in self.diagram.classes:
            # if self.diagram.any_relation_by_class(
            #         class_element):
            #     continue
            # Split the string into words

            words = class_element.text.split()
            if len(words) >= num_words:  # Ensure the string has enough words
                # Get the last 'num_words' words
                last_words = ' '.join(words[-num_words:])

                # Add the string to the dictionary based on its last words
                if last_words in endings_dict:
                    endings_dict[last_words].append(class_element)
                else:
                    endings_dict[last_words] = [class_element]

        # Filter out groups that have more than one string with the same ending
        result = {k: v for k, v in endings_dict.items() if len(v) > 1}

        return result

    def find_items_with_same_start(self, items, num_words):
        # Create a dictionary to store strings with the same ending words
        beginning_dict = {}
        for attribute in items:
            # Split the string into words

            words = attribute.text.split()
            if len(words) > num_words:  # Ensure the string has enough words
                # Get the last 'num_words' words
                first_words = ' '.join(words[:num_words])

                # Add the string to the dictionary based on its last words
                if first_words in beginning_dict:
                    beginning_dict[first_words].append(attribute)
                else:
                    beginning_dict[first_words] = [attribute]

        # Filter out groups that have more than one string with the same ending
        result = {k: v for k, v in beginning_dict.items() if len(v) > 1}

        return result

    def remove_generalized_items(self):
        generalizations = self.diagram.get_generalizations()
        for generalization in generalizations:
            self.remove_generalized_attribute(generalization)
            self.remove_generalized_operations(generalization)
            self.remove_generalized_relations(generalization)

    def same_end_to_composition(self):
        same_endings = self.find_class_with_same_ending(1)
        for ending, classes in same_endings.items():
            short_classes = [element for element in classes if element.text == ending]
            if short_classes:
                whole_class = short_classes[0]
                part_classes = [element for element in classes if element.text != ending]
                for element in part_classes:
                    without_end_name = re.sub(rf'\b{re.escape(ending)}\b', '', element.text).strip()
                    if not self.find_class_by_name(without_end_name):
                        whole_class.remove_attribute(without_end_name)
                        self.diagram.add_composition(element, whole_class, None)

    def remove_generalized_relations(self, relation):
        child = relation.source
        parent = relation.target
        child_relations = self.diagram.get_relations_of_class(child)
        for child_relation in child_relations:
            source = child_relation.source
            target = child_relation.target
            if source.text == child.text:
                if self.diagram.relation_between_exist(parent, target, False):
                    self.diagram.remove_relation(child_relation)
            else:
                if self.diagram.relation_between_exist(source, parent, False):
                    self.diagram.remove_relation(child_relation)

    def count_classes(self):
        names = []
        for sentence in self.requirement.sentences:
            for node in sentence.nlp_nodes:
                if node.tag.startswith('NOUN'):
                    names += [name for name, name_nodes in sentence.find_seq_names(node)]
        unique_names = set(names)
        n = len(unique_names)
        for element in self.diagram.classes:
            count = len([name for name in names if name == element.text])
            element.count = count
            element.frequency = count / n

    def is_weak_class(self, class_element):
        if not class_element.is_candidate():
            return False
        if self.diagram.any_no_association_relation_by_class(
                class_element):
            return False
        if len(class_element.attributes) > 0 or len(class_element.operations) > 0:
            return False
        return True

    def add_attribute_to_class(self, class_element, text, node):
        # if text in self.info_exact_terms:
        #     return
        if any(term in text for term in self.info_contain_terms + self.categorizing_words):
            return
        if node.is_infinitive():
            return
        attr_name = re.sub(rf'\b{class_element.text}\b', '', text).strip()
        attr_name = re.sub(rf'\bمورد\b', '', attr_name).strip()
        if attr_name == '':
            return
        class_element.add_attribute(attr_name, node)


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

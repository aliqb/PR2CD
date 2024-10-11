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
                if self.target_node.text != other.target_node.text or self.target_node.address != other.target_node.address:
                    return False
                return self.sentence.text == other.sentence.text

            # If 'target' is not None, return True since the 'target' comparison passed
            return True
        return False


class Relation:
    def __init__(self, source, relation_type, target, base=None, label=None):
        self.source = source
        self.relation_type = relation_type
        self.target = target
        self.label = label
        self.base = base

    def __eq__(self, other):
        return self.source == other.source and self.target == other.target and self.relation_type == other.relation_type and self.label == other.label


class ClassElement(DesignElement):
    def __init__(self, text, node=None, attributes=None, operations=None, sentence=None):
        super().__init__(text, node)
        self.attributes = []
        self.operations = []
        self.sentence = sentence
        self._count = 0
        self._frequency = 0
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

    def is_candidate(self):
        if self.node is None:
            return True
        if self.node.is_obj():
            return True
        return False

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, new_count):
        self._count = new_count

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, new_frequency):
        self._frequency = new_frequency


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
        new_relations = []
        for relation in self.relations:
            if relation.source.text != class_element.text and relation.target.text != class_element.text:
                new_relations.append(relation)
            else:
                if relation.relation_type == 'ASSOCIATION':
                    self.convert_association_to_operation(relation)
        self.relations = [relation for relation in self.relations if
                          relation.source.text != class_element.text and relation.target.text != class_element.text]

    def convert_association_to_operation(self, relation):
        target = relation.target
        source = relation.source
        title = relation.base.relation_title
        source.add_operation(f"{title.text} {target.text}", title.node)

    def merge_classes(self, classes, text):
        attrs = []
        short_class_list = [element for element in self.classes if element.text == text]
        subj_nodes = [element.node for element in classes if element.node.is_subject()]
        if subj_nodes:
            node = subj_nodes[0]
        else:
            node = classes[0].node

        if short_class_list:
            new_class = short_class_list[0]
            new_class.node = node
        else:
            new_class = ClassElement(text, node)
            self.add_class(new_class)
        for element in classes:
            for relation in self.relations:
                if relation.source.text == element.text:
                    relation.source = new_class
                if relation.target and relation.target.text == element.text:
                    relation.target = new_class
            if element.text != text:
                attrs += element.attributes
                if text in element.text:
                    new_attr_text = re.sub(rf'\b{re.escape(text)}\b', '', element.text).strip()
                    attrs.append(DesignElement(new_attr_text, element.node))
                self.remove_class(element)
        for attr in attrs:
            new_class.add_attribute(attr.text, attr.node)

    def add_base_relation(self, relation):
        if not self.base_relation_exist(relation):
            self.base_relations.append(relation)

    def base_relation_exist(self, input_relation):
        return any(input_relation == relation for relation in self.base_relations)

    def relation_exist(self, input_relation):
        return any(input_relation == relation for relation in self.relations)

    def relation_with_base_exist(self, base_relation):
        return any(base_relation == relation.base for relation in self.relations)

    def any_relation_by_class(self, class_element):
        return any(
            class_element.text == relation.source.text or class_element.text == relation.target.text for relation in
            self.relations)

    def any_no_association_relation_by_class(self, class_element):
        return any(
            class_element.text == relation.source.text or class_element.text == relation.target.text for relation in
            self.relations if relation.relation_type != 'ASSOCIATION')

    def add_generalization(self, child, parent, base):
        relation = Relation(child, 'GENERALIZATION', parent, base)
        if not self.relation_exist(relation):
            self.relations.append(relation)

    def get_generalizations(self):
        return [relation for relation in self.relations if relation.relation_type == 'GENERALIZATION']

    def add_aggregation(self, child, parent, base):
        relation = Relation(child, 'AGGREGATION', parent, base)
        if not self.relation_exist(relation):
            self.relations.append(relation)

    def get_aggregations(self):
        return [relation for relation in self.relations if relation.relation_type == 'AGGREGATION']

    def add_composition(self, child, parent, base):
        relation = Relation(child, 'COMPOSITION', parent, base)
        if not self.relation_exist(relation):
            self.relations.append(relation)

    def get_compositions(self):
        return [relation for relation in self.relations if relation.relation_type == 'COMPOSITION']

    def add_association(self, source, target, base):
        relation = Relation(source, 'ASSOCIATION', target, base, base.relation_title.text)
        if not self.relation_exist(relation):
            self.relations.append(relation)

    def get_associations(self):
        return [relation for relation in self.relations if relation.relation_type == 'ASSOCIATION']

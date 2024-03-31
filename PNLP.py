from typing import List, Literal
from hazm import Normalizer, SentenceTokenizer, WordTokenizer, Lemmatizer, POSTagger, DependencyParser


class NLPNode:
    def __init__(self, address: int, text: str, tag: str, rel: str, lemma: str, head: int, deps: dict):
        self.deps = deps
        self.head = head
        self.lemma = lemma
        self.rel = rel
        self.tag = tag
        self.text = text
        self.address = address


class Sentence:
    def __init__(self, text, nlp_nodes: List[NLPNode], find_seq_method: Literal['dep', 'ezafe'] = 'dep',
                 with_ezafe_tag: bool = False):
        self.with_ezafe_tag = with_ezafe_tag
        self.text = text
        self.nlp_nodes = nlp_nodes
        self.find_seq_method = find_seq_method

    def find_node_by_address(self, address):
        filtered = [node for node in self.nlp_nodes if node.address == address]
        if len(filtered) > 0:
            return filtered[0]
        return None

    def find_seq_name(self, node):
        if self.find_seq_method == 'dep':
            return self.find_seq_dependency_name(node)
        if self.with_ezafe_tag:
            raise Exception('with_ezafe_tag is false')
        return self.find_ezafe_name(node)

    def find_seq_dependency_name(self, node):
        seq_dependencies = ['amod', 'nmod', 'flat']
        addresses = []
        ezafe = node.tag.endswith('EZ')
        name = node.lemma
        deps_with_main_tag = {dep.split(':')[0]: dep for dep in node.deps}
        if ezafe or not self.with_ezafe_tag:
            for dep in seq_dependencies:

                if dep in deps_with_main_tag:
                    addresses += node.deps[deps_with_main_tag[dep]]
            for address in addresses:
                next_node = self.find_node_by_address(address)
                middle_ezafe = next_node.tag.endswith('EZ')
                name += ' ' + next_node.text
                if not middle_ezafe and self.with_ezafe_tag:
                    break
        return name

    def find_ezafe_name(self, node):
        ezafe = node.tag.endswith('EZ')
        # if name.endswith('ه') and ezafe:
        #     name += "‌ی"
        name = node.lemma
        address = node.address
        while ezafe:
            next_address = address + 1
            next_node = self.find_node_by_address(next_address)
            name += ' ' + next_node.text
            ezafe = next_node.tag.endswith('EZ')
            address = next_node.address
        return name


class HazmExtractor:
    def __init__(self, parser, lemmatizer, with_ezafe_tag:bool=False):
        self.with_ezafe_tag = with_ezafe_tag
        self.lemmatizer = lemmatizer
        self.parser = parser


    def extract(self, text: str):
        normalizer = Normalizer()
        sentence_tokenizer = SentenceTokenizer()
        word_tokenizer = WordTokenizer()
        # parser = DependencyParser(tagger=POSTagger(model='pos_tagger.model'), lemmatizer=lemmatizer)
        text = normalizer.normalize(text)
        raw_sentences = [sentence[:-1] for sentence in sentence_tokenizer.tokenize(text)]
        sentences = []
        for sentence in raw_sentences:
            hazm_nodes = (self.parser.parse(word_tokenizer.tokenize(sentence))).nodes
            nodes = []
            for node in hazm_nodes.values():
                tag = node['tag']
                lemma = node['lemma']
                if tag == 'VERB':
                    node['lemma'] = self.lemmatizer.lemmatize(lemma, 'V')
                nodes.append(
                    NLPNode(address=node['address'], text=node['word'], tag=tag, rel=node['rel'], head=node['head'],
                            deps=node['deps'], lemma=lemma))
            sentences.append(Sentence(sentence, nodes,with_ezafe_tag=self.with_ezafe_tag))

        return sentences

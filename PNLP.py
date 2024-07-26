from typing import List, Literal
from hazm import Normalizer, SentenceTokenizer, WordTokenizer, Lemmatizer, POSTagger, DependencyParser
import stanza


class NLPNode:
    def __init__(self, address: int, text: str, tag: str, rel: str, lemma: str, head: int, deps: dict):
        self.deps = deps
        self.head = head
        self.lemma = lemma
        self.rel = rel
        self.tag = tag
        self.text = text
        self.address = address

    def __str__(self):
        return f"{self.address}, {self.text}, rel:{self.rel}, head:{self.head}, tag:{self.tag}"


class Sentence:
    def __init__(self, text, nlp_nodes: List[NLPNode], find_seq_method: Literal['dep', 'ezafe'] = 'dep',
                 with_ezafe_tag: bool = False):
        self.with_ezafe_tag = with_ezafe_tag
        self.text = text
        self.nlp_nodes = sorted(nlp_nodes, key=lambda x: x.address)
        self.find_seq_method = find_seq_method

    def find_node_by_address(self, address):
        filtered = [node for node in self.nlp_nodes if node.address == address]
        if len(filtered) > 0:
            return filtered[0]
        return None

    def find_seq_name(self, node):
        if self.find_seq_method == 'dep':
            return self.find_seq_dependency_name(node)
        if not self.with_ezafe_tag:
            raise Exception('with_ezafe_tag is false')
        return self.find_ezafe_name(node)

    def find_dependent_nodes(self, node):
        seq_dependencies = ['amod', 'nmod', 'flat']
        # addresses = []
        nodes = []
        deps_with_main_tag = {dep.split(':')[0]: dep for dep in node.deps}
        for dep in seq_dependencies:

            if dep in deps_with_main_tag:
                addresses = node.deps[deps_with_main_tag[dep]]
                nodes += [self.find_node_by_address(address) for address in addresses]
        all_nodes = nodes.copy()
        for node in nodes:
            all_nodes += self.find_dependent_nodes(node)
        return all_nodes

    def find_seq_dependency_name(self, node):
        name = node.lemma
        dep_nodes = [node for node in self.find_dependent_nodes(node) if node.tag != 'PRON']
        dep_nodes.sort(key=lambda n: n.address)
        is_seq_root = node.tag.endswith('EZ') if self.with_ezafe_tag else (
                len(dep_nodes) and node.address + 1 == dep_nodes[0].address)

        if is_seq_root:
            for index in range(len(dep_nodes)):
                dep_node = dep_nodes[index]
                name += ' ' + dep_node.text
                middle_ezafe = dep_node.tag.endswith('EZ')
                must_break = not middle_ezafe if self.with_ezafe_tag else (
                        index != len(dep_nodes) - 1 and dep_node.address + 1 != dep_nodes[index + 1].address)
                if must_break:
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
    def __init__(self, parser, lemmatizer, with_ezafe_tag: bool = False,
                 find_seq_method: Literal['dep', 'ezafe'] = 'dep'):
        self.find_seq_method = find_seq_method
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
            sentences.append(
                Sentence(sentence, nodes, with_ezafe_tag=self.with_ezafe_tag, find_seq_method=self.find_seq_method))

        return sentences


class StanzaExtractor:
    def __init__(self):
        self.pipline = stanza.Pipeline(lang='fa', processors='tokenize,mwt,pos,lemma,depparse')

    def extract(self, text):
        doc = self.pipline(text)
        return [Sentence(stanza_sentence.text, self.get_sentence_nodes(stanza_sentence)) for stanza_sentence in
                doc.sentences]

    def get_sentence_nodes(self, sentence):
        nodes = []
        for word in sentence.words:
            nodes.append(
                NLPNode(address=word.id, text=word.text, tag=word.pos, rel=word.deprel, head=word.head,
                        deps=self.find_word_deps(sentence, word), lemma=word.lemma))
        return nodes

    def find_word_deps(self, sentence, word):
        deps = {}
        for head, rel, dep in sentence.dependencies:
            if head.id == word.id:
                if rel in deps:
                    deps[rel].append(dep.id)
                else:
                    deps[rel] = [dep.id]

        return deps

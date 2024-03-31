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
    def __init__(self, text, nlp_nodes: List[NLPNode], find_seq_method: Literal['dep', 'ezafe'] = 'dep'):
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
        return self.find_ezafe_name(node)

    def find_seq_dependency_name(self, node):
        seq_dependencies = ['amod', 'nmod', 'flat']
        addresses = []
        ezafe = node.tag.endswith('EZ')
        name = node.lemma
        if ezafe:
            for dep in seq_dependencies:
                if dep in node.deps:
                    addresses += node.deps[dep]
            for address in addresses:
                next_node = self.find_node_by_address(address)
                middle_ezafe = next_node.tag.endswith('EZ')
                name += ' ' + next_node.text
                if not middle_ezafe:
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


def hazm_extractor(text: str):
    normalizer = Normalizer()
    sentence_tokenizer = SentenceTokenizer()
    word_tokenizer = WordTokenizer()
    lemmatizer = Lemmatizer()
    parser = DependencyParser(tagger=POSTagger(model='pos_tagger.model'), lemmatizer=Lemmatizer())
    text = normalizer.normalize(text)
    raw_sentences = [sentence[:-1] for sentence in sentence_tokenizer.tokenize(text)]
    sentences = []
    for sentence in raw_sentences:
        hazm_nodes = (parser.parse(word_tokenizer.tokenize(sentence))).nodes
        nodes = []
        for node in hazm_nodes.values():
            tag = node['tag']
            lemma = node['lemma']
            if tag == 'VERB':
                node['lemma'] = lemmatizer.lemmatize(lemma, 'V')
            nodes.append(
                NLPNode(address=node['address'], text=node['word'], tag=tag, rel=node['rel'], head=node['head'],
                        deps=node['deps'], lemma=lemma))
        sentences.append(Sentence(sentence, nodes))

    return sentences

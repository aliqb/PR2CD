import re
from typing import Literal

import stanza
from hazm import Normalizer, SentenceTokenizer, WordTokenizer

from PNLP import NLPNode, Sentence


class HazmExtractor:
    def __init__(self, parser, lemmatizer, with_ezafe_tag: bool = False,
                 find_seq_method: Literal['dep', 'ezafe'] = 'dep'):
        self.find_seq_method = find_seq_method
        self.with_ezafe_tag = with_ezafe_tag
        self.lemmatizer = lemmatizer
        self.parser = parser

    def replace_words(self, text, words_to_replace, replacement_word):
        pattern = r'\b(' + '|'.join(map(re.escape, words_to_replace)) + r')\b'
        return re.sub(pattern, replacement_word, text)

    def text_preprocess(self, text):
        normalizer = Normalizer()
        text = normalizer.normalize(text)
        example_terms = [
            "نظیر",
            "همانند",
            "هم‌مانند",
            "از قبیل",
            "مثل",
            "از جمله"
        ]
        text = self.replace_words(text, example_terms, 'مانند')
        text = re.sub(r'(["\'«»\(\)])(.*?)(["\'«»\(\)])', '', text)
        return text

    def extract(self, text: str):
        sentence_tokenizer = SentenceTokenizer()
        word_tokenizer = WordTokenizer()
        final_text = self.text_preprocess(text)
        raw_sentences = [sentence[:-1] for sentence in sentence_tokenizer.tokenize(final_text)]
        sentences = []
        for index in range(len(raw_sentences)):
            sentence = raw_sentences[index]
            hazm_nodes = (self.parser.parse(word_tokenizer.tokenize(sentence))).nodes
            nodes = []
            for node in hazm_nodes.values():
                tag = node['tag']
                lemma = node['lemma']
                if tag == 'VERB':
                    spaced_replaced = re.sub(r"‌", " ", lemma)
                    node['lemma'] = self.lemmatizer.lemmatize(spaced_replaced, 'VERB')
                nodes.append(
                    NLPNode(address=node['address'], text=node['word'], tag=tag, rel=node['rel'], head=node['head'],
                            deps=node['deps'], lemma=node['lemma']))
            sentences.append(
                Sentence(index, sentence, nodes, with_ezafe_tag=self.with_ezafe_tag,
                         find_seq_method=self.find_seq_method))

        return sentences


class StanzaExtractor:
    def __init__(self):
        self.pipline = stanza.Pipeline(lang='fa', processors='tokenize,mwt,pos,lemma,depparse')

    # def replace_words(self, text, words_to_replace, replacement_word):
    #     pattern = r'\b(' + '|'.join(map(re.escape, words_to_replace)) + r')\b'
    #     return re.sub(pattern, replacement_word, text)
    #
    # def text_preprocess(self, text):
    #     normalizer = Normalizer()
    #     text = normalizer.normalize(text)
    #     example_terms = [
    #         "نظیر",
    #         "همانند",
    #         "هم‌مانند",
    #         "از قبیل",
    #         "مثل",
    #         "از جمله"
    #     ]
    #     text = self.replace_words(text, example_terms, 'مانند')
    #     text = re.sub(r'(["\'«»\(\)])(.*?)(["\'«»\(\)])', '', text)
    #     return text

    def extract(self, text):
        doc = self.pipline(text)
        return [Sentence(index, stanza_sentence.text, self.get_sentence_nodes(stanza_sentence)) for
                index, stanza_sentence in
                enumerate(doc.sentences)]

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
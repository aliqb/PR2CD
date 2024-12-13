from hazm import Normalizer, SentenceTokenizer, WordTokenizer, Lemmatizer, POSTagger, DependencyParser
from PNLP import Sentence, NLPNode
from typing import List


class Requirement:
    def __init__(self, text, extractor):
        self.text = text
        self.sentences: List[Sentence] = extractor(self.text)

    def serialize(self):
        return {
            'text': self.text,
            'sentences': [sentence.serialize() for sentence in self.sentences]
        }

    def get_sentences_count(self):
        return len(self.sentences)

    def get_tokens_count(self):
        return sum(len(sentence.nlp_nodes) for sentence in self.sentences)

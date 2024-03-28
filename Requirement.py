from hazm import Normalizer, SentenceTokenizer, WordTokenizer, Lemmatizer, POSTagger, DependencyParser


class Requirement:
    def __init__(self, text):
        normalizer = Normalizer()
        sentence_tokenizer = SentenceTokenizer()
        self.word_tokenizer = WordTokenizer()
        self.lemmatizer = Lemmatizer()
        self.posTagger = POSTagger(model='pos_tagger.model')
        self.parser = DependencyParser(tagger=POSTagger(model='pos_tagger.model'), lemmatizer=Lemmatizer())
        self.text = normalizer.normalize(text)
        self.sentences = sentence_tokenizer.tokenize(self.text)
        self.dependency_graphs = self.make_dependency_graphs()

    def make_dependency_graphs(self):
        dependency_graphs = [self.parser.parse(self.word_tokenizer.tokenize(sentence)) for sentence in self.sentences]
        for dg in dependency_graphs:
            for node in dg.nodes.values():
                tag = node['tag']
                if tag == 'VERB':
                    lemma = node['lemma']
                    node['lemma'] = self.lemmatizer.lemmatize(lemma, 'V')

        return dependency_graphs

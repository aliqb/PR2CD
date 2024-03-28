# Press the green button in the gutter to run the script.
from hazm.dependency_parser import SpacyDependencyParser
from hazm import POSTagger, Lemmatizer, DependencyParser


def printGraph(dg):
    for head, rel, dep in dg.triples():
        # print('({h[0]}, {h[1]}), {r}, ({d[0]}, {d[1]})'.format(h=head, r=rel, d=dep))

        print(f'head:{head[0]}, {head[1]}')
        print(rel)
        print(f'dep:{dep[0]}, {dep[1]}')
        print('-----------------------------------')


if __name__ == '__main__':
    parser = DependencyParser(tagger=POSTagger(model='pos_tagger.model'), lemmatizer=Lemmatizer())
    dg = parser.parse(['من', 'به', 'مدرسه', 'رفته بودم', '.'])
    dg.tree().pprint()
    printGraph(dg)
    # tagger = POSTagger(model='pos_tagger.model')
    # lemmatizer = Lemmatizer()
    # spacy_parser = SpacyDependencyParser(tagger=tagger, lemmatizer=lemmatizer,
    #                                      model_file='./spacy_dependency_parser/parser/model',
    #                                      working_dir='./spacy_dependency_parser')
    dg1 = parser.parse_sents(sentences='من به مدرسته رفته بودم.')
    print(dg1)
    # spacy_parser = SpacyDependencyParser(tagger=POSTagger(model='pos_tagger.model'), lemmatizer=Lemmatizer())


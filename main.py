# Press the green button in the gutter to run the script.
from hazm.dependency_parser import SpacyDependencyParser
from hazm import POSTagger, Lemmatizer, DependencyParser
from Requirement import Requirement

def printGraph(dg):
    for node in dg.nodes.values():
        print(node)
        # print('({h[0]}, {h[1]}), {r}, ({d[0]}, {d[1]})'.format(h=head, r=rel, d=dep))

        # print(f'head:{head[0]}, {head[1]}')
        # print(rel)
        # print(f'dep:{dep[0]}, {dep[1]}')
        # print('-----------------------------------')


if __name__ == '__main__':
    # parser = DependencyParser(tagger=POSTagger(model='pos_tagger.model'), lemmatizer=Lemmatizer())
    # dg = parser.parse(['من', 'به', 'مدرسه', 'رفته بودم', '.'])
    # dg.tree().pprint()
    # printGraph(dg)
    requirement = Requirement('گزینه ها باید به کاربر نشان داده شود. کاربر باید بتواند انتخاب کند.')
    for dg in requirement.dependency_graphs:
        printGraph(dg)

    # spacy_parser = SpacyDependencyParser(tagger=POSTagger(model='pos_tagger.model'), lemmatizer=Lemmatizer())


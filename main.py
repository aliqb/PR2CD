# Press the green button in the gutter to run the script.
from hazm.dependency_parser import SpacyDependencyParser
from hazm import POSTagger, Lemmatizer, DependencyParser, word_tokenize
from Requirement import Requirement
from ClassDiagramExtractor import ClassDiagramExtractor
from PNLP import  HazmExtractor, StanzaExtractor

def printGraph(dg):
    for node in dg.nodes.values():
        print(node)
        # print('({h[0]}, {h[1]}), {r}, ({d[0]}, {d[1]})'.format(h=head, r=rel, d=dep))

        # print(f'head:{head[0]}, {head[1]}')
        # print(rel)
        # print(f'dep:{dep[0]}, {dep[1]}')
        # print('-----------------------------------')


if __name__ == '__main__':


    atm = 'سیستم باید از شبکه‌ی بانکی کامپیوتری پشتیبانی کند که شامل صندوق‌داران انسانی و دستگاه‌های خودپرداز است. ' \
          'شبکه‌ی بانکی کامپیوتری توسط اتحادیه‌ی بانک‌ها مورد استفاده قرار خواهد گرفت. ' \
          ' هر بانک یک رایانه فراهم می‌کند که حساب‌های بانکی را نگهداری می‌کند و تراکنش‌ها را بر روی حساب‌ها پردازش می‌کند. ' \
          ' ایستگاه‌های صندوق‌دار توسط بانک‌های فردی اداره شده و مستقیماً با رایانه‌های بانک ارتباط برقرار می‌کنند. ' \
          'صندوق‌داران انسانی داده‌های حساب و داده‌های تراکنش را وارد می‌کنند.' \
          'دستگاه خودپرداز با یک رایانه مرکزی ارتباط برقرار می‌کند.' \
          ' رایانه مرکزی تراکنش‌ها را با بانک‌ها تسویه می‌کند.' \
          'یک دستگاه خودپرداز کارت نقدی را قبول کرده و با کاربر ارتباط برقرار می‌کند.' \
          'دستگاه خودپرداز با رایانه مرکزی برای انجام تراکنش‌ها ارتباط برقرار می‌کند.' \
          'دستگاه خودپرداز پول نقد را پرداخت کرده و رسید چاپ می‌کند.' \
          'سیستم نیاز به ذخیره اطلاعات و تدابیر امنیتی مناسب دارد.' \
          'سیستم باید دسترسی همزمان به یک حساب را به درستی فراهم کند.' \
          'بانک‌ها نرم‌افزار مخصوص به بانک خود را تهیه خواهند کرد.'

    lemmatizer = Lemmatizer()
    tagger = POSTagger(model='pos_tagger.model')
    parser = DependencyParser(tagger=tagger, lemmatizer=lemmatizer)
    spacy_parser = SpacyDependencyParser(tagger=tagger, lemmatizer=lemmatizer,
                                         model_file='./spacy_dependency_parser',
                                         working_dir='./spacy_dependency_parser')
    hazm_extractor = HazmExtractor(spacy_parser, lemmatizer, with_ezafe_tag=True)
    stanza_extractor = StanzaExtractor()

    requirement = Requirement(atm, hazm_extractor.extract)

    extractor = ClassDiagramExtractor(requirement)
    extractor.extract_class_names()
    for element in extractor.class_names:
        print(element['text'])


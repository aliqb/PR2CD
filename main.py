# Press the green button in the gutter to run the script.
from hazm.dependency_parser import SpacyDependencyParser
from hazm import POSTagger, Lemmatizer, DependencyParser, word_tokenize
from Requirement import Requirement
from ClassDiagramExtractor import ClassDiagramExtractor, ClassDiagram,ExtractorEvaluator
from PNLP import HazmExtractor, StanzaExtractor


def printGraph(dg):
    for node in dg.nodes.values():
        print(node)
        # print('({h[0]}, {h[1]}), {r}, ({d[0]}, {d[1]})'.format(h=head, r=rel, d=dep))

        # print(f'head:{head[0]}, {head[1]}')
        # print(rel)
        # print(f'dep:{dep[0]}, {dep[1]}')
        # print('-----------------------------------')


def print_for_debug(extractor):
    extractor.extract_class_names()
    for element in extractor.diagram.classes:
        print(element.text, element.node.rel)


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

    course_enroll = "در ابتدای هر ترم، دانشجویان می‌توانند کاتالوگ دروس حاوی لیستی از دروس ارائه شده برای ترم را درخواست کنند." \
                    "اطلاعات مربوط به هر درس، مانند استاد، دانشکده، و پیش‌نیازها برای کمک به دانش آموزان در تصمیم گیری آگاهانه گنجانده خواهد‌شد." \
                    "سیستم جدید ثبت نام آنلاین به دانشجویان این امکان را می دهد که چهار درس  برای ترم آینده انتخاب کنند." \
                    "علاوه بر این، هر دانشجو دو درس جایگزین انتخاب خواهد کرد که در صورت حذف و یا تکمیل یک درس انتخابی، انتخاب خواهند شد." \
                    "هیچ درسی بیش از ده دانشجو نخواهد داشت." \
                    "هیچ درسی کم‌تر از سه دانشجو نخواهد‌داشت." \
                    "درس ارائه شده با کمتر از سه دانشجو لغو خواهد‌شد." \
                    "پس از تکمیل مراحل ثبت نام برای دانشجو، سامانه ثبت نام اطلاعات را به سامانه مالی ارسال می کند، بنابراین دانشجو می‌تواند صورت‌حساب خود را دریافت کند." \
                    "اساتید باید بتوانند به سیستم آنلاین دسترسی داشته باشند تا مشخص کنند که کدام درس را تدریس خواهند‌کرد." \
                    "اساتید همچنین باید ببینند کدام دانشجو برای درس ثبت‌نام کرده است." \
                    "برای هر ترم، یک دوره زمانی وجود دارد که دانشجویان می توانند برنامه های خود را تغییر دهند." \
                    "دانشجویان باید بتوانند در این مدت به سیستم آنلاین دسترسی داشته باشند تا درس‌ها را اضافه یا حذف کنند." \
                    "سیستم مالی به تمام دانش‌آموزان برای درس‌هایی که در این مدت زمان حذف شده‌اند اعتبار می‌دهد."

    restaurant = "رستوران یلماز بیش از یک نفر پرسنل و میز غذاخوری دارد." \
                 " پرسنل ممکن است در زمان های خاصی استخدام یا مرخص شوند." \
                 " هر پرسنل دارای اطلاعات نام، سن و جنسیت است." \
                 " رستوران یلماز بیش از یک بخش دارد." \
                 " این بخش ها آشپزخانه، سرویس و صندوق هستند." \
                 " پرسنل بر اساس بخش های خود کار می کنند." \
                 " پرسنل می توانند آشپز، پیشخدمت و صندوقدار باشند." \
                 " آشپز در آشپزخانه می ماند و سفارشات را آماده می کند." \
                 " هنگامی که آشپز سفارش را آماده می کند، سیستم جزئیات سفارش و شماره جدول را نشان می دهد." \
                 " پیشخدمت در بخش خدمات به مشتری خدمت می دهد." \
                 "هنگامی که پیشخدمت خدمت می کند، سیستم نام پیشخدمت و شماره میز را نشان می دهد." \
                 " صندوقدار صورت‌حساب را با توجه به جزئیات سفارش در سیستم تنظیم می کند."
    game = "یک بازی کامپیوتری را می توان با بیش از یک بازیکن انجام داد." \
           " بازیکنان می توانند وارد بازی شوند یا از بازی خارج شوند. " \
           "همه بازیکنان در سیستم باید لیست شده و اطلاعات هر یک باید نشان داده شود." \
           " بازیکنان اطلاعاتی مانند نام، نوع، جنسیت، سطح و سلاح مورد استفاده خود دارند." \
           "بازیکنان در چهار گروه دسته بندی می شوند: جنگجویان،  کمانداران، جادوگران و وحشی ها." \
           "این بازیکنان وظایف مختلفی در رابطه با نقشی که دارند بر عهده دارند." \
           " جنگجو سلاح جمع می کند و دشمن را می کشد." \
           " کماندار با پرتاب تیر به سمت دشمنان از قلعه محافظت می کند." \
           " جادوگران زخمی‌ها را درمان می کنند و بازیکنان را با جادوگری تقویت می کنند." \
           " اگر جنگجو دشمنی را در بازی بکشد، اطلاعاتی مانند نام و سلاح ظاهر می شود." \
           "هنگامی که جادوگران جادو می کنند، نام جادوها و جادوگران توسط سیستم نمایش داده می شود." \
           " علاوه بر این، هنگامی که تیر‌های کمانداران تمام شد، باید یک هشدار توسط سیستم ایجاد شود. "

    rental_car = "دستیار فروشگاه باید اطلاعات مربوط به هر خودرو را مانند پلاک، مدل، قیمت روز و غیره  ذخیره کند." \
                 "هنگامی که مشتریان می خواهند خودرویی را اجاره کنند، سیستم باید سوابق خودروهای موجود در نمایشگاه را نشان دهد و آن‌ها را بر اساس قیمت مرتب کند." \
                 "هنگامی که شخص دستیار فروشگاه دکمه مربوطه را می‌زند، سیستم سوابق خودروی اجاره‌ای را لیست می کند." \
                 "دستیار فروشگاه خودروهای موجود را جستجو می کند و اجاره خودرو را ثبت می‌کند و گزارش‌های اجاره را تهیه می کند." \
                 " دستیار فروشگاه وقتی خودرویی را اجاره می‌دهد یا خودرویی را پس می گیرد، لیست اجاره را به روز می کند." \
                 " دفتر اصلی به دلیل دیر رسیدن اخطار ارسال می کند. " \
                 "دستیار فروشگاه اطلاعات مشتریان از قبیل نام، نام خانوادگی، پلاک نشانی خودروی اجاره ای و شرایط اجاره را ثبت می کند." \

    lemmatizer = Lemmatizer()
    tagger = POSTagger(model='pos_tagger.model')
    parser = DependencyParser(tagger=tagger, lemmatizer=lemmatizer)
    spacy_parser = SpacyDependencyParser(tagger=tagger, lemmatizer=lemmatizer,
                                         model_file='./spacy_dependency_parser',
                                         working_dir='./spacy_dependency_parser')
    hazm_extractor = HazmExtractor(spacy_parser, lemmatizer, with_ezafe_tag=True)
    # stanza_extractor = StanzaExtractor()

    # atm_requirement = Requirement(atm, hazm_extractor.extract)
    #
    # atm_extractor = ClassDiagramExtractor(atm_requirement)
    # print_for_debug(atm_extractor)

    # course_req = Requirement(course_enroll, hazm_extractor.extract)
    # course_extractor = ClassDiagramExtractor(course_req)
    # print('----------------------------------------------------------')
    # print_for_debug(course_extractor)

    # restaurant_req = Requirement(restaurant, hazm_extractor.extract)
    # restaurant_extractor = ClassDiagramExtractor(restaurant_req)
    # print_for_debug(restaurant_extractor)

    # game_req = Requirement(game, hazm_extractor.extract)
    # game_extractor = ClassDiagramExtractor(game_req)
    # print_for_debug(game_extractor)

    # rental_car_req = Requirement(rental_car, hazm_extractor.extract)
    # rental_car_extractor = ClassDiagramExtractor(rental_car_req)
    # print_for_debug(rental_car_extractor)

    test = 'اعضا به عضو عادی و عضو دانشجو دسته بندی می شوند.'
    test_req = Requirement(test, hazm_extractor.extract)
    test_extractor = ClassDiagramExtractor(test_req)
    print_for_debug(test_extractor)
    # print(test_extractor.evaluate_classes(['بانک',
    #                                        'رایانه',
    #                                        ]))
    standard_diagram = ClassDiagram(['بانک',
                                     'رایانه',
                                     'موز'
                                     ])
    evaluator = ExtractorEvaluator(test_extractor.diagram, standard_diagram)
    print(evaluator.evaluate_classes())

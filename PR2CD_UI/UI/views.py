import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from Extractors import HazmExtractor
from Requirement import Requirement
from ClassDiagramExtractor import ClassDiagramExtractor, ExtractorEvaluator
from Diagram import ClassDiagram
from hazm.dependency_parser import SpacyDependencyParser
from hazm import POSTagger, Lemmatizer, DependencyParser, word_tokenize
from .forms import RequirementForm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
model_path = os.path.join(BASE_DIR, 'pos_tagger.model')
# Path to the model file
spacy_parser_path = os.path.join(BASE_DIR, 'spacy_dependency_parser')
lemmatizer = Lemmatizer()
tagger = POSTagger(model=model_path)
spacy_parser = SpacyDependencyParser(tagger=tagger, lemmatizer=lemmatizer,
                                     model_file=spacy_parser_path,
                                     working_dir=spacy_parser_path)
hazm_extractor = HazmExtractor(spacy_parser, lemmatizer, with_ezafe_tag=True)


def index(request):
    if request.method == 'POST':
        form = RequirementForm(request.POST)
        if form.is_valid():
            req_text = form.cleaned_data['req']
            if req_text is None or req_text == "":
                return render(request, 'UI/index.html', {
                    "error": "متنی وارد نکرده‌اید."
                })

            requirement = Requirement(req_text, hazm_extractor.extract)
            extractor = ClassDiagramExtractor(requirement)
            extractor.extract_diagram()
            request.session['result'] = {
                'classes': [{'text': element.text, 'attributes': [attr.text for attr in element.attributes],
                             'operations': [operation.text for operation in element.operations]} for element in
                            extractor.diagram.classes],
                'relations': [
                    {'source': relation.source.text, 'relation_type': relation.relation_type,
                     'target': relation.target.text,
                     'label': relation.label} for relation in extractor.diagram.relations]
            }
            request.session['mermaid'] = extractor.diagram.to_mermaid()
            request.session['req'] = requirement.serialize()
            return HttpResponseRedirect(reverse('UI:diagram'))
        else:
            req_text = form.data['req']
    else:
        req_text = ''
        old_req = request.session.get('req')
        if old_req is not None:
            req_text = old_req['text']
        form = RequirementForm(initial={'req': req_text})
    return render(request, 'UI/index.html', {'req': req_text, 'form': form})


def submit_req(request):
    if request.method == 'POST':
        form = RequirementForm(request.POST)
        if form.is_valid():
            req_text = form.cleaned_data['req']
            if req_text is None or req_text == "":
                return render(request, 'UI/index.html', {
                    "error": "متنی وارد نکرده‌اید."
                })

            requirement = Requirement(req_text, hazm_extractor.extract)
            extractor = ClassDiagramExtractor(requirement)
            extractor.extract_diagram()
            request.session['result'] = {
                'classes': [{'text': element.text, 'attributes': [attr.text for attr in element.attributes],
                             'operations': [operation.text for operation in element.operations]} for element in
                            extractor.diagram.classes],
                'relations': [
                    {'source': relation.source.text, 'relation_type': relation.relation_type,
                     'target': relation.target.text,
                     'label': relation.label} for relation in extractor.diagram.relations]
            }
            request.session['mermaid'] = extractor.diagram.to_mermaid()
            request.session['req'] = requirement.serialize()
            return HttpResponseRedirect(reverse('UI:diagram'))


def diagram(request):
    result = request.session.get('result')
    requirement = request.session.get('req')
    result_json = json.dumps(result, ensure_ascii=False)
    requirement_json = json.dumps(requirement, ensure_ascii=False)
    warning_nodes_addresses = []
    for sentence in requirement['sentences']:
        for node in sentence['nlp_nodes']:
            if (node['tag'] == 'VERB' and 'شد' in node['lemma']) or node['tag'] == 'PRON':
                warning_nodes_addresses.append([sentence['index'], node['address']])
    return render(request, 'UI/diagram.html',
                  {'result': result_json, 'req': requirement_json, 'req_text': requirement['text'],
                   'warning_nodes': warning_nodes_addresses, 'mermaid': request.session.get('mermaid')})


def about(request):
    return render(request, 'UI/about.html')


def contact(request):
    return render(request, 'UI/contact.html')


def samples(request):
    id = int(request.GET.get('id', '0'))
    print('ffffffffffff')
    print(id)

    samples = [
        {
            'id': 0,
            'title': 'فروشگاه آنلاین',
            'text': (
                "سیستم خرید آنلاین به مشتری‌ها این امکان را می‌دهد که محصول‌ها را بر اساس دسته‌بندی جستجو کرده و "
                "آن‌ها را سفارش دهند. هر دسته‌بندی شامل دسته‌بندی یا محصول‌ها است. مشتری‌ها می‌توانند محصول‌هایی "
                "را که با معیارهای جستجوی آن‌ها مطابقت دارد، جستجو کنند. یک ادمین دسته‌بندی‌ها و اطلاعات محصول "
                "را مدیریت می‌کند. مشتری‌ها می‌توانند حساب کاربری ایجاد کنند. یک حساب کاربری شامل اطلاعاتی مانند "
                "نام، آدرس، شماره تلفن،آدرس ایمیل خواهد بود.\n\n"
                "مشتری‌ها می‌توانند یک یا چند محصول را به سبد خرید خود اضافه کنند. سبد خرید فهرستی از محصول‌ها را "
                "نمایش می‌دهد و قیمت آن‌ها را نشان می‌دهد. سبد خرید قیمت کل اقلام موجود در سبد خرید را نیز نشان "
                "می‌دهد. مشتری‌ها می‌توانند قبل از پرداخت، محصول‌ها را از سبد خرید حذف کنند.\n\n"
                "فرآیند پرداخت زمانی آغاز می‌شود که مشتری‌ها سفارش خود را تأیید کنند. مشتری‌ها پرداخت خواهند کرد "
                "و یک ایمیل تأیید دریافت خواهند کرد. ایمیل تأیید، سفارش را نشان می‌دهد. اطلاعات سفارش شامل "
                "مشتری، محصول‌ها، قیمت‌ها، مقادیر، آدرس تحویل و تاریخ تحویل است."
            ),
            'src': 'online shopping.svg'
        },
        {
            'id': 1,
            'title': 'گروه موسیقی',
            'text': "یک گروه موسیقی بیش از یک نوازنده دارد.یک نوازنده جدید می تواند به گروه موسیقی ملحق شود یا هر "
                    "نوازنده ای می تواند گروه موسیقی را ترک کند. نوازنده دارای اطلاعات نام، سن، جنسیت، نام گروه  "
                    "موسیقی و ساز است. نوازنده‌ها با نواختن ساز به اجرای نمایش می پردازند. سازها در 3 گروه گیتار، "
                    "درام و کیبورد دسته بندی می شوند. نوازنده‌ها نوازنده گیتار،نوازنده کیبورد و نوازنده درام هستند. "
                    "نوازنده گیتار گیتار می نوازد. نوازنده درام درام می‌نوازد. نوازنده کیبورد کیبورد می‌نوازد.  هنگام "
                    "نواختن سازها سیستم باید نام ساز و نوازنده را نشان دهد.",
            'src': 'Music band.svg'
        }
    ]

    if id > len(samples) - 1:
        id = 0
    return render(request, 'UI/samples.html', samples[id])

# UI/forms.py

from django import forms

from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox


class RequirementForm(forms.Form):
    req = forms.CharField(
        label='متن نیازمندی را وارد کنید',
        required=True,
        widget=forms.Textarea(attrs={
            'id': 'req',
            'class': 'req-input',
            'rows': 12,
        }),
        error_messages={
            'required': 'نیازمندی نمی‌تواند خالی باشد.',  # Custom error message in Farsi
        }
    )
    # requirement_file = forms.FileField(
    #     label='بارگذاری فایل',
    #     required=False,
    #     widget=forms.ClearableFileInput(attrs={
    #         'id': 'requirement-file',
    #         'class': 'd-none',
    #         'accept': '.txt, .pdf, .doc, .docx, text/plain, application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    #     })
    # )
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox(api_params={'hl':'fa'}))

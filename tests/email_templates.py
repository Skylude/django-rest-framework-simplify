from django import forms
from django.conf import settings
from django.utils import timezone


from rest_framework_simplify.forms import EmailTemplateForm


class EmailService:
    @staticmethod
    def send_email(form=None):
        # send your email here from the form
        return {
            'id': 'agsjyfg7eg4j27', 'to': form.to, 'from': form._from,
            'subject': form.subject, 'html': form.html,
        }


class DynamicEmailTemplate(EmailTemplateForm):
    to = forms.CharField(required=True)
    firstName = forms.CharField(required=True)
    signUpUrl = forms.CharField(required=True)
    teamName = forms.CharField(required=True)
    copyrightYear = forms.CharField(required=False, initial=timezone.now().strftime('%Y'))

    def __init__(self, *args, **kwargs):
        kwargs['default_data'] = {
            'subject': 'Welcome',
            'from': '"%[Team-Name]" <support@example.com>',
            'templateName': 'DynamicEmail',
            'templatePath': settings.EMAIL_TEMPLATES_BASE_PATH + 'DynamicEmail.html',
            'sendEmailMethod': EmailService.send_email,
        }
        super().__init__(*args, **kwargs)


class DynamicEmailAndSubjectTemplate(EmailTemplateForm):
    to = forms.CharField(required=True)
    firstName = forms.CharField(required=True)
    signUpUrl = forms.CharField(required=True)
    copyrightYear = forms.CharField(required=False, initial=timezone.now().strftime('%Y'))

    def __init__(self, *args, **kwargs):
        kwargs['default_data'] = {
            'subject': 'Welcome to %[Location]',
            'from': '"Our Team" <support@example.com>',
            'templateName': 'DynamicEmailAndSubject',
            'templatePath': settings.EMAIL_TEMPLATES_BASE_PATH + 'DynamicEmail.html',
            'sendEmailMethod': EmailService.send_email,
        }
        super().__init__(*args, **kwargs)


class EmailWithExtraSimplifyMLTemplate(EmailTemplateForm):
    to = forms.CharField(required=True)
    firstName = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        kwargs['default_data'] = {
            'subject': 'Welcome',
            'from': '"Our Team" <support@example.com>',
            'templateName': 'EmailWithExtraSimplifyML',
            'templatePath': settings.EMAIL_TEMPLATES_BASE_PATH + 'EmailWithExtraSimplifyML.html',
            'sendEmailMethod': EmailService.send_email,
        }
        super().__init__(*args, **kwargs)


class TemplateNameWithoutHtmlFileTemplate(EmailTemplateForm):
    to = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        kwargs['default_data'] = {
            'subject': 'Welcome',
            'from': '"Our Team" <support@example.com>',
            'templateName': 'TemplateNameWithoutHtmlFile',
            'templatePath': None,
            'sendEmailMethod': EmailService.send_email,
        }
        super().__init__(*args, **kwargs)


class TemplateNameWithInvalidHtmlFileTemplate(EmailTemplateForm):
    to = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        kwargs['default_data'] = {
            'subject': 'Welcome',
            'from': '"Our Team" <support@example.com>',
            'templateName': 'TemplateNameWithInvalidHtmlFile',
            'templatePath': settings.EMAIL_TEMPLATES_BASE_PATH + 'no-a-real-html-file.html',
            'sendEmailMethod': EmailService.send_email,
        }
        super().__init__(*args, **kwargs)


class TemplateWithoutSendEmailMethodTemplate(EmailTemplateForm):
    to = forms.CharField(required=True)
    firstName = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        kwargs['default_data'] = {
            'subject': 'Welcome',
            'from': '"Our Team" <support@example.com>',
            'templateName': 'TemplateWithoutSendEmailMethod',
            'templatePath': settings.EMAIL_TEMPLATES_BASE_PATH + 'without-send-email-method.html',
            'sendEmailMethod': None,
        }
        super().__init__(*args, **kwargs)

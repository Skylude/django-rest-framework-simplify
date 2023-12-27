import django
import os
import unittest.mock

from rest_framework_simplify.exceptions import EmailTemplateException
from rest_framework_simplify.forms import EmailTemplateForm

from tests.email_templates import DynamicEmailTemplate, DynamicEmailAndSubjectTemplate, EmailWithExtraSimplifyMLTemplate, TemplateNameWithInvalidHtmlFileTemplate, TemplateWithoutSendEmailMethodTemplate, TemplateNameWithoutHtmlFileTemplate


class EmailTemplateTests(unittest.TestCase):

    def test_generate_html_raises_exception_if_invalid_params(self):
        # arrange
        body = {
            'somethingWrong': 'you@example.com',
            'signUpUrl': 'https://mywebsite.com/signup?token=LLK69FkQ12',
        }
        form = DynamicEmailTemplate(body)

        # act
        with self.assertRaises(EmailTemplateException) as ex:
            form.generate_html()

        # assert
        self.assertEqual(ex.exception.args[0], EmailTemplateForm.ErrorMessages.INVALID_PARAMS.format('DynamicEmail'))

    def test_generate_html_raises_exception_if_missing_email_template(self):
        # arrange
        body = {
            'to': 'you@example.com',
        }
        form = TemplateNameWithoutHtmlFileTemplate(body)

        # act
        with self.assertRaises(EmailTemplateException) as ex:
            form.generate_html()

        # assert
        self.assertEqual(ex.exception.args[0], EmailTemplateForm.ErrorMessages.MISSING_EMAIL_TEMPLATE_PATH.format('TemplateNameWithoutHtmlFile'))

    def test_generate_html_raises_exception_if_invalid_email_template_path(self):
        # arrange
        body = {
            'to': 'you@example.com',
        }
        form = TemplateNameWithInvalidHtmlFileTemplate(body)

        # act
        with self.assertRaises(EmailTemplateException) as ex:
            form.generate_html()

        # assert
        self.assertEqual(ex.exception.args[0], EmailTemplateForm.ErrorMessages.INVALID_EMAIL_TEMPLATE_PATH.format('TemplateNameWithInvalidHtmlFile'))

    def test_generate_html_raises_exception_if_html_has_extra_rdml(self):
        # arrange
        body = {'to': 'you@example.com', 'firstName': 'Chris'}
        form = EmailWithExtraSimplifyMLTemplate(body)

        # act
        with self.assertRaises(EmailTemplateException) as ex:
            form.generate_html()

        # assert
        self.assertEqual(ex.exception.args[0], EmailTemplateForm.ErrorMessages.UNABLE_TO_POPULATE_TEMPLATE.format('EmailWithExtraSimplifyML', 'Extra-Simplifyml'))

    def test_generate_html_raises_exception_if_subject_has_extra_rdml(self):
        # arrange
        body = {
            'to': 'you@example.com',
            'firstName': 'Chris',
            'signUpUrl': 'https://mywebsite.com/signup?token=LLK69FkQ12',
        }
        form = DynamicEmailAndSubjectTemplate(body)

        # act
        with self.assertRaises(EmailTemplateException) as ex:
            form.generate_html()

        # assert
        self.assertEqual(ex.exception.args[0], EmailTemplateForm.ErrorMessages.UNABLE_TO_POPULATE_TEMPLATE.format('DynamicEmailAndSubject', 'Location'))

    def test_send_email_raises_exception_if_missing_send_email_method(self):
        # arrange
        body = {'to': 'you@example.com', 'firstName': 'Chris'}
        form = TemplateWithoutSendEmailMethodTemplate(body)

        # act
        with self.assertRaises(EmailTemplateException) as ex:
            form.send_email()

        # assert
        self.assertEqual(ex.exception.args[0], EmailTemplateForm.ErrorMessages.MISSING_SEND_EMAIL_METHOD)

    @unittest.mock.patch('tests.email_templates.EmailService.send_email')
    def test_send_email_raises_exception_if_send_email_method_fails(self, mock_send_email_method):
        # arrange
        body = {
            'to': 'you@example.com',
            'firstName': 'Chris',
            'teamName': 'Our Team',
            'signUpUrl': 'https://mywebsite.com/signup?token=LLK69FkQ12',
        }
        form = DynamicEmailTemplate(body)
        mock_send_email_method.side_effect = Exception('Error')

        # act
        with self.assertRaises(EmailTemplateException) as ex:
            form.send_email()

        # assert
        self.assertEqual(ex.exception.args[0], EmailTemplateForm.ErrorMessages.ERROR_SENDING_EMAIL)

    def test_send_email_happy_path(self):
        # arrange
        body = {
            'to': 'you@example.com',
            'firstName': 'Chris',
            'teamName': 'Our Team',
            'signUpUrl': 'https://mywebsite.com/signup?token=LLK69FkQ12',
        }
        form = DynamicEmailTemplate(body)

        # act
        result = form.send_email()

        # assert
        self.assertEqual(result['to'], body['to'])
        self.assertEqual(result['from'], '"Our Team" <support@example.com>')

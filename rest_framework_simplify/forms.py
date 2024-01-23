import re
import requests

from django import forms

from rest_framework_simplify.exceptions import EmailTemplateException
from rest_framework_simplify.helpers import handle_bytes_decoding
from rest_framework_simplify.services.sql_executor.exceptions import EngineNotSupported
from rest_framework_simplify.services.sql_executor.service import SQLExecutorService


class StoredProcedureForm(forms.Form):
    supported_engines = ['sqlserver', 'postgres']

    class ErrorMessages:
        UNSUPPORTED_ENGINE_ERROR = '{0} engine not supported!'
        METHOD_NOT_IMPLEMENTED = 'Method not implemented for this engine'

    def __init__(self, *args, **kwargs):
        # call base constructor
        connection_data = kwargs.pop('connection_data', None)
        super(StoredProcedureForm, self).__init__(*args, **kwargs)
        # setup supported engines
        self.engine_map = {
            'sqlserver': SQLServerStoredProcedureForm,
            'postgres': PostgresStoredProcedureForm
        }
        self.sp_name = connection_data.get('sp_name', None)

        # make sure we are dealing with a supported engine
        engine = connection_data.get('engine', None)
        if engine not in self.supported_engines:
            error = 'NoneType' if not engine else engine
            raise EngineNotSupported(self.ErrorMessages.UNSUPPORTED_ENGINE_ERROR.format(error))
        self.engine = engine
        self.connection_data = {
            'server': connection_data.get('server', None),
            'database': connection_data.get('database', None),
            'username': connection_data.get('username', None),
            'password': connection_data.get('password', None),
            'port': connection_data.get('port', None)
        }
        self.__class__ = self.engine_map.get(self.engine, StoredProcedureForm)

    def execute_sp(self):
        # call stored procedure
        sp_service = SQLExecutorService(
            self.connection_data['server'],
            self.connection_data['database'],
            self.connection_data['username'],
            self.connection_data['password'],
            port=self.connection_data['port'],
            engine=self.engine
        )
        result = sp_service.call_stored_procedure(self.sp_name, self.format_params)

        for item in result:
            handle_bytes_decoding(item)

        return result



class PostgresStoredProcedureForm(StoredProcedureForm):
    # method will get params and put form parameters in the correct order that the stored procedure needs
    def format_params(self, sp_params):
        params = []
        for field in sp_params:
            try:
                # todo this could cause issues with someone wanting to pass in an empty string as a param
                if self.cleaned_data[field] != '':
                    params.append(self.cleaned_data[field])
                else:
                    params.append(None)
            except KeyError:
                # issue with data
                raise KeyError
        return params


class SQLServerStoredProcedureForm(StoredProcedureForm):
    # method will get params and put form parameters in the correct order that the stored procedure needs
    def format_params(self, sp_params):
        params = []
        for field in sp_params:
            try:
                field_name = field.lstrip('@')
                params.append(self.cleaned_data[field_name])
            except KeyError:
                # issue with data
                raise KeyError
        return params


class EmailTemplateForm(forms.Form):

    class ErrorMessages:
        INVALID_EMAIL_TEMPLATE = 'Email template {0} is not defined'
        MISSING_EMAIL_TEMPLATE_PATH = 'Email template path {0} is not defined'
        INVALID_EMAIL_TEMPLATE_PATH = 'Email template path {0} could not be found'
        INVALID_PARAMS = 'Params for email template {0} invalid'
        ERROR_SENDING_EMAIL = 'An error occurred while sending the email'
        UNABLE_TO_POPULATE_TEMPLATE = 'Unable to populate all the needed fields in {0}. Field: {1}'
        MISSING_SEND_EMAIL_METHOD = 'Missing a send email method'

    def __init__(self, *args, **kwargs):
        # call base constructor
        default_data = kwargs.pop('default_data', None)
        super(EmailTemplateForm, self).__init__(*args, **kwargs)
        # setup template
        self.default_data = {
            'subject': default_data.get('subject', None),
            'from': default_data.get('from', None),
            'templateName': default_data.get('templateName', None),
            'templatePath': default_data.get('templatePath', None),
            'templateContents': default_data.get('templateContents', None),
            'sendEmailMethod': default_data.get('sendEmailMethod', None)
        }

        # populate default values if they are missing
        for field in self.fields:
            if self.fields[field].initial and not self.data.get(field, None):
                self.data[field] = self.fields[field].initial

    def generate_html(self):
        if not self.is_valid():
            raise EmailTemplateException(self.ErrorMessages.INVALID_PARAMS.format(self.default_data['templateName']))

        # check template path
        if not self.default_data['templatePath'] and not self.default_data['templateContents']:
            raise EmailTemplateException(self.ErrorMessages.MISSING_EMAIL_TEMPLATE_PATH.format(self.default_data['templateName']))

        if self.default_data['templateContents']:
            html = self.default_data['templateContents']
        elif self.default_data['templatePath'][:7].lower() == 'http://' or self.default_data['templatePath'][:8].lower() == 'https://':
            # get template via requests.get
            req = requests.get(self.default_data['templatePath'])
            if req.status_code != 200:
                raise EmailTemplateException(self.ErrorMessages.INVALID_EMAIL_TEMPLATE_PATH.format(self.default_data['templateName']))
            else:
                html = req.text
        else:
            # get local email html
            try:
                doc = self.default_data['templatePath']
                with open(doc, 'r', encoding='utf-8') as email_template:
                    html = email_template.read()
            except (FileNotFoundError, TypeError):
                raise EmailTemplateException(self.ErrorMessages.INVALID_EMAIL_TEMPLATE_PATH.format(self.default_data['templateName']))

        # populate email
        for key in self.declared_fields:
            # convert key to simplify ML (firstName -> %[First-Name]) and update HTML and Subject
            simplify_ml = '%[{0}]'.format(re.sub(r'(?!^)([A-Z])', lambda m: '-' + m.group(1), key).title())
            html = html.replace(simplify_ml, self.cleaned_data[key])
            self.default_data['subject'] = self.default_data['subject'].replace(simplify_ml, self.cleaned_data[key])
            self.default_data['from'] = self.default_data['from'].replace(simplify_ml, self.cleaned_data[key])

        # validate (make sure there aren't any simplify MLs left in the HTML or Subject)
        simplifyml_regex = re.compile('%\[(.+?)]')
        simplify_mls = simplifyml_regex.findall(html) + simplifyml_regex.findall(self.default_data['subject']) + simplifyml_regex.findall(self.default_data['from'])
        if len(simplify_mls) > 0:
            raise EmailTemplateException(self.ErrorMessages.UNABLE_TO_POPULATE_TEMPLATE.format(self.default_data['templateName'],
                                                                                               ', '.join(simplify_mls)))

        # save the values to the form, so we can use them later
        self.to = self.cleaned_data['to']
        self._from = self.default_data['from']
        self.subject = self.default_data['subject']
        self.html = html

        return html

    def send_email(self):
        if not self.default_data['sendEmailMethod']:
            raise EmailTemplateException(self.ErrorMessages.MISSING_SEND_EMAIL_METHOD)

        try:
            # this will save all the values to self
            self.generate_html()
        except EmailTemplateException as ex:
            raise EmailTemplateException(ex.args[0])

        # send email
        try:
            return self.default_data['sendEmailMethod'](self)
        except:
            raise EmailTemplateException(self.ErrorMessages.ERROR_SENDING_EMAIL)

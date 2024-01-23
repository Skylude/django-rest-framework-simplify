import json

from Crypto.Cipher import AES
from Crypto import Random
import base64

from django.conf import settings
from django.core.exceptions import FieldError, ImproperlyConfigured, ValidationError
from django.db import models
from django.utils.encoding import force_bytes, force_str
from django.utils.functional import cached_property

BLOCK_SIZE = 16


class SimplifyEncryptedField(models.Field):
    _internal_type = 'BinaryField'

    def __init__(self, *args, **kwargs):
        if kwargs.get('primary_key'):
            raise ImproperlyConfigured('%s does not support primary_key=True.' % self.__class__.__name__)

        if kwargs.get('unique'):
            raise ImproperlyConfigured('%s does not support unique=True.' % self.__class__.__name__)

        if kwargs.get('display_chars'):
            self.display_chars = kwargs.get('display_chars')
            del kwargs['display_chars']

        super(SimplifyEncryptedField, self).__init__(*args, **kwargs)

    @cached_property
    def keys(self):
        keys = getattr(settings, 'DB_ENCRYPTION_KEY', None)

        if keys is None:
            keys = [settings.SECRET_KEY]
        return keys

    @property
    def algorithm(self):
        IV = Random.new().read(BLOCK_SIZE)
        if len(self.keys) > 0:
            return AES.new(self.keys.encode(), AES.MODE_ECB)

    def get_internal_type(self):
        return self._internal_type

    def get_db_prep_save(self, value, connection):
        value = super(SimplifyEncryptedField, self).get_db_prep_save(value, connection)

        if value is not None:
            remainder = len(value) % BLOCK_SIZE
            pad_length = BLOCK_SIZE - remainder
            value += pad_length * '\0'
            encrypted_value = self.algorithm.encrypt(value.encode())
            return connection.Database.Binary(encrypted_value)

    def from_db_value(self, value, expression, connection):
        if value is not None:
            value = bytes(value)
            decrypted_value = self.algorithm.decrypt(value).split(b'\0')[0]
            return self.to_python(decrypted_value)

    def to_python(self, value):
        if value is not None:
            value = force_str(value)
            if hasattr(self, 'display_chars') and self.display_chars != 0:
                value = value[self.display_chars:]

        return value


def get_prep_lookup(self):
    raise FieldError("{} '{}' does not support lookups".format(self.lhs.field.__class__.__name__, self.lookup_name))


for name, lookup in models.Field.class_lookups.items():
    if name != 'isnull':
        lookup_class = type('EncryptedField' + name, (lookup,), {
            'get_prep_lookup': get_prep_lookup
        })
        SimplifyEncryptedField.register_lookup(lookup_class)


class SimplifyEncryptedCharField(SimplifyEncryptedField):
    def __init__(self, *args, **kwargs):
        if kwargs.get('display_chars'):
            self.display_chars = kwargs.get('display_chars')

        super(SimplifyEncryptedCharField, self).__init__(*args, **kwargs)


class SimplifyJsonTextField(models.TextField):

    class ErrorMessages:
        INVALID_DB_VALUE = 'Invalid db value for SimplifyJsonTextField instance: {0}'
        INVALID_PYTHON_VALUE = 'Invalid python value for SimplifyJsonTextField instance: {0}'

    def __init__(self, *args, db_collation=None, **kwargs):
        super().__init__(*args, db_collation, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value

        try:
            new_value = json.loads(value)
        except Exception as e:
            raise ValidationError(SimplifyJsonTextField.ErrorMessages.INVALID_DB_VALUE
                                  .format(str(value)))

        return new_value

    def to_python(self, value):
        if isinstance(value, str):
            return value

        if value is None:
            return value

        try:
            new_value = json.dumps(value)
        except Exception as e:
            raise ValidationError(SimplifyJsonTextField.ErrorMessages.INVALID_PYTHON_VALUE
                                  .format(str(value)))

        return new_value

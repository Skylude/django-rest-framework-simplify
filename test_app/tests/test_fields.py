import django
import os
import unittest

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_proj.settings'
django.setup()

from test_app.tests.helpers import DataGenerator
from test_app.models import EncryptedClass


class CustomFieldTests(unittest.TestCase):
    def test_encrypted_field_returns_decrypted_value(self):
        value = '123456789'
        encrypted_class = DataGenerator.set_up_encrypted_class(value=value)

        encrypted_return = EncryptedClass.objects.get(id=encrypted_class.id)

        self.assertEqual(value[-4:], encrypted_return.encrypted_val[-4:])
        self.assertEqual(len(encrypted_return.encrypted_val), 4)
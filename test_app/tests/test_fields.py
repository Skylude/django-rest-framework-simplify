import django
import os
import unittest

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_proj.settings'
django.setup()

from test_app.tests.helpers import DataGenerator
from test_app.models import EncryptedClass, EncryptedClassNoDisplayChars


class CustomFieldTests(unittest.TestCase):
    def test_encrypted_field_returns_decrypted_value(self):
        value = '123456789'
        encrypted_class = DataGenerator.set_up_encrypted_class(value=value)

        encrypted_return = EncryptedClass.objects.get(id=encrypted_class.id)

        self.assertEqual(value[-4:], encrypted_return.encrypted_val[-4:])
        self.assertEqual(len(encrypted_return.encrypted_val), 4)

    def test_encrypted_field_returns_decrypted_value(self):
        value = '1234 56789 937395'
        encrypted_class = DataGenerator.set_up_encrypted_class(value=value)

        encrypted_return = EncryptedClass.objects.get(id=encrypted_class.id)

        self.assertEqual(value[-4:], encrypted_return.encrypted_val[-4:])
        self.assertEqual(len(encrypted_return.encrypted_val), 4)

    def test_encrypted_field_returns_full_descrypted_value(self):
        value = '123456789abcdefgfff'
        encrypted_class = DataGenerator.set_up_encrypted_class_with_no_display_value(value=value)

        encrypted_return = EncryptedClassNoDisplayChars.objects.get(id=encrypted_class.id)

        self.assertEqual(value, encrypted_return.encrypted_val)
import json
from typing import List
from unittest import skip
from unittest.mock import patch

import django
import os
import unittest

from django.core.exceptions import ValidationError

from rest_framework_simplify.fields import SimplifyJsonTextField

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_proj.settings'
django.setup()

from test_app.tests.helpers import DataGenerator
from test_app.models import EncryptedClass, EncryptedClassNoDisplayChars, JsonTextFieldClass


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

    def test_json_text_field_accepts_json_value(self):
        value = '123456789'
        encrypted_class = DataGenerator.set_up_encrypted_class(value=value)

        encrypted_return = EncryptedClass.objects.get(id=encrypted_class.id)

        self.assertEqual(value[-4:], encrypted_return.encrypted_val[-4:])
        self.assertEqual(len(encrypted_return.encrypted_val), 4)

    class JsonTextFieldTests(unittest.TestCase):

        @patch.object(SimplifyJsonTextField, 'to_python')
        def test_json_text_field_calls_mock_to_python_when_set(self, mock_to_python):
            # arrange
            mock_to_python.return_value = []
            json_text = json.loads('[{ "description": "isn\'t it beautiful outside?" }]')

            # act
            jt_class = DataGenerator.set_up_json_text_field_class(
                json_text=json_text)

            # assert
            self.assertTrue(mock_to_python.called)

        @patch.object(SimplifyJsonTextField, 'from_db_value')
        def test_json_text_field_calls_mock_from_db_value_when_retrieved_from_db(self, mock_from_db):
            # arrange
            mock_from_db.return_value = []
            json_text = json.loads('[{ "description": "isn\'t it beautiful outside?" }]')
            jt_class = DataGenerator.set_up_json_text_field_class(
                json_text=json_text)

            # act
            jt_return = JsonTextFieldClass.objects.get(id=jt_class.id)

            # assert
            self.assertTrue(mock_from_db.called)

        def test_json_text_field_returns_json_value_as_list(self):
            # arrange
            json_text = json.loads('[{ "description": "isn\'t it beautiful outside?" }]')
            jt_class = DataGenerator.set_up_json_text_field_class(
                json_text=json_text)

            # act
            jt_return = JsonTextFieldClass.objects.get(id=jt_class.id)

            # assert
            self.assertIsNotNone(jt_return)
            self.assertTrue(isinstance(jt_return.json_text, List))

        def test_json_text_field_returns_json_value_as_list_when_to_python_called_twice(self):
            # arrange
            json_text = [{ "description": "isn\'t it beautiful outside?" }]
            jt_class = DataGenerator.set_up_json_text_field_class(
                json_text=json_text)

            jt_class.json_text = json.dumps(json_text)
            jt_class.save()

            # act
            jt_return = JsonTextFieldClass.objects.get(id=jt_class.id)

            # assert
            self.assertIsNotNone(jt_return)
            self.assertTrue(isinstance(jt_return.json_text, List))

        def test_json_text_field_returns_json_value_as_object(self):
            # arrange
            json_text = json.loads('{ "description": "isn\'t it beautiful outside?" }')
            jt_class = DataGenerator.set_up_json_text_field_class(
                json_text=json_text)

            # act
            jt_return = JsonTextFieldClass.objects.get(id=jt_class.id)

            # assert
            self.assertIsNotNone(jt_return)
            self.assertTrue(isinstance(jt_return.json_text, dict))

        def test_json_text_field_returns_json_value_as_none(self):
            # arrange
            json_text = None
            jt_class = DataGenerator.set_up_json_text_field_class(
                json_text=json_text)

            # act
            jt_return = JsonTextFieldClass.objects.get(id=jt_class.id)

            # assert
            self.assertIsNone(jt_return.json_text)

        def test_json_text_field_throws_error_when_json_in_database_is_malformed(self):
            # arrange
            json_text_in_db = '[{ \'description\':: \'isn\'t it beautiful outside?\' }]'

            # act
            jt_class = DataGenerator.set_up_json_text_field_class(
                json_text=json_text_in_db)

            # act / assert
            with self.assertRaises(ValidationError) as ex:
                jt_return = JsonTextFieldClass.objects.get(id=jt_class.id)
            self.assertEqual(ex.exception.args[0], SimplifyJsonTextField.
                             ErrorMessages.INVALID_DB_VALUE.format(json_text_in_db))

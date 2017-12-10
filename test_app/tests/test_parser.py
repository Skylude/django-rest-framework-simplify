import django
import os
import unittest
import uuid

from rest_framework_simplify.errors import DjangoErrorMessages, ErrorMessages
from rest_framework_simplify.exceptions import ParseException

os.environ['DJANGO_SETTINGS_MODULE']='test_proj.settings'
django.setup()

from test_app.models import BasicClass


class BasicClassTests(unittest.TestCase):
    def test_parse_with_valid_data(self):
        request_data = {
            'name': 'Justin'
        }
        basic_class = BasicClass.parse(request_data)
        self.assertIsNotNone(basic_class)

    def test_parse_with_missing_field(self):
        request_data = {
        }
        with self.assertRaises(ParseException) as ex:
            basic_class = BasicClass.parse(request_data)
        self.assertEqual(ex.exception.args[0]['name'][0].message, DjangoErrorMessages.FIELD_CANNOT_BE_BLANK)

    def test_parse_with_none(self):
        with self.assertRaises(ParseException) as ex:
            basic_class = BasicClass.parse(None)
        self.assertEqual(ex.exception.args[0], ErrorMessages.NO_DATA_OR_DATA_NOT_DICT)

    def test_parse_with_invalid_data_type(self):
        with self.assertRaises(ParseException) as ex:
            basic_class = BasicClass.parse(1)
        self.assertEqual(ex.exception.args[0], ErrorMessages.NO_DATA_OR_DATA_NOT_DICT)

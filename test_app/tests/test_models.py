import django
import os
import unittest
import uuid

from rest_framework_simplify.errors import DjangoErrorMessages, ErrorMessages
from rest_framework_simplify.exceptions import ParseException

os.environ['DJANGO_SETTINGS_MODULE']='test_proj.settings'
django.setup()

from test_app.models import BasicClass


class BasicClassParserTests(unittest.TestCase):
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


class BasicClassChangeTrackingFieldsTests(unittest.TestCase):

    def test_change_tracking_fields_without_changes(self):
        # Arrange
        basic_class = BasicClass(name='Initial Value')
        # Act
        # Assert
        self.assertFalse(basic_class.change_tracking_field_has_changed('name'))
        self.assertEqual(basic_class._name_initial, 'Initial Value')

    def test_change_tracking_fields_with_changes(self):
        # Arrange
        basic_class = BasicClass(name='Initial Value')
        # Act
        basic_class.name = 'Then I change it to this'
        # Assert
        self.assertTrue(basic_class.change_tracking_field_has_changed('name'))
        self.assertEqual(basic_class._name_initial, 'Initial Value')

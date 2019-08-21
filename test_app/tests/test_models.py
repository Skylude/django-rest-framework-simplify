import django
import os
import unittest
import uuid

from rest_framework_simplify.errors import DjangoErrorMessages, ErrorMessages
from rest_framework_simplify.exceptions import ParseException

os.environ['DJANGO_SETTINGS_MODULE']='test_proj.settings'
django.setup()

from test_app.models import BasicClass, ChildClass


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
        initial_value = str(uuid.uuid4())[:15]
        basic_class = BasicClass(name=initial_value)
        basic_class.save()
        basic_class_db = BasicClass.objects.get(id=basic_class.id)
        # Act
        # Assert
        self.assertFalse(basic_class_db.change_tracking_field_has_changed('name'))
        self.assertEqual(basic_class_db.get_change_tracking_field_initial_value('name'), initial_value)

    def test_change_tracking_fields_with_changes(self):
        # Arrange
        initial_value = str(uuid.uuid4())[:15]
        new_value = str(uuid.uuid4())[:15]
        basic_class = BasicClass(name=initial_value)
        basic_class.save()
        basic_class_db = BasicClass.objects.get(id=basic_class.id)
        # Act
        basic_class_db.name = new_value
        # Assert
        self.assertTrue(basic_class_db.change_tracking_field_has_changed('name'))
        self.assertEqual(basic_class_db.get_change_tracking_field_initial_value('name'), initial_value)

    def test_change_tracking_fields_with_changes_of_a_foreign_key(self):
        # Arrange
        initial_child_class = ChildClass(name=str(uuid.uuid4())[:15])
        initial_child_class.save()
        new_child_class = ChildClass(name=str(uuid.uuid4())[:15])
        new_child_class.save()
        basic_class = BasicClass(name=str(uuid.uuid4())[:15], child_one=initial_child_class)
        basic_class.save()
        basic_class_db = BasicClass.objects.get(id=basic_class.id)
        # Act
        basic_class_db.child_one = new_child_class
        # Assert
        self.assertTrue(basic_class_db.change_tracking_field_has_changed('child_one'))
        self.assertEqual(basic_class_db.get_change_tracking_field_initial_value('child_one'), initial_child_class.id)

import random
import unittest
import uuid
from unittest.mock import MagicMock

from rest_framework_simplify.mapper import Mapper


class MapperTests(unittest.TestCase):

    def test_camelcase_to_underscore_not_capitalized(self):
        camel_case = 'camelCase'
        underscore = 'camel_case'
        val = Mapper.camelcase_to_underscore(camel_case)
        self.assertEqual(val, underscore)

    def test_camelcase_to_underscore_capitalized(self):
        camel_case = 'CamelCase'
        underscore = 'camel_case'
        val = Mapper.camelcase_to_underscore(camel_case)
        self.assertEqual(val, underscore)

    def test_camelcase_to_underscore_array_of_numbers(self):
        camel_case = {'camelCase': [1, 10]}
        underscore = {'camel_case': [1, 10]}
        val = Mapper.camelcase_to_underscore(camel_case)
        self.assertEqual(val, underscore)

    def test_camelcase_to_underscore_array_of_strings(self):
        camel_case = {'camelCase': ['camelCase']}
        underscore = {'camel_case': ['camelCase']}
        val = Mapper.camelcase_to_underscore(camel_case)
        self.assertEqual(val, underscore)

    def test_camelcase_to_underscore_array_of_bools(self):
        camel_case = {'camelCase': [True, False]}
        underscore = {'camel_case': [True, False]}
        val = Mapper.camelcase_to_underscore(camel_case)
        self.assertEqual(val, underscore)

    def test_camelcase_to_underscore_empty_array(self):
        camel_case = {'camelCase': []}
        underscore = {'camel_case': []}
        val = Mapper.camelcase_to_underscore(camel_case)
        self.assertEqual(val, underscore)

    def test_camelcase_to_underscore_array_of_objects(self):
        camel_case = {'camelCase': [{'camelCase': 1}]}
        underscore = {'camel_case': [{'camel_case': 1}]}
        val = Mapper.camelcase_to_underscore(camel_case)
        self.assertEqual(val, underscore)

    def test_camelcase_to_underscore_array_of_mixed_types(self):
        int_type_value = random.randint(1, 10)
        str_type_value = str(uuid.uuid4())[:4]
        bool_type_value = False
        obj_type_value = {'camelCase': 1}
        ary_type_value = [int_type_value, obj_type_value]
        underscore = MagicMock(obj_type_value={'camel_case': 1}, ary_type_value=[int_type_value, {'camel_case': 1}])
        camel_case = {'camelCase': [int_type_value, str_type_value, obj_type_value, ary_type_value, bool_type_value]}
        underscore = {'camel_case': [int_type_value, str_type_value, underscore.obj_type_value, underscore.ary_type_value, bool_type_value]}
        val = Mapper.camelcase_to_underscore(camel_case)
        self.assertEqual(val, underscore)

    def test_underscore_to_camelcase(self):
        underscore = 'camel_case'
        camel_case = 'camelCase'
        val = Mapper.underscore_to_camelcase(underscore)
        self.assertEqual(val, camel_case)

    # I know this is horrible, but we have api's relying on this bug and we cannot fix it safely
    def test_underscore_to_backwards_compatible(self):
        underscore = 'address_line_1'
        camel_case = 'addressLine_1'
        val = Mapper.underscore_to_camelcase(underscore)
        self.assertEqual(val, camel_case)

    def test_underscore_to_camelcase_embedded(self):
        underscore = [{'camel_case': [{'more_camel_case': 5}]}]
        camel_case = [{'camelCase': [{'moreCamelCase': 5}]}]
        val = Mapper.underscore_to_camelcase(underscore)
        self.assertEqual(val, camel_case)

    def test_title_case_full_upper(self):
        upper = 'SSN'
        lower = 'ssn'
        val = Mapper.titlecase_to_camelcase(upper)
        self.assertEqual(val, lower)

    def test_title_case_mixed_bag(self):
        title = 'PMSystemID'
        camel = 'pmSystemId'
        val = Mapper.titlecase_to_camelcase(title)
        self.assertEqual(val, camel)

    def test_underscore_t0_titlecase(self):
        underscore = 'sum_charges'
        title = 'SumCharges'
        val = Mapper.underscore_to_titlecase(underscore)
        self.assertEqual(val, title)

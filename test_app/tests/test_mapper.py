import unittest

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
        camel_case = {'camelCase': [1]}
        underscore = {'camel_case': [1]}
        val = Mapper.camelcase_to_underscore(camel_case)
        self.assertEqual(val, underscore)

    def test_camelcase_to_underscore_array_of_objects(self):
        camel_case = {'camelCase': [{'camelCase': 1}]}
        underscore = {'camel_case': [{'camel_case': 1}]}
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

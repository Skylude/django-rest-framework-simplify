import django
import os
import unittest.mock
import uuid

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal
from rest_framework_simplify.errors import ErrorMessages
from rest_framework_simplify.helpers import generate_str
from rest_framework_simplify.views import SimplifyStoredProcedureView, SimplifyEmailTemplateView
from rest_framework import status
from rest_framework.test import APIClient


from tests.tests.helpers import DataGenerator
from tests.models import BasicClass, ChildClass, LinkingClass, Application


class BasicClassTests(unittest.TestCase):
    api_client = APIClient()

    def tearDown(self):
        cache.clear()

    def test_delete(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        url = f'/basicClass/{basic_class.id}'

        # act
        result = self.api_client.delete(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        with self.assertRaises(ObjectDoesNotExist) as ex:
            BasicClass.objects.get(pk=basic_class.id)
        self.assertIsInstance(ex.exception, ObjectDoesNotExist)

    def test_delete_sub(self):
        # arrange
        child_one = DataGenerator.set_up_child_class()
        basic_class = DataGenerator.set_up_basic_class(child_one=child_one)
        url = f'/basicClass/{basic_class.id}/childClass/{child_one.id}'

        # act
        result = self.api_client.delete(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        with self.assertRaises(ObjectDoesNotExist) as ex:
            ChildClass.objects.get(pk=child_one.id)
        self.assertIsInstance(ex.exception, ObjectDoesNotExist)

    def test_delete_sub_only_linking_class(self):
        # arrange
        linking_class = DataGenerator.set_up_linking_class()
        url = f'/basicClass/{linking_class.basic_class.id}/childClass/{linking_class.child_class.id}?deleteLinkOnly=true'

        # act
        result = self.api_client.delete(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        # both classes should exist
        child_class = ChildClass.objects.get(pk=linking_class.child_class.id)
        basic_class = BasicClass.objects.get(pk=linking_class.basic_class.id)
        # linking class should not exist
        with self.assertRaises(ObjectDoesNotExist) as ex:
            LinkingClass.objects.get(pk=linking_class.id)
        self.assertIsInstance(ex.exception, ObjectDoesNotExist)

    def test_get_with_cache(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        url = f'/basicClass/{basic_class.id}'

        # act
        result = self.api_client.get(url, format='json')
        cached_result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(cached_result.status_code, status.HTTP_200_OK)
        self.assertTrue(cached_result.has_header('Hit'))

    def test_get_with_cache_without_cache_time(self):
        # arrange
        child_one = DataGenerator.set_up_child_class()
        basic_class = DataGenerator.set_up_basic_class(child_one=child_one)
        url = f'/basicClass/{basic_class.id}/childOne'

        # act
        result = self.api_client.get(url, format='json')
        cached_result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(cached_result.status_code, status.HTTP_200_OK)
        self.assertFalse(cached_result.has_header('Hit'))

    def test_get(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        url = f'/basicClass/{basic_class.id}'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data['id'], basic_class.id)

    def test_get_list_paging_count_only(self):
        # arrange
        basic_class_1, basic_class_2, basic_class_3 = (DataGenerator.set_up_basic_class() for x in range(3))
        url = '/basicClass?countOnly=True'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertGreater(result.data['count'], 2)
        self.assertEqual(len(result.data['data']), 0)

    def test_get_list_paging_count_only_by_page_zero(self):
        # arrange
        basic_class_1, basic_class_2, basic_class_3 = (DataGenerator.set_up_basic_class() for x in range(3))
        url = '/basicClass?page=1&pageSize=0'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertGreater(result.data['count'], 2)
        self.assertEqual(len(result.data['data']), 0)

    def test_get_list_count_by_page_zero(self):
        # arrange
        basic_class_1, basic_class_2, basic_class_3 = (DataGenerator.set_up_basic_class() for x in range(3))
        url = '/basicClass?pageSize=0'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertGreater(result.data['count'], 2)
        self.assertEqual(len(result.data['data']), 0)

    def test_get_list_no_count(self):
        # arrange
        basic_class_1, basic_class_2, basic_class_3 = (DataGenerator.set_up_basic_class() for x in range(3))
        url = '/basicClass?page=1&pageSize=3&noCount=true'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data['count'], None)
        self.assertGreater(len(result.data['data']), 1)

    def test_get_meta(self):
        # arrange
        meta_data_class = DataGenerator.set_up_meta_data_class()
        url = f'/metaDataClass?meta=true'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)

    def test_get_list_sub(self):
        # arrange
        child_one = DataGenerator.set_up_child_class()
        basic_class = DataGenerator.set_up_basic_class(child_one=child_one)
        url = f'/basicClass/{basic_class.id}/childOne'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        basic_class.refresh_from_db()
        self.assertEqual(child_one.id, result.data['id'])

    def test_get_list_sub_with_no_child_resource(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class(child_one=None)
        url = f'/basicClass/{basic_class.id}/childOne'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.data, {})

    def test_post_sub_resource_to_child_(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        url = f'/basicClasses/{basic_class.id}/childOne'
        body = {
            'name': 'test 123',
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        basic_class.refresh_from_db()
        self.assertEqual(basic_class.child_one.name, result.data['name'])

    def test_post_sub_resource_to_linking_class(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        url = f'/basicClasses/{basic_class.id}/childClass'
        body = {
            'name': 'test 123',
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        basic_class.refresh_from_db()
        linking_classes = LinkingClass.objects.filter(basic_class=basic_class)
        self.assertEqual(len(linking_classes), 1)

    def test_post_with_links_param(self):
        # arrange
        child_class = DataGenerator.set_up_child_class()
        url = f'/basicClass?links=linking_classes__child_class_id={child_class.id}'
        body = {
            'name': 'test 123',
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        child_class.refresh_from_db()
        self.assertEqual(LinkingClass.objects.filter(child_class_id=child_class.id, basic_class_id=result.data['id']).count(), 1)

    def test_post_sub_resource_to_linking_class_with_id(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        child_class = DataGenerator.set_up_child_class()
        url = f'/basicClasses/{basic_class.id}/childClass'
        body = {
            'id': child_class.id,
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        basic_class.refresh_from_db()
        linking_classes = LinkingClass.objects.filter(basic_class=basic_class, child_class=child_class)
        child_classes = ChildClass.objects.filter(name=child_class.name)
        self.assertEqual(len(linking_classes), 1)
        self.assertEqual(len(child_classes), 1)

    def test_post_sub_resource_to_linking_class_with_id_with_no_linking_cls(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        child_class = DataGenerator.set_up_child_class()
        url = f'/basicClasses/{basic_class.id}/childClassNoLinker'
        body = {
            'id': child_class.id,
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            result.data['errorMessage'], ErrorMessages.POST_SUB_WITH_ID_AND_NO_LINKING_CLASS.
            format(ChildClass.__name__),
        )

    def test_get_with_bool_filter_of_true(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class(active=True)
        url = f'/basicClass?filters=active=True'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertTrue(result.data[0].get('active'))

    def test_get_with_bool_filter_of_false(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class(active=False)
        url = f'/basicClass?filters=active=False'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertFalse(result.data[0].get('active'))

    def test_get_with_contains_all_filter_list(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class(active=False)
        url = f'/basicClass?filters=child_three__id__contains_all={basic_class.child_three.first().id}'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertFalse(result.data[0].get('active'))

    def test_post_with_required_field_missing_returns_400(self):
        # arrange
        body = {

        }
        url = '/basicClass'

        # act
        result = self.api_client.post(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_with_fields_from_foriegnkey(self):
        # arrange
        child_class_one = DataGenerator.set_up_child_class()
        basic_class = DataGenerator.set_up_basic_class(child_one=child_class_one)
        url = f'/basicClass/{basic_class.id}?fields=child_one_id'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data.keys()), 1)

    def test_get_with_include_that_has_excludes_removes_fields_properly(self):
        # arrange
        model_with_sensitive_data = DataGenerator.set_up_model_with_sensitive_data()
        basic_class = DataGenerator.set_up_basic_class(model_with_sensitive_data=model_with_sensitive_data)
        url = f'/basicClass/{basic_class.id}?include=model_with_sensitive_data'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(status.HTTP_200_OK, result.status_code)
        self.assertNotIn('topSecret', result.data['modelWithSensitiveData'].keys())

    def test_get_with_include_that_has_no_nested_child_returns_null(self):
        # arrange
        child_one = DataGenerator.set_up_child_class('test')
        basic_class = DataGenerator.set_up_basic_class(child_one=child_one)
        url = f'/basicClass/{basic_class.id}?include=child_one__nested_child'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(status.HTTP_200_OK, result.status_code)
        self.assertIsNone(result.data['childOne']['nestedChild'])

    def test_get_with_include_that_has_nested_child(self):
        # arrange
        child_one = DataGenerator.set_up_child_class('test')
        nested_child = DataGenerator.set_up_nested_child(child_one=child_one)
        basic_class = DataGenerator.set_up_basic_class(child_one=child_one)
        url = f'/basicClass/{basic_class.id}?include=child_one__nested_child'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(status.HTTP_200_OK, result.status_code)
        self.assertIsNotNone(result.data['childOne']['nestedChild'])

    def test_get_sub_with_pk_and_non_matching_parent_id_should_400(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        model = DataGenerator.set_up_model_with_parent_resource(basic_class=basic_class)
        other_model = DataGenerator.set_up_model_with_parent_resource()
        url = f'/basicClasses/{other_model.id}/modelWithParentResources/{model.id}'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(status.HTTP_400_BAD_REQUEST, result.status_code)

    def test_get_sub_with_pk_and_matching_parent_pk_should_200(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        model = DataGenerator.set_up_model_with_parent_resource(basic_class=basic_class)
        url = f'/basicClasses/{basic_class.id}/modelWithParentResources/{model.id}'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(status.HTTP_200_OK, result.status_code)

    def test_get_with_icontains_does_not_work_in_reverse(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        url = f'/basicClasses?filters=name__icontains={basic_class.name + generate_str(7)}'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(status.HTTP_200_OK, result.status_code)
        self.assertEqual(len(result.data), 0)

    def test_get_with_revicontains_matches(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        url = f'/basicClasses?filters=name__revicontains={basic_class.name + generate_str(7)}'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(status.HTTP_200_OK, result.status_code)
        self.assertEqual(len(result.data), 1)



class ReadReplicaTests(unittest.TestCase):
    api_client = APIClient()

    def test_get_should_fail_if_data_in_default_db(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class()
        url = f'/readReplicaBasicClass/{basic_class.id}'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(result.data['errorMessage'], ErrorMessages.DOES_NOT_EXIST.format(BasicClass.__name__, basic_class.id))

    def test_get_should_return_value_in_read_db_not_write_db(self):
        # arrange
        basic_class = DataGenerator.set_up_basic_class(write_db='readreplica')
        url = f'/readReplicaBasicClass/{basic_class.id}'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data['name'], basic_class.name)


class SecondDatabaseBasicClassTests(unittest.TestCase):
    api_client = APIClient()

    def test_post_successfully_saves_into_correct_db(self):
        # arrange
        url = '/secondDatabaseBasicClass'
        name = generate_str(15)
        body = {
            'name': name,
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        basic_class_count = BasicClass.objects.filter(name=name).using('readreplica').count()
        self.assertEqual(1, basic_class_count)


class StoredProcedureTests(unittest.TestCase):

    api_client = APIClient()

    @unittest.mock.patch('rest_framework_simplify.services.sql_executor.service.SQLServerExecutorService.call_stored_procedure')
    def test_post(self, mock_execute_stored_procedure):
        # arrange
        url = '/sqlStoredProcedures'
        body = {
            'spName': 'TestSQLServerStoredProc',
            'testId': 1234,
        }
        mock_execute_stored_procedure.return_value = [{'amount': Decimal('612.0000')}]

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data[0]['amount'], 612)

    def test_post_invalid_sp_returns_invalid_sp_error(self):
        # arrange
        url = '/sqlStoredProcedures'
        body = {
            'spName': str(uuid.uuid4())[:15],
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            result.data['errorMessage'],
            SimplifyStoredProcedureView.ErrorMessages.INVALID_STORED_PROCEDURE.format(body['spName']),
        )

    def test_post_without_param_returns_invalid_params_error(self):
        # arrange
        url = '/sqlStoredProcedures'
        body = {
            'spName': 'TestSQLServerStoredProc',
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            result.data['errorMessage'],
            SimplifyStoredProcedureView.ErrorMessages.INVALID_PARAMS.format(body['spName']),
        )

    @unittest.mock.patch('rest_framework_simplify.services.sql_executor.service.PostgresExecutorService.call_stored_procedure')
    def test_postgres(self, mock_execute_stored_procedure):
        # arrange
        url = '/postgresStoredProcedures'
        body = {
            'spName': 'postgres_format',
            'var_int': 1,
        }
        mock_execute_stored_procedure.return_value = [{'amount': Decimal('612.0000')}]

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)


class EmailTemplateTests(unittest.TestCase):

    api_client = APIClient()

    def test_send_email_400_if_bad_template_name(self):
        # arrange
        url = '/sendEmail'
        body = {
            'templateName': 'somethingRandom',
            'to': 'you@example.com',
            'signUpUrl': 'https://mywebsite.com/signup?token=LLK69FkQ12',
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            result.data['errorMessage'],
            SimplifyEmailTemplateView.ErrorMessages.INVALID_EMAIL_TEMPLATE.format(body['templateName']),
        )

    def test_send_email_400_if_invalid_params(self):
        # arrange
        url = '/sendEmail'
        body = {
            'templateName': 'DynamicEmail',
            'somethingWrong': 'you@example.com',
            'signUpUrl': 'https://mywebsite.com/signup?token=LLK69FkQ12',
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            result.data['errorMessage'],
            SimplifyEmailTemplateView.ErrorMessages.INVALID_PARAMS.format(body['templateName']),
        )

    def test_send_email_400_if_cant_find_html_file(self):
        # arrange
        url = '/sendEmail'
        body = {
            'templateName': 'TemplateNameWithoutHtmlFile',
            'to': 'you@example.com',
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            result.data['errorMessage'],
            SimplifyEmailTemplateView.ErrorMessages.MISSING_EMAIL_TEMPLATE_PATH.format(body['templateName']),
        )

    def test_send_email_400_if_rdml_still_in_html(self):
        # arrange
        url = '/sendEmail'
        body = {
            'templateName': 'EmailWithExtraSimplifyML',
            'to': 'you@example.com',
            'firstName': 'Chris',
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            result.data['errorMessage'],
            SimplifyEmailTemplateView.ErrorMessages.UNABLE_TO_POPULATE_TEMPLATE.format(body['templateName'], 'Extra-Simplifyml'),
        )

    @unittest.mock.patch('tests.email_templates.EmailService.send_email')
    def test_send_email_400_if_send_email_fails(self, mock_send_email):
        # arrange
        url = '/sendEmail'
        body = {
            'templateName': 'DynamicEmail',
            'to': 'you@example.com',
            'firstName': 'Chris',
            'teamName': 'Our Team',
            'signUpUrl': 'https://mywebsite.com/signup?token=LLK69FkQ12',
        }
        mock_send_email.side_effect = Exception('test')

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(result.data['errorMessage'], SimplifyEmailTemplateView.ErrorMessages.ERROR_SENDING_EMAIL)

    def test_send_email_400_if_missing_send_email_method(self):
        # arrange
        url = '/sendEmail'
        body = {
            'templateName': 'TemplateWithoutSendEmailMethod',
            'to': 'you@example.com',
            'firstName': 'Chris',
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(result.data['errorMessage'], SimplifyEmailTemplateView.ErrorMessages.MISSING_SEND_EMAIL_METHOD)

    def test_send_email_200_happy_path(self):
        # arrange
        url = '/sendEmail'
        body = {
            'templateName': 'DynamicEmail',
            'to': 'you@example.com',
            'firstName': 'Chris',
            'teamName': 'Our Team',
            'signUpUrl': 'https://mywebsite.com/signup?token=LLK69FkQ12',
        }

        # act
        result = self.api_client.post(url, body, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)


class OneToOneTests(unittest.TestCase):

    api_client = APIClient()

    def test_get_one_to_one(self):
        # arrange
        oto = DataGenerator.set_up_ont_to_one_class()
        url = f'/oneToOne/{oto.alternative_id}'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.data['alternativeId'], oto.alternative_id)


class RequestFieldsToSaveTests(unittest.TestCase):

    api_client = APIClient()

    def test_post_with_request_fields_to_save(self):
        # arrange
        url = '/requestFieldsToSaveClass'
        body = {

        }

        # act
        result = self.api_client.post(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        self.assertEqual(result.data['method'], 'POST')


class FilterablePropertiesTests(unittest.TestCase):

    api_client = APIClient()

    def test_filterable_property_properly_filters(self):
        # todo: this is a bad test due to how they are linked -- it can also cause issues expanding result set
        # arrange
        community_one = DataGenerator.set_up_community()
        community_two = DataGenerator.set_up_community(phase_group=community_one.phase_group)
        application = Application.get_lead_mgmt_application()
        community_application_one = DataGenerator.set_up_community_application(community=community_one, application=application, active=False)
        community_application_two = DataGenerator.set_up_community_application(community=community_two, application=application, active=False)

        url = f'/phaseGroups?filters=active=True|id__in={community_one.phase_group.id}'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data), 0)

    def test_filterable_property_properly_filters_false_boolean(self):
        # arrange
        community_one = DataGenerator.set_up_community()
        community_two = DataGenerator.set_up_community(phase_group=community_one.phase_group)
        application = Application.get_lead_mgmt_application()
        community_application_one = DataGenerator.set_up_community_application(community=community_one, application=application, active=False)
        community_application_two = DataGenerator.set_up_community_application(community=community_two, application=application, active=True)

        url = f'/phaseGroups?filters=active=False|id__in={community_one.phase_group.id}'

        # act
        result = self.api_client.get(url, format='json')

        # assert
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data), 1)

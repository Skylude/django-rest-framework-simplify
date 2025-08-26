import logging
import unittest
import unittest.mock

from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework.test import APIClient
from rest_framework import exceptions, status

from rest_framework_simplify.decorators import sensitive_rq_data, sensitive_rq_query_params
from rest_framework_simplify.exceptions import SimplifyAPIException


@unittest.mock.patch('test_app.views.ThrowHandler.post')
class ThrowHandlerTests(unittest.TestCase):

    def setUp(self):
        self.api_client = APIClient()

    def test_basic_exception(self, mock_post):
        # arrange
        mock_post.side_effect = Exception('random exception')

        # act
        res = self.api_client.post('/throws')

        # assert
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['errorMessage'], exceptions.APIException.default_detail)

    def test_coerce_django_404(self, mock_post):
        # arrange
        mock_post.side_effect = Http404('custom message')

        # act
        res = self.api_client.post('/throws')

        # assert
        self.assertEqual(res.status_code, exceptions.NotFound.status_code)
        self.assertEqual(res.data['errorMessage'], exceptions.NotFound.default_detail)

    def test_coerce_django_permission_denied(self, mock_post):
        # arrange
        mock_post.side_effect = PermissionDenied('custom message')

        # act
        res = self.api_client.post('/throws')

        # assert
        self.assertEqual(res.status_code, exceptions.PermissionDenied.status_code)
        self.assertEqual(res.data['errorMessage'], exceptions.PermissionDenied.default_detail)

    def test_permission_denied_error_message(self, mock_post):
        # arrange
        mock_post.side_effect = exceptions.PermissionDenied('custom message')

        # act
        res = self.api_client.post('/throws')

        # assert
        self.assertEqual(res.status_code, exceptions.PermissionDenied.status_code)
        self.assertEqual(res.data['errorMessage'], exceptions.PermissionDenied.default_detail)

    def test_custom_exception(self, mock_post):
        # arrange
        class FooException(exceptions.APIException):
            status_code = status.HTTP_418_IM_A_TEAPOT
            default_detail = 'FooException occurred'
        mock_post.side_effect = FooException()

        # act
        res = self.api_client.post('/throws')

        # assert
        self.assertEqual(res.status_code, FooException.status_code)
        self.assertEqual(res.data['errorMessage'], FooException.default_detail)

    def test_simplify_api_exception(self, mock_post):
        # arrange
        m = 'gud error'
        mock_post.side_effect = SimplifyAPIException(m, status.HTTP_418_IM_A_TEAPOT)

        # act
        res = self.api_client.post('/throws')

        # assert
        self.assertEqual(res.status_code, status.HTTP_418_IM_A_TEAPOT)
        self.assertEqual(res.data['errorMessage'], m)

    def test_exceptions_log(self, mock_post):
        # arrange
        arg = 'custom message'
        mock_exc = exceptions.ValidationError(arg)
        mock_post.side_effect = mock_exc
        logger = logging.getLogger('rest-framework-simplify-exception')
        with unittest.mock.patch.object(logger, 'exception') as mock_log:
            # act
            res = self.api_client.post('/throws?foo=bar', {'baz': 'qux'})

            # assert
            self.assertTrue(mock_log.called)
            error_message = mock_log.call_args[0][0]
            extra = mock_log.call_args[1]['extra']
            self.assertEqual(error_message, mock_exc.default_detail)
            self.assertEqual(extra['rq_query_params']['foo'], 'bar')
            self.assertEqual(extra['rq_data']['baz'], 'qux')
            self.assertEqual(extra['rq_method'], 'POST')
            self.assertEqual(extra['rq_path'], '/throws')
            self.assertEqual(extra['rs_status_code'], res.status_code)
            self.assertEqual(extra['exc_first_arg'], arg)
            self.assertEqual(extra['exc_detail'], mock_exc.detail)

    def test_log_masks(self, mock_post):
        # arrange
        @sensitive_rq_data('password', 'fav_color')
        @sensitive_rq_query_params('first_car')
        def wrapped_post(_):
            raise Exception('test exception')

        mock_post.side_effect = wrapped_post
        logger = logging.getLogger('rest-framework-simplify-exception')
        with unittest.mock.patch.object(logger, 'exception') as mock_log:
            # act
            body = {
                'username': 'gud',
                'password': 'secret',
                'fav_color': 'secret',
            }
            self.api_client.post('/throws?foo=bar&first_car=secret', body)

            # assert
            extra = mock_log.call_args[1]['extra']
            self.assertEqual(extra['rq_data']['username'], 'gud')
            self.assertNotEqual(extra['rq_data']['password'], 'secret')
            self.assertNotEqual(extra['rq_data']['fav_color'], 'secret')
            self.assertEqual(extra['rq_query_params']['foo'], 'bar')
            self.assertNotEqual(extra['rq_query_params']['first_car'], 'secret')

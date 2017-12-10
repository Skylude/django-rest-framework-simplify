import uuid
import unittest
import unittest.mock

from rest_framework_simplify.services.sql_executor.exceptions import EngineNotSupported
from rest_framework_simplify.services.sql_executor.service import SQLExecutorService, SQLServerExecutorService, PostgresExecutorService


class SQLExecutorServiceTests(unittest.TestCase):

    def test_none_type_engine_raises_engine_not_supported_exception(self):
        # arrange / act / assert
        with self.assertRaises(EngineNotSupported) as ex:
            service = SQLExecutorService(None, None, None, None)
        self.assertEqual(ex.exception.args[0], SQLExecutorService.ErrorMessages.UNSUPPORTED_ENGINE_ERROR.format('NoneType'))

    def test_engine_type_of_sql_server_gets_sql_server_class(self):
        # arrange / act
        service = SQLExecutorService(None, None, None, None, engine='sqlserver')

        # assert
        self.assertIsInstance(service, SQLServerExecutorService)

    def test_engine_type_of_postgres_server_gets_postgres_server_class(self):
        # arrange / act
        service = SQLExecutorService(None, None, None, None, engine='postgres')

        # assert
        self.assertIsInstance(service, PostgresExecutorService)

    @unittest.mock.patch('psycopg2.connect')
    def test_get_stored_procedure_params_returns_sp_params(self, mock_connect):
        # arrange
        service = SQLExecutorService(None, None, None, None, engine='postgres')
        rand_type = str(uuid.uuid4())[:20]
        param_one = str(uuid.uuid4())[:30]
        param_two = str(uuid.uuid4())[:30]
        param_three = str(uuid.uuid4())[:30]
        param_four = str(uuid.uuid4())[:30]
        returned_val = [('{1} {0}, {2} {0}, {3} {0}, {4} {0}'.format(rand_type, param_one, param_two, param_three,
                                                                     param_four),)]
        mock_connect.return_value.cursor.return_value.fetchall.return_value = returned_val

        # act
        sp_params = service.get_stored_procedure_params('SearchRentplusResidentByName')

        # assert
        self.assertEqual(sp_params, [param_one, param_two, param_three, param_four])

    @unittest.mock.patch('psycopg2.connect')
    def test_postgres_calls_correct_functions(self, mock_connection):
        sp_name = 'postgres_format'
        params = [1]
        service = PostgresExecutorService('localhost', 'rentplus', 'rentplus', 'test1234', '5432', 'postgres')
        query_result = [{'community_id': 1, 'resident_id': 123}]
        with mock_connection as c:
            c.return_value.cursor.return_value.callproc.return_value = query_result
            c.return_value.cursor.description = {'community_id', 'resident_id'}
            service.call_stored_procedure(sp_name, params)
            assert mock_connection.called
            assert mock_connection.return_value.cursor.called

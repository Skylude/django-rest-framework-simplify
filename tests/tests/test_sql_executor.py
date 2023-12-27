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

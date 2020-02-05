import datetime
import pymssql
import psycopg2
from django.db import connection
from django.conf import settings

from rest_framework_simplify.mapper import Mapper
from rest_framework_simplify.services.sql_executor.exceptions import EngineNotSupported


class SQLExecutorService:

    supported_engines = ['sqlserver', 'postgres']

    class ErrorMessages:
        UNSUPPORTED_ENGINE_ERROR = '{0} engine not supported!'
        METHOD_NOT_IMPLEMENTED = 'Method not implemented for this engine'

    def __init__(self, server, database, username, password, port=None, engine=None):
        # setup supported engines
        self.engine_map = {
            'sqlserver': SQLServerExecutorService,
            'postgres': PostgresExecutorService
        }

        # make sure we are dealing with a supported engine
        if engine not in self.supported_engines:
            error = 'NoneType' if not engine else engine
            raise EngineNotSupported(self.ErrorMessages.UNSUPPORTED_ENGINE_ERROR.format(error))
        self.engine = engine
        self.connection_data = {
            'server': server,
            'database': database,
            'username': username,
            'password': password,
            'port': port
        }
        self.__class__ = self.engine_map.get(self.engine)

    def build_sp_command(self, procedure_name, sp_params):
        raise NotImplementedError(self.ErrorMessages.METHOD_NOT_IMPLEMENTED)

    def call_stored_procedure(self, procedure_name, params_formatter):
        raise NotImplementedError(self.ErrorMessages.METHOD_NOT_IMPLEMENTED)


class PostgresExecutorService(SQLExecutorService):
    class Meta:
        proxy = True

    def build_sp_command(self, procedure_name, sp_params):
        pass

    def get_connection(self):
        if (
            settings.DATABASES['default']['HOST'] == self.connection_data['server'] and
            settings.DATABASES['default']['NAME'] == self.connection_data['database'] and
            settings.DATABASES['default']['USER'] == self.connection_data['username'] and
            settings.DATABASES['default']['PASSWORD'] == self.connection_data['password'] and
            settings.DATABASES['default']['PORT'] == str(self.connection_data['port'])
        ):
            return connection, True
        else:
            return psycopg2.connect('dbname={0} user={1} password={2} host={3} port={4}'.format(
                self.connection_data['database'], self.connection_data['username'], self.connection_data['password'],
                self.connection_data['server'], self.connection_data['port'])
            ), False

    def call_stored_procedure(self, procedure_name, params_formatter):
        connection, is_managed = self.get_connection()
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT pg_catalog.pg_get_function_arguments(p.oid)
                FROM pg_catalog.pg_proc p
                WHERE p.proname ~ '^({0})$'
                    AND pg_catalog.pg_function_is_visible(p.oid)
                LIMIT 1;
            '''.format(procedure_name.lower()))
            result = cursor.fetchall()
            params_result = []
            if len(result) == 0:
                params_result = None
            else:
                for x in result[0][0].split(','):
                    params_result.append(x.lstrip().split(' ')[0])
                if len(params_result) == 1 and params_result[0] == '':
                    params_result = []

            cursor.callproc(procedure_name, params_formatter(params_result))
            result = self.dictfetchall(cursor)

        if not is_managed:
            connection.close()
        
        return Mapper.camelcase_to_underscore(result)

    @staticmethod
    def dictfetchall(cursor):
        # Returns all rows from a cursor as a dict
        desc = cursor.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
        ]



class SQLServerExecutorService(SQLExecutorService):
    class Meta:
        proxy = True

    def build_sp_command(self, procedure_name, sp_params, params):
        command = 'EXEC ' + procedure_name
        if sp_params and len(sp_params) > 0:
            for index, param in enumerate(sp_params):
                command += ' ' + params[index] + ' = '
                if param is None:
                    command += 'NULL'
                elif type(param) == str:
                    # todo this could cause issues with someone wanting to pass in an empty string as a param
                    if len(param) == 0:
                        command += 'NULL'
                    else:
                        command += "'" + param + "'"
                elif type(param) == int:
                    command += str(param)
                elif type(param) == datetime.date:
                    command += "'" + param.strftime('%Y-%m-%d') + "'"
                elif type(param) == datetime.datetime:
                    command += "'" + param.strftime('%x %H:%M:%S') + "'"
                elif type(param) == bool:
                    command += str(int(param))
                if index < (len(sp_params) - 1):
                    command += ','
        return command

    def call_stored_procedure(self, procedure_name, params_formatter):
        with pymssql.connect(self.connection_data['server'], self.connection_data['username'],
                             self.connection_data['password'], self.connection_data['database']) as conn:
            with conn.cursor() as cursor:
                # this may need to change to only get IN params not out params -- we will see
                cursor.execute('SELECT PARAMETER_NAME FROM INFORMATION_SCHEMA.PARAMETERS WHERE SPECIFIC_NAME=%s AND PARAMETER_MODE=%s ORDER BY ORDINAL_POSITION', (procedure_name, 'IN'))
                result = cursor.fetchall()
                params = [row[0] for row in result]

                sp_command = self.build_sp_command(procedure_name, params_formatter(params), params)
                cursor.execute(sp_command)
                try:
                    result = cursor.fetchall()
                except:
                    # returns exception if the stored procedure doesn't return a value
                    conn.commit()
                    return []
                # commit so any inserts / updates are actually executed
                conn.commit()

                # grab column names back from the description -- could also possibly use as_dict
                column_names = [field[0] for field in cursor.description]
                mapped_result = [dict(zip(column_names, row)) for row in result]

                # now untitle case them, camel case them and finally snake_case them
                camel_cased_results = Mapper.titlecase_to_camelcase(mapped_result)
                snake_case_results = Mapper.camelcase_to_underscore(camel_cased_results)

                return snake_case_results

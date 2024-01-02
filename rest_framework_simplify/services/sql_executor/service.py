import datetime
from django.db import connections

from rest_framework_simplify.mapper import Mapper
from rest_framework_simplify.services.sql_executor.exceptions import EngineNotSupported


class SQLExecutorService:
    supported_engines = ["sqlserver", "postgres"]

    class ErrorMessages:
        UNSUPPORTED_ENGINE_ERROR = "{0} engine not supported!"
        METHOD_NOT_IMPLEMENTED = "Method not implemented for this engine"

    def __init__(
        self,
        server=None,
        database=None,
        username=None,
        password=None,
        port=None,
        engine=None,
        database_name="default",
    ):
        # setup supported engines
        self.engine_map = {
            "sqlserver": SQLServerExecutorService,
            "postgres": PostgresExecutorService,
        }
        # make sure we are dealing with a supported engine
        if engine not in self.supported_engines:
            error = "NoneType" if not engine else engine
            raise EngineNotSupported(
                self.ErrorMessages.UNSUPPORTED_ENGINE_ERROR.format(error)
            )
        self.engine = engine
        self.database_name = database_name
        self.__class__ = self.engine_map.get(self.engine)

    def build_sp_command(self, procedure_name, sp_params):
        raise NotImplementedError(self.ErrorMessages.METHOD_NOT_IMPLEMENTED)

    def call_stored_procedure(self, procedure_name, params_formatter):
        raise NotImplementedError(self.ErrorMessages.METHOD_NOT_IMPLEMENTED)

    @staticmethod
    def dictfetchall(cursor):
        desc = cursor.description
        return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]


class PostgresExecutorService(SQLExecutorService):
    class Meta:
        proxy = True

    def build_sp_command(self, procedure_name, sp_params):
        pass

    def get_connection(self):
        pass

    def call_stored_procedure(self, procedure_name, params_formatter):
        with connection[self.database_name].cursor() as c:
            c.execute(
                """
                SELECT pg_catalog.pg_get_function_arguments(p.oid)
                FROM pg_catalog.pg_proc p
                WHERE p.proname ~ '^({0})$'
                    AND pg_catalog.pg_function_is_visible(p.oid)
                LIMIT 1;
            """.format(procedure_name.lower())
            )
            result = c.fetchall()
            params_result = []
            if len(result) == 0:
                params_result = None
            else:
                for x in result[0][0].split(","):
                    params_result.append(x.lstrip().split(" ")[0])
                if len(params_result) == 1 and params_result[0] == "":
                    params_result = []
            c.callproc(procedure_name, params_formatter(params_result))
            result = self.dictfetchall(c)
        return result


class SQLServerExecutorService(SQLExecutorService):
    class Meta:
        proxy = True

    def build_sp_command(self, procedure_name, sp_params, params):
        command = "EXEC " + procedure_name
        if sp_params and len(sp_params) > 0:
            for index, param in enumerate(sp_params):
                command += " " + params[index] + " = "
                if param is None:
                    command += "NULL"
                elif isinstance(param, str):
                    # todo this could cause issues with someone wanting to pass in an empty string as a param
                    if len(param) == 0:
                        command += "NULL"
                    else:
                        command += "'" + param + "'"
                elif isinstance(param, int):
                    command += str(param)
                elif isinstance(param, datetime.date):
                    command += "'" + param.strftime("%Y-%m-%d") + "'"
                elif isinstance(param, datetime.datetime):
                    command += "'" + param.strftime("%x %H:%M:%S") + "'"
                elif isinstance(param, bool):
                    command += str(int(param))
                if index < (len(sp_params) - 1):
                    command += ","
        return command

    def call_stored_procedure(self, procedure_name, params_formatter):
        result = []
        with connections[self.database_name].cursor() as c:
            # this may need to change to only get IN params not out params -- we will see
            c.execute(
                "SELECT PARAMETER_NAME FROM INFORMATION_SCHEMA.PARAMETERS WHERE SPECIFIC_NAME=%s AND PARAMETER_MODE=%s ORDER BY ORDINAL_POSITION",
                (procedure_name, "IN"),
            )
            result = c.fetchall()
            params = [row[0] for row in result]
            c.callproc(procedure_name, params)
            result = self.dictfetchall(c)
            # now untitle case them, camel case them and finally snake_case them
        return result


from django import forms

from rest_framework_simplify.forms import StoredProcedureForm


# this should be a very generic form not a specific one
class TestSQLServerStoredProcForm(StoredProcedureForm):
    testId = forms.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        # add items to kwargs
        kwargs['connection_data'] = {
            'server': 'localhost',
            'database': 'test',
            'username': 'test',
            'password': 'test1234',
            'port': 1433,
            'engine': 'sqlserver',
            'sp_name': 'TestStoredProcedure'
        }
        # call base constructor
        super(TestSQLServerStoredProcForm, self).__init__(*args, **kwargs)


# this should be a very generic form not a specific one
class PostgresFormatForm(StoredProcedureForm):
    var_int = forms.IntegerField(required=True)
    var_str = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        # add items to kwargs
        kwargs['connection_data'] = {
            'server': 'localhost',
            'database': 'test',
            'username': 'test',
            'password': 'test1234',
            'port': 5432,
            'engine': 'postgres',
            'sp_name': 'postgres_format'
        }
        # call base constructor
        super(PostgresFormatForm, self).__init__(*args, **kwargs)


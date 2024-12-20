from distutils.core import setup

setup(
    name='django-rest-framework-simplify',
    version='4.0.3.dev1',
    description='Django Rest Framework Simplify',
    author='Skyler Cain',
    author_email='skylercain@gmail.com',
    url='https://github.com/Skylude/django-rest-framework-simplify',
    packages=['rest_framework_simplify', 'rest_framework_simplify.services', 'rest_framework_simplify.services.sql_executor'],
    install_requires=[
        'appdirs',
        'blinker',
        'Django',
        'djangorestframework',
        'packaging',
        'psycopg2',
        'pymssql',
        'pyparsing',
        'python-dateutil',
        'pytz',
        'requests',
        'six'
    ]
)

from distutils.core import setup

setup(
    name='django-restframework-simplify',
    version='1.0.0.dev',
    description='Django Rest Framework Simplify',
    author='Skyler Cain',
    author_email='skylercain@gmail.com',
    url='https://github.com/Skylude/django-restframework-simplify',
    packages=['rest_framework_simplify', 'rest_framework_simplify.services', 'rest_framework_simplify.services.sql_executor']
)

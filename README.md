# Django Rest Framework Simplify

This module was created in order to simplify [Django Rest Framework](https://github.com/encode/django-rest-framework) and to be able to genericize the most used views. It prevents redundant code and simplifies the views. It also adds serializer capability as well as including related models and additional properties.


## Settings
If you want to cache your GET requests you will need to specify which cache you will be using in your `settings.py`, for example:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}
```

To use the [Simplify exception handler](#exceptions) you must define it in the REST_FRAMEWORK settings:
```python
REST_FRAMEWORK = {
  'EXCEPTION_HANDLER': 'rest_framework_simplify.handler.exception_handler'
}
```
The logger named `rest-framework-simplify-exception` must be configured to see the logs.


## Models
Django Rest Framework Simplify provides a `SimplifyModel` class, which subclasses Django's `DjangoModel` class. The `SimplifyModel` allows you to have additional properties on your model, for example:
 * `CACHE` (bool) => Specifies if you want to cache the GET request.
 * `CACHE_TIME` (int) => The amount of time you would like this resource to be cached. (This number is in seconds)
 * `change_tracking_fields` (list) => All of the attributes that you would like to watch for changes (it will save the initial value as _{0}_initial)
    * ***NOTE***: When you add a foreign key, you will add the property to the list ('child_one' in the example below), but we will store the 'id' (i.e. _child_one_id_initial). You can easily get the initial value by calling get_change_tracking_field_initial_value with the field_name.
 * `get_filters` (method that returns a dict) => This will specify all of the class properties that you can filter your API query on.
 * `get_includes` (method that returns a list) => This will specify all of the related classes that your API can return with your payload.
 * `get_excludes` (method that returns a list) => This will specify all of the properties that you can exclude from an API response.

```python
from rest_framework_simplify.models import SimplifyModel

class BasicClass(SimplifyModel):
    CACHE = True
    CACHE_TIME = 15

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=15)
    active = models.BooleanField(null=False, default=True)
    child_one = models.OneToOneField('ChildClass', null=True, blank=True, related_name='basic_class_one')
    child_two = models.OneToOneField('ChildClass', null=True, blank=True, related_name='basic_class_two')
    exclude_field = models.CharField(max_length=25, null=True, blank=True)
    child_three = models.ManyToManyField('ChildClass', null=True, blank=True, related_name='basic_class_three')
    parent_class = models.ForeignKey('ParentClass', null=False, related_name='basic_class')

    change_tracking_fields = ['name', 'child_one']

    @property
    def test_prop(self):
        return True

    @staticmethod
    def get_filters():
        return {
            'active': {
                'type': bool,
                'list': False
            },
            'test_prop': {
                'type': bool,
                'list': False,
                'property': True
            },
            'child_three__id__contains_all': {
                'type': int,
                'list': True
            }
        }

    @staticmethod
    def get_includes():
        return ['child_one__id', 'child_three']

    @staticmethod
    def get_excludes():
        return ['exclude_field']
```


## Views
Django Rest Framework Simplify provides a `SimplifyView` class, which subclasses REST Framework's `APIView` class. You can then define other properties for your handler, for example:
 * `supported_methods` (list) => This is a list of the methods that are open to the API. The possible values are `GET`, `GET_SUB`, `GET_LIST`, `GET_LIST_SUB`, `PUT`, `POST_SUB`, `POST`, `DELETE`, and `DELETE_SUB`.
 * `linked_objects` (list) => This is a list of linking classes that will be open to the API via `get_includes`.

```python
from rest_framework_simplify.views import SimplifyView
from test_app.models import BasicClass, ParentClass

class BasicClassHandler(SimplifyView):
    def __init__(self):
        linked_objects = []
        linking_class = {
            'parent_resource': 'ParentClasses',
            'parent_cls': ParentClass,
            'parent_name': 'parent_class',
            'linking_cls': None,
            'sub_resource_name': None
        }
        linked_objects.append(linking_class)
        super().__init__(BasicClass, supported_methods=['GET', 'GET_LIST', 'PUT', 'POST'], linked_objects=linked_objects)
```

You will have to add the urls to your `urls.py` file.
```python
urlpatterns = [
    ...
    url(r'^(?P<parent_resource>[a-zA-z]+)/(?P<parent_pk>[0-9]+)/basicClass/(?P<pk>[0-9]+)$', BasicClassHandler.as_view()),
    url(r'^basicClass/(?P<pk>[0-9]+)$', BasicClassHandler.as_view()),
    url(r'^basicClass', BasicClassHandler.as_view()),
    ...
]
```

All endpoints have paging available. To use paging, you can add `?page=1&pageSize=50` to the end of your url.

Now we can:
 * GET `/basicClass?include=child_three&filters=active=true` => This will return a list of BasicClasses that are active and each BasicClass will have a ChildClass dict inside it.
 * GET `/basicClass/20?exclude=exclude_field` => This will return the BasicClass with an id of 20 and it won't return the exclude_field property.


## Stored Procedures/Functions
Django Rest Framework Simplify provides a `StoredProcedureForm` class and a `SimplifyStoredProcedureView` class to help you easily call stored procedures or functions from Django.

You can create your stored procedure or function like we have done here with our postgres function in `search_clients_by_zip.sql`.
```sql
CREATE OR REPLACE FUNCTION search_clients_by_zip (client_zip VARCHAR)

  RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    zip VARCHAR
  ) AS $result$

  BEGIN
    RETURN QUERY SELECT
      c.id,
      c.name,
      c.zip
    FROM client c
    WHERE c.zip = client_zip;
  END; $result$

  LANGUAGE 'plpgsql';
```

Now we will need to add them to our stored procedure forms in `forms.py`.
```python
from rest_framework_simplify.forms import StoredProcedureForm

class SearchClientsByZipForm(StoredProcedureForm):
    client_zip = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        # point this to your database
        kwargs['connection_data'] = {
            'server': settings.DATABASES['default']['HOST'],
            'database': settings.DATABASES['default']['NAME'],
            'username': settings.DATABASES['default']['USER'],
            'password': settings.DATABASES['default']['PASSWORD'],
            'port': int(settings.DATABASES['default']['PORT']),
            'engine': 'postgres',
            'sp_name': 'search_clients_by_zip'
        }
        super(SearchClientsByZipForm, self).__init__(*args, **kwargs)
```

We can make the stored procedures available via the API like we have done in our `stored_procedure_views.py`.
```python
from rest_framework_simplify.views import SimplifyStoredProcedureView
from test_app import forms

class StoredProcedureHandler(SimplifyStoredProcedureView):
    def __init__(self, *args, **kwargs):
        # point this to your database
        kwargs['forms'] = forms
        kwargs['server'] = settings.DATABASES['default']['HOST']
        kwargs['database'] = settings.DATABASES['default']['NAME']
        kwargs['username'] = settings.DATABASES['default']['USER']
        kwargs['password'] = settings.DATABASES['default']['PASSWORD']
        kwargs['port'] = int(settings.DATABASES['default']['PORT'])
        kwargs['engine'] = 'postgres'
        super(PostgresStoredProcedureHandler, self).__init__(*args, **kwargs)
```

You will have to add the urls to your `urls.py` file.
```python
urlpatterns = [
    ...
    url(r'^storedProcedures$', StoredProcedureHandler.as_view()),
    ...
]
```

Now we can:
 * POST `/storedProcedures` `{'spName': 'search_clients_by_zip', 'client_zip': '90210'}` => This will return the results of the search_clients_by_zip function.


## Email Templates
Django Rest Framework Simplify provides a `SimplifyEmailTemplateView` class and a `EmailTemplateForm` class to help you easily generate dynamic emails and send them from Django.

The `EmailTemplateForm` lets you dynamically generate emails via their simplify_ml (Simplify Markup Language). A simplify_ml starts with `%[`, contains the variable, and ends with `]`. For example, you would set up your email template like this `DynamicEmail.html`.
```html
<html>
<body>
    <p>Hello %[First-Name], sign up <a href="%[Sign-Up-Url]">here</a>.</p>
    <p>%[Copyright-Year] Copyright</p>
</body>
</html>
```

You will need to create a send email method that takes a Django Form as a parameter. It also has a `to`, `_from`, `subject`, and `html` on the form. Like we have here in `email_service.py`.
```python
class EmailService:
    @staticmethod
    def send_email(form=None):
        # You can put your logic here to send your email
        return {'id': 'agsjyfg7eg4j27', 'to': form.to, 'from': form._from, 'subject': form.subject, 'html': form.html}
```

You will need to setup your email template forms like we have done in `email_templates.py`. These will match the simplify_ml that you put in your html file.
```python
from rest_framework_simplify.forms import EmailTemplateForm
from test_app.email_service import EmailService

class DynamicEmailTemplate(EmailTemplateForm):
    to = forms.CharField(required=True)
    firstName = forms.CharField(required=True)
    signUpUrl = forms.CharField(required=True)
    teamName = forms.CharField(required=True)
    copyrightYear = forms.CharField(required=False, initial=timezone.now().strftime('%Y'))

    def __init__(self, *args, **kwargs):
        kwargs['default_data'] = {
            'subject': 'Welcome',
            'from': '"%[Team-Name]" <support@example.com>',
            'templateName': 'DynamicEmail',
            'templatePath': settings.EMAIL_TEMPLATES_BASE_PATH + 'DynamicEmail.html',
            'sendEmailMethod': EmailService.send_email
        }
        super(DynamicEmailTemplate, self).__init__(*args, **kwargs)
```

We can make the email templates available via the API with our `views.py`.
```python
from test_app import email_templates

class SendEmailHandler(SimplifyEmailTemplateView):
    def __init__(self, *args, **kwargs):
        # email_templates is your file with all you email template forms
        kwargs['templates'] = email_templates
        super(SendEmailHandler, self).__init__(*args, **kwargs)
```

You will have to add the urls to your `urls.py` file.
```python
urlpatterns = [
    ...
    url(r'^sendEmail$', SendEmailHandler.as_view()),
    ...
]
```

Now we can:
 * POST `/sendEmail` `{'templateName': 'DynamicEmail', 'to': 'to_address@test.com', 'firstName': 'Chris', 'signUpUrl': 'https://github.com/Skylude/django-rest-framework-simplify', 'teamName': 'My Team'}` => This will create the email and call `EmailService.send_email` with your form data. You can then choose what to do with that.


## Permissions

Simplify provides a variety of methods for customizing permissions that are heavily inspired by
[Rest Framework permissions](https://www.django-rest-framework.org/api-guide/permissions/).

### Queryset permission support

Permission support for a list view is facilitated by `get_queryset` whose implementation is
`return self.model.objects`. While `get_queryset` solves the problem of object level permissions on
a list view it also solves object permissions for single objects. The difference is a 404 type
exception will be raised instead of a 403 type exception. Queryset based permissions are not
sufficient for locking down all actions as `put` and `post` do not use the specified queryset.

Example:
```python
class FooHandler(SimplifyView):
    def __init__(self):
        super().__init__(FooModel, supported_methods=['GET'])

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
```

### Object creation permissions

Permissions for `post` requests are supported by `perform_create`. Keep in mind `has_permission` is
still invoked for post requests, but `has_object_permission` is not. `perform_create` is a good
place to set defaults the client should not be trusted to set or to reject creation based on the
user's permissions.

Example:
```python
class FooHandler(SimplifyView):
    def __init__(self):
        super().__init__(FooModel, supported_methods=['POST'])

    def perform_create(self, request_body):
        if request_body['group_id'] != self.request.user.group_id:
            raise ValidationError()
        request_body['created_by_id'] = request.user.id
```

### Object update permissions

While `put` requests invoke `has_object_permission` you may want to set defaults or perform
validation specific to a `put` request. `perform_update` is provided for these use cases.

Example:
```python
class FooHandler(SimplifyView):
    def __init__(self):
        super().__init__(FooModel, supported_methods=['PUT'])

    def perform_update(self, request_body):
        if request_body['group_id'] != self.request.user.group_id:
            raise ValidationError()
        request_body['updated_by_id'] = request.user.id
```

### Stored procedure forms

Stored procedure forms can perform validation and/or transformation by overriding the `clean` method
inherited from the Django `BaseForm` class. The `request` object is provided to the `clean` method
so the `user` may be accessed during cleaning.

Example:
```python
class PostgresForm(StoredProcedureForm):
    var_int = forms.IntegerField(required=True)

    def __init__(self, *args, **kwargs):
        kwargs['connection_data'] = {
          # ...
        }
        super(PostgresFormatForm, self).__init__(*args, **kwargs)

    def clean(self):
        if not self.request.user.is_super:
            return PermissionDenied()
        self.cleaned_data['var_int'] += 1
        return self.super().clean()
```

### Email forms

Email forms can perform validation and/or transformation by overriding the `clean` method inherited
from the Django `BaseForm` class. The `request` object is provided to the `clean` method so the
`user` may be accessed during cleaning.

Example:
```python
class FooEmailTemplate(EmailTemplateForm):
    to = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        kwargs['default_data'] = {
          # ...
        }
        super(DynamicEmailTemplate, self).__init__(*args, **kwargs)

    def clean(self):
        if not self.request.user.is_super:
            raise ValidationError('you gotta be super')
        self.cleaned_data['from'] = self.request.user.email
        return self.super().clean()
```

### Permission class support

> [!CAUTION]
> Permission classes making use of `has_object_permission` are partially implemented and should not be relied on.

Permission classes work as you would expect in Rest Framework. A default permission class may be
specified per Rest Framework's guidelines, otherwise the `AllowAny` permission class will be used.
Another option is to specify permission classes at the view level. This can be accomplished with the
`permission_classes` attribute or the `permission_classes` decorator if you are using function based
views. Custom permission classes are implemented by extending BasePermission which consists of two
methods `has_permission` and `has_object_permission`.

As advertised in Rest Framework's documentation, permission classes may be composed using bitwise
operators. `&` (and), `|` (or), and `~` (not). For example, `permissions_classes = [Super & ~Evil]`
a super user who is not evil.

`has_permission` is invoked before each handler (`get`, `put`, `post`, `delete`) and is intended to
resolve permissions pertaining to the model type rather than an instance of the model. Such as the
user's permission to read/write all instances of `FooModel` based on their user role.

`has_object_permission` is for resolving "row" level permissions. For example, the user may only
edit objects related to the user. `has_object_permission` is invoked when the desired instance is
fetched. Note `has_object_permission` is not invoked for a list view due to performance reasons or a
post because there is no instance. This behavior translates to Rest Framework's way of doing things.

Example:
```python
class BasicPermission(BasePermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return True


class FooHandler(SimplifyView):
    permission_classes = [BasicPermission]

    def __init__(self):
        super().__init__(FooModel, supported_methods=['GET'])
```

## Exceptions

See the [Settings](#settings) section for information on configuring the custom exception handler.

The Simplify exception handler aims to log detailed exceptions and return vague error messages to
consumers. This decision was made for security reasons.

Rest Framework's exceptions that extend APIException will propagate their status_code and
default_detail to the JSON response.

In order to raise a custom exception that will propagate to the JSON response you must extend Rest
Framework's APIException like so:
```python
from rest_framework.exceptions import APIException


class FooException(APIException):
    status_code = 418
    default_detail = 'Foo message.'
```

These JSON responses are of a consistent format like the following:
```json
{
  "errorMessage": "Foo message."
}
```

Additionally, the Simplify error handler converts Django exceptions to Rest Framework's equivalents
like the default Rest Framework exception handler.

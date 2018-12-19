import datetime
import dateutil.parser
import logging
import traceback

from decimal import Decimal
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields.related import ForeignKey, OneToOneField
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from mongoengine.errors import DoesNotExist

from rest_framework_simplify.exceptions import ParseException
from rest_framework_simplify.mapper import Mapper
from rest_framework_simplify.serializer import MongoEngineSerializer, SQLEngineSerializer
from rest_framework_simplify.services.sql_executor.service import SQLExecutorService
from rest_framework_simplify.errors import ErrorMessages


class SimplifyView(APIView):

    def __init__(self, model, linked_objects=[], supported_methods=[], read_db='default', write_db='default'):
        self.read_db = read_db
        self.write_db = write_db
        self.model = model
        self.supported_methods = supported_methods
        self.linked_objects = linked_objects
        if self.get_db_engine() == 'mongo':
            self.DoesNotExist = DoesNotExist
        else:
            self.DoesNotExist = ObjectDoesNotExist
        if self.get_db_engine() == 'mongo':
            self.serializer = MongoEngineSerializer
        else:
            self.serializer = SQLEngineSerializer

    def get_db_engine(self):
        if hasattr(self.model, 'validate'):
            return 'mongo'
        else:
            return 'sql'

    def delete(self, request, pk=None, parent_resource=None, parent_pk=None):
        if parent_pk and parent_resource and self.linked_objects:
            if 'DELETE_SUB' not in self.supported_methods:
                return self.create_response(error_message=ErrorMessages.DELETE_SUB_NOT_SUPPORTED
                                            .format(self.model.__name__))
        else:
            if 'DELETE' not in self.supported_methods:
                return self.create_response(error_message=ErrorMessages.DELETE_NOT_SUPPORTED.format(self.model.__name__))

        try:
            obj = self.model.objects.using(self.read_db).get(pk=pk)
        except self.DoesNotExist:
            raise self.DoesNotExist(ErrorMessages.DOES_NOT_EXIST.format(self.model.__name__, pk))

        # check query param to only delete linker
        delete_link_only = request.query_params.get('deleteLinkOnly', False)

        # further checks
        for linked_object in self.linked_objects:
            # we have a linking table we need to clear the linking table objects
            if linked_object['sub_resource_name'] and linked_object['linking_cls']:
                kwargs = {
                    linked_object['sub_resource_name']: obj
                }
                # get the linking table items
                linked_objs = linked_object['linking_cls'].objects.using(self.read_db).filter(**kwargs)
                for linked_obj in linked_objs:
                    linked_obj.delete(using=self.read_db)

            else:
                pass

        if not delete_link_only:
            obj.delete(using=self.write_db)

        return self.create_response()

    def get(self, request, pk=None, parent_resource=None, parent_pk=None):
        meta_request = request.query_params.get('meta', False)
        if meta_request:
            # grab models fields and return them as a dict
            meta_data = self.model.get_meta_data()
            return self.create_response(body=meta_data)

        # handle caching
        cache_key = None
        if hasattr(self.model, 'CACHE'):
            cache_key = request.get_full_path()
            result = cache.get(cache_key, None)
            if result:
                return self.create_response(body=result, using_cache=True, cache_key=cache_key)

        obj = None
        # if we have a primary key we are returning one result
        if pk:
            if not parent_resource and not parent_pk and 'GET' not in self.supported_methods:
                return self.create_response(error_message=ErrorMessages.GET_NOT_SUPPORTED.format(self.model.__name__))

            # try to get the sub resource of a parent -- this is to ensure you can only get access to sub items if you
            # have access to their parent item
            if parent_resource and parent_pk and self.linked_objects:
                if 'GET_SUB' not in self.supported_methods:
                    return self.create_response(error_message=ErrorMessages.GET_SUB_NOT_SUPPORTED.format(self.model.__name__))
                obj = self.get_obj_from_linked_objects(pk, parent_resource, parent_pk)
            # try to get the obj from db with no parent resource
            else:
                try:
                    obj = self.model.objects.using(self.read_db).get(pk=pk)
                except self.DoesNotExist:
                    raise self.DoesNotExist(ErrorMessages.DOES_NOT_EXIST.format(self.model.__name__, pk))

        else:
            # we could be a sub resource so we need to check if a parent_resource was passed in
            if parent_pk and parent_resource and self.linked_objects:

                snake_cased_url_tail = Mapper.camelcase_to_underscore(request.get_full_path().split('/')[-1])
                lives_on_parent_results = [i for i in self.linked_objects if 'lives_on_parent' in i
                                           and i['lives_on_parent'] and i['sub_resource_name'] == snake_cased_url_tail]

                if len(lives_on_parent_results) > 0:
                    if 'GET_SUB' not in self.supported_methods:
                        return self.create_response(error_message=ErrorMessages.GET_SUB_NOT_SUPPORTED.format(self.model.__name__))

                    linked_object = lives_on_parent_results[0]
                    parent_obj = linked_object['parent_cls'].objects.using(self.read_db).get(pk=parent_pk)
                    obj = getattr(parent_obj, linked_object['sub_resource_name'])
                else:
                    # check if this method has authorized sub resources
                    if 'GET_LIST_SUB' not in self.supported_methods:
                        return self.create_response(error_message=ErrorMessages.GET_LIST_SUB_NOT_SUPPORTED.format(self.model.__name__))
                    # find the resource that this request is looking for
                    obj = self.get_obj_from_linked_objects(pk, parent_resource, parent_pk)
            else:
                # trying to get ALL items in DB
                if 'GET_LIST' not in self.supported_methods:
                    return self.create_response(error_message=ErrorMessages.GET_LIST_NOT_SUPPORTED.format(self.model.__name__))
                obj = self.model.objects.using(self.read_db).all()

        # handle includes
        req_includes = request.query_params.get('include', [])
        if req_includes:
            req_includes = req_includes.split(',')
            if type(req_includes) is not list:
                req_includes = [req_includes]
        model_includes = self.model.get_includes() if hasattr(self.model, 'get_includes') else []
        include = [include.strip() for include in req_includes if Mapper.camelcase_to_underscore(include.strip()) in model_includes]

        # handle fields
        # if they explicitly ask for the field do we need to make them pass includes as well? currently yes
        req_fields = request.query_params.get('fields', [])
        if req_fields:
            req_fields = req_fields.split(',')
            if type(req_fields) is not list:
                req_fields = [req_fields]

        # todo: mucky and should be cleaned up a tid
        model_fields = []
        foreign_key_ids = []
        for field in self.model._meta.get_fields():
            model_fields.append(field.name)
            if type(field) in [OneToOneField, ForeignKey]:
                foreign_key_ids.append(field.name + '_id')
        fields = [field.strip() for field in req_fields if
                  Mapper.camelcase_to_underscore(field.strip())
                  in model_fields or field.strip() in include or Mapper.camelcase_to_underscore(field.strip()) in foreign_key_ids]

        # gefilter fish
        filters = request.query_params.get('filters', [])
        if filters:
            filter_kwargs = {}
            exclude_filter_kwargs = {}
            isolated_filter_kwargs = {}

            filters = filters.split('|')
            for filter in filters:
                exclude_filter = False
                isolate_filter = False

                filter_array = filter.split('=')
                filter_name = filter_array[0]
                filter_value = filter_array[1] if len(filter_array) > 1 else None

                # check if this is a filterable property
                if hasattr(self.model, 'get_filterable_properties'):
                    filterable_property = filter_name in self.model.get_filterable_properties().keys()
                else:
                    filterable_property = False
                filterable_properties = []

                # snake case the name
                filter_name = Mapper.camelcase_to_underscore(filter_name)
                if filter_name[0] == '!':
                    if filter_value:
                        exclude_filter = True
                    filter_name = filter_name[1:]

                if '__contains_all' in filter_name:
                    isolate_filter = True
                    #filter_name = filter_name.replace('__contains_all', '')

                # if filter is in model filters then add it to the kwargs
                model_filters = self.model.get_filters()
                if filter_name in model_filters.keys():
                    if model_filters[filter_name]['list']:
                        filter_value = [self.format_filter(filter_name, item, model_filters) for item in filter_value.split(',')]
                        # if its a not we need to add it to excluded filters

                        if exclude_filter:
                            exclude_filter_kwargs[filter_name] = filter_value
                        elif isolate_filter:
                            isolated_filter_kwargs[filter_name] = filter_value
                        else:
                            filter_kwargs[filter_name] = filter_value
                    else:
                        if exclude_filter:
                            exclude_filter_kwargs[filter_name] = self.format_filter(filter_name, filter_value,
                                                                                    model_filters)
                        elif isolate_filter:
                            isolated_filter_kwargs[filter_name] = self.format_filter(filter_name, filter_value,
                                                                                     model_filters)
                        else:
                            if filterable_property:
                                filterable_properties.append(self.model.get_filterable_properties()[filter_name]['query'])
                            else:
                                filter_kwargs[filter_name] = self.format_filter(filter_name, filter_value, model_filters)
            # narrow down items with the filters
            obj = obj.using(self.read_db).filter(**filter_kwargs)

            # filter out filterable properties
            if filterable_properties:
                obj = obj.using(self.read_db).filter(*filterable_properties)

            for filter_name, filter_value in isolated_filter_kwargs.items():
                filter_name = filter_name.replace('__contains_all', '')

                for x in range(0, len(filter_value)):
                    kwargs = {
                        '{0}'.format(filter_name): filter_value[x]
                    }
                    obj = obj.using(self.read_db).filter(**kwargs)

            # exclude any items that shouldnt be in the final list
            obj = obj.using(self.read_db).exclude(**exclude_filter_kwargs)

        # handle distinct
        distinct = request.query_params.get('distinct', False)
        if distinct:
            obj = obj.using(self.read_db).distinct()

        # handle ordering
        order_by = request.query_params.get('orderBy', None)
        if order_by:
            order_by = Mapper.camelcase_to_underscore(order_by)
            obj = obj.using(self.read_db).order_by(order_by)

        # handle paging Mr. Herman
        page = request.query_params.get('page', None)
        page_size = request.query_params.get('pageSize', None)
        total_items = None
        if page and page_size:
            # todo: if they didnt pass in an order_by and there is paging use default models paging if that doesnt
            # todo: exist use id -- if that doesnt exist dont order
            # need to get total items for response if paging
            total_items = obj.using(self.read_db).count()
            page = int(page)
            page_size = int(page_size)
            start = (page - 1) * page_size
            end = start + page_size
            obj = obj[start:end]

        # setup excludes
        excludes = self.model.get_excludes() if hasattr(self.model, 'get_excludes') else []

        return self.create_response(body=obj, serialize=True, include=include, exclude=excludes, fields=fields,
                                    count=total_items, using_cache=False, cache_key=cache_key)

    def get_obj_from_linked_objects(self, pk, parent_resource, parent_pk):
        # find the resource that this request is looking for
        for linked_object in self.linked_objects:
            if linked_object['parent_resource'] == parent_resource:
                if linked_object['parent_cls']:
                    # get the resource
                    parent_obj = linked_object['parent_cls'].objects.using(self.read_db).get(pk=parent_pk)
                else:
                    parent_obj = parent_pk
                # setup kwargs for django's orm to query
                kwargs = {
                    linked_object['parent_name']: parent_obj
                }

                # if there is a linking table do that logic
                if linked_object['linking_cls']:
                    # we have pk so we only need to check if the one linker exists
                    if pk:
                        try:
                            kwargs[linked_object['sub_resource_name']] = pk
                            linked_obj = linked_object['linking_cls'].objects.using(self.read_db).get(**kwargs)
                        except self.DoesNotExist:
                            raise self.DoesNotExist(ErrorMessages.DOES_NOT_EXIST.format(self.model.__name__, pk))
                        else:
                            return self.model.objects.using(read_db).get(pk=pk)

                    else:
                        # get the linking table items
                        linked_objs = linked_object['linking_cls'].objects.using(self.read_db).filter(**kwargs)

                        # go through linking table items and get the sub resources from each entry into a list
                        linked_obj_ids = [getattr(linked_obj, linked_object['sub_resource_name']).id for
                                          linked_obj in
                                          linked_objs]
                        return self.model.objects.using(self.read_db).filter(pk__in=linked_obj_ids)
                # no linking table and the link is on this obj itself
                else:
                    # if we have a pk we only want the exact resource we are looking for
                    if pk:
                        kwargs['pk'] = pk
                        return self.model.objects.using(self.read_db).get(**kwargs)
                    # no pk was passed in meaning we are getting the entire list of items that match the parent resource
                    else:
                        return self.model.objects.using(self.read_db).filter(**kwargs)

    def handle_exception(self, exc):
        status_code = status.HTTP_400_BAD_REQUEST
        if isinstance(exc, (exceptions.NotAuthenticated,
                            exceptions.AuthenticationFailed)):
            status_code = status.HTTP_403_FORBIDDEN

        # grab error_message from exception
        error_message = exc.args[0]

        if hasattr(self.request.query_params, 'dict'):
            query_params = self.request.query_params.dict()
        else:
            query_params = self.request.query_params

        if hasattr(self.request.data, 'dict'):
            request_data = self.request.data.dict()
        else:
            request_data = self.request.data

        # only want the last frame in generator
        exc_frame = None
        exc_filename = None
        exc_lineno = None
        exc_func = None
        for frame, lineno in traceback.walk_tb(exc.__traceback__):
            exc_frame = frame
            exc_lineno = lineno
            exc_func = frame.f_code.co_name
            exc_filename = frame.f_code.co_filename

        # log error
        logger = logging.getLogger('rest-framework-simplify-exception')
        extra_logging = {
            'rq_query_params': query_params,
            'rq_data': request_data,
            'rq_method': self.request.method,
            'rq_path': self.request.path,
            'rs_status_code': status_code,
            'exc_filename': exc_filename,
            'exc_func': exc_func,
            'exc_lineno': exc_lineno
        }

        logger.error(error_message, extra=extra_logging)
        return self.create_response(error_message=error_message, response_status=status_code)

    def post(self, request, parent_resource=None, parent_pk=None):
        # check we are authorized to POST
        if not parent_resource and not parent_pk and 'POST' not in self.supported_methods:
            return self.create_response(error_message=ErrorMessages.POST_NOT_SUPPORTED.format(self.model.__name__))

        reference_fields = None
        # have to figure out the parent_source to obj mappings i.e. /resource -> 'field_name' attr on the model
        if parent_resource and parent_pk and self.model.resource_mapping \
                and parent_resource in self.model.resource_mapping.keys():
            reference_fields = {
                self.model.resource_mapping[parent_resource]: parent_pk
            }
        # this is if we are using some id vs fk for parent
        elif parent_resource and parent_pk:
            # find the right linked obj
            for linked_object in self.linked_objects:
                if linked_object['parent_resource'] == parent_resource:
                    # should only do this if there is no parent_cls if there is a parent_cls there should be a resource
                    # mapping!
                    if not linked_object['parent_cls']:
                        request.data[linked_object['parent_name']] = parent_pk

        # check if they are passing an id in to just create a linking class
        id = request.data.get('id', None)

        # if i have an id and not an attribute linked_objects throw error
        if id and not hasattr(self, 'linked_objects'):
            return self.create_response(error_message=ErrorMessages.POST_SUB_WITH_ID_AND_NO_LINKING_CLASS.
                                        format(self.model.__name__))
        # im safe to assume i have linked_objects now lets check if we have a linking class
        if id:
            linked_classes = [linked_obj for linked_obj in self.linked_objects
                              if linked_obj['parent_resource'] == parent_resource and linked_obj['linking_cls']]
            if len(linked_classes) < 1:
                return self.create_response(error_message=ErrorMessages.POST_SUB_WITH_ID_AND_NO_LINKING_CLASS.
                                            format(self.model.__name__))

        # occasionally we may need to transform the request to fit the model -- this is generally an unrestful call
        if hasattr(self.model, 'transform_request'):
            transformed_request = self.model.transform_request(request)
            obj = self.model.parse(transformed_request, existing_id=id, reference_fields=reference_fields,
                                   request=request)
        else:
            # check for reference fields to parse them into the model
            obj = self.model.parse(request.data, existing_id=id, reference_fields=reference_fields, request=request)

        obj.cascade_save(write_db=self.write_db)

        # save linking table items -- todo: move this into cascade_save?
        if parent_pk and parent_resource and self.linked_objects:
            if 'POST_SUB' not in self.supported_methods:
                return self.create_response(error_message=ErrorMessages.POST_SUB_NOT_SUPPORTED(self.model.__name__))

            snake_cased_url_tail = Mapper.camelcase_to_underscore(request.get_full_path().split('/')[-1])
            self.execute_on_linked_object(obj, self.linked_objects, parent_resource, parent_pk, snake_cased_url_tail, self.write_db)

        return self.create_response(obj, response_status=status.HTTP_201_CREATED, serialize=True)

    def put(self, request, pk):
        if 'PUT' not in self.supported_methods:
            return self.create_response(error_message=ErrorMessages.PUT_NOT_SUPPORTED.format(self.model.__name__))
        obj = self.model.parse(request.data, existing_id=pk, request=request)

        obj.cascade_save()
        return self.create_response(obj, serialize=True)

    def create_response(self, body=None, response_status=None, error_message=None, content_type='application/json', serialize=False, exclude=[], include=[], fields=[], count=None, using_cache=False, cache_key=None):
        if using_cache:
            response = Response(body, status=status.HTTP_200_OK, content_type=content_type)
            response['Hit'] = 1
            return response

        if body is None and error_message:
            body = {
                'errorMessage': error_message
            }
            if not response_status:
                response_status = status.HTTP_400_BAD_REQUEST

        if not response_status:
            response_status = status.HTTP_200_OK

        if serialize:
            if body is None:
                body = {}
            else:
                serializer = self.serializer(exclude=exclude, include=include, fields=fields)
                body = serializer.serialize(body)
                body = Mapper.underscore_to_camelcase(body)
                if count is not None:
                    body = {
                        'count': count,
                        'data': body
                    }
        if cache_key and response_status == status.HTTP_200_OK:
            if hasattr(self.model, 'CACHE_TIME'):
                cache_time = self.model.CACHE_TIME
                cache.set(cache_key, body, cache_time)
        return Response(body, status=response_status, content_type=content_type)

    @staticmethod
    def format_filter(filter_name, filter_value, model_filters):
        if model_filters[filter_name]['type'] is datetime.datetime:
            return dateutil.parser.parse(filter_value)
        elif model_filters[filter_name]['type'] is bool:
            return filter_value.lower() == "true"
        elif model_filters[filter_name]['type'] is Decimal:
            return Decimal(filter_value)
        elif filter_value:
            return model_filters[filter_name]['type'](filter_value)
        else:
            return None

    @staticmethod
    def execute_on_linked_object(obj, linked_objects, passed_in_parent_resource, parent_pk, snake_cased_url_tail, write_db):
        linking_class_results = [i for i in linked_objects if
                                 i['parent_resource'] == passed_in_parent_resource and i['linking_cls']]
        lives_on_parent_results = [i for i in linked_objects if 'lives_on_parent' in i
                                   and i['lives_on_parent'] and i['sub_resource_name'] == snake_cased_url_tail]

        if len(lives_on_parent_results) > 0:
            linked_object = lives_on_parent_results[0]
            parent_obj = linked_object['parent_cls'].objects.get(pk=parent_pk)
            setattr(parent_obj, linked_object['sub_resource_name'], obj)
            parent_obj.save(using=write_db)
        elif len(linking_class_results) > 0:
            linked_object = linking_class_results[0]
            parent_obj = linked_object['parent_cls'].objects.get(pk=parent_pk)
            # create new linking table
            new_linking_obj = linked_object['linking_cls']()
            setattr(new_linking_obj, linked_object['parent_name'], parent_obj)
            setattr(new_linking_obj, linked_object['sub_resource_name'], obj)
            new_linking_obj.save(using=write_db)


class SimplifyStoredProcedureView(APIView):

    def __init__(self, *args, **kwargs):
        super(SimplifyStoredProcedureView, self).__init__(*args, **kwargs)
        self.forms = kwargs.get('forms', None)

    class ErrorMessages:
        INVALID_STORED_PROCEDURE = 'Stored procedure {0} is not defined'
        INVALID_PARAMS = 'Params for stored procedure {0} invalid'

    def handle_exception(self, exc):
        status_code = status.HTTP_400_BAD_REQUEST
        if isinstance(exc, (exceptions.NotAuthenticated,
                            exceptions.AuthenticationFailed)):
            status_code = status.HTTP_403_FORBIDDEN
        error_message = exc.args[0]

        if hasattr(self.request.query_params, 'dict'):
            query_params = self.request.query_params.dict()
        else:
            query_params = self.request.query_params

        if hasattr(self.request.data, 'dict'):
            request_data = self.request.data.dict()
        else:
            request_data = self.request.data

        # log error
        logger = logging.getLogger('rest-framework-simplify-exception')
        extra_logging = {
            'rq_query_params': query_params,
            'rq_data': request_data,
            'rq_method': self.request.method,
            'rq_path': self.request.path,
            'rs_status_code': status_code
        }
        logger.error(error_message, extra=extra_logging)

        return Response({'errorMessage': error_message}, status=status_code)

    def post(self, request):
        sp_name = request.data.get('spName', None)
        # get form based on sp_name
        if '_' in sp_name:
            format_sp_name = Mapper.underscore_to_titlecase(sp_name)
            form_name = format_sp_name + 'Form'
        else:
            form_name = sp_name + 'Form'
        if hasattr(self.forms, form_name):
            form_cls = getattr(self.forms, form_name)
        else:
            # form hasn't been created which means we throw an error until we create the form
            return Response({'errorMessage': self.ErrorMessages.INVALID_STORED_PROCEDURE.format(sp_name)},
                            status=status.HTTP_400_BAD_REQUEST)

        form = form_cls(request.data)

        # validate the model that was sent in
        if form.is_valid():
            result = form.execute_sp()
            camel_cased_results = Mapper().underscore_to_camelcase(result)

            # may need some type of serialization
            return Response(camel_cased_results, status=status.HTTP_200_OK)
        else:
            # not valid sp params
            return Response({'errorMessage': self.ErrorMessages.INVALID_PARAMS.format(sp_name)},
                            status=status.HTTP_400_BAD_REQUEST)


class SimplifyEmailTemplateView(APIView):

    def __init__(self, *args, **kwargs):
        super(SimplifyEmailTemplateView, self).__init__(*args, **kwargs)
        self.templates = kwargs.get('templates', None)

    class ErrorMessages:
        INVALID_EMAIL_TEMPLATE = 'Email template {0} is not defined'
        MISSING_EMAIL_TEMPLATE_PATH = 'Email template path {0} is not defined'
        INVALID_EMAIL_TEMPLATE_PATH = 'Email template path {0} could not be found'
        INVALID_PARAMS = 'Params for email template {0} invalid'
        ERROR_SENDING_EMAIL = 'An error occurred while sending the email'
        UNABLE_TO_POPULATE_TEMPLATE = 'Unable to populate all the needed fields in {0}. Field: {1}'
        MISSING_SEND_EMAIL_METHOD = 'Missing a send email method'

    def handle_exception(self, exc):
        status_code = status.HTTP_400_BAD_REQUEST
        if isinstance(exc, (exceptions.NotAuthenticated,
                            exceptions.AuthenticationFailed)):
            status_code = status.HTTP_403_FORBIDDEN
        error_message = exc.args[0]

        if hasattr(self.request.query_params, 'dict'):
            query_params = self.request.query_params.dict()
        else:
            query_params = self.request.query_params

        if hasattr(self.request.data, 'dict'):
            request_data = self.request.data.dict()
        else:
            request_data = self.request.data

        # log error
        logger = logging.getLogger('rest-framework-simplify-exception')
        extra_logging = {
            'rq_query_params': query_params,
            'rq_data': request_data,
            'rq_method': self.request.method,
            'rq_path': self.request.path,
            'rs_status_code': status_code
        }
        logger.error(error_message, extra=extra_logging)

        return Response({'errorMessage': error_message}, status=status_code)

    def post(self, request):
        template_name = request.data.get('templateName', None)
        # get form based on template_name
        form_name = template_name + 'Template'
        if hasattr(self.templates, form_name):
            form_cls = getattr(self.templates, form_name)
        else:
            # form hasn't been created which means we throw an error until we create the form
            return Response({'errorMessage': self.ErrorMessages.INVALID_EMAIL_TEMPLATE.format(template_name)},
                            status=status.HTTP_400_BAD_REQUEST)

        form = form_cls(request.data)
        res = form.send_email()

        # may need some type of serialization
        return Response(res, status=status.HTTP_200_OK)

import datetime
import decimal

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db.models import Model as DjangoModel
from django.db.models.fields import BinaryField, DateTimeField as DjangoDateTimeField, DecimalField
from django.db.models.fields.related import ForeignKey as DjangoForeignKey, OneToOneField

from mongoengine import DateTimeField, signals
from mongoengine.base.datastructures import EmbeddedDocumentList
from mongoengine.errors import DoesNotExist, ValidationError
from mongoengine.fields import ReferenceField

from .fields import SimplifyEncryptedField, SimplifyEncryptedCharField
from .errors import ErrorMessages
from .exceptions import ParseException
from .helpers import parse_binary, parse_date
from .mapper import Mapper


class SimplifyModel(DjangoModel):

    class Meta:
        abstract = True

    parseable_levels = 1
    resource_mapping = {}

    def __init__(self, *args, **kwargs):
        super(SimplifyModel, self).__init__(*args, **kwargs)
        self.related_items_to_be_saved = []
        self.encrypted_fields = []
        if hasattr(self, 'change_tracking_fields'):
            for x in self._meta.local_concrete_fields:
                if x.name in self.change_tracking_fields:
                    setattr(self, '_{0}_initial'.format(x.attname), getattr(self, x.attname))

    def change_tracking_field_has_changed(self, field_name):
        if hasattr(self, 'change_tracking_fields') and field_name in self.change_tracking_fields:
            field = self._meta.get_field(field_name)
            return getattr(self, '_{0}_initial'.format(field.attname)) != getattr(self, field.attname)
        else:
            raise Exception('{0} is not in the change_tracking_fields attribute'.format(field_name))

    def get_change_tracking_field_initial_value(self, field_name):
        if hasattr(self, 'change_tracking_fields') and field_name in self.change_tracking_fields:
            field = self._meta.get_field(field_name)
            return getattr(self, '_{0}_initial'.format(field.attname))
        else:
            raise Exception('{0} is not in the change_tracking_fields attribute'.format(field_name))

    @classmethod
    def parse(cls, data, existing_id=None, reference_fields=None, current_parse_level=1, request=None):
        """Parses a dictionary into a domain model.

        This parser will attempt to convert a dictionary object to the defined model. This is an abstract
        class and the defined model will extend this class and have this method. They can override it if they
        require additional functionality. At the end of this method it will also invoke the models business
        rules and if any of the business rules fail it will fail to parse

        :param current_parse_level: number of levels deep to parse
        :param data: dictionary to parse
        :param existing_id: if item is already in the database this is its primary key
        :param reference_fields: a list of fields which we need to pull from the database (foreign key fields)
        :return: returns a domain model from django or none if it doesn't match the definition
        """

        # if we didn't receive a dict for parsing return None
        if data is None or type(data) is not dict:
            # Django 2.0 changed to use QueryDict, if using 2.0, get the dict object from the QueryDict
            if hasattr(data, 'dict'):
                data = data.dict()
            else:
                raise ParseException(ErrorMessages.NO_DATA_OR_DATA_NOT_DICT)

        # if we have an existing_id we are retrieving the object from the database and updating its fields
        if existing_id:
            try:
                obj = cls.objects.get(pk=existing_id)
            except ObjectDoesNotExist:
                raise ParseException(ErrorMessages.UPDATE_WITH_NON_EXISTENT_ID)
        else:
            obj = cls()

        # utilize the classes meta information to get a list of all the fields -- use full_clean to validate obj
        if not hasattr(cls._meta, 'get_fields') or not hasattr(obj, 'full_clean'):
            raise ParseException(ErrorMessages.FIELD_INFO_MISSING)

        fields = cls._meta.get_fields()

        # loop through each field on the model
        for field in fields:
            field_name = field.name

            # if they passed in an id ignore it -- we've either gotten it from the db or it can't be set
            if field_name == 'id':
                continue

            else:
                # we want to map both camelCase and python_case
                cc_field = Mapper.underscore_to_camelcase(field_name)
                cc_field_value = data.get(cc_field, None)

                # use camelCase if provided if not use python_case
                field_value = cc_field_value if cc_field_value is not None else data.get(field_name, None)

                # if its a foreign key field we need to do some special processing
                if type(field) is DjangoForeignKey or type(field) is OneToOneField:
                    # reference fields are used when the id is in the url not in the data dictionary
                    if reference_fields is not None and field_name in reference_fields.keys():
                        # get the related_class of the field so we can use that to query the db to wire things up
                        related_cls = field.related_model

                        # query db for related_item_id that was passed in
                        try:
                            related_item = related_cls.objects.get(pk=reference_fields[field_name])
                            setattr(obj, field_name, related_item)
                        # couldn't find id of related_item in db so not a valid model definition
                        except ObjectDoesNotExist:
                            raise ParseException(ErrorMessages.RELATED_ITEM_DOES_NOT_EXIST.format(field_name))

                    # check if they are passing an id and want to simply change the foreign key id
                    elif field.name + '_id' in data.keys() \
                            or Mapper.underscore_to_camelcase(field.name + '_id') in data.keys():
                        # field_value will have _id in it
                        cc_field_name_id = Mapper.underscore_to_camelcase(field_name + '_id')
                        cc_field_value_id = data.get(cc_field_name_id, None)
                        setattr(obj, field.name + '_id', cc_field_value_id)

                    # check to see if we need to parse in another current_parse_level
                    elif field_name in obj.parseable_related_fields:
                        # get the related_class of the field so we can use that to query the db to wire things up
                        related_cls = field.related_model

                        # parse the object if we aren't in too deep
                        if current_parse_level <= cls.parseable_levels:
                            # if it is a dict we need to try and parse it
                            if type(field_value) is dict:
                                # check for an id so we can set existing_id on the next parse function
                                related_item_id = None
                                if 'id' in field_value.keys():
                                    related_item_id = field_value['id']
                                # increase the parse level to avoid going too deep
                                next_parse_level = current_parse_level + 1
                                # call parse on related_field
                                try:
                                    related_item = related_cls.parse(field_value, existing_id=related_item_id,
                                                                     current_parse_level=next_parse_level,
                                                                     request=request)
                                # overall parsing failed if we didn't a nested item and we should have
                                except ParseException as ex:
                                    raise ParseException(ErrorMessages.PARSEABLE_RELATED_FIELD_PARSE_FAILED.format(ex.args[0]))
                                else:
                                    setattr(obj, field_name, related_item)
                                    obj.related_items_to_be_saved.append(field_name)

                            # they are trying to set item to null todo: possibly delete item from db?
                            elif field_value is None:
                                pass
                        else:
                            raise ParseException(ErrorMessages.TOO_DEEP)

                # if the field name was passed in try to update it
                elif field_name in data.keys() or cc_field in data.keys():
                    if type(field) is DjangoDateTimeField and field_value:
                        field_value = parse_date(field_value)
                        if not field_value:
                            raise ParseException(ErrorMessages.COULD_NOT_PARSE_DATE_FIELD.format(field_name))
                    elif type(field) is BinaryField and field_value:
                        field_value = parse_binary(field_value)
                        if not field_value:
                            raise ParseException(ErrorMessages.COULD_NOT_PARSE_BINARY_FIELD.format(field_name))
                    elif (type(field) is SimplifyEncryptedCharField or type(field) is SimplifyEncryptedField) and field_value:
                        obj.encrypted_fields.append(field_name)
                    elif type(field) is DecimalField and field_value:
                        decimal_places = field.decimal_places
                        field_value = round(decimal.Decimal(field_value), decimal_places)
                    setattr(obj, field_name, field_value)

        # check if there is request data we want to save
        if hasattr(obj, 'REQUEST_FIELDS_TO_SAVE'):
            for request_field_to_save in obj.REQUEST_FIELDS_TO_SAVE:
                val = getattr(request, request_field_to_save[0], None)
                # if we are trying to save a user and its the anonymous one fail
                if val is AnonymousUser:
                    continue
                if getattr(obj, request_field_to_save[1], None) in [None, '']:
                    setattr(obj, request_field_to_save[1], val)

        # try to utilize django's full_clean method to ensure the model validates
        try:
            obj.full_clean(exclude=['id'] + obj.related_items_to_be_saved + obj.encrypted_fields)
        except DjangoValidationError as ex:
            raise ParseException(ex)

        # run business rules
        # todo: run business rules
        return obj

    def cascade_save(self, write_db='default'):
        # todo: check into optimizing this with a possible related_item.reload instead of setting the attr
        for related_item_to_be_saved in self.related_items_to_be_saved:
            related_item = getattr(self, related_item_to_be_saved)
            related_item.cascade_save(write_db=write_db)
            setattr(self, related_item_to_be_saved, related_item)
        self.save(using=write_db)

    @classmethod
    def get_meta_data(cls):
        meta_data = {
            'fields': []
        }
        fields = cls._meta.get_fields()
        for field in fields:
            field_data = {}
            internal_type = field.get_internal_type()
            name = field.name
            if internal_type in ['ForeignKey', 'OneToOne']:
                related_model = field.related_model.__name__
                field_data['related_model'] = related_model
            field_data['name'] = name
            field_data['type'] = internal_type
            if hasattr(field, 'choices'):
                field_data['choices'] = field.choices
            meta_data['fields'].append(field_data)
        return meta_data

    @property
    def parseable_related_fields(self):
        return []


class RDDocument(object):
    created = DateTimeField()
    updated = DateTimeField()

    @classmethod
    def parse(cls, data, existing_id=None, reference_fields=None):
        if data is None or type(data) is not dict:
            # Django 2.0 changed to use QueryDict, if using 2.0, get the dict object from the QueryDict
            if hasattr(data, 'dict'):
                data = data.dict()
            else:
                return None

        # if we passed in an id it means we are parsing an existing object and updating fields
        if existing_id:
            try:
                obj = cls.objects.get(pk=existing_id)
            except DoesNotExist:
                return None
        else:
            obj = cls()
        # need _fields from mongoengines Document class and validate method
        if not hasattr(obj, '_fields') or not hasattr(obj, 'validate'):
            return None

        fields = obj._fields
        # loop through each field on the model
        for field in fields:
            # if we are parsing an object from a dictionary and it has an id let's save time and get from db
            if field == 'id':
                continue
            else:
                # we want to map both camelCase and python_case
                camel_case_field = Mapper.underscore_to_camelcase(field)
                camel_case_field_value = data.get(camel_case_field, None)
                # use camelCase if provided if not use python_case
                field_value = camel_case_field_value if camel_case_field_value is not None else data.get(field, None)
                if hasattr(obj, field) and (field in data.keys() or camel_case_field in data.keys() or (reference_fields is not None and field in reference_fields.keys())):
                    if type(obj[field]) is EmbeddedDocumentList:
                        nested_cls = getattr(cls, field).field.document_type
                        list_items = []
                        for list_item in field_value if field_value else []:
                            parsed_item = nested_cls.parse(list_item)
                            list_items.append(parsed_item)
                        obj[field] = list_items

                    elif type(getattr(cls, field)) is ReferenceField and reference_fields and field in reference_fields.keys():
                        reference_cls = getattr(cls, field).document_type
                        try:
                            obj[field] = reference_cls.objects.get(pk=reference_fields[field])
                        except DoesNotExist:
                            return None
                    else:
                        obj[field] = field_value

        try:
            obj.validate()
        except ValidationError:
            return None

        return obj


def pre_save(sender, document):
    if hasattr(document, 'updated'):
        document.updated = datetime.datetime.utcnow()

    if hasattr(document, 'created') and not document.created:
        document.created = datetime.datetime.utcnow()

signals.pre_save.connect(pre_save)

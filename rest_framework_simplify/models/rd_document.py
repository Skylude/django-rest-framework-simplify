import datetime

from mongoengine import DateTimeField, signals
from mongoengine.base.datastructures import EmbeddedDocumentList
from mongoengine.errors import DoesNotExist, ValidationError
from mongoengine.fields import ReferenceField

from rest_framework_simplify.mapper import Mapper


class RDDocument:
    created = DateTimeField()
    updated = DateTimeField()

    @classmethod
    def parse(cls, data, existing_id=None, reference_fields=None):
        if data is None or type(data) is not dict:
            # Django 2.0 changed to use QueryDict, if using 2.0, get the dict object from the QueryDict
            if hasattr(data, "dict"):
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
        if not hasattr(obj, "_fields") or not hasattr(obj, "validate"):
            return None

        fields = obj._fields
        # loop through each field on the model
        for field in fields:
            # if we are parsing an object from a dictionary and it has an id let's save time and get from db
            if field == "id":
                continue
            else:
                # we want to map both camelCase and python_case
                camel_case_field = Mapper.underscore_to_camelcase(field)
                camel_case_field_value = data.get(camel_case_field, None)
                # use camelCase if provided if not use python_case
                field_value = (
                    camel_case_field_value
                    if camel_case_field_value is not None
                    else data.get(field, None)
                )
                if hasattr(obj, field) and (
                    field in data.keys()
                    or camel_case_field in data.keys()
                    or (
                        reference_fields is not None
                        and field in reference_fields.keys()
                    )
                ):
                    if type(obj[field]) is EmbeddedDocumentList:
                        nested_cls = getattr(cls, field).field.document_type
                        list_items = []
                        for list_item in field_value if field_value else []:
                            parsed_item = nested_cls.parse(list_item)
                            list_items.append(parsed_item)
                        obj[field] = list_items

                    elif (
                        type(getattr(cls, field)) is ReferenceField
                        and reference_fields
                        and field in reference_fields.keys()
                    ):
                        reference_cls = getattr(cls, field).document_type
                        try:
                            obj[field] = reference_cls.objects.get(
                                pk=reference_fields[field],
                            )
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
    if hasattr(document, "updated"):
        document.updated = datetime.datetime.utcnow()

    if hasattr(document, "created") and not document.created:
        document.created = datetime.datetime.utcnow()


signals.pre_save.connect(pre_save)

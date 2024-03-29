from django.db.models import BinaryField, QuerySet as DjangoQuerySet, DecimalField, Manager
from django.db.models.fields.related import ForeignKey as DjangoForeignKey, OneToOneField, ManyToManyField

from rest_framework_simplify.helpers import binary_string_to_string
from rest_framework_simplify.mapper import Mapper


memoized_type_mappings = {}

class SQLEngineSerializer:

    def __init__(self, include=[], exclude=[], fields=[]):
        self.include = include
        self.exclude = exclude
        self.fields = fields

    def model_to_dict(self, manager_query_or_model):
        # if its a related manager field (many to one or many to many) -- get all objs
        if issubclass(type(manager_query_or_model), Manager):
            manager_query_or_model = list(manager_query_or_model.all())

        if type(manager_query_or_model) == DjangoQuerySet:
            manager_query_or_model = list(manager_query_or_model)

        is_single_item = False
        if type(manager_query_or_model) != list:
            manager_query_or_model = [manager_query_or_model]
            is_single_item = True

        if len(manager_query_or_model) == 0:
            return []

        raw_models = [
            self.one_model_to_dict(model)
            for model
            in manager_query_or_model
        ]

        if is_single_item:
            return raw_models[0]
        else:
            return raw_models

    def one_model_to_dict(self, model):
        foreign_key_fields, decimal_fields, binary_fields, all_fields = self.get_fields_by_type(type(model))

        if self.fields:
            field_names = [
                field_name
                for field_name
                in all_fields
                if field_name in self.fields 
                or Mapper.string_underscore_to_camelcase(field_name) in self.fields
                or '{}_id'.format(field_name) in self.fields
                or Mapper.string_underscore_to_camelcase('{}_id'.format(field_name)) in self.fields
            ]
        else:
            field_names = all_fields

        raw_model = {}

        for field_name in field_names:
            if field_name in foreign_key_fields:
                id_key = '{}_id'.format(field_name)
                raw_model[id_key] = getattr(model, id_key)
            else:
                raw_attribute = getattr(model, field_name)
                if field_name in decimal_fields and raw_attribute is not None:
                    raw_model[field_name] = float(raw_attribute)
                elif field_name in binary_fields and raw_attribute is not None:
                    # this is a bad solution as we get more
                    # binary types we could run into problems as this returns and unencoded string
                    # rather than the actual byte array -- if we need the actual byte array we are
                    # going to need to fix up the serializer
                    raw_model[field_name] = binary_string_to_string(bytes(raw_attribute))
                else:
                    raw_model[field_name] = raw_attribute

        if hasattr(model, 'get_excludes'):
            for exclude in model.get_excludes():
                if exclude in raw_model.keys():
                    del raw_model[exclude]
    
        return raw_model

    def get_fields_by_type(self, model_type):
        if model_type not in memoized_type_mappings:
            all_field_types = [field for field in model_type._meta.get_fields() if not field.auto_created and field.concrete and type(field) is not ManyToManyField]
            all_fields = set((field.name for field in all_field_types))
            foreign_key_fields = set((field.name for field in all_field_types if type(field) in [DjangoForeignKey, OneToOneField]))
            decimal_fields = set((field.name for field in all_field_types if type(field) is DecimalField))
            binary_fields = set((field.name for field in all_field_types if type(field) is BinaryField))
            memoized_type_mappings[model_type] = (foreign_key_fields, decimal_fields, binary_fields, all_fields)

        return memoized_type_mappings[model_type]

    def serialize(self, obj):
        if type(obj) == DjangoQuerySet or type(obj) == list:
            # todo: check efficiency of this vs serializing entire queryset
            return [self.serialize_one(item) for item in obj]
        else:
            return self.serialize_one(obj)

    def serialize_one(self, obj):
        view_model = self.model_to_dict(obj)
        includes = {}
        for include in self.include:
            if self.fields and include not in self.fields:
                continue

            field = Mapper.camelcase_to_underscore(include.split('__', 1)[0])
            if '__' in include:
                item = Mapper.camelcase_to_underscore(include.split('__', 1)[1])
                if field in includes.keys():
                    includes[field].append(item)
                else:
                    includes[field] = [item]

            else:
                includes[field] = []

        # make a new list that groups related items together i.e. address__state and address__address_type
        # maybe have it be a dictionary { address: [state, address_type], num_communities: None }
        for field, related_items in includes.items():

            if related_items:
                try:
                    related_obj = getattr(obj, field)
                    related_obj_exists = True
                except AttributeError:
                    related_obj_exists = False

                if related_obj_exists and related_obj is not None:
                    if related_obj is not None:
                        view_model[field] = self.serialize_related(related_obj, related_items)
                    else:
                        view_model[field] = None
                else:
                    view_model[field] = None

            else:
                field = Mapper.camelcase_to_underscore(field)
                try:
                    related_obj = getattr(obj, field)
                    related_obj_exists = True
                except AttributeError:
                    related_obj_exists = False

                if related_obj_exists and related_obj is not None:
                    if type(related_obj) is list:
                        related_obj_result = []
                        for related_obj_item in related_obj:
                            if type(related_obj_item) in [int, bool, str, float, dict]:
                                related_obj_result.append(related_obj_item)
                            else:
                                related_view_model = self.model_to_dict(related_obj_item)
                                related_obj_result.append(related_view_model)
                        view_model[field] = related_obj_result
                    else:
                        if type(related_obj) in [int, bool, str, float, dict]:
                            view_model[field] = related_obj
                        else:
                            related_view_model = self.model_to_dict(related_obj)
                            view_model[field] = related_view_model
                else:
                    view_model[field] = None

        if self.exclude:
            for exclude_item in self.exclude:
                if exclude_item in view_model.keys():
                    del view_model[exclude_item]

        return view_model

    def serialize_related(self, field_obj, include_items):
        # if its a related manager field (many to one or many to many) -- get all objs
        if issubclass(type(field_obj), Manager):
            field_obj = field_obj.all()
        view_model = self.model_to_dict(field_obj)
        # we are trying to serialize a list of related objs
        if type(view_model) is list:
            for idx, vm in enumerate(view_model):
                self.add_includes_to_view_model(field_obj[idx], include_items, vm)

        else:
            self.add_includes_to_view_model(field_obj, include_items, view_model)

        # model to dict removes these but I want to make sure i also remove them here in case they try to include them
        if type(view_model) is list:
            for idx, vm in enumerate(view_model):
                if hasattr(field_obj[idx], 'get_excludes'):
                    self.remove_excludes_from_view_model(field_obj[idx].get_excludes(), vm)

        else:
            if hasattr(field_obj, 'get_excludes'):
                self.remove_excludes_from_view_model(field_obj.get_excludes(), view_model)

        return view_model

    # extracted from serialize_related to reuse when serialize related has to do a list with a list inside it
    def add_includes_to_view_model(self, field_obj, include_items, view_model):
        # do similar to what serialize one does in order to avoid overwriting objects
        # i.e. resident__person, resident__unit
        includes = {}
        for include in include_items:
            field = Mapper.camelcase_to_underscore(include.split('__', 1)[0])
            if '__' in include:
                item = Mapper.camelcase_to_underscore(include.split('__', 1)[1])
                if field in includes.keys():
                    includes[field].append(item)
                else:
                    includes[field] = [item]

            else:
                includes[field] = []

        for field, related_items in includes.items():
            if related_items and getattr(field_obj, field) is not None:
                related_obj = getattr(field_obj, field)
                view_model[field] = self.serialize_related(related_obj, related_items)
            else:
                item_to_serialize = getattr(field_obj, field, None)
                if item_to_serialize is not None:
                    # do we check if they are basic types and then not try and serialize?
                    if type(item_to_serialize) in [int, bool, str, float, dict]:
                        view_model[field] = item_to_serialize
                    else:
                        dict_item = self.model_to_dict(item_to_serialize)
                        view_model[field] = dict_item
                else:
                    view_model[field] = None

    @staticmethod
    def remove_excludes_from_view_model(exclude_items, view_model):
        for exclude_item in exclude_items:
            if exclude_item in view_model.keys():
                del view_model[exclude_item]

    @staticmethod
    def format_data(data, pk):
        data['id'] = pk
        return data

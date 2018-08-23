import datetime
import base64
import json

from bson.dbref import DBRef
from bson.objectid import ObjectId
from django.core import serializers
from django.db.models import BinaryField, QuerySet as DjangoQuerySet, DecimalField, Manager
from django.db.models.fields.related import ForeignKey as DjangoForeignKey, OneToOneField
from mongoengine.queryset import QuerySet

from rest_framework_simplify.helpers import convert_serialized_binary_to_string
from rest_framework_simplify.mapper import Mapper


class MongoEncoder(object):
    def __init__(self, obj, include=[], exclude=[], func_generic_extra_info=[], func_extra_info=[]):
        self.main_obj = obj
        self.exclude = exclude
        self.include = include
        self.final_fields = []
        self.func_extra_info = func_extra_info
        self.func_generic_extra_info = func_generic_extra_info
        obj_to_mongo = obj.to_mongo()
        self.fields = obj_to_mongo.keys()

        for f in self.fields:
            val = self.h_value(f, obj, obj_to_mongo[f])
            if val is not None:
                self._sett_attr(f, val)
        for i in self.include:
            if isinstance(i, dict):
                k = i.keys()[0]
                if not hasattr(self, k):
                    self._sett_attr(k, i.values()[0])

    def _sett_attr(self, k, v):
        setattr(self, k, v)
        self.final_fields.append(k)

    def print_all(self):
        for f in self.final_fields:
            print("F [%s] Val [%s]" % (f, getattr(self, f)))

    def to_dict(self):
        d = {}
        for f in self.final_fields:
            v = getattr(self, f, None)
            if v is not None:
                d[f] = v
        for f in self.func_generic_extra_info:
            f(d)
        for f in self.func_extra_info:
            f(d)

        return d

    def h_value(self, f, obj, obj_to_mongo):
        if f in self.exclude:
            return None
        if isinstance(obj_to_mongo, dict):
            tmp_ret = {}
            for k in obj_to_mongo:
                new_obj = obj_to_mongo[k]
                try:
                    new_obj_to_mongo = new_obj.to_mongo()
                except:
                    new_obj_to_mongo = new_obj
                val = self.h_value(k,new_obj,new_obj_to_mongo)
                if val is not None:
                    tmp_ret.update({k:val})
            return tmp_ret

        elif isinstance(obj_to_mongo, str):
            return u"%s"%obj_to_mongo
        elif isinstance(obj_to_mongo, datetime.datetime):
            return obj_to_mongo.strftime('%Y-%m-%dT%H:%M:%S')
        elif isinstance(obj_to_mongo, datetime.date):
            return obj_to_mongo.strftime('%Y-%m-%d')
        elif isinstance(obj_to_mongo, ObjectId):
            return u"%s"%str(obj_to_mongo)
        elif isinstance(obj_to_mongo, list):
            tmp_list_ret = []
            for position, tmp in enumerate(obj_to_mongo):
                if isinstance(tmp, dict):
                    tmp_list_ret.append(self.h_value(f,tmp,tmp))
                elif isinstance(tmp, DBRef):
                    new_obj = getattr(obj,f)[position]
                    new_obj_to_mongo = new_obj.to_mongo()
                    tmp_ret = {}
                    for fn in new_obj_to_mongo.keys():
                        val = self.h_value(fn,new_obj,new_obj_to_mongo[fn])
                        if val is not None:
                            tmp_ret.update({fn:val})
                    if len(tmp_ret):
                        tmp_list_ret.append(tmp_ret)
                elif isinstance(tmp, str):
                    tmp_list_ret.append(self.h_value(f, tmp, tmp))
            return tmp_list_ret
        elif isinstance(obj_to_mongo, DBRef):
            new_obj_to_mongo = getattr(obj, f).to_mongo()
            new_obj = getattr(obj, f)
            tmp_ret = {}
            for fn in new_obj_to_mongo.keys():
                val = self.h_value(fn, new_obj, new_obj_to_mongo[fn])
                if val is not None:
                    tmp_ret.update({fn: val})
            return tmp_ret
        else:
            return obj_to_mongo


class MongoEngineSerializer(object):
    def __init__(self, include=[], exclude=[], func_generic_extra_info=[], func_extra_info=[], fields=[]):
        self.include = include
        self.exclude = exclude
        self.fields = fields
        self.func_generic_extra_info = func_generic_extra_info
        self.func_extra_info = func_extra_info

    def serialize(self, obj, indent=0):
        ret = []
        if isinstance(obj, QuerySet):
            for o in obj:
                ret.append(MongoEncoder(obj=o, include=self.include, exclude=self.exclude, func_generic_extra_info=self.func_generic_extra_info, func_extra_info=self.func_extra_info).to_dict())

        else:
            ret = MongoEncoder(obj=obj, include=self.include, exclude=self.exclude, func_generic_extra_info=self.func_generic_extra_info, func_extra_info=self.func_extra_info).to_dict()

        return ret


class SQLEngineSerializer:

    def __init__(self, include=[], exclude=[], fields=[]):
        self.include = include
        self.exclude = exclude
        self.fields = fields

    def model_to_dict(self, obj):
        # if its a related manager field (many to one or many to many) -- get all objs
        if issubclass(type(obj), Manager):
            obj = obj.all()
        if type(obj) == DjangoQuerySet or type(obj) == list:
            json_data_str = serializers.serialize('json', obj)
            plain_dict = json.loads(json_data_str)
            model_dict = [self.format_data(item['fields'], item['pk']) for item in plain_dict]
            if len(model_dict) == 0:
                return []
            cls = type(obj[0])

        # serializers take a query set so if it isn't we need to make it a list
        else:
            json_data_str = serializers.serialize('json', [obj])
            plain_dict = json.loads(json_data_str)
            model_dict = plain_dict[0]['fields']
            if obj._meta.pk.attname != 'id':
                model_dict[obj._meta.pk.attname] = plain_dict[0]['pk']
            else:
                model_dict['id'] = plain_dict[0]['pk']
            cls = type(obj)


        # get a list of all foreign keys on this obj
        foreign_key_fields = [field.name for field in cls._meta.get_fields() if type(field) in [DjangoForeignKey, OneToOneField]]
        decimal_fields = [field.name for field in cls._meta.get_fields() if type(field) is DecimalField]
        binary_fields = [field.name for field in cls._meta.get_fields() if type(field) is BinaryField]
        if type(model_dict) is list:
            for item in model_dict:
                updated_fields = {}
                fields_to_remove = []
                for key in item.keys():
                    if key in foreign_key_fields:
                        # get current value -- should be an id
                        value = item[key]
                        # create new field with appended _id
                        field_with_id = key + '_id'
                        # set new id field
                        updated_fields[field_with_id] = value
                        #remove field from dict
                        fields_to_remove.append(key)
                    if key in decimal_fields and item[key] is not None:
                        updated_fields[key] = float(item[key])
                    if key in binary_fields and item[key] is not None:
                        # this is because the serializer is serializing from the db and adding on
                        # bytearray(b\ and also )' onto the end. this is a bad solution as we get more
                        # binary types we could run into problems as this returns and unencoded string
                        # rather than the actual byte array -- if we need the actual byte array we are
                        # going to need to fix up the serializer
                        updated_fields[key] = convert_serialized_binary_to_string(item[key])
                # setting all updated fields after looping through the keys to avoid changing the item we are looping
                # through
                for updated_field in updated_fields.keys():
                    item[updated_field] = updated_fields[updated_field]

                # remove all fields that we don't need after iterating through the items
                [item.pop(field_to_remove, None) for field_to_remove in fields_to_remove]

        else:
            updated_fields = {}
            fields_to_remove = []
            for key in model_dict.keys():
                if key in foreign_key_fields:
                    # get current value -- should be an id
                    value = model_dict[key]
                    # create new field with appended _id
                    field_with_id = key + '_id'
                    # set new id field
                    updated_fields[field_with_id] = value
                    # remove field from dict
                    fields_to_remove.append(key)
                if key in decimal_fields and model_dict[key] is not None:
                    updated_fields[key] = float(model_dict[key])
                if key in binary_fields and model_dict[key] is not None:
                    # this is because the serializer is serializing from the db and adding on
                    # bytearray(b\ and also )' onto the end. this is a bad solution as we get more
                    # binary types we could run into problems as this returns and unencoded string
                    # rather than the actual byte array -- if we need the actual byte array we are
                    # going to need to fix up the serializer
                    updated_fields[key] = convert_serialized_binary_to_string(model_dict[key])

            # setting all updated fields after looping through the keys to avoid changing the item we are looping
            # through
            for updated_field in updated_fields.keys():
                model_dict[updated_field] = updated_fields[updated_field]

            # remove all fields that we don't need after iterating through the items
            [model_dict.pop(field_to_remove, None) for field_to_remove in fields_to_remove]

        if hasattr(obj, 'get_excludes'):
            excludes = obj.get_excludes()
            if type(model_dict) is list:
                for item in model_dict:
                    for exclude in excludes:
                        if exclude in item.keys():
                            del item[exclude]
            else:
                for exclude in excludes:
                    if exclude in model_dict.keys():
                        del model_dict[exclude]

        if self.fields:
            if type(model_dict) is list:
                pruned_model_dicts = []
                for item in model_dict:
                    pruned_model_dict = {}
                    for key in item.keys():
                        if key in self.fields or Mapper.underscore_to_camelcase(key) in self.fields:
                            pruned_model_dict[key] = item[key]
                    pruned_model_dicts.append(pruned_model_dict)
                return pruned_model_dict
            else:
                pruned_model_dict = {}
                for key in model_dict.keys():
                    if key in self.fields or Mapper.underscore_to_camelcase(key) in self.fields:
                        pruned_model_dict[key] = model_dict[key]
                return pruned_model_dict
        else:
            return model_dict

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
                if hasattr(obj, field) and getattr(obj, field) is not None:
                    related_obj = getattr(obj, field)
                    if related_obj is not None:
                        view_model[field] = self.serialize_related(related_obj, related_items)
                    else:
                        view_model[field] = None
                else:
                    view_model[field] = None

            else:
                field = Mapper.camelcase_to_underscore(field)
                if hasattr(obj, field) and getattr(obj, field) is not None:
                    related_obj = getattr(obj, field)
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
                item_to_serialize = getattr(field_obj, field)
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

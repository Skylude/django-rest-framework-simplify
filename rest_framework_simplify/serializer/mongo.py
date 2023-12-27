import datetime

from bson.dbref import DBRef
from bson.objectid import ObjectId
from mongoengine.queryset import QuerySet

from rest_framework_simplify.helpers import binary_string_to_string
from rest_framework_simplify.mapper import Mapper


class MongoEncoder:
    def __init__(
        self,
        obj,
        include=[],
        exclude=[],
        func_generic_extra_info=[],
        func_extra_info=[],
    ):
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
            print(f"F [{f}] Val [{getattr(self, f)}]")

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
                val = self.h_value(k, new_obj, new_obj_to_mongo)
                if val is not None:
                    tmp_ret.update({k: val})
            return tmp_ret

        elif isinstance(obj_to_mongo, str):
            return "%s" % obj_to_mongo
        elif isinstance(obj_to_mongo, datetime.datetime):
            return obj_to_mongo.strftime("%Y-%m-%dT%H:%M:%S")
        elif isinstance(obj_to_mongo, datetime.date):
            return obj_to_mongo.strftime("%Y-%m-%d")
        elif isinstance(obj_to_mongo, ObjectId):
            return "%s" % str(obj_to_mongo)
        elif isinstance(obj_to_mongo, list):
            tmp_list_ret = []
            for position, tmp in enumerate(obj_to_mongo):
                if isinstance(tmp, dict):
                    tmp_list_ret.append(self.h_value(f, tmp, tmp))
                elif isinstance(tmp, DBRef):
                    new_obj = getattr(obj, f)[position]
                    new_obj_to_mongo = new_obj.to_mongo()
                    tmp_ret = {}
                    for fn in new_obj_to_mongo.keys():
                        val = self.h_value(fn, new_obj, new_obj_to_mongo[fn])
                        if val is not None:
                            tmp_ret.update({fn: val})
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


class MongoEngineSerializer:
    def __init__(
        self,
        include=[],
        exclude=[],
        func_generic_extra_info=[],
        func_extra_info=[],
        fields=[],
    ):
        self.include = include
        self.exclude = exclude
        self.fields = fields
        self.func_generic_extra_info = func_generic_extra_info
        self.func_extra_info = func_extra_info

    def serialize(self, obj, indent=0):
        ret = []
        if isinstance(obj, QuerySet):
            for o in obj:
                ret.append(
                    MongoEncoder(
                        obj=o,
                        include=self.include,
                        exclude=self.exclude,
                        func_generic_extra_info=self.func_generic_extra_info,
                        func_extra_info=self.func_extra_info,
                    ).to_dict(),
                )

        else:
            ret = MongoEncoder(
                obj=obj,
                include=self.include,
                exclude=self.exclude,
                func_generic_extra_info=self.func_generic_extra_info,
                func_extra_info=self.func_extra_info,
            ).to_dict()

        return ret

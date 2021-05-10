import re


class Mapper:

    def __init__(self):
        pass

    @staticmethod
    def camelcase_to_underscore(camel_case):
        if isinstance(camel_case, dict) or isinstance(camel_case, list):
            return Mapper.dict_camelcase_to_underscore(camel_case)
        else:
            return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', camel_case).lower().strip('_')


    @staticmethod
    def underscore_to_camelcase(underscore):
        if isinstance(underscore, dict) or isinstance(underscore, list):
            return Mapper.dict_underscore_to_camelcase(underscore)
        else:
            return Mapper.string_underscore_to_camelcase(underscore)

    @staticmethod
    def string_underscore_to_camelcase(underscore):
        if '_' in underscore:
            return re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(), underscore)
        else:
            return underscore

    @staticmethod
    def underscore_to_titlecase(underscore):
        if isinstance(underscore, dict) or isinstance(underscore, list):
            return Mapper.dict_underscore_to_titlecase(underscore)
        else:
            title_name = underscore.replace('_', ' ').title().replace(' ', '')
            return title_name

    @staticmethod
    def titlecase_to_camelcase(titlecase):
        if isinstance(titlecase, dict) or isinstance(titlecase, list):
            return Mapper.dict_titlecase_to_camelcase(titlecase)
        else:
            if titlecase.isupper():
                return titlecase.lower()
            else:
                val = titlecase[0].lower() + titlecase[1:]
                reg = re.compile('^[A-Z]+')
                front = reg.findall(titlecase)
                if len(front) > 0:
                    if front[0].isupper() and len(front[0]) > 1:
                        s1 = front[0][:-1].lower()
                        val = s1 + titlecase[len(s1):]
                if val[-2:] == "ID":
                    val = val[:-2] + "Id"
                elif val[-3:] == "IDs":
                    val = val[:-3] + "Ids"

                return val

    @staticmethod
    def dict_camelcase_to_underscore(obj):
        if isinstance(obj, dict):
            new_dict = {}
            for key, value in obj.items():
                underscore = Mapper.camelcase_to_underscore(key)
                if isinstance(value, dict) or isinstance(value, list):
                    value = Mapper.camelcase_to_underscore(value)
                new_dict[underscore] = value
            return new_dict
        elif isinstance(obj, list):
            new_list = []
            for o in obj:
                new_item = {}
                if isinstance(o, list):
                    new_item = Mapper.camelcase_to_underscore(o)
                elif isinstance(o, dict):
                    for key, value in o.items():
                        underscore = Mapper.camelcase_to_underscore(key)
                        if isinstance(value, dict) or isinstance(value, list):
                            value = Mapper.camelcase_to_underscore(value)
                        new_item[underscore] = value
                else:
                    new_item = o
                new_list.append(new_item)
            return new_list

    @staticmethod
    def dict_underscore_to_camelcase(obj):
        if isinstance(obj, dict):
            return {
                Mapper.string_underscore_to_camelcase(key) : Mapper.dict_underscore_to_camelcase(value)
                for key, value in obj.items()
            }

        if isinstance(obj, list):
            return [Mapper.dict_underscore_to_camelcase(x) for x in obj] 

        return obj

    @staticmethod
    def dict_underscore_to_titlecase(obj):
        if isinstance(obj, dict):
            new_dict = {}
            for key, value in obj.items():
                titlecase = Mapper.underscore_to_titlecase(key)
                if isinstance(value, dict) or isinstance(value, list):
                    value = Mapper.underscore_to_titlecase(value)
                new_dict[titlecase] = value
            return new_dict
        elif isinstance(obj, list):
            new_list = []
            for o in obj:
                new_dict = {}
                for key, value in o.items():
                    titlecase = Mapper.underscore_to_titlecase(key)
                    if isinstance(value, dict) or isinstance(value, list):
                        value = Mapper.underscore_to_titlecase(value)
                    new_dict[titlecase] = value
                new_list.append(new_dict)
            return new_list

    @staticmethod
    def dict_titlecase_to_camelcase(obj):
        if isinstance(obj, dict):
            new_dict = {}
            for key, value in obj.items():
                camelcase = Mapper.titlecase_to_camelcase(key)
                if isinstance(value, dict) or isinstance(value, list):
                    value = Mapper.titlecase_to_camelcase(value)
                new_dict[camelcase] = value
            return new_dict
        elif isinstance(obj, list):
            new_list = []
            for o in obj:
                new_dict = {}
                if isinstance(o, dict):
                    for key, value in o.items():
                        camelcase = Mapper.titlecase_to_camelcase(key)
                        if isinstance(value, dict) or isinstance(value, list):
                            value = Mapper.titlecase_to_camelcase(value)
                        new_dict[camelcase] = value
                    new_list.append(new_dict)
                else:
                    new_list.append(o)
        return new_list

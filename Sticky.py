# -*-coding: utf8 -*-

import os
import re
import copy

import yaml
import json
import codecs
import importlib


class FieldValueGenerator(object):
    def __init__(self):
        pass

    def get_field_keys(self, template):
        find_ = "(<[{a-zA-Z0-9._}]+>)"
        return re.findall(find_, template) or []

    def get_field_value(self, template, value):
        field_keys = self.get_field_keys(template)
        template = os.path.normpath(template)
        for key in field_keys:
            template = template.replace(key, "(.*)")

        values = re.match(template, value, re.IGNORECASE)
        if values:
            field_value = {}
            for i, key in enumerate(field_keys):
                value = values.groups()[i]
                if "_" in value:
                    return False
                field_value[key] = value
        
        return field_value

    def generate(self, template, field_value, force=False, custom_module_path=None):
        field_keys = self.get_field_keys(template)
        for key in field_keys:
            if key in field_value:
                template = template.replace(key, 
                                            field_value[key])

        if not custom_module_path is None:
            mod = importlib.import_module(custom_module_path)
            reload(mod)
            field_value = mod.execute(self.get_field_keys(template), field_value)
            template = self.generate(template, field_value, force=force)

        if "<" in template and not force:
            return False

        return template


class StickyConfig(object):
    def __init__(self, directory=None, field_value=None):
        self.directory = None
        self.field_value = None
        self.set(directory, field_value)
        self.generator = FieldValueGenerator()
        self.splitter = "--->"

    def set(self, directory, field_value):
        self.set_directory(directory)
        self.set_field_value(field_value)

    def set_directory(self, directory):
        self.directory = directory

    def set_field_value(self, field_value):
        self.field_value = field_value

    def read(self, path):
        if path.endswith(".yml"):
            yml_data = yaml.load(codecs.open(path, "r"), Loader=yaml.SafeLoader)
            return yml_data.get("info", {}), yml_data.get("data", {})

        elif path.endswith(".json"):
            json_data = json.load(codecs.open(path, "r"), "Utf8")
            return json_data.get("info", {}), json_data.get("data", {})
        return {}, {}

    def save(self, path, info=None, data={}, **args):
        if info is None:
            info = args

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        if path.endswith(".json"):
            with codecs.open(path, "w") as j:
                json.dump({"info": info, "data": data}, j, "utf8", indent=4)
        else:
            with codecs.open(path, "w") as y:
                yaml.dump({"info": info, "data": data}, y, default_flow_style=False)

    def get_key_file(self, template, directory=None):
        if directory is None:
            directory = self.directory

        key_files = os.listdir(directory)
        split_template = template.split("_")
        key_file = False
        for i in range(len(split_template)):
            if i == 0:
                check = template
            else:
                check = "_".join(split_template[:-i])
            key_name = self.generator.generate(check, self.field_value)
            if key_name:
                if "%s.yml" % key_name in key_files:
                    key_file = "%s/%s.yml" % (directory, 
                                              key_name)
                    break

        return key_file

    def get_override_file_list(self, path):
        if not os.path.exists(path):
            return []

        info, data = self.read(path)
        paths = [path]

        i = 0
        while info.get("parent", None):
            d = os.path.dirname(path)
            parent = os.path.normpath(os.path.join(path, info["parent"]))
            if os.path.exists(parent):
                paths.insert(0, parent)
                info, data = self.read(parent)
            else:
                break
            i += 1

            if i > 100:
                break

        return paths

    def values_override(self, base, override, use_field_value=False):
        def value_mapping(value, use_field_value):
            if not use_field_value:
                return value

            copy_field_value = copy.deepcopy(self.field_value)
            if isinstance(value, (str, unicode)):
                gen = self.generator.generate(value, copy_field_value, force=True)
                if gen.startswith("@"):
                    if gen.startswith("@../"):
                        gen = os.path.normpath(os.path.join(self.directory, gen)).replace("\\", "/")
                    else:
                        gen = gen[1:]

                return gen
            
            elif isinstance(value, list):
                new = []
                for v in value:
                    new.append(value_mapping(v, use_field_value))

                return new

            elif isinstance(value, dict):
                new = {}
                for k, v in value.items():
                    if isinstance(v, (str, unicode)):
                        new[k] = self.generator.generate(v, copy_field_value, force=True)
                        if new[k].startswith("@"):
                            if new[k].startswith("@../"):
                                new[k] = os.path.normpath(os.path.join(self.directory, new[k])).replace("\\", "/")
                            else:
                                new[k] = new[k][1:]

                    else:
                        new[k] = value_mapping(v, use_field_value)

                return new

            return value

        default = copy.deepcopy(override)
        if not type(base) == type(override):
            return value_mapping(base, use_field_value)

        elif isinstance(base, (int, float, bool)):
            return value_mapping(override, use_field_value)

        elif isinstance(base, dict):
            for k, v in base.items():
                if not k in override:
                    override[k] = v
                else:
                    override[k] = self.values_override(v, override[k], use_field_value)

            return value_mapping(override, self.field_value)

        elif isinstance(base, list):
            override_ = []
            if isinstance(base[0], dict) and "name" in base[0]:
                override_keys = [l["name"] for l in override]

                rm = []
                for each in base:
                    if each["name"] in override_keys:
                        for i, each2 in enumerate(override):
                            if each["name"] == each2["name"]:
                                dic = copy.deepcopy(each)
                                for k, v in each2.items():
                                    if k in dic:
                                        dic[k] = v
                                override_.append(dic)
                                rm.append(i)
                    else:
                        override_.append(each)

                rm.sort(reverse=True)
                for r in rm:
                    override.pop(r)

                for each in override:
                    override_.append(each)
                return value_mapping(override_, self.field_value)

            else:
                return value_mapping(override, self.field_value)

        else:
            return value_mapping(override, self.field_value)


    def trace_files(self, result_data, file_list):
        for each in file_list[::-1]:
            file_info, file_data = self.read(each)
            file_name = "/".join(each.replace("\\", "/").split("/")[-2:])
            self.trace_data(result_data, file_data, file_name)
        return result_data


    def trace_data(self, base, data, file_name):
        def _add_file_name(value, file_name):
            if isinstance(value, (int, float, bool)):
                value = unicode(value)

            if isinstance(value, (str, unicode)):
                # value = value.split(self.splitter)[0]
                if not self.splitter in value:
                    value = "{}{}{}".format(value, self.splitter, file_name)

            elif isinstance(value, dict):
                for k, v in value.items():
                    value[k] = _add_file_name(v, file_name)

            elif isinstance(value, list):
                ls_ = []
                for v2 in v:
                    ls.append(_add_file_name(v2))

                value = ls_

            return value

        if isinstance(base, (int, float, bool)):
            base = unicode(base)

        if isinstance(data, (int, float, bool)):
            data = unicode(data)        
        if type(base) != type(data):
            return base

        elif isinstance(base, dict):
            for k, v in base.items():
                if k in data:
                    base[k] = self.trace_data(v, data[k], file_name)
                else:
                    pass
                    # base[k] = _add_file_name(v, file_name)
            return base

        elif isinstance(base, list):
            base.insert(0, _add_file_name("", file_name))
            return base
        else:
            base = _add_file_name(base, file_name)
            return base

        return base







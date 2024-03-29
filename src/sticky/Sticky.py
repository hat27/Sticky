from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import copy

import yaml
import json
import codecs
import importlib

try:
    reload
except NameError:
    if hasattr(importlib, "reload"):
        # for py3.4+
        from importlib import reload


class FieldValueGenerator(object):
    def __init__(self):
        pass

    def get_field_keys(self, template):
        find_ = "(<[{a-zA-Z0-9._}]+>)"
        return re.findall(find_, template) or []

    def get_field_value(self, template, value):
        field_keys = self.get_field_keys(template)
        # template = os.path.normpath(template)
        for key in field_keys:
            template = template.replace(key, "(.*)")

        values = re.match(template, value, re.IGNORECASE)
        field_value = {}
        if values:
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

        if custom_module_path:
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
            with codecs.open(path, "r") as f:
                yml_data = yaml.load(f, Loader=yaml.SafeLoader)
                return yml_data["info"], yml_data["data"]

        elif path.endswith(".json"):
            with codecs.open(path, "r") as f:
                json_data = json.load(f, encoding="utf8")
                return json_data["info"], json_data["data"]

        return {}, {}

    def save(self, path, info=None, data={}, **args):
        if info is None:
            info = args

        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        if path.endswith(".json"):
            with codecs.open(path, "w", encoding="utf8") as j:
                json.dump({"info": info, "data": data}, j, ensure_ascii=False, indent=4)
        else:
            with codecs.open(path, "w", encoding="utf8") as y:
                yaml.safe_dump({"info": info, "data": data}, y, allow_unicode=True)

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
                break_flg = False
                for ext in ["yml", "json"]:
                    if "{}.{}".format(key_name, ext) in key_files:
                        key_file = "{}/{}.{}".format(directory,
                                                     key_name,
                                                     ext)
                        break_flg = True
                        break
                if break_flg:
                    break

        return key_file

    def get_override_file_list(self, path, field_value=None):
        if not os.path.exists(path):
            return []

        info, data = self.read(path)
        paths = [path]
        i = 0
        while info.get("parent", None):
            parent_path = info["parent"]
            if field_value is not None:
                for k, v in field_value.items():
                    parent_path = parent_path.replace(k, v)

            parent = os.path.normpath(os.path.join(path, parent_path))
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
            if isinstance(value, str):
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
                    if isinstance(v, str):
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
        
        if override is None:
            return None

        elif type(base) != type(override):
            return value_mapping(base, use_field_value)

        elif isinstance(base, (int, float, bool)):
            return value_mapping(override, use_field_value)

        elif isinstance(base, dict):
            for k, v in base.items():
                if k not in override:
                    override[k] = v
                else:
                    override_value = self.values_override(v, override[k], use_field_value)
                    if override_value is not None:
                        override[k] = override_value
                    else:
                        print("override value is None. key: {}".format(k))
                        del override[k]

            return value_mapping(override, self.field_value)

        elif isinstance(base, list):
            override_ = []
            if isinstance(base[0], dict) and "name" in base[0]:
                override_keys = [value_["name"] for value_ in override]

                rm = []
                for each in base:
                    if each["name"] in override_keys:
                        for i, each2 in enumerate(override):
                            if each["name"] == each2["name"]:
                                dic = copy.deepcopy(each)
                                for k, v in each2.items():
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
                return value_mapping([dic for dic in override_ if not dic.get("cancel", False)], self.field_value)
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
                value = str(value)

            if isinstance(value, str):
                if self.splitter not in value:
                    value = "{}{}{}".format(value, self.splitter, file_name)

            elif isinstance(value, dict):
                for k, v in value.items():
                    value[k] = _add_file_name(v, file_name)

            elif isinstance(value, list):
                ls_ = []
                for v2 in value:
                    ls_.append(_add_file_name(v2, file_name))

                value = ls_

            return value

        if isinstance(base, (int, float, bool)):
            base = str(base)

        if isinstance(data, (int, float, bool)):
            data = str(data)

        if type(base) != type(data):
            return base

        elif isinstance(base, dict):
            for k, v in base.items():
                if k in data:
                    base[k] = self.trace_data(v, data[k], file_name)
            return base

        elif isinstance(base, list):
            if len(base) > 0 and isinstance(base[0], dict) and "name" in base[0]:
                new_list = []
                for base_ in base:
                    is_exists = False
                    new_dict = {}
                    for each in data:
                        if base_["name"] == each["name"]:
                            keys = each.keys()
                            for key in keys:
                                new_dict[key] = _add_file_name(each[key], file_name)
                            is_exists = True
                            break

                    if is_exists:
                        new_list.append(new_dict)
                    else:
                        new_list.append(base_)

                base_keys = [v["name"].split(self.splitter)[0] for v in base]
                for each in data:
                    if each["name"] not in base_keys:
                        new_dict = {}
                        keys = each.keys()
                        for key in keys:
                            new_dict[key] = _add_file_name(each[key], file_name)
                        new_list.append(new_dict)

                return new_list
            else:
                return _add_file_name(base, file_name)
        else:
            base = _add_file_name(base, file_name)
            return base

        return base

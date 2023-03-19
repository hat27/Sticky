#-*-coding: utf-8-*-

import os
import glob
from sticky.Sticky import FieldValueGenerator, StickyConfig


class StickyProjectManager(object):
    """
    This class is used to manage project environment.
    In order to use this class, I recommand to Inheritance this class and override the get_key_config_files method.
    """
    def __init__(self):
        self.root_directory = "sample/env"
        self.field_value_generator = FieldValueGenerator()
        self.sticky = StickyConfig()

    def set(self, project, variation="default", **kwargs):
        self.project = project
        self.variation = variation
        self.tool_name = kwargs.get("tool_name", False)
        self.key_config_files = self.get_key_config_files()
        self.config_files = []

        for key_config_file in self.key_config_files:
            self.config_files.extend(self.sticky.get_override_file_list(key_config_file))

        self.config_files = [os.path.normpath(l).replace("\\", "/") for l in self.config_files]
        print("")
        print("{} {} {}".format(self.project, self.variation, self.tool_name))
        print("key file is : {}".format(self.key_config_files))
        print("related files are:")
        self.config = {}
        for each in self.config_files:
            print(each)
            override_info, override_data = self.sticky.read(each)
            self.config = self.sticky.values_override(self.config, override_data)

    def get_key_config_files(self):
        def _get(path):
            if path:
                paths = glob.glob(path)
                if len(paths) > 0:
                    paths.sort()
                    return os.path.normpath(paths[-1])

            return False

        project_pattern = "{}/{}.v*.yml".format(self.root_directory, self.project)
        base_project_pattern = "{}/base.v*.yml".format(self.root_directory)
        variation_pattern = "{}/{}.{}.v*.yml".format(self.root_directory, self.project, self.variation)
        base_variation_pattern = "{}/base.{}.v*.yml".format(self.root_directory, self.variation)
        tool_patterns = []
        if self.tool_name:
            tool_patterns.append("{}/{}.v*.yml".format(self.root_directory, self.tool_name))
            tool_patterns.append("{}/{}.{}.v*.yml".format(self.root_directory, self.tool_name, self.project))
            tool_patterns.append("{}/{}.{}.{}.v*.yml".format(self.root_directory, self.tool_name, self.project, self.variation))

        config_files = []
        temp_files = []
        for each in [base_project_pattern, project_pattern, base_variation_pattern, variation_pattern]:
            path = _get(each)
            if path:
                temp_files.append(path)
        
        if len(temp_files) == 0:
            raise Exception("No config file was found.: {}".format(self.root_directory))
        config_files.append(temp_files[-1].replace("\\", "/"))

        if len(tool_patterns) > 0:
            for tool_pattern in tool_patterns[::-1]:
                path = _get(tool_pattern)
                if path:
                    config_files.append(path)
                    break
        
        return config_files

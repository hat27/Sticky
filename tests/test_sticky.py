# -*- coding: utf8 -*-

import os
import sys

import unittest
import tempfile
import shutil

from sticky.Sticky import FieldValueGenerator, StickyConfig

sample_path = os.path.normpath(os.path.join(__file__, "../../"))
print(sample_path)
sys.path.append(sample_path)


# FieldValueGenerator
class GetFieldKeysTest(unittest.TestCase):
    def setUp(self):
        self.obj = FieldValueGenerator()

    def test_keys(self):
        template = "<a>_<b>"
        actual = self.obj.get_field_keys(template)
        self.assertEqual(actual, ["<a>", "<b>"])

        template = "<a>_<b>"
        actual = self.obj.get_field_keys(template)
        self.assertEqual(actual, ["<a>", "<b>"])

    def test_uncollect_keys(self):
        template = "(a)_(b)"
        actual = self.obj.get_field_keys(template)
        self.assertEqual(actual, [])

        template = "[a]_[b]"
        actual = self.obj.get_field_keys(template)
        self.assertEqual(actual, [])

        template = "{a}_{b}"
        actual = self.obj.get_field_keys(template)
        self.assertEqual(actual, [])

        template = "a_b"
        actual = self.obj.get_field_keys(template)
        self.assertEqual(actual, [])


class GetFieldValueTest(unittest.TestCase):
    def setUp(self):
        self.obj = FieldValueGenerator()

    def test_get_field_value_collect(self):
        template = "<a>_<b>"
        value = "test1_test2"
        actual = self.obj.get_field_value(template, value)
        self.assertEqual(actual, {"<a>": "test1",
                                  "<b>": "test2"})

    def test_get_field_value_uncollect(self):
        template = "<a>_<b>"
        value = "test1_1_test2"
        actual = self.obj.get_field_value(template, value)
        self.assertEqual(actual, False)


class GenerateTest(unittest.TestCase):
    def setUp(self):
        self.obj = FieldValueGenerator()

    def test_generate_collect(self):
        template = "<a>_<b>"
        field_value = {"<a>": "test1", "<b>": "test2"}
        actual = self.obj.generate(template, field_value)
        self.assertEqual(actual, "test1_test2")

    def test_generate_no_fields(self):
        template = "a_b"
        field_value = {"<a>": "test1", "<b>": "test2"}
        actual = self.obj.generate(template, field_value)
        self.assertEqual(actual, "a_b")

    def test_force(self):
        template = "<a>_<b>"
        field_value = {"<a>": "test1", "<b2>": "test2"}
        actual = self.obj.generate(template, field_value, force=True)
        self.assertEqual(actual, "test1_<b>")

    def test_custum(self):
        template = "<shot{scene}>_<shot{cut}>"
        field_value = {"<shot>": "s01c01"}
        actual = self.obj.generate(template, field_value, custom_module_path="sample.custom.sample")
        self.assertEqual(actual, "s01_c01")

    def test_custum2(self):
        template = "<episode>_<shot{scene}>_<shot{cut}>_<shot{cut}>"
        field_value = {"<shot>": "s05c20", "<episode>": "Ep99"}
        actual = self.obj.generate(template, field_value, custom_module_path="sample.custom.sample")
        self.assertEqual(actual, "Ep99_s05_c20_c20")


# StickyConfig
class GetKeyFileTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp().replace("\\", "/")
        for f in ["ep01_s01_c01_anim", "ep01_s01_c01", "ep01_s01", "ep01"]:
            with open("{}/{}.yml".format(self.directory, f), "w") as f:
                pass

        self.obj = StickyConfig(self.directory)

    def test_get_get_key_file_collect(self):
        template = "<episode>_<scene>_<cut>_<progress>"
        fields = {"<episode>": "ep01", "<scene>": "s01"}

        self.obj.set_field_value(fields)
        actual = self.obj.get_key_file(template)
        self.assertEqual(os.path.basename(actual), "ep01_s01.yml")

        template = "<episode>_<scene>_<cut>_<progress>"
        fields = {"<episode>": "ep01", "<scene>": "s01", "<progress>": "anim"}
        self.obj.set_field_value(fields)
        actual = self.obj.get_key_file(template)
        self.assertEqual(os.path.basename(actual), "ep01_s01.yml")

        template = "<episode>_<scene>_<cut>_<progress>"
        fields = {"<episode>": "ep01", "<scene>": "s01", "<cut>": "c01", "<progress>": "anim"}
        self.obj.set_field_value(fields)
        actual = self.obj.get_key_file(template)
        self.assertEqual(os.path.basename(actual), "ep01_s01_c01_anim.yml")

    def tearDown(self):
        shutil.rmtree(self.directory)


class ValueOverrideTest(unittest.TestCase):
    def setUp(self):
        self.obj = StickyConfig()

    def test_dict_override1(self):
        base = {"a": 1, "b": 2, "c": 3}
        override = {"a": 2, "b": 4}
        actual = self.obj.values_override(base, override)
        self.assertEqual(actual, {"a": 2, "b": 4, "c": 3})

    def test_dict_override2(self):
        base = {"a": [1, 2, 3, 4], "b": 5}
        override = {"a": [3, 4]}
        actual = self.obj.values_override(base, override)
        self.assertEqual(actual, {"a": [3, 4], "b": 5})

    def test_dict_list_override1(self):
        base = [{"a": 1, "b": 2}]

        override = [{"a": 2},
                    {"b": 2222, "c": 44444}]

        actual = self.obj.values_override(base, override)
        self.assertEqual(actual, [{"a": 2}, {"b": 2222, "c": 44444}])

    def test_dict_list_override2(self):
        base = [{"a": 2},
                {"b": 2222, "c": 44444}]

        override = [{"a": 1, "b": 2}]

        actual = self.obj.values_override(base, override)
        self.assertEqual(actual, [{"a": 1, "b": 2}])


class ValueOverrideKeywordDictTest(unittest.TestCase):
    def setUp(self):
        self.obj = StickyConfig()

    def test_keyword_dict_list_override1(self):
        base = [{"name": "a", "value": 1},
                {"name": "b", "value": 2}]

        override = [{"name": "a", "value": 10}]

        actual = self.obj.values_override(base, override)

        self.assertEqual(actual, [{"name": "a", "value": 10}, {"name": "b", "value": 2}])

    def test_keyword_dict_list_override2(self):
        base = [{"name": "a", "value": 1},
                {"name": "b", "value": 2}]

        override = [{"name": "a", "value": 10},
                    {"name": "c", "value": 5}]

        actual = self.obj.values_override(base, override)

        self.assertEqual(actual, [{"name": "a", "value": 10},
                                  {"name": "b", "value": 2},
                                  {"name": "c", "value": 5}])

    def test_keyword_dict_list_override3(self):
        base = [{"name": "b", "value": 2},
                {"name": "a", "value": 1}]

        override = [{"name": "a", "value": 10},
                    {"name": "c", "value": 5}]

        actual = self.obj.values_override(base, override)

        self.assertNotEqual(actual, [
                                  {"name": "a", "value": 10},
                                  {"name": "b", "value": 2},
                                  {"name": "c", "value": 5}])

        self.assertNotEqual(actual, [
                                  {"name": "c", "value": 5},
                                  {"name": "a", "value": 10},
                                  {"name": "b", "value": 2}
                                  ])

        self.assertEqual(actual, [{"name": "b", "value": 2},
                                  {"name": "a", "value": 10},
                                  {"name": "c", "value": 5}])


class ValueOverrideHiearachyTest(unittest.TestCase):
    def setUp(self):
        self.obj = StickyConfig()

    def test_hiearachy_override1(self):
        base = {"a": {"b": [1, 2, 3]}, "c": [1, 2, 3]}
        override = {"c": [2, 3, 4]}

        actual = self.obj.values_override(base, override)

        self.assertEqual(actual, {"a": {"b": [1, 2, 3]}, "c": [2, 3, 4]})

    def test_hiearachy_override2(self):
        base = {"a": {"b": {"d": 10}}, "c": [1, 2, 3]}
        override = {"a": {"b": {"d": 1, "e": 2}}}

        actual = self.obj.values_override(base, override)

        self.assertEqual(actual, {"a": {"b": {"d": 1, "e": 2}},
                                  "c": [1, 2, 3]})

    def test_hiearachy_override3(self):
        base = {"a": {"b": {"f": [1, 2, 3, 4, 5]}}, "c": [1, 2, 3]}
        override = {"a": {"b": {"f": [0]}}}

        actual = self.obj.values_override(base, override)

        self.assertEqual(actual, {"a": {"b": {"f": [0]}}, "c": [1, 2, 3]})

    def test_hiearachy_override4(self):
        base = {"a": {"b": {"f": [{"name": "a1", "value": 1},
                                  {"name": "b1", "value": 2},
                                  {"name": "c1", "value": 3},
                                  {"name": "d1", "value": 6}]}}}

        override = {"a": {"b": {"f": [{"name": "a1", "value": 5},
                                      {"name": "d1", "value": 4},
                                      {"name": "b1", "value": 3}]}}}

        actual = self.obj.values_override(base, override)

        self.assertEqual(actual, {"a": {"b": {"f": [{"name": "a1", "value": 5},
                                                    {"name": "b1", "value": 3},
                                                    {"name": "c1", "value": 3},
                                                    {"name": "d1", "value": 4}]}}})

    def test_hiearachy_override5(self):
        base_proj = {
                    "general": {
                          "app": "maya2018.exe",
                          "batch": "maya2018.mayapy",
                          "env": [{"name": "MODULE1", "path": "C:/aaaa", "mode": "set"},
                                  {"name": "TEMP", "path": "C:/trush/xxxx", "mode": "append"},
                                  {"name": "USERNAME", "value": "test_user"}]},
                    "shot": {
                             "general": {
                                     "fps": 24,
                                     "width": 640,
                                     "height": 360,
                                     },

                            },
                    "asset": {
                             "path": "/<asset_id>/<lod>/<asset_id>.ma",
                             "light": "/light/<project>_master_light.ma",
                             "camera": "/camera/<project>_master_camera.ma"
                             }
                     }

        proj2 = {
                    "general": {
                          "app": "maya2015.exe",
                          "batch": "maya2015.mayapy",
                          "env": [{"name": "MODULE1", "path": "C:/bbbb", "mode": "set"}]
                          },

                    "shot": {
                             "general": {
                                     "fps": 30
                                     },

                            },
                     }

        actual = self.obj.values_override(base_proj, proj2)
        check = {
                    "general": {
                          "app": "maya2015.exe",
                          "batch": "maya2015.mayapy",
                          "env": [{"name": "MODULE1", "path": "C:/bbbb", "mode": "set"},
                                  {"name": "TEMP", "path": "C:/trush/xxxx", "mode": "append"},
                                  {"name": "USERNAME", "value": "test_user"}]},
                    "shot": {
                             "general": {
                                     "fps": 30,
                                     "width": 640,
                                     "height": 360,
                                     },

                            },
                    "asset": {
                             "path": "/<asset_id>/<lod>/<asset_id>.ma",
                             "light": "/light/<project>_master_light.ma",
                             "camera": "/camera/<project>_master_camera.ma"
                             }
                     }
        self.assertEqual(actual, check)


class ValueMappingTest(unittest.TestCase):
    def setUp(self):
        self.obj = StickyConfig()
        self.maxDiff = None

    def test_value_mapping1(self):
        base = {"a": {"b": [1, 2, 3]}, "c": [1, 2, 3]}
        override = {"c": [2, 3, "<project>"]}
        field_value = {"<project>": "PROJ1"}
        self.obj.set_field_value(field_value)

        actual = self.obj.values_override(base, override, use_field_value=True)

        self.assertEqual(actual, {"a": {"b": [1, 2, 3]}, "c": [2, 3, "PROJ1"]})

    def test_value_mapping2(self):
        base = {"a": {"b": {"f": [{"name": "a1", "value": 1},
                                  {"name": "b1", "value": 2},
                                  {"name": "c1", "value": 3},
                                  {"name": "d1", "value": 6}]}}}

        override = {"a": {"b": {"f": [{"name": "a1", "value": "<project>_<scene>"},
                                      {"name": "d1", "value": 4},
                                      {"name": "b1", "value": 3}]}}}

        field_value = {"<project>": "PROJ1", "<scene>": "s01c05"}
        self.obj.set_field_value(field_value)
        actual = self.obj.values_override(base, override, use_field_value=True)

        self.assertEqual(actual, {"a": {"b": {"f": [{"name": "a1", "value": "PROJ1_s01c05"},
                                                    {"name": "b1", "value": 3},
                                                    {"name": "c1", "value": 3},
                                                    {"name": "d1", "value": 4}]}}})

    def test_value_mapping3(self):
        base_proj = {
                    "general": {
                          "app": "maya2018.exe",
                          "batch": "maya2018.mayapy",
                          "env": [{"name": "MODULE1", "path": "C:/aaaa", "mode": "set"},
                                  {"name": "TEMP", "path": "C:/trush/xxxx", "mode": "append"},
                                  {"name": "USERNAME", "value": "test_user"}]},
                    "shot": {
                             "general": {
                                     "fps": 24,
                                     "width": 640,
                                     "height": 360,
                                     },

                            },
                    "asset": {
                             "path": "<workspace>/<asset_id>/<lod>/<asset_id>.ma",
                             "light": "<workspace>/light/<project>_master_light.ma",
                             "camera": "<workspace>/camera/<project>_master_camera.ma"
                             }
                     }

        proj2 = {
                    "general": {
                          "app": "maya2015.exe",
                          "batch": "maya2015.mayapy",
                          "env": [{"name": "MODULE1", "path": "C:/bbbb", "mode": "set"}]
                          },

                    "shot": {
                             "general": {
                                     "fps": 30
                                     },

                            },
                    "asset": {
                              "toolA": "@../../toolA",
                              "toolB": "@C:/test/toolB"
                             }
                     }
        field_value = {"<project>": "PROJ1", "<workspace>": "C:/proj1/data/maya/scenes"}
        directory = "C:/test/config/directory/env"
        self.obj.set(directory, field_value)
        actual = self.obj.values_override(base_proj, proj2, use_field_value=True)
        check = {
                    "general": {
                          "app": "maya2015.exe",
                          "batch": "maya2015.mayapy",
                          "env": [{"name": "MODULE1", "path": "C:/bbbb", "mode": "set"},
                                  {"name": "TEMP", "path": "C:/trush/xxxx", "mode": "append"},
                                  {"name": "USERNAME", "value": "test_user"}]},
                    "shot": {
                             "general": {
                                     "fps": 30,
                                     "width": 640,
                                     "height": 360,
                                     },

                            },
                    "asset": {
                             "path": "C:/proj1/data/maya/scenes/<asset_id>/<lod>/<asset_id>.ma",
                             "light": "C:/proj1/data/maya/scenes/light/PROJ1_master_light.ma",
                             "camera": "C:/proj1/data/maya/scenes/camera/PROJ1_master_camera.ma",
                             "toolA": "C:/test/config/directory/env/toolA",
                             "toolB": "C:/test/toolB"
                             }
                     }
        self.assertEqual(actual, check)


class GetProjectFileOtherLocationTest(unittest.TestCase):
    def setUp(self):
        self.directory = "{}/other_location".format(tempfile.mkdtemp().replace("\\", "/"))
        self.obj = StickyConfig(self.directory)

        info = {"name": "base"}
        data = {"base": "", "xxx": "12345"}

        self.obj.save("%s/somewhere/%s.yml" % (self.directory, info["name"]), info=info, data=data)

        self.map_data = {"<other_location>": "{}/somewhere".format(self.directory)}
        info = {"name": "ep01",
                "parent": "<other_location>/base.yml"}
        data = {"test3": "b", "yyy": 12345}
        self.obj.save("{}/{}.yml".format(self.directory, info["name"]), info=info, data=data)

        info = {"name": "ep01_s01",
                "parent": "../ep01.yml"}
        data = {"test2": "b"}

        self.obj.save("{}/{}.yml".format(self.directory, info["name"]), info=info, data=data)

        info = {"name": "ep01_s01_c01",
                "parent": "../ep01_s01.yml"}

        data = {"test": "a", "base": "new", "test3": "-----------------"}

        self.obj.save("{}/{}.yml".format(self.directory, info["name"]), info=info, data=data)

        data = {}
        info = {"name": "ep01_s01_c01_anim",
                "parent": "../ep01_s01_c01.yml"}
        self.obj.save("{}/{}.yml".format(self.directory, info["name"]), info=info, data=data)

    def test_get_override_file_list(self):
        template = "<episode>_<scene>_<cut>_<progress>"
        fields = {"<episode>": "ep01", "<scene>": "s01", "<cut>": "c01", "<progress>": "anim"}
        self.obj.set_field_value(fields)
        f = self.obj.get_key_file(template)

        actual = self.obj.get_override_file_list(f, field_value={"<other_location>": "{}/somewhere".format(self.directory)})
        actual = [os.path.basename(path) for path in actual]

        self.assertEqual(actual, ["base.yml",
                                  "ep01.yml",
                                  "ep01_s01.yml",
                                  "ep01_s01_c01.yml",
                                  "ep01_s01_c01_anim.yml"])


class GetProjectFileTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp().replace("\\", "/")
        self.obj = StickyConfig(self.directory)

        info = {"name": "base"}
        data = {"base": "", "yyy": 12345}

        self.obj.save("{}/{}.yml".format(self.directory, info["name"]), info=info, data=data)

        info = {"name": "ep01",
                "parent": "../base.yml"}
        data = {"test3": "b"}
        self.obj.save("{}/{}.yml".format(self.directory, info["name"]), info=info, data=data)

        info = {"name": "ep01_s01",
                "parent": "../ep01.yml"}
        data = {"test2": "b"}

        self.obj.save("{}/{}.yml".format(self.directory, info["name"]), info=info, data=data)

        info = {"name": "ep01_s01_c01",
                "parent": "../ep01_s01.yml"}

        data = {"test": "a", "base": "new", "test3": "-----------------"}

        self.obj.save("{}/{}.yml".format(self.directory, info["name"]), info=info, data=data)

        data = {}
        info = {"name": "ep01_s01_c01_anim",
                "parent": "../ep01_s01_c01.yml"}
        self.obj.save("{}/{}.yml".format(self.directory, info["name"]), info=info, data=data)

    def test_get_override_file_list(self):
        template = "<episode>_<scene>_<cut>_<progress>"
        fields = {"<episode>": "ep01", "<scene>": "s01", "<cut>": "c01", "<progress>": "anim"}
        self.obj.set_field_value(fields)
        f = self.obj.get_key_file(template)

        actual = self.obj.get_override_file_list(f)
        actual = [os.path.basename(path) for path in actual]

        self.assertEqual(actual, ["base.yml",
                                  "ep01.yml",
                                  "ep01_s01.yml",
                                  "ep01_s01_c01.yml",
                                  "ep01_s01_c01_anim.yml"])

    def test_merge_override_file_list(self):
        template = "<episode>_<scene>_<cut>_<progress>"
        fields = {"<episode>": "ep01", "<scene>": "s01", "<cut>": "c01", "<progress>": "anim"}
        self.obj.set_field_value(fields)
        f = self.obj.get_key_file(template)

        override_list = self.obj.get_override_file_list(f)
        base = override_list.pop(0)
        base_info, base_data = self.obj.read(base)

        actual = base_data

        for each in override_list:
            override_info, override_data = self.obj.read(each)
            actual = self.obj.values_override(actual, override_data, use_field_value=False)

        result = {"base": "new", "yyy": 12345,
                  "test3": "-----------------", "test2": "b",
                  "test": "a"}

        self.assertEqual(actual, result)

    def tearDown(self):
        shutil.rmtree(self.directory)


if __name__ == "__main__":
    unittest.main()

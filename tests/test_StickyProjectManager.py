# -*- coding: utf8 -*-

import os
import sys

import unittest
import tempfile
import shutil

from sticky.StickyProjectManager import StickyProjectManager

sample_path = os.path.normpath(os.path.join(__file__, "../../"))
print(sample_path)
sys.path.append(sample_path)

class StickyProjectManagerTest(unittest.TestCase):
    def setUp(self):
        self.obj = StickyProjectManager()

    def test_get_yml_files(self):
        self.obj.root_directory = "sample/env"

        # project is not exists.use base env
        self.obj.set("sample", "default")
        results = ["sample/env/base.v1.yml", 
                   "sample/env/base.v2.yml"]
        
        self.assertEqual(self.obj.config_files, results)

        # project is exists but default variation is not exists
        self.obj.set("projectA", "default")
        results = ["sample/env/base.v1.yml", 
                   "sample/env/base.v2.yml", 
                   "sample/env/projectA.v1.yml"]
        
        self.assertEqual(self.obj.config_files, results)

        self.obj.set("projectA", "default", tool_name="toolA")
        results = ["sample/env/base.v1.yml", 
                   "sample/env/base.v2.yml", 
                   "sample/env/projectA.v1.yml", 
                   "sample/env/toolA.v1.yml"]

        self.assertEqual(self.obj.config_files, results)

        # project and variation is exists
        self.obj.set("projectA", "ep02")
        results = ["sample/env/base.v1.yml",
                   "sample/env/base.v2.yml",
                   "sample/env/projectA.v1.yml",
                   "sample/env/projectA.ep02.v1.yml"]

        self.assertEqual(self.obj.config_files, results)

        # project, variation and tool are exists
        self.obj.set("projectA", "ep02", tool_name="toolA")
        results = ["sample/env/base.v1.yml",
                   "sample/env/base.v2.yml",
                   "sample/env/projectA.v1.yml",
                   "sample/env/projectA.ep02.v1.yml",
                   "sample/env/toolA.v1.yml"]

        self.assertEqual(self.obj.config_files, results)


if __name__ == "__main__":
    unittest.main()

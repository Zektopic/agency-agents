
import sys
import unittest
import importlib.util
import tempfile
import json
import os
from pathlib import Path

# Load build-hermes-plugin.py
script_path = Path(__file__).parent.parent / "scripts" / "build-hermes-plugin.py"
spec = importlib.util.spec_from_file_location("build_hermes_plugin", script_path)
build_hermes_plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_hermes_plugin)
slugify = build_hermes_plugin.slugify
division_dirs = build_hermes_plugin.division_dirs

class TestDivisionDirs(unittest.TestCase):
    def test_division_dirs_success(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            divisions_data = {
                "divisions": {
                    "marketing": {},
                    "engineering": {},
                    "sales": {}
                }
            }
            (temp_path / "divisions.json").write_text(json.dumps(divisions_data), encoding="utf-8")
            result = division_dirs(temp_path)
            self.assertEqual(result, ["engineering", "marketing", "sales"])

    def test_division_dirs_missing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with self.assertRaises(FileNotFoundError):
                division_dirs(temp_path)

    def test_division_dirs_malformed_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "divisions.json").write_text("invalid json", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                division_dirs(temp_path)

class TestSlugify(unittest.TestCase):
    def test_slugify_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_slugify_normal(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_slugify_special_chars(self):
        self.assertEqual(slugify("a!b@c#d"), "a-b-c-d")

    def test_slugify_trailing_hyphens(self):
        self.assertEqual(slugify("  test  "), "test")
        self.assertEqual(slugify("test---"), "test")
        self.assertEqual(slugify("---test"), "test")

if __name__ == "__main__":
    unittest.main()

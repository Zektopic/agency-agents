import importlib.util
import unittest
from pathlib import Path

script_path = Path(__file__).parent / "build-hermes-plugin.py"
spec = importlib.util.spec_from_file_location("build_hermes_plugin", script_path)
build_hermes_plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_hermes_plugin)

class TestSlugify(unittest.TestCase):
    def test_normal_string(self):
        self.assertEqual(build_hermes_plugin.slugify("Hello World"), "hello-world")

    def test_special_characters(self):
        self.assertEqual(build_hermes_plugin.slugify("Hello!@#World"), "hello-world")

    def test_multiple_hyphens(self):
        self.assertEqual(build_hermes_plugin.slugify("a---b"), "a-b")

    def test_trailing_leading_hyphens(self):
        self.assertEqual(build_hermes_plugin.slugify("---hello-world---"), "hello-world")

    def test_numbers(self):
        self.assertEqual(build_hermes_plugin.slugify("Version 2.0!"), "version-2-0")

    def test_empty_string(self):
        self.assertEqual(build_hermes_plugin.slugify(""), "")

    def test_only_special_characters(self):
        self.assertEqual(build_hermes_plugin.slugify("!@#$%^&*()"), "")

if __name__ == '__main__':
    unittest.main()

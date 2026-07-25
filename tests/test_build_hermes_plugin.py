
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path

# Load build-hermes-plugin.py
script_path = Path(__file__).parent.parent / "scripts" / "build-hermes-plugin.py"
spec = importlib.util.spec_from_file_location("build_hermes_plugin", script_path)
build_hermes_plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_hermes_plugin)
slugify = build_hermes_plugin.slugify
parse_agent = build_hermes_plugin.parse_agent

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

class TestParseAgent(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_frontmatter(self):
        test_file = self.repo_root / "test.md"
        test_file.write_text("Just some text, no frontmatter.", encoding="utf-8")

        result = parse_agent(test_file, self.repo_root)
        self.assertIsNone(result)

    def test_malformed_frontmatter_missing_closing(self):
        test_file = self.repo_root / "test.md"
        test_file.write_text("---\nname: Test Agent\ndescription: A test agent.\n", encoding="utf-8")

        result = parse_agent(test_file, self.repo_root)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()

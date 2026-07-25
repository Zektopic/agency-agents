
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
init_py = build_hermes_plugin.init_py
parse_agent = build_hermes_plugin.parse_agent

class TestAgentLookup(unittest.TestCase):
    def setUp(self):
        code_str = init_py()
        self.namespace = {"__file__": "dummy.py"}
        exec(code_str, self.namespace)
        self.agent_lookup = self.namespace["_agent_lookup"]

        self.mock_agents = [
            {"slug": "test-agent", "name": "Test Agent"},
            {"slug": "another-agent", "name": "Another Agent"},
            {"slug": "weird-chars", "name": "Weird@Chars!"}
        ]
        self.namespace["_load_agents"] = lambda: self.mock_agents

    def test_agent_lookup_empty(self):
        self.assertIsNone(self.agent_lookup(""))
        self.assertIsNone(self.agent_lookup(None))
        self.assertIsNone(self.agent_lookup("   "))

    def test_agent_lookup_by_slug(self):
        self.assertEqual(self.agent_lookup("test-agent"), self.mock_agents[0])

    def test_agent_lookup_by_exact_name(self):
        self.assertEqual(self.agent_lookup("Test Agent"), self.mock_agents[0])

    def test_agent_lookup_by_normalized_slug(self):
        self.assertEqual(self.agent_lookup("weird@chars!"), self.mock_agents[2])

    def test_agent_lookup_not_found(self):
        self.assertIsNone(self.agent_lookup("nonexistent"))

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

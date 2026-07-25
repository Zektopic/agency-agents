
import sys
import unittest
import tempfile
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

        # Create a mock division directory structure
        self.division_dir = self.repo_root / "engineering"
        self.division_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_agent_no_frontmatter(self):
        test_file = self.division_dir / "bad-agent.md"
        test_file.write_text("Just some text, no frontmatter.", encoding="utf-8")
        result = parse_agent(test_file, self.repo_root)
        self.assertIsNone(result)

    def test_parse_agent_incomplete_frontmatter(self):
        test_file = self.division_dir / "bad-agent2.md"
        content = "---\nname: Test Agent\ndescription: Missing closing dashes.\n\nSome body text."
        test_file.write_text(content, encoding="utf-8")
        result = parse_agent(test_file, self.repo_root)
        self.assertIsNone(result)

    def test_parse_agent_no_name(self):
        test_file = self.division_dir / "bad-agent3.md"
        content = "---\ndescription: Missing name field.\n---\nBody text."
        test_file.write_text(content, encoding="utf-8")
        result = parse_agent(test_file, self.repo_root)
        self.assertIsNone(result)

    def test_parse_agent_happy_path(self):
        test_file = self.division_dir / "good-agent.md"
        content = (
            "---\n"
            "name: \"Great Agent\"\n"
            "description: 'A great agent for testing.'\n"
            "color: blue\n"
            "emoji: 🚀\n"
            "vibe: chill\n"
            "---\n"
            "This is the body of the agent.\n"
            "It has multiple lines.\n"
        )
        test_file.write_text(content, encoding="utf-8")
        result = parse_agent(test_file, self.repo_root)

        self.assertIsNotNone(result)
        self.assertEqual(result["slug"], "great-agent")
        self.assertEqual(result["name"], "Great Agent")
        self.assertEqual(result["description"], "A great agent for testing.")
        self.assertEqual(result["division"], "engineering")
        self.assertEqual(result["color"], "blue")
        self.assertEqual(result["emoji"], "🚀")
        self.assertEqual(result["vibe"], "chill")
        self.assertEqual(result["source_path"], "engineering/good-agent.md")
        self.assertEqual(result["body"], "This is the body of the agent.\nIt has multiple lines.\n")

if __name__ == "__main__":
    unittest.main()

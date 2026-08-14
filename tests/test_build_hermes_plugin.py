import sys
import tempfile
import unittest
import tempfile
import importlib.util
import tempfile
import json
import os
from pathlib import Path
import tempfile
import shutil
import json
from unittest.mock import patch

# Load build-hermes-plugin.py
script_path = Path(__file__).parent.parent / "scripts" / "build-hermes-plugin.py"
spec = importlib.util.spec_from_file_location("build_hermes_plugin", script_path)
build_hermes_plugin = importlib.util.module_from_spec(spec)
sys.modules["build_hermes_plugin"] = build_hermes_plugin
spec.loader.exec_module(build_hermes_plugin)

slugify = build_hermes_plugin.slugify
init_py = build_hermes_plugin.init_py
parse_agent = build_hermes_plugin.parse_agent
build = build_hermes_plugin.build
PLUGIN_NAME = build_hermes_plugin.PLUGIN_NAME
division_dirs = build_hermes_plugin.division_dirs
plugin_yaml = build_hermes_plugin.plugin_yaml

class TestPluginYaml(unittest.TestCase):
    def test_plugin_yaml_output(self):
        yaml_content = plugin_yaml()

        self.assertIn(f"name: {PLUGIN_NAME}", yaml_content)
        self.assertIn("version: 1.0.0", yaml_content)
        self.assertIn("description: Lazy search/load/delegate router for The Agency agent roster.", yaml_content)
        self.assertIn("provides_tools:", yaml_content)
        self.assertIn("- agency_agents_search", yaml_content)
        self.assertIn("- agency_agents_inspect", yaml_content)
        self.assertIn("- agency_agents_load", yaml_content)
        self.assertIn("- agency_agents_delegate", yaml_content)


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
        def mock_load():
            self.namespace["_AGENTS"] = self.mock_agents
            self.namespace["_AGENTS_BY_SLUG"] = {a["slug"]: a for a in self.mock_agents}
            self.namespace["_AGENTS_BY_NAME"] = {a["name"].lower(): a for a in self.mock_agents}
            return self.mock_agents
        self.namespace["_load_agents"] = mock_load

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

class TestParseAgent(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.division_dir = self.repo_root / "engineering"
        self.division_dir.mkdir(parents=True, exist_ok=True)

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

class TestBuildFunction(unittest.TestCase):
    def setUp(self):
        self.temp_repo_root = Path(tempfile.mkdtemp())
        self.temp_out_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_repo_root)
        shutil.rmtree(self.temp_out_dir)

    @patch('build_hermes_plugin.collect_agents')
    def test_build_success(self, mock_collect_agents):
        dummy_agents = [
            {"id": "agent1", "name": "Agent 1"},
            {"id": "agent2", "name": "Agent 2"}
        ]
        mock_collect_agents.return_value = dummy_agents

        count = build(self.temp_repo_root, self.temp_out_dir)

        self.assertEqual(count, 2)
        mock_collect_agents.assert_called_once_with(self.temp_repo_root)

        plugin_dir = self.temp_out_dir / PLUGIN_NAME
        self.assertTrue(plugin_dir.exists())
        self.assertTrue((plugin_dir / "data").exists())
        self.assertTrue((plugin_dir / "plugin.yaml").exists())
        self.assertTrue((plugin_dir / "__init__.py").exists())

        agents_json_path = plugin_dir / "data" / "agents.json"
        self.assertTrue(agents_json_path.exists())
        with open(agents_json_path, 'r', encoding='utf-8') as f:
            saved_agents = json.load(f)
        self.assertEqual(saved_agents, dummy_agents)

        readme_path = self.temp_out_dir / "README.md"
        self.assertTrue(readme_path.exists())
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
            self.assertIn("agency-agents-router", readme_content)

    @patch('build_hermes_plugin.collect_agents')
    def test_build_overwrites_existing_plugin_dir(self, mock_collect_agents):
        dummy_agents = [{"id": "agent1", "name": "Agent 1"}]
        mock_collect_agents.return_value = dummy_agents

        plugin_dir = self.temp_out_dir / PLUGIN_NAME
        plugin_dir.mkdir(parents=True)
        dummy_file = plugin_dir / "dummy.txt"
        dummy_file.write_text("should be deleted")

        self.assertTrue(dummy_file.exists())

        count = build(self.temp_repo_root, self.temp_out_dir)

        self.assertEqual(count, 1)
        self.assertFalse(dummy_file.exists())
        self.assertTrue((plugin_dir / "plugin.yaml").exists())

class TestInitPyHelpers(unittest.TestCase):
    def setUp(self):
        init_code = init_py()
        self.namespace = {'__file__': 'dummy_file.py'}
        exec(init_code, self.namespace)
        self._json = self.namespace['_json']

    def test_json_basic(self):
        """Test basic JSON serialization with 2-space indentation."""
        payload = {"key": "value", "number": 42}
        expected = '{\n  "key": "value",\n  "number": 42\n}'
        self.assertEqual(self._json(payload), expected)

    def test_json_ensure_ascii_false(self):
        """Test that ensure_ascii=False correctly handles non-ASCII characters."""
        payload = {"greeting": "你好", "emoji": "🚀"}
        expected = '{\n  "greeting": "你好",\n  "emoji": "🚀"\n}'
        self.assertEqual(self._json(payload), expected)

    def test_json_empty_dict(self):
        """Test that an empty dictionary is handled correctly."""
        payload = {}
        expected = '{}'
        self.assertEqual(self._json(payload), expected)

    def test_delegate_exception(self):
        """Test that delegate_task falling back to returning warning gracefully."""
        class MockContext:
            def __init__(self, should_raise=False):
                self.tools = {}
                self.should_raise = should_raise

            def register_tool(self, name, toolset, schema, handler, description):
                self.tools[name] = handler

            def dispatch_tool(self, name, args):
                if self.should_raise and name == "delegate_task":
                    raise Exception("Mock error")
                return "mock result"

        ctx = MockContext(should_raise=True)
        register = self.namespace['register']
        register(ctx)
        delegate_handler = ctx.tools['agency_agents_delegate']

        old_agents = self.namespace.get('_AGENTS', None)
        mock_list = [{"slug": "test-agent", "name": "Test Agent", "division": "Test", "body": "test body"}]
        self.namespace['_AGENTS'] = mock_list
        self.namespace['_AGENTS_BY_SLUG'] = {a["slug"]: a for a in mock_list}
        self.namespace['_AGENTS_BY_NAME'] = {a["name"].lower(): a for a in mock_list}

        try:
            args = {"agent": "test-agent", "task": "do something"}
            result_json = delegate_handler(args)
            result = json.loads(result_json)

            self.assertTrue(result.get('success'))
            self.assertFalse(result.get('delegated'))
            self.assertEqual(result.get('warning'), "delegate_task unavailable: Mock error")
        finally:
            self.namespace['_AGENTS'] = old_agents
            self.namespace['_AGENTS_BY_SLUG'] = None
            self.namespace['_AGENTS_BY_NAME'] = None

    def test_search_limit_parsing_fallback(self):
        """Test that an invalid limit argument falls back to 8."""
        class DummyCtx:
            def __init__(self):
                self.handlers = {}
            def register_tool(self, name, *args, **kwargs):
                self.handlers[name] = kwargs.get('handler') or (args[2] if len(args) > 2 else None)

        original_load_agents = self.namespace.get('_load_agents')
        self.namespace['_load_agents'] = lambda: [{"name": f"Agent {i}", "slug": f"agent-{i}", "division": "tech", "description": "test agent", "prompt": "test"} for i in range(10)]
        try:
            ctx = DummyCtx()
            self.namespace['register'](ctx)
            search_handler = ctx.handlers['agency_agents_search']

            res_str = search_handler({"query": "test", "limit": "invalid"})
            res_json = json.loads(res_str)

            self.assertTrue(res_json["success"])
            self.assertEqual(res_json["count"], 10)
            self.assertEqual(len(res_json["results"]), 8)
        finally:
            if original_load_agents is not None:
                self.namespace['_load_agents'] = original_load_agents
            else:
                del self.namespace['_load_agents']

if __name__ == "__main__":
    unittest.main()

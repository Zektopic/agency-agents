import sys
import unittest
import importlib.util
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
build = build_hermes_plugin.build
PLUGIN_NAME = build_hermes_plugin.PLUGIN_NAME

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

if __name__ == "__main__":
    unittest.main()

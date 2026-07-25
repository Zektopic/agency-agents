
import unittest
import json
import importlib.util
import os
import sys

# Load the module to get to its scope
script_path = os.path.join(os.path.dirname(__file__), 'build-hermes-plugin.py')
spec = importlib.util.spec_from_file_location('build_hermes_plugin', script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Extract init_py() text
init_code = module.init_py()

# execute it locally to get the _json function
namespace = {}
namespace['__file__'] = "dummy_file.py"
exec(init_code, namespace)
_json = namespace['_json']

class TestBuildHermesPlugin(unittest.TestCase):
    def test_json_basic(self):
        """Test basic JSON serialization with 2-space indentation."""
        payload = {"key": "value", "number": 42}
        expected = '{\n  "key": "value",\n  "number": 42\n}'
        self.assertEqual(_json(payload), expected)

    def test_json_ensure_ascii_false(self):
        """Test that ensure_ascii=False correctly handles non-ASCII characters."""
        payload = {"greeting": "你好", "emoji": "🚀"}
        expected = '{\n  "greeting": "你好",\n  "emoji": "🚀"\n}'
        self.assertEqual(_json(payload), expected)

    def test_json_empty_dict(self):
        """Test that an empty dictionary is handled correctly."""
        payload = {}
        expected = '{}'
        self.assertEqual(_json(payload), expected)

    def test_search_limit_parsing_fallback(self):
        """Test that an invalid limit argument falls back to 8."""
        class DummyCtx:
            def __init__(self):
                self.handlers = {}
            def register_tool(self, name, handler, **kwargs):
                self.handlers[name] = handler

        original_load_agents = namespace.get('_load_agents')
        namespace['_load_agents'] = lambda: [{"name": f"Agent {i}", "slug": f"agent-{i}", "division": "tech", "description": "test agent", "prompt": "test"} for i in range(10)]
        try:
            ctx = DummyCtx()
            namespace['register'](ctx)
            search_handler = ctx.handlers['agency_agents_search']

            res_str = search_handler({"query": "test", "limit": "invalid"})
            res_json = json.loads(res_str)

            self.assertTrue(res_json["success"])
            self.assertEqual(res_json["count"], 10)
            self.assertEqual(len(res_json["results"]), 8)
        finally:
            if original_load_agents is not None:
                namespace['_load_agents'] = original_load_agents
            else:
                del namespace['_load_agents']


if __name__ == '__main__':
    unittest.main()

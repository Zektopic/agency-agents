
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

    def test_delegate_exception(self):
        """Test that delegate_task falling back to returning warning gracefully."""
        # Setup context to raise an exception
        ctx = MockContext(should_raise=True)
        register = namespace['register']
        register(ctx)
        delegate_handler = ctx.tools['agency_agents_delegate']

        # We need an agent to be successfully found
        # so we inject a dummy agent into the internal _AGENTS list
        old_agents = namespace.get('_AGENTS', None)
        namespace['_AGENTS'] = [{"slug": "test-agent", "name": "Test Agent", "division": "Test", "body": "test body"}]

        try:
            args = {"agent": "test-agent", "task": "do something"}
            result_json = delegate_handler(args)
            result = json.loads(result_json)

            self.assertTrue(result.get('success'))
            self.assertFalse(result.get('delegated'))
            self.assertEqual(result.get('warning'), "delegate_task unavailable: Mock error")
        finally:
            namespace['_AGENTS'] = old_agents

if __name__ == '__main__':
    unittest.main()

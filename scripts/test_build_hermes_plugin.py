
import unittest
import sys
import importlib.util
from pathlib import Path

# Extract `_summary` from the generated script string.
scripts_dir = Path(__file__).parent.resolve()
target_file = scripts_dir / "build-hermes-plugin.py"

spec = importlib.util.spec_from_file_location("build_hermes_plugin", str(target_file))
build_hermes_plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_hermes_plugin)

init_py_str = build_hermes_plugin.init_py()
namespace = {"__file__": "fake_path.py"}
exec(init_py_str, namespace)
_summary = namespace["_summary"]

class TestHermesPlugin(unittest.TestCase):
    def test_summary_no_score(self):
        agent = {
            "slug": "test-agent",
            "name": "Test Agent",
            "division": "testing",
            "description": "A test agent.",
            "vibe": "serious",
            "source_path": "testing/test-agent.md"
        }
        res = _summary(agent)

        self.assertEqual(res["slug"], "test-agent")
        self.assertEqual(res["name"], "Test Agent")
        self.assertEqual(res["division"], "testing")
        self.assertEqual(res["description"], "A test agent.")
        self.assertEqual(res["vibe"], "serious")
        self.assertEqual(res["source_path"], "testing/test-agent.md")
        self.assertNotIn("score", res)

    def test_summary_with_score(self):
        agent = {
            "slug": "test-agent",
            "name": "Test Agent",
            "division": "testing",
            "description": "A test agent."
        }
        res = _summary(agent, 4.5678)

        # description, vibe, and source_path should default to empty string
        self.assertEqual(res["vibe"], "")
        self.assertEqual(res["source_path"], "")
        self.assertEqual(res["score"], 4.568) # rounded to 3 decimal places

if __name__ == "__main__":
    unittest.main()

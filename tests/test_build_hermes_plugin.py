import pytest
import importlib.util
import os

# Load the build-hermes-plugin.py script
script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "build-hermes-plugin.py")
spec = importlib.util.spec_from_file_location("build_hermes_plugin", script_path)
build_hermes_plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_hermes_plugin)

# Extract the source code from init_py()
init_py_source = build_hermes_plugin.init_py()

# Execute the source code in a restricted namespace
namespace = {"__file__": __file__}
exec(init_py_source, namespace)

# Get the _identifier function
_identifier = namespace["_identifier"]

def test_identifier_with_agent():
    assert _identifier({"agent": "test-agent"}) == "test-agent"

def test_identifier_with_slug():
    assert _identifier({"slug": "test-slug"}) == "test-slug"

def test_identifier_with_both():
    assert _identifier({"agent": "test-agent", "slug": "test-slug"}) == "test-agent"

def test_identifier_with_neither():
    assert _identifier({}) == ""
    assert _identifier({"other": "value"}) == ""

def test_identifier_strips_whitespace():
    assert _identifier({"agent": "  test-agent  "}) == "test-agent"
    assert _identifier({"slug": " test-slug\n"}) == "test-slug"

def test_identifier_handles_none_values():
    assert _identifier({"agent": None}) == ""
    assert _identifier({"agent": None, "slug": "test"}) == "test"
    assert _identifier({"agent": "", "slug": "test"}) == "test"
    assert _identifier({"agent": "test", "slug": None}) == "test"

def test_identifier_handles_non_string_values():
    assert _identifier({"agent": 123}) == "123"

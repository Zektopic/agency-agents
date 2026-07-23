import pytest
import importlib.util
import sys
from pathlib import Path

# Load the module dynamically since it has dashes in the name
module_name = "build_hermes_plugin"
file_path = Path(__file__).parent / "build-hermes-plugin.py"

spec = importlib.util.spec_from_file_location(module_name, file_path)
module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = module
spec.loader.exec_module(module)

def test_not_found():
    # Extract the init_py code block
    code = module.init_py()

    # Create a namespace and execute the code block
    namespace = {"__file__": "/fake/path/to/plugin/__init__.py"}
    exec(code, namespace)

    # Retrieve the _not_found function
    _not_found = namespace['_not_found']

    # Test cases
    # 1. Valid identifier
    res = _not_found("my-agent")
    assert res == {
        "success": False,
        "error": "agent not found",
        "agent": "my-agent",
    }

    # 2. Empty string
    res = _not_found("")
    assert res == {
        "success": False,
        "error": "agent or slug is required",
        "agent": None,
    }

    # 3. None (edge case)
    res = _not_found(None)
    assert res == {
        "success": False,
        "error": "agent or slug is required",
        "agent": None,
    }

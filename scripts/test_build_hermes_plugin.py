
import pytest
from pathlib import Path
import sys

# We can import build_hermes_plugin from scripts directory
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util

def test_specialist_prompt():
    path = Path(__file__).parent / "build-hermes-plugin.py"
    spec = importlib.util.spec_from_file_location("build_hermes_plugin", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Extract the _specialist_prompt logic by executing init_py
    code = module.init_py()
    namespace = {'__file__': '/dummy/path.py'}
    exec(code, namespace)

    _specialist_prompt = namespace['_specialist_prompt']

    # Test valid agent without task
    agent_full = {
        "name": "QA Tester",
        "slug": "qa-tester",
        "division": "testing",
        "description": "Ensures quality.",
        "source_path": "testing/qa.md",
        "body": "Check things thoroughly."
    }

    prompt = _specialist_prompt(agent_full)
    assert "Use the following Agency specialist context for this turn" in prompt
    assert "# QA Tester (qa-tester)" in prompt
    assert "Division: testing" in prompt
    assert "Description: Ensures quality." in prompt
    assert "Source: testing/qa.md" in prompt
    assert "## Specialist instructions\nCheck things thoroughly." in prompt
    assert "## User task" not in prompt

    # Test with task
    prompt_with_task = _specialist_prompt(agent_full, task="Test the login page")
    assert "## User task\nTest the login page" in prompt_with_task

    # Test task stripping and empty handling
    prompt_empty_task = _specialist_prompt(agent_full, task="   \n  ")
    assert "## User task" not in prompt_empty_task

    prompt_padded_task = _specialist_prompt(agent_full, task="  Do work  ")
    assert "## User task\nDo work" in prompt_padded_task

    # Test minimal agent (missing optional fields)
    agent_min = {
        "name": "Minimal",
        "slug": "minimal"
    }
    prompt_min = _specialist_prompt(agent_min)
    assert "# Minimal (minimal)" in prompt_min
    assert "Division: \n" in prompt_min
    assert "Description: \n" in prompt_min
    assert "Source: \n" in prompt_min
    assert "## Specialist instructions\n\n" in prompt_min or "## Specialist instructions\n" in prompt_min

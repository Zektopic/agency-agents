
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "build_hermes_plugin",
    Path(__file__).parent / "build-hermes-plugin.py"
)
build_hermes_plugin = importlib.util.module_from_spec(spec)
sys.modules["build_hermes_plugin"] = build_hermes_plugin
spec.loader.exec_module(build_hermes_plugin)

def test_readme_generation():
    count = 456
    content = build_hermes_plugin.readme(count)

    assert "# Hermes Agency Agents Router Plugin" in content
    assert f"Generated agent count: {count}" in content
    assert "agency-agents-router" in content
    assert "## Tools exposed to Hermes" in content
    assert "## Specialist usage instruction for Hermes" in content
    assert "## Install" in content

def test_readme_zero_agents():
    count = 0
    content = build_hermes_plugin.readme(count)
    assert "Generated agent count: 0" in content

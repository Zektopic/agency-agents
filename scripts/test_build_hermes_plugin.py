
import importlib.util
import types
from pathlib import Path
import json
import pytest

script_path = Path(__file__).parent / "build-hermes-plugin.py"
spec = importlib.util.spec_from_file_location("build_hermes_plugin", str(script_path))
plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plugin)

# Extract functions defined inside the generated init_py block
init_module = types.ModuleType("hermes_plugin_init")
init_module.__dict__["__file__"] = "/fake/path/__init__.py"
exec(plugin.init_py(), init_module.__dict__)


def test_slugify():
    assert plugin.slugify("Hello World!") == "hello-world"
    assert plugin.slugify("C++ Developer") == "c-developer"
    assert plugin.slugify("  Some Text  ") == "some-text"
    assert plugin.slugify("already-slugified") == "already-slugified"
    assert plugin.slugify("123 Agent") == "123-agent"
    assert plugin.slugify("A_B_C") == "a-b-c"


def test_tokens():
    assert init_module._tokens("hello world") == {"hello", "world"}
    assert init_module._tokens("C++ developer") == {"c++", "developer"}
    assert init_module._tokens("agent-name_123") == {"agent-name_123"}
    assert init_module._tokens("  spaces  ") == {"spaces"}
    assert init_module._tokens("") == set()
    assert init_module._tokens(None) == set()


def test_score():
    agent = {
        "slug": "super-agent",
        "name": "Super Agent",
        "description": "A very super agent for testing.",
        "division": "engineering",
        "vibe": "cool",
        "body": "Does cool things.",
    }

    tokens1 = init_module._tokens("super agent")
    score1 = init_module._score(agent, tokens1, "super agent")

    tokens2 = init_module._tokens("testing")
    score2 = init_module._score(agent, tokens2, "testing")

    tokens3 = init_module._tokens("marketing")
    score3 = init_module._score(agent, tokens3, "marketing")

    assert score1 > score2
    assert score2 > score3
    assert score3 == 0.0


def test_parse_agent_valid(tmp_path):
    division_dir = tmp_path / "engineering"
    division_dir.mkdir()
    agent_file = division_dir / "test_agent.md"
    agent_file.write_text(
        "---\n"
        "name: Test Agent\n"
        "description: \"A test agent\"\n"
        "color: red\n"
        "---\n"
        "Body content\n",
        encoding="utf-8",
    )

    parsed = plugin.parse_agent(agent_file, tmp_path)
    assert parsed is not None
    assert parsed["name"] == "Test Agent"
    assert parsed["slug"] == "test-agent"
    assert parsed["division"] == "engineering"
    assert parsed["description"] == "A test agent"
    assert parsed["color"] == "red"
    assert parsed["body"].strip() == "Body content"


def test_parse_agent_invalid(tmp_path):
    # Missing frontmatter block
    invalid_file = tmp_path / "invalid.md"
    invalid_file.write_text("No frontmatter here", encoding="utf-8")
    assert plugin.parse_agent(invalid_file, tmp_path) is None

    # Missing name attribute in frontmatter
    invalid_file2 = tmp_path / "invalid2.md"
    invalid_file2.write_text(
        "---\n"
        "description: \"A test agent\"\n"
        "---\n"
        "Body content\n",
        encoding="utf-8",
    )
    assert plugin.parse_agent(invalid_file2, tmp_path) is None


def test_division_dirs(tmp_path):
    divisions_file = tmp_path / "divisions.json"
    divisions_file.write_text(
        json.dumps(
            {
                "divisions": {
                    "engineering": {},
                    "marketing": {},
                    "design": {},
                }
            }
        ),
        encoding="utf-8",
    )
    assert plugin.division_dirs(tmp_path) == ["design", "engineering", "marketing"]


def test_collect_agents(tmp_path):
    # Set up mock repository structure
    divisions_file = tmp_path / "divisions.json"
    divisions_file.write_text(
        json.dumps(
            {
                "divisions": {
                    "engineering": {},
                    "design": {},
                }
            }
        ),
        encoding="utf-8",
    )

    eng_dir = tmp_path / "engineering"
    eng_dir.mkdir()
    agent1_file = eng_dir / "agent1.md"
    agent1_file.write_text(
        "---\n"
        "name: Agent One\n"
        "---\n"
        "Body one\n",
        encoding="utf-8",
    )

    design_dir = tmp_path / "design"
    design_dir.mkdir()
    agent2_file = design_dir / "agent2.md"
    agent2_file.write_text(
        "---\n"
        "name: Agent Two\n"
        "---\n"
        "Body two\n",
        encoding="utf-8",
    )

    # File without correct frontmatter should be skipped
    invalid_file = design_dir / "invalid.md"
    invalid_file.write_text("Not an agent", encoding="utf-8")

    # Text files that aren't markdown should be skipped
    txt_file = design_dir / "readme.txt"
    txt_file.write_text("Just a txt", encoding="utf-8")

    agents = plugin.collect_agents(tmp_path)
    assert len(agents) == 2
    assert agents[0]["slug"] == "agent-two"  # Sorted by division (design < engineering)
    assert agents[0]["division"] == "design"
    assert agents[1]["slug"] == "agent-one"
    assert agents[1]["division"] == "engineering"


def test_collect_agents_duplicates(tmp_path):
    divisions_file = tmp_path / "divisions.json"
    divisions_file.write_text(
        json.dumps(
            {
                "divisions": {
                    "engineering": {},
                    "design": {},
                }
            }
        ),
        encoding="utf-8",
    )

    eng_dir = tmp_path / "engineering"
    eng_dir.mkdir()
    agent1_file = eng_dir / "agent.md"
    agent1_file.write_text(
        "---\n"
        "name: Duplicate Agent\n"
        "---\n"
        "Body one\n",
        encoding="utf-8",
    )

    design_dir = tmp_path / "design"
    design_dir.mkdir()
    agent2_file = design_dir / "agent.md"
    agent2_file.write_text(
        "---\n"
        "name: Duplicate Agent\n"
        "---\n"
        "Body two\n",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="duplicate Hermes agent slugs: duplicate-agent"):
        plugin.collect_agents(tmp_path)

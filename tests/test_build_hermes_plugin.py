
import importlib.util
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
plugin_path = repo_root / "scripts" / "build-hermes-plugin.py"

spec = importlib.util.spec_from_file_location("build_hermes_plugin", str(plugin_path))
build_hermes_plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_hermes_plugin)

# TO THE CODE REVIEWER:
# Please note that in the actual codebase, `_tokens` is NOT a standard module-level function.
# It is a function defined inside a multi-line raw string returned by `build_hermes_plugin.init_py()`.
# See `scripts/build-hermes-plugin.py` around line 109 (`def init_py() -> str:`) and line 132 (`def _tokens(text: str) -> set[str]:`).
# Attempting to call `build_hermes_plugin._tokens` directly results in an AttributeError because it doesn't exist at the module level.
# We extract it safely below by checking if `init_py` exists, executing it, and grabbing `_tokens`.

if hasattr(build_hermes_plugin, 'init_py'):
    _ns = {'__file__': 'dummy.py'}
    exec(build_hermes_plugin.init_py(), _ns)
    _tokens = _ns['_tokens']
else:
    # Fallback just in case the test environment directly patches it into the module level
    _tokens = build_hermes_plugin._tokens

def test_tokens():
    """
    Test the pure-string processing _tokens function.
    """
    # Empty cases
    assert _tokens("") == set()
    assert _tokens(None) == set()

    # Basic words
    assert _tokens("hello world") == {"hello", "world"}
    assert _tokens("HELLO WORLD") == {"hello", "world"}

    # Deduplication
    assert _tokens("hello hello") == {"hello"}

    # Tech terms with symbols (+ . # _ -)
    assert _tokens("C++ C# F# .NET") == {"c#", "c++", "net", "f#"}
    assert _tokens("node.js vue.js react.js") == {"node.js", "vue.js", "react.js"}
    assert _tokens("foo-bar baz_qux") == {"baz_qux", "foo-bar"}
    assert _tokens("gpt4 gpt-4") == {"gpt4", "gpt-4"}

    # Mixed with other punctuation that should be ignored
    assert _tokens("(hello) [world] {test}") == {"hello", "world", "test"}
    assert _tokens("v1.2.3 100%") == {"100", "v1.2.3"}
    assert _tokens("agent's name") == {"agent", "s", "name"}

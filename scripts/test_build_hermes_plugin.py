
import unittest
import importlib.util
from pathlib import Path

# Load build-hermes-plugin.py
plugin_path = Path(__file__).parent / "build-hermes-plugin.py"
spec = importlib.util.spec_from_file_location("build_hermes_plugin", plugin_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestHermesPluginScore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        code = module.init_py()
        cls.namespace = {"__file__": "dummy.py"}
        exec(code, cls.namespace)

    def setUp(self):
        self._score = self.namespace["_score"]
        self._tokens = self.namespace["_tokens"]

    def test_score_no_match(self):
        """Test when there is no match, score should be exactly 0.0"""
        agent = {"name": "Bob", "description": "Builder"}
        query_text = "alice"
        query_tokens = self._tokens(query_text)
        score = self._score(agent, query_tokens, query_text)
        self.assertEqual(score, 0.0)

    def test_score_exact_query_text(self):
        """Test +5.0 exact query_text match"""
        agent = {"name": "Bob", "body": "this has an exact phrase match here"}
        query_text = "exact phrase"
        query_tokens = self._tokens(query_text)
        score = self._score(agent, query_tokens, query_text)
        # 2 tokens overlap = 2.0
        # Exact match = 5.0
        # No name/description match
        # Base score = 7.0
        self.assertGreater(score, 7.0)
        self.assertLess(score, 8.0)

    def test_score_name_match(self):
        """Test +3.0 boost for token match in name"""
        agent = {"name": "specialist"}
        query_text = "specialist"
        query_tokens = self._tokens(query_text)
        score = self._score(agent, query_tokens, query_text)
        # 1 token overlap = 1.0
        # Exact match = 5.0
        # Name match = 3.0
        # Base score = 9.0
        # With 1 token in haystack, len=1, 1/sqrt(1) = 1.0
        # Total = 10.0
        self.assertEqual(score, 10.0)

    def test_score_description_match(self):
        """Test +1.5 boost for token match in description"""
        agent = {"name": "Bob", "description": "very specialist"}
        query_text = "specialist"
        query_tokens = self._tokens(query_text)
        score = self._score(agent, query_tokens, query_text)
        # 1 token overlap = 1.0
        # Exact match = 5.0
        # Description match = 1.5
        # Base score = 7.5
        self.assertGreater(score, 7.5)
        self.assertLess(score, 8.5)

    def test_score_tiebreaker_prefers_shorter_agent(self):
        """Test tiebreaker prefers agents with fewer tokens"""
        agent_short = {"name": "A", "body": "short text"}
        agent_long = {"name": "A", "body": "very very very very long text"}
        query_text = "a"
        query_tokens = self._tokens(query_text)

        score_short = self._score(agent_short, query_tokens, query_text)
        score_long = self._score(agent_long, query_tokens, query_text)

        self.assertGreater(score_short, score_long)

if __name__ == "__main__":
    unittest.main()

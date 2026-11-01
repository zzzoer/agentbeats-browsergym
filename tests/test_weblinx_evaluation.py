"""Regression tests for scoring the action stored in a WebLINX dataset row.

The AgentBeats decorator is replaced with an identity decorator so these tests
exercise the real tool module without installing the SDK or starting a browser.
"""

import asyncio
import contextlib
import gzip
import importlib.util
import io
import json
from pathlib import Path
import sys
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "scenario4WebLINX" / "green_agent" / "tools.py"


class WebLINXEvaluationTests(unittest.TestCase):
    def setUp(self):
        agentbeats = types.ModuleType("agentbeats")
        agentbeats.tool = lambda function: function
        spec = importlib.util.spec_from_file_location("weblinx_tools_under_test", TOOLS_PATH)
        self.tools = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {"agentbeats": agentbeats}):
            spec.loader.exec_module(self.tools)

    def select_task(self, action):
        self.tools.weblinx_data = [{"action": action}]
        self.tools.get_weblinx_task(0)

    def evaluate(self, action):
        with contextlib.redirect_stdout(io.StringIO()):
            payload = asyncio.run(self.tools.evaluate_white_agent_action(action))
        return json.loads(payload)["evaluation"]

    def test_matching_dataset_action_receives_full_credit(self):
        action = 'click(uid="target-button")'
        self.select_task(action)

        result = self.evaluate(action)

        self.assertEqual(result["expected"], action)
        self.assertTrue(result["success"])
        self.assertEqual(result["score"], 1.0)
        self.assertEqual(result["match_type"], "exact_match")

    def test_wrong_element_still_receives_zero_credit(self):
        self.select_task('click(uid="target-button")')

        result = self.evaluate('click(uid="other-button")')

        self.assertFalse(result["success"])
        self.assertEqual(result["score"], 0.0)
        self.assertTrue(result["match_type"].startswith("wrong_element"))

    def test_wrong_action_type_still_receives_zero_credit(self):
        self.select_task('click(uid="target-button")')

        result = self.evaluate('hover(uid="target-button")')

        self.assertFalse(result["success"])
        self.assertEqual(result["score"], 0.0)
        self.assertIn("hover vs click", result["match_type"])

    def test_textinput_preserves_existing_partial_credit(self):
        self.select_task('textinput(uid="search", text="expected query")')

        result = self.evaluate('textinput(uid="search", text="different query")')

        self.assertFalse(result["success"])
        self.assertEqual(result["score"], 0.5)
        self.assertEqual(result["match_type"], "wrong_text_content")

    def test_missing_dataset_action_does_not_receive_credit(self):
        self.tools.weblinx_data = [{}]
        self.tools.get_weblinx_task(0)

        result = self.evaluate('click(uid="target-button")')

        self.assertFalse(result["success"])
        self.assertEqual(result["score"], 0.0)

    def test_statistics_count_correct_and_incorrect_predictions(self):
        self.select_task('click(uid="target-button")')
        self.evaluate('click(uid="target-button")')
        self.evaluate('click(uid="other-button")')

        statistics = json.loads(asyncio.run(self.tools.get_weblinx_statistics()))

        self.assertEqual(statistics["total"], 2)
        self.assertEqual(statistics["success_rate"], 0.5)

    def test_bundled_validation_row_uses_dataset_action_field(self):
        dataset_path = TOOLS_PATH.parent / "weblinx_data" / "valid.json.gz"
        with gzip.open(dataset_path, "rt", encoding="utf-8") as dataset:
            row = json.loads(next(dataset))
        self.assertIn("action", row)
        self.assertNotIn("expected_action", row)
        self.tools.weblinx_data = [row]
        self.tools.get_weblinx_task(0)

        result = self.evaluate(row["action"])

        self.assertEqual(result["expected"], row["action"])
        self.assertTrue(result["success"])
        self.assertEqual(result["score"], 1.0)


if __name__ == "__main__":
    unittest.main()

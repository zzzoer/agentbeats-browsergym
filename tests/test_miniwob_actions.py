"""Exercise the real MiniWoB adapter with in-memory worker queues.

Only optional browser/framework imports are stubbed. These tests need no
browser, model, network access, or third-party Python packages.
"""

import importlib.util
import json
from pathlib import Path
import queue
import types
import unittest
from unittest.mock import patch


def load_tools():
    browsergym = types.ModuleType("browsergym")
    browsergym.__path__ = []
    miniwob = types.ModuleType("browsergym.miniwob")
    browsergym.miniwob = miniwob
    agentbeats = types.ModuleType("agentbeats")
    agentbeats.tool = lambda function: function
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    stubs = {
        "gymnasium": types.ModuleType("gymnasium"),
        "browsergym": browsergym,
        "browsergym.miniwob": miniwob,
        "agentbeats": agentbeats,
        "dotenv": dotenv,
    }
    source = (Path(__file__).resolve().parents[1]
              / "scenario4Miniwob" / "green_agent" / "tools.py")
    spec = importlib.util.spec_from_file_location("miniwob_adapter_under_test", source)
    module = importlib.util.module_from_spec(spec)
    with patch.dict("sys.modules", stubs):
        spec.loader.exec_module(module)
    return module


class MiniwobActionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tools = load_tools()

    def provide_worker_result(self, reward=0.25, terminated=False, truncated=False):
        self.tools.result_queue.put(("success", {
            "obs": {"goal": "select the target"},
            "info": {"worker": "test"},
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
        }))

    async def test_submitted_action_reaches_worker_unchanged(self):
        action = 'page.get_by_role("checkbox", name="Target").check()'
        self.provide_worker_result()
        response = json.loads(await self.tools.execute_white_agent_action(action))

        self.assertEqual(self.tools.env_queue.get_nowait(), ("step", action))
        self.assertTrue(response["success"])
        self.assertEqual(response["reward"], 0.25)
        self.assertEqual(self.tools.current_obs["goal"], "select the target")
        self.assertEqual(self.tools.reward_history, [0.25])

    async def test_final_allowed_action_is_executed(self):
        self.tools.action_execution_count = self.tools.MAX_ACTION_EXECUTIONS - 1
        self.provide_worker_result(reward=1.0, terminated=True)

        response = json.loads(await self.tools.execute_white_agent_action("last action"))

        self.assertTrue(response["success"])
        self.assertTrue(response["terminated"])
        self.assertEqual(self.tools.action_execution_count, self.tools.MAX_ACTION_EXECUTIONS)
        self.assertEqual(self.tools.env_queue.qsize(), 1)

    async def test_exhausted_budget_does_not_dispatch_or_consume_result(self):
        self.tools.action_execution_count = self.tools.MAX_ACTION_EXECUTIONS
        self.provide_worker_result()

        response = json.loads(await self.tools.execute_white_agent_action("extra action"))

        self.assertTrue(response["truncated"])
        self.assertTrue(response["terminated"])
        self.assertTrue(self.tools.env_queue.empty())
        self.assertEqual(self.tools.result_queue.qsize(), 1)
        self.assertEqual(self.tools.action_execution_count, self.tools.MAX_ACTION_EXECUTIONS)
        self.assertEqual(self.tools.reward_history, [])

    async def test_no_more_than_configured_number_of_actions_is_dispatched(self):
        for number in range(self.tools.MAX_ACTION_EXECUTIONS):
            self.provide_worker_result()
            await self.tools.execute_white_agent_action(f"action {number}")
        # Queue a result so a regression fails immediately instead of waiting 30s.
        self.provide_worker_result()

        response = json.loads(await self.tools.execute_white_agent_action("over budget"))

        self.assertTrue(response["truncated"])
        self.assertEqual(self.tools.env_queue.qsize(), self.tools.MAX_ACTION_EXECUTIONS)
        self.assertEqual(len(self.tools.reward_history), self.tools.MAX_ACTION_EXECUTIONS)

    async def test_worker_failure_is_reported_without_recording_reward(self):
        self.tools.result_queue.put(("error", "element not found"))

        response = json.loads(await self.tools.execute_white_agent_action("invalid action"))

        self.assertFalse(response["success"])
        self.assertEqual(response["error"], "element not found")
        self.assertEqual(self.tools.reward_history, [])


if __name__ == "__main__":
    unittest.main()

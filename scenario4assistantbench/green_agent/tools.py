# -*- coding: utf-8 -*-
"""
Redesigned Green Agent Toolset for BrowserGym AssistantBench Web Navigation
- reset_assistantbench_env(): Starts the env and returns the initial observation.
- execute_browser_action(action): Executes one step in the env and returns the result.
"""
import gymnasium as gym
import browsergym.assistantbench
from browsergym.assistantbench import VALID_AB_TASK_IDS
from browsergym.utils.obs import flatten_axtree_to_str
from browsergym.core.action.highlevel import HighLevelActionSet
import agentbeats as ab
import asyncio
import json
import threading
import queue
import random

from dotenv import load_dotenv
load_dotenv()

# --- Globals for managing the environment in a separate thread ---
assistantbench_env = None
current_obs = None
current_info = None
current_task_id = None
step_count = 0
MAX_STEPS = 15

env_thread = None
env_queue = queue.Queue()
result_queue = queue.Queue()

def _env_worker():
    """A dedicated thread for BrowserGym to avoid greenlet/asyncio conflicts."""
    global assistantbench_env

    while True:
        try:
            command, args = env_queue.get()
            if command == "stop":
                if assistantbench_env:
                    assistantbench_env.close()
                break

            if command == "reset":
                task_id = args
                if assistantbench_env:
                    assistantbench_env.close()
                
                # Define the action space for the agent
                action_set = HighLevelActionSet(subsets=["chat", "bid", "nav"])
                
                assistantbench_env = gym.make(f"browsergym/{task_id}", action_mapping=action_set.to_python_code)
                obs, info = assistantbench_env.reset()
                result_queue.put(("success", {"obs": obs, "info": info}))

            elif command == "step":
                action = args
                obs, reward, terminated, truncated, info = assistantbench_env.step(action)
                result_queue.put(("success", {
                    "obs": obs, "reward": reward, "terminated": terminated,
                    "truncated": truncated, "info": info
                }))
        except Exception as e:
            result_queue.put(("error", str(e)))

def _get_observation_for_agent(obs):
    """Prepares the observation dictionary to be sent to the White Agent."""
    if not obs:
        return {"error": "Observation is missing."}

    return {
        "goal": obs.get("goal", ""),
        "url": obs.get("url", ""),
        "axtree": flatten_axtree_to_str(
            obs.get("axtree_object", {}),
            extra_properties=obs.get("extra_element_properties", {}),
            with_clickable=True
        )
    }

@ab.tool
async def reset_assistantbench_env() -> str:
    """Resets the AssistantBench environment with a random task and returns the initial observation."""
    global env_thread, current_task_id, current_obs, current_info, step_count
    
    step_count = 0
    current_task_id = random.choice(VALID_AB_TASK_IDS)
    #current_rask_id = max(VALID_AB_TASK_IDS)
    
    if env_thread is None or not env_thread.is_alive():
        env_thread = threading.Thread(target=_env_worker, daemon=True)
        env_thread.start()

    env_queue.put(("reset", current_task_id))

    def _wait_result():
        status, data = result_queue.get(timeout=60)
        if status == "error":
            raise Exception(data)
        return data

    try:
        result = await asyncio.to_thread(_wait_result)
        current_obs = result["obs"]
        current_info = result["info"]
        agent_obs = _get_observation_for_agent(current_obs)
        return json.dumps(agent_obs, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to reset environment: {e}"})

@ab.tool
async def execute_browser_action(action: str) -> str:
    """Executes a single browser action and returns the new state and result."""
    global current_obs, current_info, step_count

    if step_count >= MAX_STEPS:
        return json.dumps({
            "error": "Maximum step limit reached.",
            "reward": 0.0,
            "terminated": True
        })
    step_count += 1

    env_queue.put(("step", action))

    def _wait_result():
        status, data = result_queue.get(timeout=30)
        if status == "error":
            raise Exception(data)
        return data

    try:
        result = await asyncio.to_thread(_wait_result)
        current_obs = result["obs"]
        current_info = result["info"]
        
        terminated = result["terminated"] or result["truncated"]

        final_reward = result["reward"]
        
        # reCAPTCHA Detection Logic 
        agent_observation = _get_observation_for_agent(current_obs)
        axtree_lower = agent_observation.get("axtree", "").lower()
        recaptcha_keywords = ["recaptcha", "i'm not a robot", "verify you are human"]
        
        if any(keyword in axtree_lower for keyword in recaptcha_keywords):
            final_reward = 0.0
            return json.dumps({
                "new_observation": agent_observation,
                "error": "reCAPTCHA detected. Terminating task as it is unsolvable.",
                "reward": final_reward,
                "terminated": True,
                "step": step_count
            })
        # End of reCAPTCHA Logic
        
        response_payload = {
            "new_observation": _get_observation_for_agent(current_obs),
            "reward": result["reward"],
            "terminated": terminated,
            "step": step_count
        }
        return json.dumps(response_payload, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to execute action: {e}",
            "reward": 0.0,
            "terminated": True
        })


@ab.tool
async def evaluate_task_completion() -> str:
    """
    Call this after the task is terminated. Returns a final JSON report
    summarizing the task performance.
    """
    global current_task_id, step_count, final_reward, gold_answer, current_obs

    provided_answer = "N/A (not submitted)"
    if current_obs and current_obs.get("chat_messages"):
        for msg in reversed(current_obs["chat_messages"]):
            if msg["role"] == "assistant":
                provided_answer = msg["message"]
                break

    evaluation = {
        "task_id": current_task_id,
        "total_steps": step_count,
        "final_reward": final_reward,
        "success": final_reward > 0.5,
        "expected_answer": gold_answer,
        "provided_answer": provided_answer,
    }

    return json.dumps(evaluation, ensure_ascii=False, indent=2, default=str)

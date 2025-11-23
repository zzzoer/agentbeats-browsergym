
# -*- coding: utf-8 -*-
"""
WebLINX Green Agent Toolset 
Fixed version with correct field names for WebLINX dataset
"""

import agentbeats as ab
from datasets import load_dataset
import json

# Global variables to store current task state
weblinx_dataset = None
current_task = None
current_task_id = None
task_history = []


@ab.tool
async def reset_weblinx_env(split: str = "validation") -> str:
    """
    Reset WebLINX environment and load dataset
    
    Args:
        split: Dataset split to use ("validation" or "test_iid")
    
    Returns:
        Success message with dataset info
    """
    global weblinx_dataset, current_task, current_task_id, task_history
    
    try:
        # Load WebLINX dataset from HuggingFace
        # 注意大小写: WebLINX (不是 weblinx)
        print(f"Loading WebLINX {split} dataset...")
        weblinx_dataset = load_dataset("McGill-NLP/WebLINX", split=split)
        
        # Reset state
        current_task = None
        current_task_id = None
        task_history = []
        
        return json.dumps({
            "success": True,
            "message": f"✅ WebLINX environment reset successfully",
            "split": split,
            "total_tasks": len(weblinx_dataset),
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": f"❌ Failed to reset WebLINX environment"
        }, indent=2)


@ab.tool
async def get_weblinx_task(task_id: int = 0) -> str:
    """
    Get a WebLINX task description
    
    Args:
        task_id: Index of the task in the dataset (default: 0)
    
    Returns:
        JSON string containing task information
    """
    global weblinx_dataset, current_task, current_task_id
    
    if weblinx_dataset is None:
        return json.dumps({
            "error": "Environment not initialized. Please call reset_weblinx_env first."
        })
    
    try:
        # Get task from dataset
        sample = weblinx_dataset[task_id]
        current_task_id = task_id
        
        # Extract key information using CORRECT field names from WebLINX dataset:
        # - demo (not demo_name)
        # - turn (not turn_index)
        # - action (target action)
        # - action_history (previous actions)
        # - utterances (conversation)
        # - candidates (UI elements)
        # - clean_html (page HTML)
        # - viewport (screen size)
        
        current_task = {
            "task_id": task_id,
            "demo": sample.get("demo", ""),                      # ✅ 演示ID
            "turn": sample.get("turn", 0),                       # ✅ 回合号
            "expected_action": sample.get("action", ""),         # ✅ 目标动作
            "action_history": sample.get("action_history", ""),  # ✅ 历史动作
            "utterances": sample.get("utterances", ""),          # ✅ 对话内容
            "candidates": sample.get("candidates", ""),          # ✅ 候选元素
            "clean_html": sample.get("clean_html", ""),          # ✅ HTML内容
            "viewport": sample.get("viewport", ""),              # ✅ 视口大小
        }
        
        # Create task description for White Agent
        # 注意: 不包含 expected_action (这是要让 White Agent 预测的目标)
        task_description = {
            "task_id": task_id,
            "demo": current_task["demo"],
            "turn": current_task["turn"],
            "utterances": current_task["utterances"],
            "action_history": current_task["action_history"],
            "candidates": current_task["candidates"],
            "viewport": current_task["viewport"],
        }
        
        return json.dumps(task_description, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "message": "Failed to get task"
        })


@ab.tool
async def evaluate_white_agent_action(agent_action: str) -> str:
    """
    Evaluate White Agent's action against expected action
    
    Args:
        agent_action: The action string returned by White Agent
    
    Returns:
        JSON string with evaluation results
    """
    global current_task, task_history
    
    if current_task is None:
        return json.dumps({
            "error": "No active task. Please call get_weblinx_task first."
        })
    
    try:
        expected_action = current_task["expected_action"]
        
        # Normalize actions for comparison
        agent_action_norm = agent_action.strip().lower()
        expected_action_norm = expected_action.strip().lower()
        
        # Exact match check
        exact_match = (agent_action_norm == expected_action_norm)
        
        # Extract action type (e.g., "click", "say", "load")
        agent_action_type = agent_action_norm.split("(")[0] if "(" in agent_action_norm else agent_action_norm
        expected_action_type = expected_action_norm.split("(")[0] if "(" in expected_action_norm else expected_action_norm
        
        # Calculate score
        if exact_match:
            score = 1.0
            success = True
        elif agent_action_type == expected_action_type:
            # Same action type but different parameters
            score = 0.5
            success = False
        else:
            # Completely different action
            score = 0.0
            success = False
        
        # Store result in history
        result = {
            "task_id": current_task["task_id"],
            "demo": current_task["demo"],
            "turn": current_task["turn"],
            "utterances": current_task["utterances"],
            "expected_action": expected_action,
            "agent_action": agent_action,
            "success": success,
            "score": score,
            "exact_match": exact_match,
        }
        task_history.append(result)
        
        return json.dumps({
            "success": True,
            "evaluation": result,
            "message": "✅ Evaluation completed" if success else "❌ Action incorrect"
        }, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "message": "Failed to evaluate action"
        })


@ab.tool
async def get_weblinx_statistics() -> str:
    """
    Get statistics from all evaluated tasks
    
    Returns:
        JSON string with statistics
    """
    global task_history
    
    if not task_history:
        return json.dumps({
            "message": "No tasks evaluated yet",
            "total_tasks": 0,
            "success_rate": 0.0
        })
    
    total_tasks = len(task_history)
    successful_tasks = sum(1 for t in task_history if t["success"])
    exact_matches = sum(1 for t in task_history if t["exact_match"])
    success_rate = successful_tasks / total_tasks
    exact_match_rate = exact_matches / total_tasks
    average_score = sum(t["score"] for t in task_history) / total_tasks
    
    stats = {
        "total_tasks": total_tasks,
        "successful_tasks": successful_tasks,
        "exact_matches": exact_matches,
        "failed_tasks": total_tasks - successful_tasks,
        "success_rate": round(success_rate, 3),
        "exact_match_rate": round(exact_match_rate, 3),
        "average_score": round(average_score, 3),
        "task_details": task_history  # 包含所有任务的详细结果
    }
    
    return json.dumps(stats, ensure_ascii=False, indent=2)
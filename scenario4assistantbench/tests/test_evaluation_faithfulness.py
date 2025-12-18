import pytest
import json

# The only function we need to import is the official scorer from BrowserGym.
try:
    from browsergym.assistantbench.evaluation.evaluator import question_scorer
except ImportError:
    pytest.skip("Skipping faithfulness tests: `browsergym[assistantbench]` is not installed.", allow_module_level=True)

# ============================================================================
# Test Cases for Evaluation Logic Faithfulness
# ============================================================================

# --- Test Case 1: Simple String and Number Matching ---

def test_exact_string_match():
    """Validates that a perfect string match receives a score of 1.0."""
    gold_answer = "RWTH Aachen"
    agent_answer = "RWTH Aachen"
    score, _ = question_scorer(agent_answer, gold_answer)
    assert score == 1.0

def test_string_normalization():
    """Validates that the scorer ignores case, punctuation, and articles."""
    gold_answer = "The Green Climbers Home"
    agent_answer = "green climbers home."
    score, _ = question_scorer(agent_answer, gold_answer)
    assert score == 1.0

def test_exact_number_match():
    """Validates that a perfect number match receives a score of 1.0."""
    gold_answer = "1991"
    agent_answer = "1991"
    score, _ = question_scorer(agent_answer, gold_answer)
    assert score == 1.0

def test_number_normalization():
    """Validates that the scorer handles currency symbols and commas."""
    gold_answer = "110$"
    agent_answer = "110"
    score, _ = question_scorer(agent_answer, gold_answer)
    assert score == 1.0

# --- Test Case 2: Partial Match Scoring (F1 Score) ---

def test_partial_string_match_f1():
    """
    Validates the F1 score for a partial string match.
    Gold: "Dean Potter"
    Agent: "Dean"
    Precision = 1/1 = 1.0; Recall = 1/2 = 0.5
    F1 = 2 * (1.0 * 0.5) / (1.0 + 0.5) = 1 / 1.5 = 0.666...
    """
    gold_answer = "Dean Potter"
    agent_answer = "Dean"
    score, _ = question_scorer(agent_answer, gold_answer)
    assert pytest.approx(score) == 0.6666666666666666

# --- Test Case 3: Numerical Closeness (Order of Magnitude Metric) ---

def test_numerical_close_match():
    """
    Validates the order of magnitude metric for a close numerical answer.
    Metric is based on natural log: 1 - ln(max/min)
    Calculation: 1 - ln(45 / 38) = 1 - 0.169... = 0.8309...
    """
    gold_answer = "38"
    agent_answer = "45"
    score, _ = question_scorer(agent_answer, gold_answer)
    assert pytest.approx(score) == 0.830923669956066

def test_numerical_far_match():
    """
    Validates that a numerically distant answer receives a low score.
    The original code uses log (natural log), not log10.
    Calculation: 1 - ln(500 / 38) = 1 - 2.57... = -1.57, so score is max(0, -1.57) = 0.
    """
    gold_answer = "38"
    agent_answer = "500"
    score, _ = question_scorer(agent_answer, gold_answer)
    assert score == 0.0

# --- Test Case 4: Complex Types (JSON/List) ---

def test_json_list_exact_match():
    """Validates that a correct list of strings in a different order gets a perfect score."""
    gold_answer = ["Mercury", "Venus", "Earth"] # Gold answer is a Python list
    agent_answer = ["Earth", "Mercury", "Venus"]
    score, _ = question_scorer(agent_answer, gold_answer)
    assert score == 1.0

def test_json_list_partial_match():
    """
    Validates partial credit for a list with a missing item.
    The scorer should match the two correct items, resulting in an average score.
    (1.0 for Mercury + 1.0 for Venus) / 3 total items in gold = 0.666...
    """
    gold_answer = ["Mercury", "Venus", "Earth"] # Gold answer is a Python list
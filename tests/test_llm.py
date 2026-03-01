"""
Unit tests for src/llm/llm_agent.py.

Tests cover:
- Prompt handling (empty / whitespace / None -> None)
- Stub mode (no backend -> None)
- Custom backend injection
- Backend exception -> None (defensive)
- System prompt loading from docs/system_prompt.md
- Prompt builders: build_decision_prompt, build_risk_check_prompt
"""

from __future__ import annotations

import pytest

from src.llm.llm_agent import LLMAgent
from src.types import Decision

# ---------------------------------------------------------------------------
# Shared fixture: minimal valid Decision
# ---------------------------------------------------------------------------

_DECISION_DICT = {
    "ticker": "TEST",
    "as_of": "2025-08-11",
    "recommendation": "BUY",
    "target_price_12m": 120.0,
    "expected_total_return_pct": 15.0,
    "risk_rating": "Medium",
    "thesis": ["Strong growth momentum"],
    "key_risks": ["Competition from incumbents"],
    "valuation": {"blended": 120.0},
    "scenarios": {
        "bull": {"prob": 0.25, "fair_value": 150.0},
        "base": {"prob": 0.50, "fair_value": 120.0},
        "bear": {"prob": 0.25, "fair_value": 90.0},
    },
    "technicals": {
        "trend": "Up",
        "ma_cross": "50>200",
        "rsi_14": 65.0,
        "levels": {},
    },
    "sentiment": {"analyst_consensus": "Buy"},
}


def _decision() -> Decision:
    return Decision.validate_or_raise(_DECISION_DICT)


# ---------------------------------------------------------------------------
# Legacy stub test (must still pass)
# ---------------------------------------------------------------------------


def test_llm_agent():
    agent = LLMAgent()
    assert agent.interact("") is None


# ---------------------------------------------------------------------------
# interact() -- prompt handling
# ---------------------------------------------------------------------------


def test_interact_empty_string_returns_none():
    assert LLMAgent().interact("") is None


def test_interact_whitespace_returns_none():
    assert LLMAgent().interact("   \n\t  ") is None


def test_interact_none_returns_none():
    assert LLMAgent().interact(None) is None


def test_interact_no_backend_returns_none():
    assert LLMAgent().interact("Analyse AAPL") is None


# ---------------------------------------------------------------------------
# interact() -- custom backend
# ---------------------------------------------------------------------------


def test_interact_custom_backend_called():
    called = []
    agent = LLMAgent(backend=lambda p: called.append(p) or "ok")
    result = agent.interact("hello")
    assert result == "ok"
    assert called == ["hello"]


def test_interact_backend_receives_prompt_unchanged():
    received = []
    agent = LLMAgent(backend=lambda p: received.append(p) or "")
    agent.interact("specific prompt text")
    assert received[0] == "specific prompt text"


def test_interact_backend_exception_returns_none():
    def bad(_):
        raise RuntimeError("API down")

    agent = LLMAgent(backend=bad)
    assert agent.interact("some prompt") is None


def test_interact_backend_returns_its_string():
    agent = LLMAgent(backend=lambda _: "LLM response here")
    assert agent.interact("prompt") == "LLM response here"


# ---------------------------------------------------------------------------
# system_prompt
# ---------------------------------------------------------------------------


def test_system_prompt_is_string():
    assert isinstance(LLMAgent().system_prompt, str)


def test_system_prompt_not_empty():
    assert len(LLMAgent().system_prompt.strip()) > 0


def test_custom_system_prompt_accepted():
    agent = LLMAgent(system_prompt="My custom prompt")
    assert agent.system_prompt == "My custom prompt"


def test_system_prompt_contains_pipeline_context():
    """The default prompt should reference the analysis pipeline."""
    prompt = LLMAgent().system_prompt.lower()
    assert any(kw in prompt for kw in ("analysis", "pipeline", "equity"))


# ---------------------------------------------------------------------------
# build_decision_prompt
# ---------------------------------------------------------------------------


def test_build_decision_prompt_returns_str():
    result = LLMAgent().build_decision_prompt(_decision())
    assert isinstance(result, str)


def test_build_decision_prompt_not_empty():
    result = LLMAgent().build_decision_prompt(_decision())
    assert len(result.strip()) > 0


def test_build_decision_prompt_contains_ticker():
    assert "TEST" in LLMAgent().build_decision_prompt(_decision())


def test_build_decision_prompt_contains_recommendation():
    assert "BUY" in LLMAgent().build_decision_prompt(_decision())


def test_build_decision_prompt_contains_thesis():
    result = LLMAgent().build_decision_prompt(_decision())
    assert "Strong growth momentum" in result


def test_build_decision_prompt_contains_key_risks():
    result = LLMAgent().build_decision_prompt(_decision())
    assert "Competition" in result


def test_build_decision_prompt_contains_target_price():
    result = LLMAgent().build_decision_prompt(_decision())
    assert "120" in result


# ---------------------------------------------------------------------------
# build_risk_check_prompt
# ---------------------------------------------------------------------------


def test_build_risk_check_prompt_returns_str():
    result = LLMAgent().build_risk_check_prompt(_decision())
    assert isinstance(result, str)


def test_build_risk_check_prompt_not_empty():
    result = LLMAgent().build_risk_check_prompt(_decision())
    assert len(result.strip()) > 0


def test_build_risk_check_prompt_contains_ticker():
    assert "TEST" in LLMAgent().build_risk_check_prompt(_decision())


def test_build_risk_check_prompt_contains_risk_context():
    """Should include the key_risks from the decision."""
    result = LLMAgent().build_risk_check_prompt(_decision())
    assert "Competition" in result

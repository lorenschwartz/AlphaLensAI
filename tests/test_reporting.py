"""
Unit tests for src/reporting/reporter.py.
"""

from __future__ import annotations

import pytest

from src.reporting.reporter import Reporter
from src.types import Decision

# ---------------------------------------------------------------------------
# Shared fixture
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
    "valuation": {
        "blended": 120.0,
        "dcf_fair_value": 115.0,
        "multiples_fair_value": 125.0,
        "wacc": 0.09,
    },
    "scenarios": {
        "bull": {"prob": 0.25, "fair_value": 150.0},
        "base": {"prob": 0.50, "fair_value": 120.0},
        "bear": {"prob": 0.25, "fair_value": 90.0},
    },
    "technicals": {
        "trend": "Up",
        "ma_cross": "50>200",
        "rsi_14": 65.0,
        "levels": {"support": [100.0], "resistance": [130.0]},
    },
    "sentiment": {"analyst_consensus": "Buy", "avg_target": 128.0},
    "assumptions": {"rev_cagr_3y": 0.12},
    "monitoring": [
        {"metric": "Revenue", "threshold": "< $10B", "action": "Downgrade to HOLD"}
    ],
}


def _decision() -> Decision:
    return Decision.validate_or_raise(_DECISION_DICT)


# ---------------------------------------------------------------------------
# Legacy stub test (must still pass)
# ---------------------------------------------------------------------------


def test_reporter():
    reporter = Reporter()
    assert reporter.report(None) is None


# ---------------------------------------------------------------------------
# report(None / falsy)
# ---------------------------------------------------------------------------


def test_report_none_returns_none():
    assert Reporter().report(None) is None


# ---------------------------------------------------------------------------
# report(Decision) -- happy path
# ---------------------------------------------------------------------------


def test_report_decision_returns_str():
    result = Reporter().report(_decision())
    assert isinstance(result, str)


def test_report_returns_html_document():
    result = Reporter().report(_decision())
    assert "<html" in result.lower()


def test_report_contains_ticker():
    assert "TEST" in Reporter().report(_decision())


def test_report_contains_recommendation():
    assert "BUY" in Reporter().report(_decision())


def test_report_contains_target_price():
    result = Reporter().report(_decision())
    assert "120" in result


def test_report_contains_risk_rating():
    assert "Medium" in Reporter().report(_decision())


def test_report_contains_thesis_bullet():
    assert "Strong growth momentum" in Reporter().report(_decision())


def test_report_contains_key_risk():
    assert "Competition" in Reporter().report(_decision())


def test_report_contains_scenarios():
    result = Reporter().report(_decision())
    assert "bull" in result.lower() or "Bull" in result


def test_report_contains_valuation_blended():
    result = Reporter().report(_decision())
    assert "120" in result


def test_report_contains_technicals():
    result = Reporter().report(_decision())
    assert "Up" in result or "65" in result


def test_report_contains_sentiment():
    result = Reporter().report(_decision())
    assert "Buy" in result


def test_report_contains_monitoring_rule():
    result = Reporter().report(_decision())
    assert "Revenue" in result


def test_report_contains_assumptions():
    result = Reporter().report(_decision())
    assert "rev_cagr_3y" in result


# ---------------------------------------------------------------------------
# report(dict) -- accepts raw dict
# ---------------------------------------------------------------------------


def test_report_accepts_dict():
    result = Reporter().report(_DECISION_DICT)
    assert isinstance(result, str)
    assert "TEST" in result


def test_report_dict_and_model_produce_same_ticker():
    r1 = Reporter().report(_DECISION_DICT)
    r2 = Reporter().report(_decision())
    assert "TEST" in r1 and "TEST" in r2


# ---------------------------------------------------------------------------
# report(invalid type) -- defensive
# ---------------------------------------------------------------------------


def test_report_invalid_type_returns_none():
    assert Reporter().report(["not", "a", "decision"]) is None


def test_report_empty_dict_returns_none():
    assert Reporter().report({}) is None


# ---------------------------------------------------------------------------
# report is deterministic
# ---------------------------------------------------------------------------


def test_report_deterministic():
    r1 = Reporter().report(_decision())
    r2 = Reporter().report(_decision())
    assert r1 == r2

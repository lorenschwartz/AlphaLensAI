"""
Unit tests for the Orchestrator module.

Input contract for Orchestrator.run(input_data):
  Required top-level keys (Decision scalars):
    ticker, as_of, recommendation, target_price_12m,
    expected_total_return_pct, risk_rating, thesis, key_risks,
    valuation (dict with at least 'blended'), scenarios (bull/base/bear dicts)
  Optional engine-input sections:
    technicals, fundamentals, macro, sentiment
  Optional pass-through Decision keys:
    catalysts_next_6_12m, citations, assumptions, monitoring, artifacts
"""

import math

import pytest
from src.orchestrator.orchestrator import Orchestrator
from src.types import Decision, Technicals


def _minimal_input():
    """Minimal valid input dict; every required Decision field is present."""
    return {
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
        "technicals": {"trend": "Up", "ma_cross": "50>200", "rsi_14": 60.0},
        "sentiment": {"analyst_consensus": "Buy"},
    }


# ---------------------------------------------------------------------------
# Falsy / null input
# ---------------------------------------------------------------------------


def test_orchestrator_run():
    """None input returns None (unchanged from stub contract)."""
    assert Orchestrator().run(None) is None


def test_orchestrator_run_empty_dict():
    """Empty dict is falsy → returns None."""
    assert Orchestrator().run({}) is None


# ---------------------------------------------------------------------------
# Happy path — Decision construction
# ---------------------------------------------------------------------------


def test_orchestrator_run_returns_decision():
    """Minimal valid input produces a Decision instance."""
    out = Orchestrator().run(_minimal_input())
    assert isinstance(out, Decision)


def test_orchestrator_run_fields_preserved():
    """Scalar Decision fields are passed through verbatim."""
    out = Orchestrator().run(_minimal_input())
    assert out.ticker == "TEST"
    assert out.as_of == "2025-08-11"
    assert out.recommendation == "BUY"
    assert out.target_price_12m == 120.0
    assert out.expected_total_return_pct == 15.0
    assert out.risk_rating == "Medium"


def test_orchestrator_run_short_summary():
    """short_summary() contains ticker and recommendation."""
    out = Orchestrator().run(_minimal_input())
    summary = out.short_summary()
    assert "TEST" in summary
    assert "BUY" in summary


def test_orchestrator_run_thesis_and_risks_preserved():
    """thesis and key_risks lists are preserved."""
    out = Orchestrator().run(_minimal_input())
    assert out.thesis == ["Strong growth momentum"]
    assert out.key_risks == ["Competition from incumbents"]


def test_orchestrator_run_scenarios_built():
    """Bull/base/bear scenario objects are constructed from input dicts."""
    out = Orchestrator().run(_minimal_input())
    assert set(out.scenarios.keys()) == {"bull", "base", "bear"}
    assert math.isclose(out.scenarios["base"].fair_value, 120.0)
    total_prob = sum(s.prob for s in out.scenarios.values())
    assert math.isclose(total_prob, 1.0, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# TechnicalsEngine wiring
# ---------------------------------------------------------------------------


def test_orchestrator_run_technicals_from_precomputed():
    """Pre-computed technicals dict is forwarded through TechnicalsEngine."""
    out = Orchestrator().run(_minimal_input())
    assert isinstance(out.technicals, Technicals)
    assert out.technicals.trend == "Up"
    assert out.technicals.rsi_14 == 60.0


def test_orchestrator_run_technicals_from_prices():
    """Raw price series → TechnicalsEngine computes RSI=100, trend=Up."""
    data = _minimal_input()
    data["technicals"] = {"prices": [100.0 + i * 0.5 for i in range(220)]}
    out = Orchestrator().run(data)
    assert out.technicals.rsi_14 == 100.0
    assert out.technicals.trend == "Up"
    assert out.technicals.ma_cross == "50>200"


def test_orchestrator_run_technicals_default_when_absent():
    """No 'technicals' key → safe neutral Technicals defaults used."""
    data = _minimal_input()
    del data["technicals"]
    out = Orchestrator().run(data)
    assert isinstance(out.technicals, Technicals)
    assert out.technicals.rsi_14 == 50.0
    assert out.technicals.trend == "Sideways"
    assert out.technicals.ma_cross == "none"


# ---------------------------------------------------------------------------
# Sentiment wiring (SentimentEngine is still a stub → raw dict fallback)
# ---------------------------------------------------------------------------


def test_orchestrator_run_sentiment_from_dict():
    """Sentiment is built from the raw 'sentiment' sub-dict."""
    out = Orchestrator().run(_minimal_input())
    assert out.sentiment.analyst_consensus == "Buy"


def test_orchestrator_run_sentiment_optional_field():
    """Optional sentiment fields are preserved when provided."""
    data = _minimal_input()
    data["sentiment"] = {
        "analyst_consensus": "Hold",
        "avg_target": 115.0,
        "short_interest_pct_float": 4.5,
    }
    out = Orchestrator().run(data)
    assert out.sentiment.analyst_consensus == "Hold"
    assert out.sentiment.avg_target == 115.0


def test_orchestrator_run_sentiment_default_when_absent():
    """Missing 'sentiment' key → neutral Hold consensus default."""
    data = _minimal_input()
    del data["sentiment"]
    out = Orchestrator().run(data)
    assert out.sentiment.analyst_consensus == "Hold"


# ---------------------------------------------------------------------------
# FundamentalsEngine → assumptions injection
# ---------------------------------------------------------------------------


def test_orchestrator_run_fundamentals_injected_into_assumptions():
    """FundamentalsEngine results are injected into Decision.assumptions."""
    data = _minimal_input()
    data["fundamentals"] = {
        "revenue_history": [100.0, 110.0, 121.0, 133.1],
        "fcf_history": [100.0, 100.0, 100.0],
    }
    out = Orchestrator().run(data)
    assert "rev_cagr_3y" in out.assumptions
    assert math.isclose(out.assumptions["rev_cagr_3y"], 0.1, rel_tol=1e-6)
    assert "fcf_stability_score" in out.assumptions
    assert math.isclose(out.assumptions["fcf_stability_score"], 1.0, rel_tol=1e-6)


def test_orchestrator_run_caller_assumptions_not_overwritten():
    """Caller-supplied assumption values are not overwritten by engine output."""
    data = _minimal_input()
    data["assumptions"] = {"rev_cagr_3y": 0.99}
    data["fundamentals"] = {"revenue_history": [100.0, 110.0, 121.0, 133.1]}
    out = Orchestrator().run(data)
    # Engine computes 0.1 but caller supplied 0.99 — must be preserved
    assert math.isclose(out.assumptions["rev_cagr_3y"], 0.99)


# ---------------------------------------------------------------------------
# MacroEngine wiring
# ---------------------------------------------------------------------------


def test_orchestrator_run_macro_accepted():
    """Macro sub-dict is accepted without raising."""
    data = _minimal_input()
    data["macro"] = {
        "rate_regime": "Stable",
        "inflation_trend": "Falling",
        "sector": "Technology",
    }
    out = Orchestrator().run(data)
    assert out is not None
    assert isinstance(out, Decision)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_orchestrator_run_missing_required_field_raises():
    """Omitting a required Decision field (ticker) raises an exception."""
    data = _minimal_input()
    del data["ticker"]
    with pytest.raises(Exception):
        Orchestrator().run(data)

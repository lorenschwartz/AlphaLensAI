"""
Unit tests for src/tools/api_fetcher.py and src/tools/validator.py.

Both follow the standard Red → Green → Refactor TDD cycle.
"""

from __future__ import annotations

import pytest

from src.tools.api_fetcher import APIFetcher
from src.tools.validator import Validator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_decision_dict():
    return {
        "ticker": "TEST",
        "as_of": "2025-08-11",
        "recommendation": "BUY",
        "target_price_12m": 120.0,
        "expected_total_return_pct": 15.0,
        "risk_rating": "Medium",
        "thesis": ["Strong growth"],
        "key_risks": ["Competition"],
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
            "levels": {"support": [100.0], "resistance": [130.0]},
        },
        "sentiment": {"analyst_consensus": "Buy"},
    }


# ---------------------------------------------------------------------------
# APIFetcher
# ---------------------------------------------------------------------------


def test_api_fetcher_unknown_endpoint_raises():
    fetcher = APIFetcher()
    with pytest.raises(ValueError, match="unknown_xyz"):
        fetcher.fetch("unknown_xyz", {})


def test_api_fetcher_empty_string_endpoint_raises():
    fetcher = APIFetcher()
    with pytest.raises(ValueError):
        fetcher.fetch("", {})


def test_api_fetcher_register_and_call():
    fetcher = APIFetcher()
    fetcher.register("my_ep", lambda params: {"echo": params.get("k")})
    result = fetcher.fetch("my_ep", {"k": "hello"})
    assert result == {"echo": "hello"}


def test_api_fetcher_register_overwrites_existing():
    fetcher = APIFetcher()
    fetcher.register("fundamentals", lambda p: {"custom": True})
    result = fetcher.fetch("fundamentals", {})
    assert result == {"custom": True}


def test_api_fetcher_default_fundamentals_returns_dict():
    result = APIFetcher().fetch("fundamentals", {"ticker": "AAPL"})
    assert isinstance(result, dict)


def test_api_fetcher_default_technicals_returns_dict():
    result = APIFetcher().fetch("technicals", {"ticker": "AAPL"})
    assert isinstance(result, dict)


def test_api_fetcher_default_sentiment_returns_dict_with_consensus():
    result = APIFetcher().fetch("sentiment", {"ticker": "AAPL"})
    assert isinstance(result, dict)
    assert "analyst_consensus" in result


def test_api_fetcher_default_macro_returns_dict():
    result = APIFetcher().fetch("macro", {"sector": "Technology"})
    assert isinstance(result, dict)


def test_api_fetcher_none_params_treated_as_empty():
    result = APIFetcher().fetch("fundamentals", None)
    assert isinstance(result, dict)


def test_api_fetcher_deterministic():
    fetcher = APIFetcher()
    r1 = fetcher.fetch("sentiment", {"ticker": "AAPL"})
    r2 = fetcher.fetch("sentiment", {"ticker": "AAPL"})
    assert r1 == r2


def test_api_fetcher_returns_dict_not_none():
    fetcher = APIFetcher()
    for ep in ("fundamentals", "technicals", "sentiment", "macro"):
        assert fetcher.fetch(ep, {}) is not None


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def test_validator_valid_dict_returns_dict():
    v = Validator()
    result = v.validate(_minimal_decision_dict())
    assert isinstance(result, dict)
    assert result["ticker"] == "TEST"
    assert result["recommendation"] == "BUY"


def test_validator_none_input_raises():
    with pytest.raises((ValueError, TypeError)):
        Validator().validate(None)


def test_validator_empty_dict_raises():
    with pytest.raises((ValueError, TypeError)):
        Validator().validate({})


def test_validator_invalid_recommendation_raises():
    data = _minimal_decision_dict()
    data["recommendation"] = "STRONG_BUY"
    with pytest.raises(Exception):
        Validator().validate(data)


def test_validator_missing_ticker_raises():
    data = _minimal_decision_dict()
    del data["ticker"]
    with pytest.raises(Exception):
        Validator().validate(data)


def test_validator_accepts_decision_object():
    from src.types import Decision

    decision = Decision.validate_or_raise(_minimal_decision_dict())
    result = Validator().validate(decision)
    assert isinstance(result, dict)
    assert result["ticker"] == "TEST"


def test_validator_non_dict_non_model_raises_type_error():
    with pytest.raises((TypeError, ValueError)):
        Validator().validate(["not", "a", "dict"])


def test_validator_custom_model_cls():
    from src.types import FundamentalsSummary

    data = {"revenue_cagr_3y": 0.1, "fcf_stability_score": 0.8}
    result = Validator().validate(data, model_cls=FundamentalsSummary)
    assert isinstance(result, dict)
    assert result["revenue_cagr_3y"] == 0.1


def test_validator_preserves_all_fields():
    data = _minimal_decision_dict()
    result = Validator().validate(data)
    assert result["target_price_12m"] == 120.0
    assert result["risk_rating"] == "Medium"
    assert result["thesis"] == ["Strong growth"]

# tests/test_types.py

import math
from src.types import (
    Decision,
    Technicals,
    Sentiment,
    Valuation,
    Scenario,
    Levels,
    Catalyst,
    MonitoringRule,
)

def _dummy_decision_dict():
    return {
        "as_of": "2025-08-11",
        "ticker": "TEST",
        "recommendation": "BUY",
        "target_price_12m": 123.45,
        "expected_total_return_pct": 18.2,
        "horizon_months": 12,
        "risk_rating": "Medium",
        "thesis": [
            "Growing share in core market.",
            "Margin expansion from mix and scale.",
            "Strong balance sheet enables buybacks."
        ],
        "key_risks": [
            "New entrant could compress pricing.",
            "Supply chain disruption risk.",
            "Regulatory scrutiny in key region."
        ],
        "catalysts_next_6_12m": [
            {"event": "Product refresh", "window": "Q4", "impact": "High"},
            {"event": "Cost-out program update", "window": "Q1–Q2", "impact": "Medium"},
        ],
        "valuation": {
            "dcf_fair_value": 118.0,
            "multiples_fair_value": 126.0,
            "blended": 121.5,
            "wacc": 0.093,
            "terminal_g": 0.02,
            "peer_multiples_used": ["EV/EBITDA", "P/E"]
        },
        "scenarios": {
            "bull": {"prob": 0.25, "eps": 6.1, "fair_value": 150.0},
            "base": {"prob": 0.50, "eps": 5.2, "fair_value": 121.0},
            "bear": {"prob": 0.25, "eps": 4.1, "fair_value": 95.0},
        },
        "technicals": {
            "trend": "Up",
            "ma_cross": "50>200",
            "rsi_14": 58.0,
            "levels": {
                "support": [105.0, 98.0],
                "resistance": [118.0, 125.0]
            },
            "ma_20": 112.0,
            "ma_50": 110.0,
            "ma_200": 100.0,
            "macd_line": 1.2,
            "macd_signal": 0.9,
            "atr_14": 2.5
        },
        "sentiment": {
            "analyst_consensus": "Buy",
            "avg_target": 120.4,
            "short_interest_pct_float": 3.1,
            "insider_net_buy_90d": -0.2,
            "news_sentiment_score": 0.12,
            "delta_analyst_upgrades_90d": 2,
            "delta_avg_target_90d": 1.4
        },
        "citations": [
            {"type": "filing", "id": "10Q-2025Q2", "url": "https://example.com/10q", "loc": "MD&A"},
            {"type": "news", "id": "n-001", "url": "https://example.com/news/1"},
            {"type": "api", "id": "prices"}
        ],
        "assumptions": {
            "rev_cagr_3y": 8.5,
            "op_margin_trend": "expanding 80bps/yr",
            "capex_pct_sales": 6.0
        },
        "monitoring": [
            {"metric": "gross margin", "threshold": "< 42% for 2 qtrs", "action": "downgrade to HOLD"}
        ],
        "artifacts": None
    }

def test_decision_model_roundtrip():
    data = _dummy_decision_dict()
    decision = Decision.validate_or_raise(data)
    assert isinstance(decision, Decision)

    # short_summary should produce a concise string with core fields
    summary = decision.short_summary()
    assert isinstance(summary, str)
    assert "TEST" in summary
    assert "BUY" in summary
    assert "123.45" in summary

    # probabilities should sum to ~1.0
    p_sum = sum(d.prob for d in decision.scenarios.values())
    assert math.isclose(p_sum, 1.0, rel_tol=1e-9, abs_tol=1e-9)

def test_technicals_bounds_and_levels():
    # RSI bounds enforced by schema (0..100)
    good = Technicals(
        trend="Sideways",
        ma_cross="none",
        rsi_14=50.0,
        levels=Levels(support=[90.0], resistance=[110.0]),
    )
    assert good.rsi_14 == 50.0
    assert good.levels.support and good.levels.resistance

def test_sentiment_minimal_valid():
    # Minimal valid sentiment object
    sent = Sentiment(analyst_consensus="Hold")
    assert sent.analyst_consensus == "Hold"

def test_valuation_model_basic():
    val = Valuation(
        dcf_fair_value=100.0,
        multiples_fair_value=110.0,
        blended=105.0,
        wacc=0.09,
        terminal_g=0.02,
        peer_multiples_used=["EV/EBITDA"],
    )
    assert val.blended == 105.0

def test_build_decision_from_models():
    # Build via models to ensure type compatibility
    t = Technicals(
        trend="Up",
        ma_cross="50>200",
        rsi_14=55.0,
        levels=Levels(support=[100.0], resistance=[120.0]),
    )
    s = Sentiment(analyst_consensus="Buy", avg_target=125.0)
    v = Valuation(dcf_fair_value=118.0, multiples_fair_value=126.0, blended=122.0)
    bull = Scenario(prob=0.3, eps=6.0, fair_value=150.0)
    base = Scenario(prob=0.5, eps=5.0, fair_value=122.0)
    bear = Scenario(prob=0.2, eps=4.0, fair_value=95.0)

    d = Decision(
        as_of="2025-08-11",
        ticker="TEST",
        recommendation="BUY",
        target_price_12m=124.0,
        expected_total_return_pct=15.0,
        risk_rating="Medium",
        thesis=["Solid topline growth", "Operating leverage coming through"],
        key_risks=["Execution risk", "Competitive pricing"],
        catalysts_next_6_12m=[Catalyst(event="Earnings beat?", window="Q4", impact="High")],
        valuation=v,
        scenarios={"bull": bull, "base": base, "bear": bear},
        technicals=t,
        sentiment=s,
        citations=[],
        assumptions={"rev_cagr_3y": 9.0},
        monitoring=[MonitoringRule(metric="Op margin", threshold="< 15% for 2 qtrs", action="downgrade")],
    )

    assert isinstance(d, Decision)
    assert "→" in d.short_summary()
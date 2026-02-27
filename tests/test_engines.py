"""
Unit tests for Engines modules.
"""

import math

import pytest
from src.engines.fundamentals import FundamentalsEngine
from src.engines.macro import MacroEngine
from src.engines.sentiment import SentimentEngine
from src.engines.technicals import TechnicalsEngine

# ---------------------------------------------------------------------------
# FundamentalsEngine
# ---------------------------------------------------------------------------


def test_fundamentals_engine():
    """None input returns None."""
    engine = FundamentalsEngine()
    assert engine.analyze(None) is None


def test_fundamentals_engine_empty_dict():
    """Empty dict is falsy → returns None."""
    engine = FundamentalsEngine()
    assert engine.analyze({}) is None


def test_fundamentals_engine_revenue_cagr():
    """Revenue CAGR: 100 → 133.1 over 3 years = exactly 10 %."""
    engine = FundamentalsEngine()
    out = engine.analyze({"revenue_history": [100.0, 110.0, 121.0, 133.1]})
    assert out is not None
    assert math.isclose(out.revenue_cagr_3y, 0.1, rel_tol=1e-6)


def test_fundamentals_engine_revenues_alias():
    """'revenues' key is accepted as an alias for 'revenue_history'."""
    engine = FundamentalsEngine()
    out = engine.analyze({"revenues": [100.0, 110.0, 121.0, 133.1]})
    assert out is not None
    assert math.isclose(out.revenue_cagr_3y, 0.1, rel_tol=1e-6)


def test_fundamentals_engine_insufficient_revenue_data():
    """Fewer than 4 revenue points → revenue_cagr_3y is None, no exception."""
    engine = FundamentalsEngine()
    out = engine.analyze({"revenue_history": [100.0, 110.0, 121.0]})
    assert out is not None
    assert out.revenue_cagr_3y is None


def test_fundamentals_engine_op_margin_trend():
    """Op margin +4 pp over 1 year → +400 bps/year."""
    engine = FundamentalsEngine()
    out = engine.analyze({"op_margin_history": [0.10, 0.14]})
    assert out is not None
    assert math.isclose(out.op_margin_trend_bps_per_year, 400.0, rel_tol=1e-6)


def test_fundamentals_engine_op_margin_declining_trend():
    """Declining op margin → negative bps/year value."""
    engine = FundamentalsEngine()
    out = engine.analyze({"op_margin_history": [0.20, 0.18, 0.16]})
    assert out is not None
    assert out.op_margin_trend_bps_per_year is not None
    assert out.op_margin_trend_bps_per_year < 0


def test_fundamentals_engine_op_margins_alias():
    """'op_margins' key is accepted as an alias for 'op_margin_history'."""
    engine = FundamentalsEngine()
    out = engine.analyze({"op_margins": [0.10, 0.14]})
    assert out is not None
    assert math.isclose(out.op_margin_trend_bps_per_year, 400.0, rel_tol=1e-6)


def test_fundamentals_engine_op_margin_insufficient():
    """Single op margin point → trend is None."""
    engine = FundamentalsEngine()
    out = engine.analyze({"op_margin_history": [0.15]})
    assert out is not None
    assert out.op_margin_trend_bps_per_year is None


def test_fundamentals_engine_fcf_stability_stable():
    """Perfectly stable FCF (zero variance) → stability score = 1.0."""
    engine = FundamentalsEngine()
    out = engine.analyze({"fcf_history": [100.0, 100.0, 100.0]})
    assert out is not None
    assert math.isclose(out.fcf_stability_score, 1.0, rel_tol=1e-6)


def test_fundamentals_engine_fcf_stability_volatile():
    """High-variance FCF → stability score in (0, 1)."""
    engine = FundamentalsEngine()
    out = engine.analyze({"fcf_history": [100.0, 0.0]})
    assert out is not None
    assert out.fcf_stability_score is not None
    assert 0.0 < out.fcf_stability_score < 1.0


def test_fundamentals_engine_fcf_stability_clamped():
    """Stability score is always in [0, 1] regardless of input variance."""
    engine = FundamentalsEngine()
    out = engine.analyze({"fcf_history": [1_000_000.0, 1.0]})
    assert out is not None
    assert out.fcf_stability_score is not None
    assert 0.0 <= out.fcf_stability_score <= 1.0


def test_fundamentals_engine_fcfs_alias():
    """'fcfs' key is accepted as an alias for 'fcf_history'."""
    engine = FundamentalsEngine()
    out = engine.analyze({"fcfs": [100.0, 100.0]})
    assert out is not None
    assert math.isclose(out.fcf_stability_score, 1.0, rel_tol=1e-6)


def test_fundamentals_engine_fcf_insufficient():
    """Single FCF value → stability score is None."""
    engine = FundamentalsEngine()
    out = engine.analyze({"fcf_history": [100.0]})
    assert out is not None
    assert out.fcf_stability_score is None


def test_fundamentals_engine_fcf_mean_zero():
    """FCF series whose mean is zero → stability score is None (avoids ZeroDivision)."""
    engine = FundamentalsEngine()
    out = engine.analyze({"fcf_history": [50.0, -50.0]})
    assert out is not None
    assert out.fcf_stability_score is None


def test_fundamentals_engine_all_metrics():
    """All three metrics computed correctly from a combined input dict."""
    engine = FundamentalsEngine()
    out = engine.analyze(
        {
            "revenue_history": [100.0, 110.0, 121.0, 133.1],
            "op_margin_history": [0.10, 0.14],
            "fcf_history": [100.0, 100.0, 100.0],
        }
    )
    assert out is not None
    assert math.isclose(out.revenue_cagr_3y, 0.1, rel_tol=1e-6)
    assert math.isclose(out.op_margin_trend_bps_per_year, 400.0, rel_tol=1e-6)
    assert math.isclose(out.fcf_stability_score, 1.0, rel_tol=1e-6)


def test_fundamentals_engine_returns_fundamentals_summary():
    """Return type is FundamentalsSummary when data is provided."""
    from src.types import FundamentalsSummary

    engine = FundamentalsEngine()
    out = engine.analyze({"revenue_history": [100.0, 110.0, 121.0, 133.1]})
    assert isinstance(out, FundamentalsSummary)


def test_technicals_engine():
    engine = TechnicalsEngine()
    assert engine.analyze(None) is None


def test_technicals_engine_empty_dict():
    engine = TechnicalsEngine()
    assert engine.analyze({}) is None


def test_technicals_engine_precomputed():
    """Pre-computed values are passed through to the model unchanged."""
    engine = TechnicalsEngine()
    data = {
        "trend": "Up",
        "ma_cross": "50>200",
        "rsi_14": 62.5,
        "ma_20": 145.0,
        "ma_50": 140.0,
        "ma_200": 130.0,
        "macd_line": 1.2,
        "macd_signal": 0.9,
        "atr_14": 3.5,
        "support": [130.0, 135.0],
        "resistance": [150.0, 155.0],
    }
    out = engine.analyze(data)
    assert out is not None
    assert out.trend == "Up"
    assert out.ma_cross == "50>200"
    assert out.rsi_14 == 62.5
    assert out.ma_20 == 145.0
    assert out.ma_50 == 140.0
    assert out.ma_200 == 130.0
    assert out.macd_line == 1.2
    assert out.macd_signal == 0.9
    assert out.atr_14 == 3.5
    assert out.levels.support == [130.0, 135.0]
    assert out.levels.resistance == [150.0, 155.0]


def test_technicals_engine_from_prices():
    """Engine derives all indicators from a raw ascending price series."""
    engine = TechnicalsEngine()
    # 220 steadily-ascending closes; all gains → RSI = 100, MA50 > MA200
    prices = [100.0 + i * 0.5 for i in range(220)]
    out = engine.analyze({"prices": prices})
    assert out is not None
    assert out.trend == "Up"  # last price well above MA200
    assert out.ma_cross == "50>200"  # faster MA tracks higher in uptrend
    assert out.rsi_14 == 100.0  # all-gain series → RSI maxed
    assert out.ma_50 is not None
    assert out.ma_200 is not None
    assert out.macd_line is not None
    assert out.macd_line > 0  # EMA12 > EMA26 in sustained uptrend


def test_technicals_engine_too_few_prices():
    """With very few prices optional indicators are None, required use defaults."""
    engine = TechnicalsEngine()
    out = engine.analyze({"prices": [100.0, 101.0, 102.0]})
    assert out is not None
    assert out.rsi_14 == 50.0  # neutral default; RSI needs 15+ prices
    assert out.ma_20 is None  # needs 20 prices
    assert out.ma_50 is None
    assert out.ma_200 is None
    assert out.macd_line is None
    assert out.trend == "Sideways"  # no MA reference → Sideways


def test_technicals_engine_rsi_all_losses():
    """Purely descending series yields RSI = 0."""
    engine = TechnicalsEngine()
    prices = [200.0 - i for i in range(20)]  # 200, 199, …, 181
    out = engine.analyze({"prices": prices})
    assert out is not None
    assert out.rsi_14 == 0.0


def test_technicals_engine_ma_cross_bearish():
    """MA cross is 50<200 when the 50-day MA is below the 200-day MA."""
    engine = TechnicalsEngine()
    out = engine.analyze({"ma_50": 90.0, "ma_200": 110.0})
    assert out is not None
    assert out.ma_cross == "50<200"


def test_technicals_engine_ma_cross_none():
    """MA cross is 'none' when MAs are unavailable."""
    engine = TechnicalsEngine()
    out = engine.analyze({"rsi_14": 55.0})
    assert out is not None
    assert out.ma_cross == "none"


def test_technicals_engine_atr_computed():
    """ATR(14) is computed when highs and lows are supplied."""
    engine = TechnicalsEngine()
    n = 20
    closes = [100.0 + i for i in range(n)]
    highs = [c + 2.0 for c in closes]
    lows = [c - 2.0 for c in closes]
    out = engine.analyze({"prices": closes, "highs": highs, "lows": lows})
    assert out is not None
    assert out.atr_14 is not None
    assert out.atr_14 > 0


def test_technicals_engine_levels_structure():
    """Support and resistance are lists of floats; obvious extremes detected."""
    engine = TechnicalsEngine()
    # Clear dip at index 5, clear peak at index 15 (21 prices, window=5)
    prices = [100.0] * 5 + [90.0] + [100.0] * 9 + [110.0] + [100.0] * 5
    out = engine.analyze({"prices": prices})
    assert out is not None
    assert isinstance(out.levels.support, list)
    assert isinstance(out.levels.resistance, list)
    assert all(isinstance(x, float) for x in out.levels.support)
    assert all(isinstance(x, float) for x in out.levels.resistance)
    assert 90.0 in out.levels.support
    assert 110.0 in out.levels.resistance


def test_sentiment_engine():
    engine = SentimentEngine()
    assert engine.analyze(None) is None


# ---------------------------------------------------------------------------
# SentimentEngine — full coverage
# ---------------------------------------------------------------------------


def test_sentiment_engine_none_returns_none():
    assert SentimentEngine().analyze(None) is None


def test_sentiment_engine_empty_dict_returns_none():
    assert SentimentEngine().analyze({}) is None


def test_sentiment_engine_happy_path():
    engine = SentimentEngine()
    data = {
        "analyst_consensus": "Buy",
        "avg_target": 130.0,
        "short_interest_pct_float": 2.5,
        "news_sentiment_score": 0.6,
    }
    result = engine.analyze(data)
    assert result is not None
    assert result.analyst_consensus == "Buy"
    assert result.avg_target == 130.0
    assert result.short_interest_pct_float == 2.5
    assert result.news_sentiment_score == 0.6


def test_sentiment_engine_returns_sentiment_type():
    from src.types import Sentiment

    result = SentimentEngine().analyze({"analyst_consensus": "Hold"})
    assert isinstance(result, Sentiment)


def test_sentiment_engine_consensus_buy_variants():
    eng = SentimentEngine()
    for raw in ["Buy", "Strong Buy", "Outperform", "Overweight", "strong_buy"]:
        r = eng.analyze({"analyst_consensus": raw})
        assert r is not None and r.analyst_consensus == "Buy", f"Failed for: {raw!r}"


def test_sentiment_engine_consensus_sell_variants():
    eng = SentimentEngine()
    for raw in ["Sell", "Strong Sell", "Underperform", "Underweight"]:
        r = eng.analyze({"analyst_consensus": raw})
        assert r is not None and r.analyst_consensus == "Sell", f"Failed for: {raw!r}"


def test_sentiment_engine_consensus_hold_variants():
    eng = SentimentEngine()
    for raw in ["Hold", "Neutral", "Market Perform", "Equal Weight"]:
        r = eng.analyze({"analyst_consensus": raw})
        assert r is not None and r.analyst_consensus == "Hold", f"Failed for: {raw!r}"


def test_sentiment_engine_unknown_consensus_defaults_to_hold():
    result = SentimentEngine().analyze({"analyst_consensus": "XYZ Rating"})
    assert result is not None
    assert result.analyst_consensus == "Hold"


def test_sentiment_engine_missing_consensus_defaults_to_hold():
    result = SentimentEngine().analyze({"avg_target": 100.0})
    assert result is not None
    assert result.analyst_consensus == "Hold"


def test_sentiment_engine_alias_short_interest_pct():
    """short_interest_pct is accepted as an alias for short_interest_pct_float."""
    result = SentimentEngine().analyze(
        {"analyst_consensus": "Hold", "short_interest_pct": 5.0}
    )
    assert result is not None
    assert result.short_interest_pct_float == 5.0


def test_sentiment_engine_short_interest_clamped_to_zero():
    result = SentimentEngine().analyze(
        {"analyst_consensus": "Hold", "short_interest_pct_float": -3.0}
    )
    assert result is not None
    assert result.short_interest_pct_float >= 0.0


def test_sentiment_engine_news_score_clamped_high():
    result = SentimentEngine().analyze(
        {"analyst_consensus": "Buy", "news_sentiment_score": 9.9}
    )
    assert result is not None
    assert result.news_sentiment_score == 1.0


def test_sentiment_engine_news_score_clamped_low():
    result = SentimentEngine().analyze(
        {"analyst_consensus": "Buy", "news_sentiment_score": -9.9}
    )
    assert result is not None
    assert result.news_sentiment_score == -1.0


def test_sentiment_engine_news_score_in_range_unchanged():
    result = SentimentEngine().analyze(
        {"analyst_consensus": "Hold", "news_sentiment_score": 0.3}
    )
    assert result is not None
    assert math.isclose(result.news_sentiment_score, 0.3, rel_tol=1e-9)


def test_sentiment_engine_invalid_avg_target_yields_none_field():
    result = SentimentEngine().analyze(
        {"analyst_consensus": "Buy", "avg_target": "not-a-number"}
    )
    assert result is not None
    assert result.avg_target is None


def test_sentiment_engine_invalid_news_score_yields_none_field():
    result = SentimentEngine().analyze(
        {"analyst_consensus": "Hold", "news_sentiment_score": "bad"}
    )
    assert result is not None
    assert result.news_sentiment_score is None


def test_sentiment_engine_delta_fields_passed_through():
    result = SentimentEngine().analyze(
        {
            "analyst_consensus": "Buy",
            "delta_analyst_upgrades_90d": 3,
            "delta_avg_target_90d": 5.0,
        }
    )
    assert result is not None
    assert result.delta_analyst_upgrades_90d == 3
    assert result.delta_avg_target_90d == 5.0


def test_sentiment_engine_insider_net_buy():
    result = SentimentEngine().analyze(
        {"analyst_consensus": "Buy", "insider_net_buy_90d": 1_500_000.0}
    )
    assert result is not None
    assert result.insider_net_buy_90d == 1_500_000.0


def test_sentiment_engine_partial_data_no_exception():
    """Only required field available — no exception, optional fields are None."""
    result = SentimentEngine().analyze({"analyst_consensus": "Sell"})
    assert result is not None
    assert result.avg_target is None
    assert result.short_interest_pct_float is None
    assert result.news_sentiment_score is None


# ---------------------------------------------------------------------------
# MacroEngine
# ---------------------------------------------------------------------------


def test_macro_engine():
    """None input returns None."""
    engine = MacroEngine()
    assert engine.analyze(None) is None


def test_macro_engine_empty_dict():
    """Empty dict is falsy → returns None."""
    engine = MacroEngine()
    assert engine.analyze({}) is None


def test_macro_engine_sample_input():
    """Full input → all fields populated correctly."""
    engine = MacroEngine()
    sample = {
        "rate_regime": "Rising",
        "inflation_trend": "Stable",
        "fx_headwind_tailwind": "Neutral",
        "commodity_links": ["Oil", "Copper"],
        "sector": "Materials",
        "notes": "Sample note",
    }
    out = engine.analyze(sample)
    assert out is not None
    assert out.rate_regime == "Rising"
    assert out.inflation_trend == "Stable"
    assert out.fx_headwind_tailwind == "Neutral"
    assert out.commodity_links == ["Oil", "Copper"]
    assert out.sector == "Materials"
    assert out.notes == "Sample note"


def test_macro_engine_partial_input():
    """Only rate_regime provided; unset fields default to None / empty list."""
    engine = MacroEngine()
    out = engine.analyze({"rate_regime": "Falling"})
    assert out is not None
    assert out.rate_regime == "Falling"
    assert out.inflation_trend is None
    assert out.fx_headwind_tailwind is None
    assert out.commodity_links == []
    assert out.sector is None


def test_macro_engine_notes_pass_through():
    """notes string is preserved verbatim in the output model."""
    engine = MacroEngine()
    out = engine.analyze({"notes": "Stagflation risk rising."})
    assert out is not None
    assert out.notes == "Stagflation risk rising."


def test_macro_engine_returns_macro_industry_summary():
    """Return type is MacroIndustrySummary when data is provided."""
    from src.types import MacroIndustrySummary

    engine = MacroEngine()
    out = engine.analyze({"sector": "Energy"})
    assert isinstance(out, MacroIndustrySummary)

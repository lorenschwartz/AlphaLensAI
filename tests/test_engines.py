"""
Unit tests for Engines modules.
"""

import pytest
from src.engines.fundamentals import FundamentalsEngine
from src.engines.technicals import TechnicalsEngine
from src.engines.sentiment import SentimentEngine
from src.engines.macro import MacroEngine


def test_fundamentals_engine():
    engine = FundamentalsEngine()
    assert engine.analyze(None) is None


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


def test_macro_engine():
    engine = MacroEngine()
    assert engine.analyze(None) is None


def test_macro_engine_sample_input():
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

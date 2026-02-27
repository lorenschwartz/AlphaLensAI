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


def test_technicals_engine_sample_input():
    engine = TechnicalsEngine()
    sample = {
        "ma_50": 120.0,
        "ma_200": 100.0,
        "rsi_14": 65.0,
        "support_levels": [95.0, 90.0],
        "resistance_levels": [130.0, 125.0],
        "macd_line": 1.2,
        "macd_signal": 1.0,
        "atr_14": 2.5,
    }
    out = engine.analyze(sample)
    assert out is not None
    assert out.trend == "Up"
    assert out.ma_cross == "50>200"
    assert out.rsi_14 == 65.0
    assert out.levels.support == [90.0, 95.0]
    assert out.levels.resistance == [125.0, 130.0]


def test_technicals_engine_defensive_defaults():
    engine = TechnicalsEngine()
    sample = {
        "ma_50": "bad",
        "ma_200": "worse",
        "rsi_14": "bad",
        "levels": {"support": ["x", 80.0], "resistance": []},
    }
    out = engine.analyze(sample)
    assert out is not None
    assert out.trend == "Sideways"
    assert out.ma_cross == "none"
    assert out.rsi_14 == 50.0
    assert out.levels.support == [80.0]
    assert out.levels.resistance == []

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

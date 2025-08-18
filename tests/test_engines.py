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

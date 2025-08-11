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

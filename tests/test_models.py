"""
Unit tests for Models.
"""
import pytest
from src.models.decision import Decision
from src.models.valuation import Valuation
from src.models.technicals import Technicals
from src.models.sentiment import Sentiment
from src.models.macro import Macro

def test_decision_model():
    model = Decision(result=None)
    assert model.result is None

def test_valuation_model():
    model = Valuation(value=None)
    assert model.value is None

def test_technicals_model():
    model = Technicals(metrics=None)
    assert model.metrics is None

def test_sentiment_model():
    model = Sentiment(score=None)
    assert model.score is None

def test_macro_model():
    model = Macro(indicators=None)
    assert model.indicators is None

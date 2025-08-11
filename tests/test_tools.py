"""
Unit tests for Tools modules.
"""
import pytest
from src.tools.api_fetcher import APIFetcher
from src.tools.validator import Validator

def test_api_fetcher():
    fetcher = APIFetcher()
    assert fetcher.fetch('', {}) is None

def test_validator():
    validator = Validator()
    assert validator.validate(None) is None or validator.validate(None) is False

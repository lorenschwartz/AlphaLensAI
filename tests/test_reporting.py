"""
Unit tests for Reporting module.
"""
import pytest
from src.reporting.reporter import Reporter

def test_reporter():
    reporter = Reporter()
    assert reporter.report(None) is None

"""
Unit tests for LLM module.
"""
import pytest
from src.llm.llm_agent import LLMAgent

def test_llm_agent():
    agent = LLMAgent()
    assert agent.interact('') is None

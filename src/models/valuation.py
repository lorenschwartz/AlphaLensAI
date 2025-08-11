"""
Pydantic model for Valuation output contract.
"""
from pydantic import BaseModel
from typing import Any

class Valuation(BaseModel):
    """Represents a valuation output from the pipeline."""
    value: Any

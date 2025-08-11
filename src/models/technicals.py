"""
Pydantic model for Technicals output contract.
"""
from pydantic import BaseModel
from typing import Any

class Technicals(BaseModel):
    """Represents technicals output from the pipeline."""
    metrics: Any

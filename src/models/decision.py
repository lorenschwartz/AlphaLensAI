"""
Pydantic model for Decision output contract.
"""
from pydantic import BaseModel
from typing import Any

class Decision(BaseModel):
    """Represents a decision output from the pipeline."""
    result: Any

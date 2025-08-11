"""
Pydantic model for Macro output contract.
"""
from pydantic import BaseModel
from typing import Any

class Macro(BaseModel):
    """Represents macroeconomic output from the pipeline."""
    indicators: Any

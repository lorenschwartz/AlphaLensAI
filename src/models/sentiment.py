"""
Pydantic model for Sentiment output contract.
"""
from pydantic import BaseModel
from typing import Any

class Sentiment(BaseModel):
    """Represents sentiment output from the pipeline."""
    score: Any

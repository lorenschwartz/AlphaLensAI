"""
src/api/schemas.py

Pydantic request/response schemas for the AlphaLensAI REST API.

These are intentionally kept separate from src/types.py so the API contract
can remain stable even if internal types evolve.  Field names and literals
are kept consistent with src/types.py.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Nested input models
# ---------------------------------------------------------------------------


class ValuationInput(BaseModel):
    """Valuation sub-object within an AnalyzeRequest."""

    dcf_fair_value: Optional[float] = None
    multiples_fair_value: Optional[float] = None
    blended: float
    wacc: Optional[float] = Field(default=None, ge=0)
    terminal_g: Optional[float] = None
    peer_multiples_used: List[str] = Field(default_factory=list)


class ScenarioInput(BaseModel):
    """Bull / base / bear scenario within an AnalyzeRequest."""

    prob: float = Field(..., ge=0, le=1)
    eps: Optional[float] = None
    fair_value: float


# ---------------------------------------------------------------------------
# Top-level request model
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    """Request body for POST /analyze.

    Required fields mirror the Decision contract.  Optional engine-input
    sections (fundamentals, macro, technicals, sentiment) are passed through
    to the respective engines unchanged.
    """

    # --- Required Decision fields -------------------------------------------
    ticker: str
    as_of: str
    recommendation: Literal["BUY", "HOLD", "SELL"]
    target_price_12m: float
    expected_total_return_pct: float
    risk_rating: Literal["Low", "Medium", "High"]
    thesis: List[str]
    key_risks: List[str]
    valuation: ValuationInput
    scenarios: Dict[str, ScenarioInput]

    # --- Optional engine input sections -------------------------------------
    fundamentals: Optional[Dict[str, Any]] = None
    macro: Optional[Dict[str, Any]] = None
    technicals: Optional[Dict[str, Any]] = None
    sentiment: Optional[Dict[str, Any]] = None

    # --- Optional pass-through Decision fields ------------------------------
    horizon_months: int = 12
    assumptions: Optional[Dict[str, Union[float, str]]] = None
    catalysts_next_6_12m: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[Dict[str, Any]]] = None
    monitoring: Optional[List[Dict[str, Any]]] = None
    artifacts: Optional[Dict[str, Any]] = None

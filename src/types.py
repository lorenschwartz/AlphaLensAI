"""
src/types.py

Central data contracts for EquitySentinel.
These Pydantic models define the shapes exchanged between tools, engines,
the LLM layer, and the final report. Keep this file stable—everything else
should conform to these types.

Compatibility: Works with Pydantic v1 and v2.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union, Any
from pydantic import BaseModel, Field, AnyUrl


# ----- Enums (as Literals for simplicity & Copilot-friendliness) -----

RiskRating = Literal["Low", "Medium", "High"]
Reco = Literal["BUY", "HOLD", "SELL"]
Trend = Literal["Up", "Down", "Sideways"]
MACross = Literal["50>200", "50<200", "none"]
AnalystConsensus = Literal["Buy", "Hold", "Sell"]


# ----- Small building blocks -----

class Levels(BaseModel):
    """Key technical price levels detected by the technicals engine."""
    support: List[float] = Field(default_factory=list, description="Ascending list of support levels.")
    resistance: List[float] = Field(default_factory=list, description="Ascending list of resistance levels.")


class Catalyst(BaseModel):
    """Potential value-moving events in the next 6–12 months."""
    event: str
    window: str = Field(..., description="Time window, e.g., 'Q1–Q2' or a date range.")
    impact: Literal["Low", "Medium", "High"] = "Medium"


class Citation(BaseModel):
    """Traceability for facts & numbers used in the thesis/recommendation."""
    type: Literal["filing", "news", "api"]
    id: str
    url: Optional[AnyUrl] = None
    loc: Optional[str] = Field(default=None, description="Section/locator within the source (e.g., 'MD&A').")


class MonitoringRule(BaseModel):
    """Falsifiable monitor that would change the recommendation if breached."""
    metric: str
    threshold: str
    action: str


# ----- Domain models (section outputs) -----

class Technicals(BaseModel):
    """Summarized technical state of the equity."""
    trend: Trend
    ma_cross: MACross
    rsi_14: float = Field(..., ge=0, le=100)
    levels: Levels
    ma_20: Optional[float] = None
    ma_50: Optional[float] = None
    ma_200: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    atr_14: Optional[float] = None


class Sentiment(BaseModel):
    """Composite of street view, positioning, and media tone."""
    analyst_consensus: AnalystConsensus
    avg_target: Optional[float] = None
    short_interest_pct_float: Optional[float] = Field(default=None, ge=0)
    insider_net_buy_90d: Optional[float] = None
    news_sentiment_score: Optional[float] = Field(
        default=None, description="Normalized sentiment (e.g., -1..+1) if available."
    )
    # Optional deltas vs. prior 90d
    delta_analyst_upgrades_90d: Optional[int] = None
    delta_avg_target_90d: Optional[float] = None


class Scenario(BaseModel):
    """Value & earnings under a particular path with a probability weight."""
    prob: float = Field(..., ge=0, le=1)
    eps: Optional[float] = None
    fair_value: float


class Valuation(BaseModel):
    """Valuation outputs from DCF, multiples, and blended result."""
    dcf_fair_value: Optional[float] = None
    multiples_fair_value: Optional[float] = None
    blended: float
    wacc: Optional[float] = Field(default=None, ge=0)
    terminal_g: Optional[float] = None
    peer_multiples_used: List[str] = Field(default_factory=list)


# ----- Final decision object (top-level contract) -----

class Decision(BaseModel):
    """
    Canonical output the orchestrator must produce and downstream consumers will read.
    This is the contract Copilot should aim to satisfy when implementing logic.
    """
    as_of: str = Field(..., description="ISO date the analysis is based on (e.g., '2025-08-11').")
    ticker: str = Field(..., description="Primary listing symbol, e.g., 'AAPL'.")
    recommendation: Reco
    target_price_12m: float
    expected_total_return_pct: float
    horizon_months: int = 12
    risk_rating: RiskRating

    thesis: List[str] = Field(..., description="Top 2–5 arguments for the call, short bullets.")
    key_risks: List[str] = Field(..., description="Top 2–5 risks that could impair the call.")
    catalysts_next_6_12m: List[Catalyst] = Field(default_factory=list)

    valuation: Valuation
    scenarios: Dict[Literal["bull", "base", "bear"], Scenario]

    technicals: Technicals
    sentiment: Sentiment

    citations: List[Citation] = Field(default_factory=list)

    assumptions: Dict[str, Union[float, str]] = Field(
        default_factory=dict, description="Explicit inputs (rev_cagr_3y, op_margin_trend, capex_pct_sales, etc.)."
    )
    monitoring: List[MonitoringRule] = Field(default_factory=list)

    # Optional passthroughs (for report building / debugging)
    artifacts: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional references to generated charts, sensitivity tables, etc. (e.g., base64 images)."
    )

    # ----- Convenience helpers -----

    @classmethod
    def validate_or_raise(cls, data: Dict[str, Any]) -> "Decision":
        """
        Pydantic v1/v2 compatible validation entrypoint.
        Use this in the LLM compose layer to enforce schema correctness.
        """
        # v2: model_validate; v1: parse_obj
        validate = getattr(cls, "model_validate", None) or getattr(cls, "parse_obj", None)
        if not validate:
            raise RuntimeError("Unsupported Pydantic version: missing model_validate/parse_obj.")
        return validate(data)

    def short_summary(self) -> str:
        """Handy one-liner for logs/CLI."""
        return f"{self.as_of} | {self.ticker} → {self.recommendation} @ {self.target_price_12m:.2f} "\
               f"({self.expected_total_return_pct:.1f}% / {self.horizon_months}m, risk={self.risk_rating})"


# ----- Optional: Thin wrappers for intermediate engine outputs -----

class FundamentalsSummary(BaseModel):
    """
    Snapshot derived from financial statements for downstream valuation.
    Keep this intentionally compact so engines stay decoupled from raw providers.
    """
    revenue_cagr_3y: Optional[float] = None
    gross_margin_trend_bps_per_year: Optional[float] = None
    op_margin_trend_bps_per_year: Optional[float] = None
    fcf_stability_score: Optional[float] = Field(
        default=None, description="0..1 stability proxy (lower variance → higher score)."
    )
    net_debt_to_ebitda: Optional[float] = None
    current_ratio: Optional[float] = None
    roe: Optional[float] = None
    roic: Optional[float] = None
    notes: Optional[str] = None


class MacroIndustrySummary(BaseModel):
    """
    Lightweight macro/industry context to condition valuations and scenarios.
    """
    rate_regime: Optional[Literal["Rising", "Falling", "Stable"]] = None
    inflation_trend: Optional[Literal["Rising", "Falling", "Stable"]] = None
    fx_headwind_tailwind: Optional[Literal["Headwind", "Tailwind", "Neutral"]] = None
    commodity_links: List[str] = Field(default_factory=list, description="Relevant commodity exposures, if any.")
    sector: Optional[str] = None
    notes: Optional[str] = None
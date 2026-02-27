"""
Orchestrator for coordinating the AlphaLensAI pipeline.

Accepts a structured input dict, fans out to each engine, and assembles
the results into a single validated ``Decision`` object.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.engines.fundamentals import FundamentalsEngine
from src.engines.macro import MacroEngine
from src.engines.sentiment import SentimentEngine
from src.engines.technicals import TechnicalsEngine
from src.types import (
    Catalyst,
    Citation,
    Decision,
    Levels,
    MonitoringRule,
    Scenario,
    Sentiment,
    Technicals,
    Valuation,
)


class Orchestrator:
    """Wires all engine outputs into a single ``Decision``.

    Input dict accepted by ``run()`` has two kinds of keys:

    **Engine input sections** (optional sub-dicts forwarded to each engine):

        fundamentals  — keys accepted by ``FundamentalsEngine.analyze()``
        macro         — keys accepted by ``MacroEngine.analyze()``
        technicals    — keys accepted by ``TechnicalsEngine.analyze()``
        sentiment     — keys accepted by ``SentimentEngine.analyze()``

    **Decision fields** (passed through directly):

        ticker, as_of, recommendation, target_price_12m,
        expected_total_return_pct, risk_rating, thesis, key_risks,
        catalysts_next_6_12m, valuation, scenarios, citations,
        assumptions, monitoring, artifacts

    Engine outputs enrich the result where possible:

    - ``TechnicalsEngine`` output is preferred; safe neutral defaults are
      used when no technicals data is provided.
    - ``SentimentEngine`` is still a stub; the raw ``"sentiment"`` dict is
      used as fallback, with a neutral Hold default when absent.
    - ``FundamentalsEngine`` results are injected into ``assumptions``
      (caller-supplied values are *not* overwritten).
    - ``MacroEngine`` runs for validation; its output is discarded for now
      (no dedicated field on ``Decision``).
    """

    def run(self, input_data: Optional[Dict[str, Any]]) -> Optional[Decision]:
        """Run the full pipeline and return a ``Decision``.

        Args:
            input_data: Structured dict (see class docstring).  Must contain
                all required ``Decision`` fields at the top level.

        Returns:
            ``Decision`` on success, ``None`` when ``input_data`` is falsy.

        Raises:
            KeyError: if a required top-level key is absent.
            pydantic.ValidationError: if a field value is invalid.
        """
        if not input_data:
            return None

        # -- Run engines -------------------------------------------------------
        fundamentals = FundamentalsEngine().analyze(input_data.get("fundamentals"))
        MacroEngine().analyze(input_data.get("macro"))

        technicals_raw = input_data.get("technicals") or {}
        technicals: Technicals = TechnicalsEngine().analyze(
            technicals_raw
        ) or Technicals(
            trend="Sideways",
            ma_cross="none",
            rsi_14=50.0,
            levels=Levels(),
        )

        # SentimentEngine is still a stub → fall back to raw dict
        sentiment_result = SentimentEngine().analyze(input_data.get("sentiment"))
        if sentiment_result is not None:
            sentiment: Sentiment = sentiment_result
        else:
            sentiment_dict = input_data.get("sentiment") or {}
            if isinstance(sentiment_dict, dict) and sentiment_dict:
                sentiment = Sentiment(**sentiment_dict)
            else:
                sentiment = Sentiment(analyst_consensus="Hold")

        # -- Build sub-models --------------------------------------------------
        valuation_raw = input_data.get("valuation", {})
        valuation: Valuation = (
            valuation_raw
            if isinstance(valuation_raw, Valuation)
            else Valuation(**valuation_raw)
        )

        scenarios: Dict[str, Scenario] = {
            k: Scenario(**v) if isinstance(v, dict) else v
            for k, v in input_data.get("scenarios", {}).items()
        }

        catalysts: List[Catalyst] = [
            Catalyst(**c) if isinstance(c, dict) else c
            for c in (input_data.get("catalysts_next_6_12m") or [])
        ]

        monitoring: List[MonitoringRule] = [
            MonitoringRule(**m) if isinstance(m, dict) else m
            for m in (input_data.get("monitoring") or [])
        ]

        citations: List[Citation] = [
            Citation(**c) if isinstance(c, dict) else c
            for c in (input_data.get("citations") or [])
        ]

        # -- Enrich assumptions from FundamentalsEngine ------------------------
        # Use `or {}` so an explicit None value is also treated as empty.
        assumptions: Dict[str, Any] = dict(input_data.get("assumptions") or {})
        if fundamentals is not None:
            _inject = {
                "rev_cagr_3y": fundamentals.revenue_cagr_3y,
                "op_margin_trend_bps_per_year": fundamentals.op_margin_trend_bps_per_year,
                "fcf_stability_score": fundamentals.fcf_stability_score,
            }
            for key, value in _inject.items():
                if value is not None:
                    assumptions.setdefault(key, value)

        # -- Assemble and return Decision --------------------------------------
        return Decision(
            as_of=input_data["as_of"],
            ticker=input_data["ticker"],
            recommendation=input_data["recommendation"],
            target_price_12m=float(input_data["target_price_12m"]),
            expected_total_return_pct=float(input_data["expected_total_return_pct"]),
            horizon_months=int(input_data.get("horizon_months", 12)),
            risk_rating=input_data["risk_rating"],
            thesis=list(input_data["thesis"]),
            key_risks=list(input_data["key_risks"]),
            catalysts_next_6_12m=catalysts,
            valuation=valuation,
            scenarios=scenarios,
            technicals=technicals,
            sentiment=sentiment,
            citations=citations,
            assumptions=assumptions,
            monitoring=monitoring,
            artifacts=input_data.get("artifacts"),
        )

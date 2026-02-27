"""
src/engines/sentiment.py

SentimentEngine — deterministic, side-effect-free analyst-sentiment aggregator.

Input dict keys accepted
------------------------
analyst_consensus       str  — raw street consensus label (mapped to Buy/Hold/Sell)
avg_target              float — consensus 12-month price target
short_interest_pct_float float — short interest as % of float (clamped ≥ 0)
short_interest_pct      float — alias for short_interest_pct_float
insider_net_buy_90d     float — net insider $ bought/sold over 90 days
news_sentiment_score    float — normalised news tone; clamped to [−1, +1]
delta_analyst_upgrades_90d int — net upgrades − downgrades over 90 days
delta_avg_target_90d    float — change in consensus target over 90 days

The engine never raises on bad/missing data.  Missing keys → None fields.
Returns None when `data` is falsy.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.types import Sentiment

# ---------------------------------------------------------------------------
# Consensus mapping
# ---------------------------------------------------------------------------

_CONSENSUS_MAP: Dict[str, str] = {
    # Buy-side
    "buy": "Buy",
    "strong buy": "Buy",
    "outperform": "Buy",
    "overweight": "Buy",
    "market outperform": "Buy",
    "sector outperform": "Buy",
    "add": "Buy",
    # Hold-side
    "hold": "Hold",
    "neutral": "Hold",
    "market perform": "Hold",
    "sector perform": "Hold",
    "equal weight": "Hold",
    "in-line": "Hold",
    "peer perform": "Hold",
    "market neutral": "Hold",
    # Sell-side
    "sell": "Sell",
    "strong sell": "Sell",
    "underperform": "Sell",
    "underweight": "Sell",
    "market underperform": "Sell",
    "sector underperform": "Sell",
    "reduce": "Sell",
}


def _map_consensus(raw: Any) -> str:
    """Normalise a raw consensus string to 'Buy' | 'Hold' | 'Sell'."""
    if not isinstance(raw, str) or not raw.strip():
        return "Hold"
    key = raw.replace("_", " ").strip().lower()
    return _CONSENSUS_MAP.get(key, "Hold")


def _safe_float(val: Any) -> Optional[float]:
    """Convert val to float; return None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    """Convert val to int; return None on failure."""
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class SentimentEngine:
    """Converts a raw sentiment dict into a typed Sentiment object.

    The engine is stateless and deterministic — the same input always
    produces the same output with no I/O side-effects.
    """

    def analyze(self, data: Optional[Dict[str, Any]]) -> Optional[Sentiment]:
        """Parse *data* and return a :class:`~src.types.Sentiment` or None.

        Args:
            data: Raw sentiment dict from an API fetcher or orchestrator.
                  Keys are optional; see module docstring for accepted keys.

        Returns:
            A populated :class:`Sentiment` instance, or ``None`` if *data*
            is falsy (``None``, ``{}``, etc.).
        """
        if not data:
            return None

        try:
            analyst_consensus = _map_consensus(data.get("analyst_consensus"))
        except Exception:
            analyst_consensus = "Hold"

        avg_target = _safe_float(data.get("avg_target"))

        # Accept alias key short_interest_pct
        si_raw = data.get("short_interest_pct_float")
        if si_raw is None:
            si_raw = data.get("short_interest_pct")
        si_float = _safe_float(si_raw)
        if si_float is not None:
            si_float = max(0.0, si_float)

        insider_net = _safe_float(data.get("insider_net_buy_90d"))

        # news_sentiment_score clamped to [−1, +1]
        nss = _safe_float(data.get("news_sentiment_score"))
        if nss is not None:
            nss = max(-1.0, min(1.0, nss))

        delta_upgrades = _safe_int(data.get("delta_analyst_upgrades_90d"))
        delta_target = _safe_float(data.get("delta_avg_target_90d"))

        try:
            return Sentiment(
                analyst_consensus=analyst_consensus,
                avg_target=avg_target,
                short_interest_pct_float=si_float,
                insider_net_buy_90d=insider_net,
                news_sentiment_score=nss,
                delta_analyst_upgrades_90d=delta_upgrades,
                delta_avg_target_90d=delta_target,
            )
        except Exception:
            return None

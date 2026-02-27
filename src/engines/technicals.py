"""
Technicals engine for equity analysis.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.types import Levels, Technicals


class TechnicalsEngine:
    """Handles technical analysis logic."""

    def analyze(self, data: Optional[Dict[str, Any]]) -> Optional[Technicals]:
        """Analyze technicals data into the canonical `Technicals` model."""
        if not data:
            return None

        def _to_float_or_none(value: Any) -> Optional[float]:
            try:
                if value is None:
                    return None
                return float(value)
            except Exception:
                return None

        ma_20 = _to_float_or_none(data.get("ma_20"))
        ma_50 = _to_float_or_none(data.get("ma_50"))
        ma_200 = _to_float_or_none(data.get("ma_200"))
        macd_line = _to_float_or_none(data.get("macd_line"))
        macd_signal = _to_float_or_none(data.get("macd_signal"))
        atr_14 = _to_float_or_none(data.get("atr_14"))

        trend = data.get("trend")
        if trend not in {"Up", "Down", "Sideways"}:
            try:
                if ma_50 is not None and ma_200 is not None:
                    if ma_50 > ma_200:
                        trend = "Up"
                    elif ma_50 < ma_200:
                        trend = "Down"
                    else:
                        trend = "Sideways"
                else:
                    trend = "Sideways"
            except Exception:
                trend = "Sideways"

        ma_cross = data.get("ma_cross")
        if ma_cross not in {"50>200", "50<200", "none"}:
            try:
                if ma_50 is not None and ma_200 is not None:
                    if ma_50 > ma_200:
                        ma_cross = "50>200"
                    elif ma_50 < ma_200:
                        ma_cross = "50<200"
                    else:
                        ma_cross = "none"
                else:
                    ma_cross = "none"
            except Exception:
                ma_cross = "none"

        try:
            rsi_14 = float(data.get("rsi_14", 50.0))
            rsi_14 = max(0.0, min(100.0, rsi_14))
        except Exception:
            rsi_14 = 50.0

        # Be tolerant if callers pass a pre-validated Levels model.
        levels_data = data.get("levels") or {}
        if hasattr(levels_data, "model_dump"):
            levels_data = levels_data.model_dump()

        support_src = levels_data.get("support") or data.get("support_levels") or []
        resistance_src = (
            levels_data.get("resistance") or data.get("resistance_levels") or []
        )

        def _to_sorted_levels(raw_levels: Any) -> List[float]:
            parsed: List[float] = []
            for level in raw_levels or []:
                try:
                    parsed.append(float(level))
                except Exception:
                    continue
            return sorted(parsed)

        levels = Levels(
            support=_to_sorted_levels(support_src),
            resistance=_to_sorted_levels(resistance_src),
        )

        return Technicals(
            trend=trend,
            ma_cross=ma_cross,
            rsi_14=rsi_14,
            levels=levels,
            ma_20=ma_20,
            ma_50=ma_50,
            ma_200=ma_200,
            macd_line=macd_line,
            macd_signal=macd_signal,
            atr_14=atr_14,
        )

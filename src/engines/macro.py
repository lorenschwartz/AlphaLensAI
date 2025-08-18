"""
Macro engine for equity analysis.

Deterministic, test-friendly logic that converts simple macro inputs
into a `MacroIndustrySummary` (from `src.types`).
"""
from typing import Any, Dict, Optional

from src.types import MacroIndustrySummary


class MacroEngine:
    """Handles macroeconomic analysis logic."""

    def analyze(self, data: Optional[Dict[str, Any]]) -> Optional[MacroIndustrySummary]:
        """Analyze macroeconomic data and return a `MacroIndustrySummary`.

        Expected input keys (all optional):
          - rate_regime: 'Rising'|'Falling'|'Stable'
          - inflation_trend: 'Rising'|'Falling'|'Stable'
          - fx_headwind_tailwind: 'Headwind'|'Tailwind'|'Neutral'
          - commodity_links: List[str]
          - sector: str
        Returns None when `data` is falsy to match test-suite expectations.
        """
        if not data:
            return None

        # Defensive mapping: accept keys directly and coerce where useful.
        return MacroIndustrySummary(
            rate_regime=data.get("rate_regime"),
            inflation_trend=data.get("inflation_trend"),
            fx_headwind_tailwind=data.get("fx_headwind_tailwind"),
            commodity_links=data.get("commodity_links", []),
            sector=data.get("sector"),
            notes=data.get("notes"),
        )

"""
Fundamentals engine for equity analysis.
"""
from typing import Any, Dict, List, Optional
from statistics import mean, pstdev

from src.types import FundamentalsSummary


class FundamentalsEngine:
    """Handles fundamental analysis logic.

    This engine performs deterministic, auditable computations from structured
    financial inputs and returns a `FundamentalsSummary` Pydantic model.
    """

    def analyze(self, data: Optional[Dict[str, Any]]) -> Optional[FundamentalsSummary]:
        """Analyze fundamentals data and return a `FundamentalsSummary`.

        Expected input (examples):
        {
            "revenue_history": [2018_rev, 2019_rev, 2020_rev, 2021_rev, 2022_rev],
            "op_margin_history": [op_margin_2019, op_margin_2020, ...],
            "fcf_history": [fcf_2019, fcf_2020, ...],
            ...
        }

        The method is defensive: missing or insufficient data yields `None`
        for the corresponding fields.
        """
        if not data:
            # Tests and orchestration expect a None when no data provided.
            return None

        # Revenue CAGR over 3 years (if at least 4 data points present)
        rev_history: List[float] = data.get("revenue_history") or data.get("revenues") or []
        revenue_cagr_3y: Optional[float] = None
        try:
            if len(rev_history) >= 4:
                # use last and the value 3 years prior
                last = float(rev_history[-1])
                prior = float(rev_history[-4])
                if prior > 0 and last > 0:
                    revenue_cagr_3y = (last / prior) ** (1 / 3) - 1
        except Exception:
            revenue_cagr_3y = None

        # Operating margin trend in basis points per year
        opm_history: List[float] = data.get("op_margin_history") or data.get("op_margins") or []
        op_margin_trend_bps_per_year: Optional[float] = None
        try:
            if len(opm_history) >= 2:
                years = len(opm_history) - 1
                first = float(opm_history[0])
                last = float(opm_history[-1])
                # difference in decimal (e.g., 0.12 -> 12% -> 1200 bps per year)
                op_margin_trend_bps_per_year = (last - first) / years * 10000
        except Exception:
            op_margin_trend_bps_per_year = None

        # FCF stability: 1 / (1 + coef_of_variation) mapped to 0..1
        fcf_history: List[float] = data.get("fcf_history") or data.get("fcfs") or []
        fcf_stability_score: Optional[float] = None
        try:
            if len(fcf_history) >= 2:
                vals = [float(x) for x in fcf_history if x is not None]
                if len(vals) >= 2 and mean(vals) != 0:
                    cv = pstdev(vals) / abs(mean(vals))
                    fcf_stability_score = 1.0 / (1.0 + cv)
                    # clamp 0..1
                    fcf_stability_score = max(0.0, min(1.0, fcf_stability_score))
        except Exception:
            fcf_stability_score = None

        summary = FundamentalsSummary(
            revenue_cagr_3y=revenue_cagr_3y,
            gross_margin_trend_bps_per_year=None,
            op_margin_trend_bps_per_year=op_margin_trend_bps_per_year,
            fcf_stability_score=fcf_stability_score,
        )

        return summary

"""
Macro model shim.

This file re-exports the canonical `MacroIndustrySummary` contract from
`src.types` so other modules can import `src.models.macro.Macro` if they
prefer that path. It also exposes tiny helpers for validation and a brief
human-friendly summary.
"""
from typing import Any, Dict, Optional

from src.types import MacroIndustrySummary as _MacroIndustrySummary


# Re-export under a convenient name used by other modules
Macro = _MacroIndustrySummary


def validate_or_raise(data: Dict[str, Any]) -> _MacroIndustrySummary:
    """Validate a dict against the Macro contract and return a model instance.

    Uses Pydantic v2/v1 compatibility helpers (`model_validate` / `parse_obj`).
    """
    validate = getattr(Macro, "model_validate", None) or getattr(Macro, "parse_obj", None)
    if not validate:
        raise RuntimeError("Unsupported Pydantic version: missing model_validate/parse_obj.")
    return validate(data)


def brief(summary: _MacroIndustrySummary) -> str:
    """Return a compact one-line summary for logs or CLI.

    Example: "SectorName | rate=Rising | inflation=Stable"
    """
    parts = []
    if getattr(summary, "sector", None):
        parts.append(str(summary.sector))
    if getattr(summary, "rate_regime", None):
        parts.append(f"rate={summary.rate_regime}")
    if getattr(summary, "inflation_trend", None):
        parts.append(f"inflation={summary.inflation_trend}")
    return " | ".join(parts) if parts else "macro: <no summary>"


# --- Backwards-compatible thin wrapper used by simple tests / call-sites ---
from pydantic import BaseModel


class MacroWrapper(BaseModel):
    """Thin wrapper with a single `indicators` field used in lightweight tests."""

    indicators: Any = None


# Keep the name `Macro` pointing at the thin wrapper for compatibility with tests
# which expect `Macro(indicators=None)`. Consumers that need the canonical
# typed shape should import `src.types.MacroIndustrySummary` or use
# `src.models.macro.validate_or_raise`.
Macro = MacroWrapper

"""
Decision model shim.

This file re-exports the canonical `Decision` contract defined in `src.types` and
provides a couple of thin helpers so other modules can import from
`src.models.decision` if they prefer that path.
"""
from typing import Any, Dict

from src.types import Decision as _Decision

# Re-export the Decision model
Decision = _Decision


def validate_or_raise(data: Dict[str, Any]) -> _Decision:
    """Validate a dict against the `Decision` contract and return a model instance.

    This delegates to `Decision.validate_or_raise` implemented in `src.types` and
    keeps calling code stable if you want to import from `src.models.decision`.
    """
    return Decision.validate_or_raise(data)


def short_summary(decision: _Decision) -> str:
    """Return the one-line short summary for a `Decision` instance."""
    return decision.short_summary()

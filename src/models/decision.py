"""
Decision model shim.

This file provides a tiny, test-friendly wrapper `Decision` (has a single
`result` field) so callers that import `src.models.decision.Decision` get a
lightweight object. It also exposes helpers that delegate to the canonical
`Decision` model defined in `src.types` when callers need full validation or
the official `short_summary` behavior.
"""
from typing import Any, Dict, Union

from pydantic import BaseModel

from src.types import Decision as _Decision


class Decision(BaseModel):
    """Thin wrapper used by older call sites and tests.

    Field:
        result: Any — opaque passthrough for quick smoke tests and callers who
        don't need the full canonical Decision contract.
    """

    result: Any = None


def validate_or_raise(data: Dict[str, Any]) -> _Decision:
    """Validate a dict against the canonical `Decision` contract and return the model instance."""
    validate = getattr(_Decision, "model_validate", None) or getattr(_Decision, "parse_obj", None)
    if not validate:
        raise RuntimeError("Unsupported Pydantic version: missing model_validate/parse_obj.")
    return validate(data)


def short_summary(decision: Union[_Decision, Decision]) -> str:
    """Return a one-line summary.

    If given the canonical `_Decision`, use its `short_summary`. If given the
    thin wrapper, return a compact placeholder reflecting presence/absence of
    `result`.
    """
    if isinstance(decision, _Decision):
        return decision.short_summary()
    if isinstance(decision, Decision):
        return "result: <present>" if decision.result is not None else "result: None"
    return str(decision)

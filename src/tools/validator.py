"""
src/tools/validator.py

Validator -- validates pipeline data against Pydantic schemas.

The default target schema is ``Decision``.  Callers can pass a different
``model_cls`` to validate engine-level sub-objects (e.g. FundamentalsSummary).

Usage::

    v = Validator()
    validated = v.validate(raw_dict)            # -> dict (Decision)
    validated = v.validate(decision_obj)        # -> dict (round-trip check)
    validated = v.validate(data, FundamentalsSummary)  # -> dict

Raises
------
ValueError           -- data is None or empty
TypeError            -- data is not a dict or a Pydantic model instance
pydantic.ValidationError -- data fails schema validation
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type

from pydantic import BaseModel


class Validator:
    """Validates pipeline data against a Pydantic schema.

    Accepts either a plain ``dict`` or an existing Pydantic model instance.
    Returns the validated data as a plain ``dict`` so callers always receive
    a consistent serialisable type.
    """

    def validate(
        self,
        data: Any,
        model_cls: Optional[Type[BaseModel]] = None,
    ) -> Dict[str, Any]:
        """Validate *data* against *model_cls* (default: ``Decision``).

        Args:
            data:      A plain dict or a Pydantic model instance.
            model_cls: Target Pydantic model class.  Defaults to
                       :class:`~src.types.Decision`.

        Returns:
            The validated data as a plain dict.

        Raises:
            ValueError: If *data* is ``None`` or an empty dict.
            TypeError:  If *data* is neither a dict nor a Pydantic model.
            pydantic.ValidationError: If *data* does not satisfy the schema.
        """
        if not data:
            raise ValueError(
                "data must be a non-empty dict or a Pydantic model instance"
            )

        from src.types import Decision

        target: Type[BaseModel] = model_cls or Decision

        if isinstance(data, BaseModel):
            # Round-trip through dict to catch any post-init violations.
            raw: Dict[str, Any] = getattr(data, "model_dump", data.dict)()
        elif isinstance(data, dict):
            raw = data
        else:
            raise TypeError(
                f"Expected a dict or Pydantic model instance, "
                f"got {type(data).__name__}"
            )

        # Validate using the appropriate Pydantic v1/v2 API.
        if hasattr(target, "validate_or_raise"):
            # Decision exposes this helper for v1/v2 compat.
            validated = target.validate_or_raise(raw)  # type: ignore[attr-defined]
        else:
            fn = getattr(target, "model_validate", None) or getattr(
                target, "parse_obj", None
            )
            if fn is None:
                raise RuntimeError(
                    f"Cannot validate: {target} has no model_validate/parse_obj method"
                )
            validated = fn(raw)

        return getattr(validated, "model_dump", validated.dict)()

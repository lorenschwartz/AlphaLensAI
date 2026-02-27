"""
src/tools/api_fetcher.py

Deterministic, registry-based API data fetcher.

Design
------
``APIFetcher`` maintains a dict of ``endpoint -> handler`` callables.
``fetch(endpoint, params)`` dispatches to the registered handler and returns
the handler's result dict.  No network I/O is performed by default -- the
built-in handlers return structured skeleton dicts that the engines can
process (all handle missing/empty keys gracefully).

Callers can override or extend the default handlers by calling ``register()``.

Built-in endpoints
------------------
fundamentals  -- returns {}  (FundamentalsEngine accepts missing keys)
technicals    -- returns {}  (TechnicalsEngine uses safe defaults)
sentiment     -- returns {"analyst_consensus": "Hold"}
macro         -- returns {}  (MacroEngine accepts missing keys)
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class APIFetcher:
    """Registry-based deterministic API data fetcher.

    All built-in handlers are pure functions (same input -> same output, no I/O)
    to satisfy the determinism requirement in CLAUDE.md.

    Example::

        fetcher = APIFetcher()
        fetcher.register("fundamentals", my_real_api_handler)
        data = fetcher.fetch("fundamentals", {"ticker": "AAPL"})
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self._register_defaults()

    # ------------------------------------------------------------------
    # Default handlers
    # ------------------------------------------------------------------

    @staticmethod
    def _default_fundamentals(params: Dict[str, Any]) -> Dict[str, Any]:
        """Return an empty dict -- FundamentalsEngine handles missing keys."""
        return {}

    @staticmethod
    def _default_technicals(params: Dict[str, Any]) -> Dict[str, Any]:
        """Return an empty dict -- TechnicalsEngine uses safe defaults."""
        return {}

    @staticmethod
    def _default_sentiment(params: Dict[str, Any]) -> Dict[str, Any]:
        """Return minimum valid sentiment dict."""
        return {"analyst_consensus": "Hold"}

    @staticmethod
    def _default_macro(params: Dict[str, Any]) -> Dict[str, Any]:
        """Return an empty dict -- MacroEngine handles missing keys."""
        return {}

    def _register_defaults(self) -> None:
        self._handlers["fundamentals"] = self._default_fundamentals
        self._handlers["technicals"] = self._default_technicals
        self._handlers["sentiment"] = self._default_sentiment
        self._handlers["macro"] = self._default_macro

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(
        self,
        endpoint: str,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """Register (or replace) the handler for *endpoint*.

        Args:
            endpoint: Endpoint name, e.g. ``"fundamentals"``.
            handler:  Callable accepting params dict, returning result dict.
                      Should be deterministic and side-effect-free.
        """
        self._handlers[endpoint] = handler

    def fetch(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Dispatch to the registered handler for *endpoint*.

        Args:
            endpoint: Registered endpoint name.
            params:   Query parameters.  ``None`` is treated as ``{}``.

        Returns:
            The handler's result dict.

        Raises:
            ValueError: If *endpoint* has no registered handler.
        """
        handler = self._handlers.get(endpoint)
        if handler is None:
            raise ValueError(
                f"Unknown endpoint: {endpoint!r}.  "
                f"Registered endpoints: {sorted(self._handlers)}"
            )
        return handler(params or {})

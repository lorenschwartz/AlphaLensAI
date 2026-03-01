"""
src/api/main.py

FastAPI application for AlphaLensAI.

Endpoints
---------
GET  /health              — Liveness probe.
POST /analyze             — Run the full pipeline; return a Decision (JSON).
POST /analyze/html        — Same pipeline; return a self-contained HTML report.
GET  /analyze/{ticker}    — Return a pre-populated template for a ticker
                            so the UI can pre-fill the analysis form.

Design constraints (from CLAUDE.md / TODO.md):
- Stateless: no session state, no database.
- All computation stays in src/; this module only handles HTTP
  serialisation / deserialisation.
- CORS allowed origins are configurable via the CORS_ORIGINS env var
  (comma-separated list; defaults to localhost only).
"""

from __future__ import annotations

import os
from datetime import date
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.api.schemas import AnalyzeRequest
from src.orchestrator.orchestrator import Orchestrator
from src.reporting.reporter import Reporter

app = FastAPI(
    title="AlphaLensAI",
    version="0.1.0",
    description="Modular agentic equity research pipeline.",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost,http://localhost:8080")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize(obj: Any) -> Any:
    """Pydantic v1/v2 compatible model → dict serialiser."""
    dump = getattr(obj, "model_dump", None) or getattr(obj, "dict", None)
    return dump(mode="json") if dump else obj


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["ops"])
def health() -> Dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/analyze", tags=["analysis"])
def analyze(req: AnalyzeRequest) -> Any:
    """Run the AlphaLensAI pipeline and return a Decision.

    The request body maps directly to the ``Orchestrator.run()`` input dict.
    Engine sub-sections (fundamentals, macro, technicals, sentiment) are
    forwarded as-is; the orchestrator handles all computation.

    Returns the serialised ``Decision`` object on success (HTTP 200).
    FastAPI returns HTTP 422 automatically for any schema validation failure.
    """
    # Convert nested Pydantic models to plain dicts for the orchestrator
    input_dict = _serialize(req)
    decision = Orchestrator().run(input_dict)
    return _serialize(decision)


@app.post("/analyze/html", tags=["analysis"], response_class=HTMLResponse)
def analyze_html(req: AnalyzeRequest) -> HTMLResponse:
    """Run the AlphaLensAI pipeline and return a self-contained HTML report.

    Accepts the same request body as ``POST /analyze``.  Returns an HTML
    document that can be saved directly as a ``.html`` file or opened in
    a browser — no external assets required.
    """
    input_dict = _serialize(req)
    decision = Orchestrator().run(input_dict)
    html_str = Reporter().report(decision)
    return HTMLResponse(content=html_str or "", status_code=200)


@app.get("/analyze/{ticker}", tags=["analysis"])
def analyze_template(ticker: str) -> Dict[str, Any]:
    """Return a pre-populated analysis template for *ticker*.

    The UI can use this to pre-fill the analysis form so the analyst only
    needs to complete/override the fields relevant to their view.  All
    numeric placeholders default to 0.0; lists default to empty.
    """
    today = date.today().isoformat()
    t = ticker.upper()
    return {
        "ticker": t,
        "as_of": today,
        "recommendation": "HOLD",
        "target_price_12m": 0.0,
        "expected_total_return_pct": 0.0,
        "horizon_months": 12,
        "risk_rating": "Medium",
        "thesis": [],
        "key_risks": [],
        "valuation": {
            "blended": 0.0,
            "dcf_fair_value": None,
            "multiples_fair_value": None,
            "wacc": None,
            "terminal_g": None,
            "peer_multiples_used": [],
        },
        "scenarios": {
            "bull": {"prob": 0.25, "fair_value": 0.0, "eps": None},
            "base": {"prob": 0.50, "fair_value": 0.0, "eps": None},
            "bear": {"prob": 0.25, "fair_value": 0.0, "eps": None},
        },
        "fundamentals": None,
        "macro": None,
        "technicals": None,
        "sentiment": None,
        "assumptions": {},
        "catalysts_next_6_12m": [],
        "citations": [],
        "monitoring": [],
        "artifacts": None,
    }

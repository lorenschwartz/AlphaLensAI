# Pipeline Overview

This document describes the architecture and data flow of the AlphaLensAI
pipeline. All modules are fully implemented. See `src/types.py` for the
canonical data contracts.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Entry points                          │
│  Python API  ·  FastAPI REST  ·  Alpine.js UI               │
└──────────────────────────┬──────────────────────────────────┘
                           │  input dict / AnalyzeRequest
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  Orchestrator  (src/orchestrator/orchestrator.py)            │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │Fundamentals │  │ Technicals  │  │ SentimentEngine      │ │
│  │Engine       │  │ Engine      │  │ (consensus mapping,  │ │
│  │(CAGR, margin│  │ (trend, MA, │  │  short interest,     │ │
│  │ FCF stab.)  │  │  RSI, MACD) │  │  news sentiment)     │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬───────────┘ │
│         │                │                    │             │
│  ┌──────▼────────────────▼────────────────────▼───────────┐ │
│  │  MacroEngine (rate regime, FX, sector)                 │ │
│  └──────────────────────────┬──────────────────────────── ┘ │
│                             │ engine outputs                │
│                             ▼                               │
│  Assemble Decision (src.types.Decision)                     │
│  • caller assumptions never overwritten (setdefault)        │
└──────────────────────────┬───────────────────────────────── ┘
                           │  Decision
                           ▼
        ┌──────────────────┴────────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────────┐               ┌───────────────────────┐
│  LLMAgent         │               │  Reporter             │
│  (gap-fill /      │               │  (HTML export)        │
│   narrative)      │               │                       │
│  backend-agnostic │               │  self-contained .html │
│  stub by default  │               │  with inline CSS      │
└───────────────────┘               └───────────────────────┘
        │                                       │
        └───────────────┬───────────────────────┘
                        │
                        ▼
              FastAPI REST layer
              POST /analyze        → Decision JSON
              POST /analyze/html   → HTML document
              GET  /analyze/{t}    → form template
              GET  /health         → {"status":"ok"}
                        │
                        ▼
              ui/index.html (Alpine.js)
              three-tab form + report view
```

---

## Module responsibilities

### Engines (`src/engines/`)

Each engine is a stateless class with a single public method
`analyze(data: dict | None) -> TypedOutput | None`. Engines:

- Never raise on missing or malformed data (defensive).
- Return `None` when `data` is falsy.
- Compute only from the provided dict; no I/O.

| Engine | Input | Output |
|--------|-------|--------|
| `FundamentalsEngine` | Revenue / margin / FCF history lists | `FundamentalsSummary` |
| `TechnicalsEngine` | Price series or pre-computed scalars | `Technicals` |
| `SentimentEngine` | Consensus string, short interest, news score | `Sentiment` |
| `MacroEngine` | Rate regime, sector, FX, commodity links | `MacroIndustrySummary` |

### Orchestrator (`src/orchestrator/orchestrator.py`)

`Orchestrator.run(input_data: dict) -> Decision | None`

1. Returns `None` for falsy input.
2. Calls all four engines with the relevant sub-dict from `input_data`.
3. Falls back to safe defaults when an engine returns `None`
   (e.g. `Technicals` defaults to `trend="Sideways"`, `rsi_14=50.0`).
4. Injects engine-computed metrics into `assumptions` via `setdefault`
   (caller-supplied values are never overwritten).
5. Assembles and returns a fully-typed `Decision`.

### Tools (`src/tools/`)

| Tool | Purpose |
|------|---------|
| `APIFetcher` | Registry-based data fetcher. Register endpoint handlers; built-in stubs return minimal valid dicts. |
| `Validator` | Validates a dict or Pydantic model against a schema (default: `Decision`). Returns validated dict or raises. |

### LLM Agent (`src/llm/llm_agent.py`)

Backend-agnostic — injects any `(prompt: str) -> str` callable. Stub mode
(default) returns `None` without any network calls. Provides:

- `build_decision_prompt(decision)` — structured multi-section analysis prompt
- `build_risk_check_prompt(decision)` — focused risk-assessment prompt

### Reporter (`src/reporting/reporter.py`)

`Reporter.report(result) -> str | None`

Accepts `Decision`, `dict`, or `None`. Generates a self-contained HTML
document (inline CSS) covering: header, thesis/risks, scenarios, valuation,
technicals, sentiment, assumptions, monitoring rules, catalysts.

### FastAPI layer (`src/api/`)

Thin HTTP serialisation/deserialisation layer. All business logic stays in
`src/`; the API only:
1. Validates the request body via `AnalyzeRequest` (Pydantic).
2. Calls `Orchestrator().run()`.
3. Serialises the `Decision` to JSON or delegates to `Reporter` for HTML.

---

## Data-flow example (Python)

```python
from src.orchestrator.orchestrator import Orchestrator
from src.reporting.reporter import Reporter

decision = Orchestrator().run({
    "ticker": "AAPL",
    "as_of": "2025-08-11",
    "recommendation": "BUY",
    "target_price_12m": 240.0,
    "expected_total_return_pct": 18.5,
    "risk_rating": "Medium",
    "thesis": ["Services revenue approaching 40% of sales"],
    "key_risks": ["FTC antitrust action"],
    "valuation": {"blended": 240.0},
    "scenarios": {
        "bull": {"prob": 0.30, "fair_value": 290.0},
        "base": {"prob": 0.50, "fair_value": 240.0},
        "bear": {"prob": 0.20, "fair_value": 170.0},
    },
    "fundamentals": {"revenue_history": [365, 394, 383, 391]},
    "technicals": {"rsi_14": 58.0, "trend": "Up", "ma_cross": "50>200"},
    "sentiment": {"analyst_consensus": "Outperform", "avg_target": 248.0},
})

print(decision.short_summary())
# 2025-08-11 | AAPL → BUY @ 240.00 (18.5% / 12m, risk=Medium)

html_report = Reporter().report(decision)
with open("aapl_report.html", "w") as f:
    f.write(html_report)
```

---

## Extensibility

- **New engine**: add `src/engines/<name>.py`, output type in `src/types.py`,
  wire into `Orchestrator.run()`, write tests first.
- **Real API data**: register a handler with `APIFetcher.register()`.
- **Real LLM calls**: inject a backend callable into `LLMAgent(backend=...)`.
- **New report format**: subclass or extend `Reporter`; the HTML template
  is built from plain Python string operations — no external template engine.

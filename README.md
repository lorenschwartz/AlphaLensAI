# AlphaLensAI

A modular, agentic equity research pipeline. Given a ticker and financial/market
data, it produces a structured `Decision` — recommendation (BUY/HOLD/SELL),
valuation, bull/base/bear scenarios, risks, monitoring rules, and citations —
all verifiable and auditable.

**Backend analysis library** with a FastAPI REST layer and an Alpine.js web UI
on top. No database. All data flows through Pydantic models. The primary output
is a `src.types.Decision` instance.

---

## Quick start

```bash
# 1 — clone and install
git clone <repo-url> AlphaLensAI && cd AlphaLensAI
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2 — run tests (194 tests, ~2 s)
pytest tests

# 3 — start the API server
uvicorn src.api.main:app --reload
# → http://localhost:8000/docs  (Swagger UI)

# 4 — open the web UI (no build step required)
python -m http.server 8080 --directory ui
# → http://localhost:8080
```

---

## Architecture

```
API Fetchers ──→ Validator ──→ Engines (parallel)
                                  ├── FundamentalsEngine → FundamentalsSummary
                                  ├── TechnicalsEngine   → Technicals
                                  ├── SentimentEngine    → Sentiment
                                  └── MacroEngine        → MacroIndustrySummary
                              ↓
                          Orchestrator ──→ Decision  (src.types.Decision)
                              ↓
                          LLM Agent  (gap-fill / narrative)
                              ↓
                          Reporter   (HTML export)
                              ↓
                          FastAPI  (REST)  ←→  ui/index.html  (Alpine.js)
```

All inter-module communication uses the Pydantic models in `src/types.py`.

### Repository layout

```
AlphaLensAI/
├── src/
│   ├── types.py                 # Canonical data contracts (read first)
│   ├── engines/
│   │   ├── fundamentals.py      # Revenue CAGR, margin trend, FCF stability
│   │   ├── macro.py             # Macro/industry context
│   │   ├── technicals.py        # Trend, MAs, RSI, MACD, ATR, S/R levels
│   │   └── sentiment.py         # Analyst consensus, short interest, news
│   ├── orchestrator/
│   │   └── orchestrator.py      # Wires engine outputs into a Decision
│   ├── llm/
│   │   └── llm_agent.py         # Backend-agnostic LLM adapter + prompt builders
│   ├── reporting/
│   │   └── reporter.py          # Self-contained HTML report generator
│   ├── tools/
│   │   ├── api_fetcher.py       # Registry-based deterministic data fetcher
│   │   └── validator.py         # Pydantic schema validator
│   ├── api/
│   │   ├── main.py              # FastAPI app (CORS, 4 endpoints)
│   │   └── schemas.py           # Request/response Pydantic models
│   └── models/                  # Thin backwards-compat shims
├── tests/                       # 194 pytest unit tests (mirrors src/)
├── ui/
│   └── index.html               # Alpine.js SPA — no build step
├── docs/
│   ├── TODO.md                  # Roadmap
│   ├── pipeline_overview.md     # Data-flow architecture
│   ├── output_contracts.md      # Decision schema reference
│   ├── system_prompt.md         # LLM system prompt
│   └── risk_checker_prompt.md   # Risk-checker LLM prompt
├── requirements.txt
├── setup.cfg                    # flake8 config (max-line-length = 130)
└── .github/workflows/ci.yml     # CI: flake8 → black → pytest
```

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness probe → `{"status": "ok"}` |
| `POST` | `/analyze` | Run full pipeline → serialised `Decision` (JSON) |
| `POST` | `/analyze/html` | Same pipeline → self-contained HTML report |
| `GET` | `/analyze/{ticker}` | Pre-populated form template for a ticker |

All endpoints are documented interactively at `http://localhost:8000/docs`
once the server is running.

### POST /analyze — minimal request body

```json
{
  "ticker": "AAPL",
  "as_of": "2025-08-11",
  "recommendation": "BUY",
  "target_price_12m": 240.0,
  "expected_total_return_pct": 18.5,
  "risk_rating": "Medium",
  "thesis": ["Services revenue approaching 40% of sales"],
  "key_risks": ["FTC antitrust action on App Store"],
  "valuation": { "blended": 240.0 },
  "scenarios": {
    "bull": { "prob": 0.30, "fair_value": 290.0 },
    "base": { "prob": 0.50, "fair_value": 240.0 },
    "bear": { "prob": 0.20, "fair_value": 170.0 }
  }
}
```

Optional sections: `fundamentals`, `technicals`, `sentiment`, `macro`,
`assumptions`, `catalysts_next_6_12m`, `citations`, `monitoring`.

---

## Web UI

`ui/index.html` is a single-page app (Alpine.js from CDN, no build step).

**Three-tab analysis form:**
- **Core** — ticker, date, recommendation, target, return, risk rating,
  thesis bullets, key risks, valuation, bull/base/bear scenarios
- **Engines** — pre-computed technicals, sentiment inputs, raw CSV price /
  margin / FCF series, macro / industry context
- **Assumptions** — key-value editor to override engine-computed values
  (e.g. `rev_cagr_3y`, `op_margin_trend_bps_per_year`)

**Decision report view** (rendered after submit):
- Header badge: ticker · recommendation · target price · expected return · risk
- Thesis and key risks bullet lists
- Scenarios and valuation tables
- Technicals and sentiment summaries
- Engine assumptions, monitoring rules, catalysts
- **Re-run with overrides** — edit any assumption in-place and resubmit

```bash
# Serve the UI (API must already be running on :8000)
python -m http.server 8080 --directory ui
```

---

## Implemented modules

| Module | Class | Status |
|--------|-------|--------|
| `src/engines/fundamentals.py` | `FundamentalsEngine` | ✅ Implemented |
| `src/engines/macro.py` | `MacroEngine` | ✅ Implemented |
| `src/engines/technicals.py` | `TechnicalsEngine` | ✅ Implemented |
| `src/engines/sentiment.py` | `SentimentEngine` | ✅ Implemented |
| `src/orchestrator/orchestrator.py` | `Orchestrator` | ✅ Implemented |
| `src/tools/api_fetcher.py` | `APIFetcher` | ✅ Implemented |
| `src/tools/validator.py` | `Validator` | ✅ Implemented |
| `src/llm/llm_agent.py` | `LLMAgent` | ✅ Implemented |
| `src/reporting/reporter.py` | `Reporter` | ✅ Implemented |
| `src/api/main.py` | FastAPI app | ✅ Implemented |
| `ui/index.html` | Alpine.js SPA | ✅ Implemented |

---

## Engine reference

### FundamentalsEngine

Input keys: `revenue_history` / `revenues`, `op_margin_history` / `op_margins`,
`fcf_history` / `fcfs` (lists of floats).

Computes: revenue CAGR (3 yr), operating-margin trend (bps/yr),
FCF stability score `1/(1 + CV)` clamped to `[0, 1]`.

### TechnicalsEngine

Input: pre-computed scalars (`rsi_14`, `ma_50`, `ma_200`, `macd_line`, etc.)
**or** raw series (`prices`/`close_prices`, `highs`, `lows`). Pre-computed
values take precedence.

Computes: trend (Up/Down/Sideways), MA cross, RSI(14), MACD, ATR(14),
support/resistance via sliding-window local min/max.

### SentimentEngine

Input keys: `analyst_consensus` (raw string — mapped to Buy/Hold/Sell),
`avg_target`, `short_interest_pct_float` (alias: `short_interest_pct`),
`news_sentiment_score` (clamped to `[−1, +1]`), `insider_net_buy_90d`,
`delta_analyst_upgrades_90d`, `delta_avg_target_90d`.

Maps 20+ raw consensus labels (Outperform, Neutral, Underweight, …) to
the canonical `Buy / Hold / Sell` literals.

### MacroEngine

Input keys: `rate_regime`, `inflation_trend`, `fx_headwind_tailwind`,
`commodity_links`, `sector`, `notes`.

### Orchestrator

Fans out to all four engines in sequence, assembles engine outputs into a
`Decision`. Caller-supplied `assumptions` values are never overwritten by
engine-computed values (`setdefault` semantics).

### LLMAgent

Backend-agnostic. Inject any `(prompt: str) -> str` callable as `backend=`.
Default is stub mode (no network calls, fully testable). Provides two prompt
builders:

- `build_decision_prompt(decision)` — full analysis context for gap-filling
- `build_risk_check_prompt(decision)` — focused risk-assessment context

```python
from anthropic import Anthropic
from src.llm.llm_agent import LLMAgent

client = Anthropic()
agent = LLMAgent(
    backend=lambda p: client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": p}],
    ).content[0].text
)
response = agent.interact(agent.build_decision_prompt(decision))
```

### APIFetcher

Registry-based. Built-in handlers for `fundamentals`, `technicals`,
`sentiment`, `macro` (all return empty/minimal dicts — engines handle
missing keys gracefully). Override with real API handlers:

```python
fetcher = APIFetcher()
fetcher.register("fundamentals", my_real_api_handler)
data = fetcher.fetch("fundamentals", {"ticker": "AAPL"})
```

### Reporter

Accepts `Decision`, `dict`, or `None`. Returns a self-contained HTML string
(inline CSS, dark theme) that can be saved as `.html` or served directly.

---

## Running tests and linters

```bash
# All tests
pytest tests

# Linting
flake8 src tests

# Format check (CI enforces this)
black --check src tests

# Auto-format
black src tests
```

CI (`.github/workflows/ci.yml`) runs `flake8 → black --check → pytest` on
every push to `main`/`master` and on every PR.

---

## Development setup

### Devcontainer (recommended)

Open in VS Code and choose **Reopen in Container**. Python 3.11 and all
tooling are pre-installed.

### Local setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Adding a new engine (TDD workflow)

1. Define (or confirm) the output type in `src/types.py`.
2. Create `src/engines/<name>.py` with a stub `analyze()` that returns `None`.
3. Write failing tests in `tests/test_engines.py` (Red).
4. Implement until all tests pass (Green).
5. Refactor; keep the suite Green.
6. Wire into `src/orchestrator/orchestrator.py`.

---

## License & community

This project is licensed under the **MIT License** — see `LICENSE` for details.

Please follow `CODE_OF_CONDUCT.md` when contributing. If you discover a
security issue, see `SECURITY.md` for reporting guidance. Contributions are
welcome — see `CONTRIBUTING.md` for the developer setup guide.

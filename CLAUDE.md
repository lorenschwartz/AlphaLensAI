# CLAUDE.md — AlphaLensAI

This file provides guidance for AI assistants (Claude, Copilot, etc.) working in
this repository. Read it before touching any code.

---

## Project Purpose

**AlphaLensAI** is a modular, agentic equity research pipeline. Given a ticker
and raw financial/market data, it produces a structured `Decision` object that
contains a recommendation (BUY/HOLD/SELL), valuation, scenarios, risks,
monitoring rules, and citations — all verifiable and auditable.

This is a **backend analysis library** with no REST API, no database, and no
frontend. All data flows through Pydantic models. The primary output is a
`src.types.Decision` instance.

---

## Repository Layout

```
AlphaLensAI/
├── src/
│   ├── types.py            # THE canonical data contracts — read this first
│   ├── engines/
│   │   ├── fundamentals.py # Revenue CAGR, margin trend, FCF stability (DONE)
│   │   ├── macro.py        # Macro/industry context converter (DONE)
│   │   ├── technicals.py   # Trend, MAs, RSI, MACD, ATR, levels (DONE)
│   │   └── sentiment.py    # Stub — not yet implemented
│   ├── models/             # Thin backwards-compat shims (wrap src.types)
│   ├── orchestrator/
│   │   └── orchestrator.py # Stub — wires engine outputs into Decision
│   ├── llm/
│   │   └── llm_agent.py    # Stub — LLM reasoning / gap-filling
│   ├── reporting/
│   │   └── reporter.py     # Stub — HTML/PDF export
│   └── tools/
│       ├── api_fetcher.py  # Stub — deterministic API data retrieval
│       └── validator.py    # Stub — schema & data-integrity checks
├── tests/                  # pytest unit tests (mirrors src/ structure)
├── docs/
│   ├── TODO.md             # Prioritised roadmap
│   ├── pipeline_overview.md
│   ├── system_prompt.md    # LLM system-prompt for the agent layer
│   └── risk_checker_prompt.md
├── .github/workflows/ci.yml  # CI: flake8 → black → pytest
├── .devcontainer/          # Python 3.11 devcontainer + Copilot CLI
└── CLAUDE.md               # This file
```

---

## Data-Flow Architecture

```
API Fetchers → Validator → Engines (parallel)
                               ├── FundamentalsEngine  → FundamentalsSummary
                               ├── TechnicalsEngine    → Technicals
                               ├── SentimentEngine     → Sentiment
                               └── MacroEngine         → MacroIndustrySummary
                           ↓
                       Orchestrator  ──→  Decision (src.types.Decision)
                           ↓
                       LLM Agent (gap-fill / narrative)
                           ↓
                       Reporter (HTML/PDF)
```

All inter-module communication uses the Pydantic models defined in `src/types.py`.

---

## The Central Contract: `src/types.py`

**This file is the source of truth.** Every engine, orchestrator, and reporter
must produce and consume types defined here. Keep this file stable.

Key types:

| Type | Purpose |
|---|---|
| `Decision` | Top-level output — the thing the orchestrator must produce |
| `FundamentalsSummary` | Compact financial-statement snapshot |
| `MacroIndustrySummary` | Macro/industry context for conditioning valuations |
| `Technicals` | Technical indicators (trend, MA cross, RSI, levels…) |
| `Sentiment` | Analyst consensus, short interest, news sentiment |
| `Valuation` | DCF, multiples, blended fair values |
| `Scenario` | Bull/base/bear case with probability weight |
| `Catalyst` | Upcoming value-moving event |
| `Citation` | Source traceability (filing, news, api) |
| `MonitoringRule` | Falsifiable threshold — breach changes recommendation |

Literal type aliases (used as enums):

```python
RiskRating = Literal["Low", "Medium", "High"]
Reco       = Literal["BUY", "HOLD", "SELL"]
Trend      = Literal["Up", "Down", "Sideways"]
MACross    = Literal["50>200", "50<200", "none"]
AnalystConsensus = Literal["Buy", "Hold", "Sell"]
```

`Decision` helpers:
- `Decision.validate_or_raise(data: dict)` — Pydantic v1/v2 compatible
  constructor. Always use this to build a `Decision` from a raw dict.
- `decision.short_summary()` — one-line log string.

---

## Implemented vs. Stub Modules

### Implemented (write tests before changing)

**`src/engines/fundamentals.py` — `FundamentalsEngine.analyze(data)`**
- Input keys: `revenue_history` / `revenues`, `op_margin_history` / `op_margins`,
  `fcf_history` / `fcfs` (all lists of floats).
- Calculates: revenue CAGR over 3 years, operating-margin trend (bps/year),
  FCF stability score `1/(1 + CV)` clamped to [0, 1].
- Returns `FundamentalsSummary` or `None` if `data` is falsy.
- Defensive: missing/insufficient data yields `None` fields, never raises.

**`src/engines/macro.py` — `MacroEngine.analyze(data)`**
- Input: plain dict with keys `rate_regime`, `inflation_trend`,
  `fx_headwind_tailwind`, `commodity_links`, `sector`, `notes`.
- Returns `MacroIndustrySummary` or `None` if `data` is falsy.

**`src/engines/technicals.py` — `TechnicalsEngine.analyze(data)`**
- Input keys: `prices`/`close_prices`, `highs`, `lows` (raw series); or
  pre-computed scalars `rsi_14`, `ma_20`, `ma_50`, `ma_200`, `macd_line`,
  `macd_signal`, `atr_14`, `support`, `resistance`, `trend`, `ma_cross`.
- Pre-computed values take precedence; raw series used as fallback.
- Computes: trend (Up/Down/Sideways), MA cross, RSI(14), MACD, ATR(14),
  support/resistance levels via sliding-window local min/max.
- Returns `Technicals` or `None` if `data` is falsy.
- Defensive: missing/insufficient data yields `None` or neutral defaults for
  required fields (`rsi_14=50.0`, `trend="Sideways"`, `ma_cross="none"`).

### Stubs (high-priority TODO)

| Module | Class | Method | Expected output |
|---|---|---|---|
| `src/engines/sentiment.py` | `SentimentEngine` | `analyze(data)` | `Sentiment` |
| `src/tools/api_fetcher.py` | `APIFetcher` | `fetch(endpoint, params)` | dict |
| `src/tools/validator.py` | `Validator` | `validate(data)` | validated dict |
| `src/orchestrator/orchestrator.py` | `Orchestrator` | `run(input_data)` | `Decision` |
| `src/llm/llm_agent.py` | `LLMAgent` | `interact(prompt)` | str |
| `src/reporting/reporter.py` | `Reporter` | `report(result)` | str/bytes |

### Model shims (`src/models/`)

Thin wrappers that delegate to canonical `src.types` classes. They exist for
backwards-compatibility and test ergonomics. Do not add business logic here.

---

## Development Setup

### Devcontainer (recommended)

Open the repo in VS Code and choose **Reopen in Container**. The devcontainer
provides Python 3.11 and GitHub Copilot CLI.

### Local setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install black flake8 pytest pydantic
```

There is no `requirements.txt` yet — adding it is a medium-priority TODO.

---

## Running Tests and Linters

```bash
# Run all tests
pytest tests

# Lint
flake8 src tests

# Check formatting (CI enforces this)
black --check src tests

# Auto-format
black src tests
```

All three checks run in CI on every push to `main`/`master` and on every PR.

---

## Test-Driven Development (TDD)

All engine and utility code must follow a **Red → Green → Refactor** cycle.
Tests are the specification; implementation exists to satisfy them.

### The Cycle

1. **Red** — Write a failing test that precisely describes the expected
   behaviour *before writing any implementation code*.  Run `pytest` and
   confirm the test fails for the right reason.
2. **Green** — Write the minimum implementation needed to make all tests pass.
3. **Refactor** — Improve clarity, remove duplication, enforce style — then
   re-run the suite to confirm it is still Green.

### Required Coverage per Module

Every `analyze()` (or other non-trivial public method) must have tests for:

| Scenario | What to assert |
|---|---|
| **Happy path** | Correct output type and key field values from representative input |
| **Falsy input** (`None`, `{}`) | Returns `None` (for engines), never raises |
| **Partial input** | Missing optional keys → `None` fields, no exceptions |
| **Alias keys** | Alternative key names accepted (e.g. `revenues` vs `revenue_history`) |
| **Boundary / edge values** | Minimum data required, off-by-one, exact cutoffs |
| **Invalid / malformed data** | Non-numeric values, zero denominators — never raises |
| **Output bounds** | Scores clamped [0, 1]; RSI [0, 100]; probabilities [0, 1] |

### Naming Convention

Use `test_<unit>_<scenario>`:

```python
def test_fundamentals_engine_revenue_cagr(): ...
def test_fundamentals_engine_insufficient_revenue_data(): ...
def test_fundamentals_engine_fcf_mean_zero(): ...
```

### Test Structure (Arrange → Act → Assert)

```python
def test_fundamentals_engine_revenue_cagr():
    # Arrange
    engine = FundamentalsEngine()
    data = {"revenue_history": [100.0, 110.0, 121.0, 133.1]}
    # Act
    result = engine.analyze(data)
    # Assert
    assert result is not None
    assert math.isclose(result.revenue_cagr_3y, 0.1, rel_tol=1e-6)
```

### What NOT to Test

- Private helpers (`_sma`, `_rsi`, etc.) — test only through the public
  `analyze()` interface; helpers are implementation details.
- Internal state or call counts.
- Real network I/O or filesystem access in unit tests.

---

## Coding Conventions

### General

- **Python 3.11+**. Use `from __future__ import annotations` at the top of every
  module.
- **Pydantic v1/v2 compatible**. Use `validate_or_raise` / `model_validate` with
  a `parse_obj` fallback. Do not use v2-only APIs without a guard.
- **No external dependencies** beyond `pydantic`, `pytest`, `black`, `flake8`,
  and the standard library until `requirements.txt` exists.

### Naming

| Construct | Convention | Example |
|---|---|---|
| Module/file | `snake_case` | `api_fetcher.py` |
| Class | `PascalCase` | `FundamentalsEngine` |
| Method/function | `snake_case` | `analyze()`, `validate_or_raise()` |
| Pydantic field | `snake_case` | `revenue_cagr_3y` |
| Literal alias | `PascalCase` | `RiskRating`, `Reco` |

### Style

- **black** enforces formatting (88-char line length default).
- **flake8** enforces style. Fix all warnings — CI fails on any flake8 error.
- Add docstrings to every public class and method (Google style).
- Engine methods must be **deterministic and side-effect-free** — same input
  always produces same output, no I/O.

### Defensive data handling

Engines must never raise on missing/malformed data. Use `try/except Exception`
around each calculation and set the result field to `None` on failure. Return
`None` (not an empty model) when the entire `data` argument is falsy.

### Type safety

- All inter-module data uses Pydantic models from `src/types.py`.
- Never pass raw dicts across module boundaries — validate at ingestion, pass
  models after that.
- Use `Optional[T]` and `Field(default=None)` for genuinely optional fields.

---

## Adding a New Engine

Follow the TDD cycle — tests are written **before** implementation:

1. Define (or confirm) the output type in `src/types.py`.
2. Create `src/engines/<name>.py` with a **stub** `<Name>Engine.analyze()`
   that just returns `None`.
3. **Write tests first** in `tests/test_engines.py` covering all scenarios in
   the Required Coverage table above.  Run `pytest` and confirm they **fail**
   (Red).
4. Implement `analyze(self, data: Optional[Dict[str, Any]]) -> Optional[<OutputType>]`
   until all tests pass (Green).
5. Refactor for clarity and style; keep the suite Green.
6. Wire the engine into `src/orchestrator/orchestrator.py`.

---

## Key Files to Read First

When working on a new feature, read these files in order:

1. `src/types.py` — understand the contracts
2. `docs/pipeline_overview.md` — understand the data flow
3. `docs/TODO.md` — understand what is and isn't done
4. The relevant engine or stub file

---

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):

- **Trigger**: push to `main`/`master`, any PR targeting those branches.
- **Python**: 3.11 on `ubuntu-latest`.
- **Jobs** (in order):
  1. `flake8 src tests`
  2. `black --check src tests`
  3. `pytest tests`
- All three must pass for a PR to be mergeable.

---

## Current Roadmap (from `docs/TODO.md`)

**High priority**
- Implement `SentimentEngine` (deterministic, testable)
- Implement `APIFetcher` and `Validator`
- Wire `Orchestrator` to produce a full `Decision`

**Medium priority**
- `LLMAgent` and prompt adapters
- `Reporter` with HTML export
- Add `requirements.txt` / `pyproject.toml` with pinned dependencies

**Low priority**
- Architecture diagrams in `docs/`
- Integration tests
- Example datasets and templates

---

## What AI Assistants Should NOT Do

- Do not modify `src/types.py` fields without updating all downstream consumers
  and tests.
- Do not add business logic to `src/models/` shims — they are thin wrappers
  only.
- Do not introduce external dependencies without adding them to the CI install
  step and a `requirements.txt`.
- Do not make engines stateful or give them side effects (no I/O, no global
  state).
- Do not skip `flake8` or `black` fixes — CI will reject the PR.
- Do not guess at Pydantic v2-only APIs — use `validate_or_raise()` helper
  for model construction.

# TODO / Roadmap

This document captures short-term tasks that are actionable for contributors.

## High priority

- Implement `SentimentEngine` in `src/engines/sentiment.py` (deterministic, testable).
- Implement deterministic `APIFetcher` (`src/tools/api_fetcher.py`) and `Validator`
  (`src/tools/validator.py`).

## Medium priority

- LLM agent and prompt adapters (`src/llm/llm_agent.py`).
- Reporting implementation (`src/reporting/reporter.py`) with HTML export.
- Add `requirements.txt` / `pyproject.toml` and pin dependencies.

## Web UI (FastAPI + React/HTML)

A browser-based front end is planned to make the pipeline accessible without
writing Python code.  The UI must remain a thin layer over the existing library:
all business logic stays in `src/`; the web layer only marshals inputs/outputs.

### Back end — FastAPI (`src/api/`)

- [ ] **`src/api/main.py`** — FastAPI application entry point; CORS, lifespan,
  health endpoint (`GET /health`).
- [ ] **`POST /analyze`** — accept a JSON body that maps to the
  `Orchestrator.run()` input dict, call the orchestrator, return the serialised
  `Decision`.  Validate with Pydantic before passing to the orchestrator.
- [ ] **`GET /analyze/{ticker}`** — convenience endpoint: fetches a minimal
  pre-built template for a ticker so the UI can pre-populate the form.
- [ ] **`POST /analyze`** with `assumptions` override support — the body may
  include an `assumptions` dict; the orchestrator's `setdefault` logic already
  honours caller values, so no orchestrator changes are needed.
- [ ] **`src/api/schemas.py`** — request/response Pydantic models that are
  independent of (but consistent with) `src/types.py`.  Keeps the API contract
  stable even if internal types evolve.
- [ ] Add `fastapi` and `uvicorn[standard]` to `requirements.txt` and CI.

### Front end (`ui/`)

- [ ] **`ui/index.html`** — single-page app (vanilla HTML + JS or a lightweight
  framework such as Alpine.js; no build step required).
- [ ] **Analysis form** — input fields for ticker, as-of date, recommendation,
  target price, thesis bullets, key risks, and the three engine sub-sections
  (fundamentals, technicals, macro, sentiment).
- [ ] **Assumptions panel** — secondary form section that exposes the
  `assumptions` dict as editable key-value pairs so analysts can override
  computed engine values before re-running.
- [ ] **Decision report view** — structured display of the returned `Decision`:
  - Header: ticker · recommendation badge · target price · expected return ·
    risk rating
  - Thesis & key risks bullet lists
  - Scenarios table (bull / base / bear: prob, fair value)
  - Valuation section (DCF, multiples, blended)
  - Technicals summary (trend, RSI, MA cross)
  - Monitoring rules table
- [ ] **Re-run with overrides** — after viewing a report the analyst can edit
  assumption values in-place and re-submit without re-entering all inputs.

### Testing

- [ ] Unit tests for each API endpoint using FastAPI's `TestClient` (no network
  required).
- [ ] Tests for invalid request bodies → 422 response.
- [ ] Tests for valid body → 200 response with correct `Decision` fields.

### Non-functional requirements

- The API must be **stateless** — no session state, no database.
- All computation remains in `src/`; `src/api/` only handles HTTP
  serialisation/deserialisation.
- CORS should default to allow `localhost` only; make the allowed origins
  configurable via an environment variable.
- The front end must not require a build step or bundler (keep it simple).

## Low priority / Nice to have

- Add architecture diagrams to `docs/`.
- Add more comprehensive integration tests.
- Add templates and example datasets for reproducible experiments.

---

Please open issues for tasks you want to pick up and reference this file.

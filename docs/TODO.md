# TODO / Roadmap

This document captures the current state of the project and remaining work.

## Completed

All high and medium priority items have been implemented.

### Engines
- [x] `FundamentalsEngine` — revenue CAGR, op-margin trend, FCF stability
- [x] `MacroEngine` — macro/industry context converter
- [x] `TechnicalsEngine` — trend, MAs, RSI, MACD, ATR, support/resistance
- [x] `SentimentEngine` — analyst consensus mapping, short interest, news sentiment

### Orchestrator
- [x] `Orchestrator.run()` — fans out to all engines, assembles `Decision`
- [x] Caller `assumptions` are never overwritten by engine-computed values

### Tools
- [x] `APIFetcher` — registry-based deterministic fetcher; built-in handlers
      for `fundamentals`, `technicals`, `sentiment`, `macro`
- [x] `Validator` — validates dict or Pydantic model against Decision schema
      (or any model via `model_cls=`)

### LLM
- [x] `LLMAgent` — backend-agnostic adapter; stub mode by default (no network);
      `build_decision_prompt()` and `build_risk_check_prompt()` builders;
      system prompt loaded from `docs/system_prompt.md`

### Reporting
- [x] `Reporter.report()` — self-contained HTML export with inline CSS

### Web layer
- [x] `src/api/main.py` — FastAPI app with CORS
  - `GET  /health`
  - `POST /analyze` (JSON Decision)
  - `POST /analyze/html` (HTML report)
  - `GET  /analyze/{ticker}` (form template)
- [x] `src/api/schemas.py` — `AnalyzeRequest`, `ValuationInput`, `ScenarioInput`
- [x] `ui/index.html` — Alpine.js SPA (no build step)
  - Three-tab form: Core / Engines / Assumptions
  - Decision report view with re-run support

### Infrastructure
- [x] `requirements.txt` with pinned dependencies
- [x] CI updated to install from `requirements.txt`
- [x] 194 passing unit tests

---

## Remaining (low priority)

### Docs & diagrams
- [ ] Add architecture diagrams (Mermaid or PNG) to `docs/`
- [ ] Flesh out `docs/thesis_composer_prompt.md`

### Testing
- [ ] Integration tests that run the full pipeline end-to-end with example data
- [ ] Add example datasets under `tests/fixtures/` for reproducible experiments

### LLM integration
- [ ] Concrete Anthropic SDK backend example / wrapper in `src/llm/`
- [ ] Prompt versioning / template system for `system_prompt.md`

### Reporting
- [ ] PDF export option (e.g. via `weasyprint` — add to requirements.txt + CI
      if introduced)
- [ ] Charts / sensitivity tables in the `artifacts` dict

### Infrastructure
- [ ] `pyproject.toml` with build metadata and pinned dev-dependency groups
- [ ] Pre-commit hooks (black + flake8 as git hooks)

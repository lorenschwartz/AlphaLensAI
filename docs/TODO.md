# TODO / Roadmap

This document captures short-term tasks that are actionable for contributors.

High priority
- Implement `TechnicalsEngine` in `src/engines/technicals.py` (deterministic, testable).
- Implement `SentimentEngine` in `src/engines/sentiment.py` (deterministic, testable).
- Implement deterministic `APIFetcher` (`src/tools/api_fetcher.py`) and `Validator` (`src/tools/validator.py`).
- Finish Orchestrator wiring in `src/orchestrator/orchestrator.py` to assemble a canonical `Decision`.

Medium priority
- LLM agent and prompt adapters (`src/llm/llm_agent.py`).
- Reporting implementation (`src/reporting/reporter.py`) with HTML export.
- Add `requirements.txt` / `pyproject.toml` and pin dependencies.

Low priority / Nice to have
- Add architecture diagrams to `docs/`.
- Add more comprehensive integration tests.
- Add templates and example datasets for reproducible experiments.

Please open issues for tasks you want to pick up and reference this file.

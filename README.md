# AlphaLensAI: Modular Agentic Equity Research Pipeline

## Purpose

A modular, agentic pipeline for equity research, leveraging clean architecture
and LLMs for robust, explainable decision-making.

## Architecture

- **Orchestrator**: Coordinates agent modules and workflow.
- **Engines**: Specialized modules for fundamentals, technicals, sentiment, and macro analysis.
- **Tools**: Deterministic API fetchers and validators.
- **Reporting**: Output formatting and contract enforcement.
- **LLM**: Agentic interaction and reasoning.
- **Models**: Strongly typed Pydantic models for all data contracts.

## How to Run Locally

1. Clone the repo.
2. Use the provided devcontainer or set up Python 3.11.
3. Install dependencies (see future requirements.txt).
4. Run tests: `pytest`
5. Use orchestrator entrypoint for pipeline execution.

---

See `docs/` for prompts, contracts, and pipeline overview.

## Implemented vs Planned

Implemented

- Project scaffolding, repository, and developer tooling (devcontainer, `.vscode` recommendations).
- Canonical Pydantic contracts in `src/types.py` (Decision, FundamentalsSummary, MacroIndustrySummary, Valuation, Technicals, Sentiment, etc.).
- Model shims in `src/models/*` that re-export or wrap canonical models for backwards compatibility and tests.
- `FundamentalsEngine` implemented (`src/engines/fundamentals.py`) with deterministic calculations (revenue CAGR, op-margin trend, FCF stability).
- `MacroEngine` implemented (`src/engines/macro.py`) converting simple macro inputs to `MacroIndustrySummary`.
- Tests: focused unit tests for models and engines under `tests/` (engines tests for fundamentals & macro pass locally).
- CI basics: GitHub Actions workflow added for linting and tests (`.github/workflows/ci.yml`).

Planned / TODO

- Implement `TechnicalsEngine` and `SentimentEngine` with deterministic, testable logic.
- Implement deterministic `APIFetcher` and `Validator` in `src/tools/` and add end-to-end tests mocking network providers.
- Orchestrator wiring: implement `src/orchestrator/orchestrator.py` to call engines/tools and assemble a canonical `Decision`.
- LLM agent implementation (`src/llm/llm_agent.py`) and prompt adapters to call deterministic tools.
- Reporting: implement `src/reporting/reporter.py` to render final human-readable reports and export formats (PDF/HTML).
- Add `requirements.txt` or `pyproject.toml` and pin dependencies for CI and reproducible dev environments.
- Expand unit tests and add integration tests covering orchestration and report generation.
- Improve docs: flesh out `docs/` prompts, add architecture diagrams, and provide contributor guides.

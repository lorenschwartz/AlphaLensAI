# AlphaLensAI: Modular Agentic Equity Research Pipeline

## Purpose
A modular, agentic pipeline for equity research, leveraging clean architecture and LLMs for robust, explainable decision-making.

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

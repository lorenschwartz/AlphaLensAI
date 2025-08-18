# Contributing & Developer Setup

This guide shows how to set up a development environment that matches the project’s expectations and Copilot context.

## Goals
- Ensure VS Code recommends and installs Copilot and Python tooling.
- Provide a reproducible devcontainer for consistent environments.
- Offer a quick local setup script for machines not using devcontainers.

## Steps
1. Install Docker (for devcontainer).
2. Open the repository in VS Code and accept the devcontainer prompt, or open the `.devcontainer` folder and click "Reopen in container".
3. Recommended extensions are in `.vscode/extensions.json` (Copilot, Pylance, Python, GitLens).
4. Create a Python 3.11 virtualenv (if not using the devcontainer):

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick setup script (non-devcontainer)
Run `scripts/setup-dev.sh` to clone the repo, create a venv, and install minimal dependencies.

## GitHub Copilot Notes
- Copilot will infer project context from repository files and prompts in `docs/`.
- To get the same agent experience across machines: use the devcontainer, keep `docs/` updated (system prompt, pipeline overview), and enable Copilot in VS Code.

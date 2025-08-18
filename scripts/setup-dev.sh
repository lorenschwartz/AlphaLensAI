#!/usr/bin/env bash
set -euo pipefail

# Quick setup script for local development (non-devcontainer)
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  pip install pydantic pytest black flake8
fi

echo "Setup complete. Activate the venv with: source .venv/bin/activate"

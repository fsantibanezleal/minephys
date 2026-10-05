#!/usr/bin/env bash
# Bootstrap a local development environment on Linux/macOS. It NEVER installs system software: it checks for uv and
# git and tells you what is missing, then creates the venv (NumPy + PyYAML + dev tools) and runs the tests.
set -euo pipefail
cd "$(dirname "$0")/.."

missing=()
for tool in uv git; do command -v "$tool" >/dev/null 2>&1 || missing+=("$tool"); done
if [ ${#missing[@]} -gt 0 ]; then
  echo "Missing tools: ${missing[*]}"
  echo "Install them yourself (uv: https://docs.astral.sh/uv/), then re-run."
  exit 1
fi

uv sync --all-groups --locked
uv run pytest -m "not gpu" -q
echo "Ready. Tests: uv run pytest  ·  lint: uv run ruff check .  ·  types: uv run mypy src"

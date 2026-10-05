# Bootstrap a local development environment on Windows (PowerShell 7+). It NEVER installs system software: it checks
# for uv and git and tells you what is missing, then creates the venv (NumPy + PyYAML + dev tools) and runs the tests.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$missing = @()
foreach ($tool in 'uv', 'git') {
  if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { $missing += $tool }
}
if ($missing.Count -gt 0) {
  Write-Host "Missing tools: $($missing -join ', ')" -ForegroundColor Yellow
  Write-Host "Install them yourself (uv: https://docs.astral.sh/uv/), then re-run."
  exit 1
}

uv sync --all-groups --locked
uv run pytest -m "not gpu" -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Ready. Tests: uv run pytest  ·  lint: uv run ruff check .  ·  types: uv run mypy src" -ForegroundColor Green

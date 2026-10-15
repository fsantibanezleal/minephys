"""Test-support helpers: build a miniature repository tree on disk and run a `tools/` script against it.

Used by the foundation contract tests (T-000-013 to T-000-016, T-000-030 to T-000-033), which exercise the repository
tools on hand-written fixture trees. Nothing here is a model or an oracle; it only writes files and runs a process.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

GOOD_BIB = """\
@article{doe2020,
  author = {Doe, Jane},
  title = {A sourced model},
  journal = {Journal of Tests},
  year = {2020},
  doi = {10.1000/xyz123},
  access = {open}
}

@techreport{agency2025,
  organization = {Example Agency},
  title = {Emission factors},
  year = {2025},
  url = {https://example.org/factors.pdf},
  access = {regulation}
}

@book{sharealike2019,
  author = {Roe, Richard},
  title = {A share-alike handbook},
  publisher = {Open Press},
  year = {2019},
  doi = {10.1000/sa2019},
  access = {open},
  licence = {CC-BY-SA-4.0}
}
"""


def row(
    row_id: str,
    *,
    value: Any = 1.0,
    role: str = "model_constant",
    citation: str = "doe2020",
    verification: str = "UNVERIFIED",
    symbol: str = "minephys.demo.f",
    units: str = "1",
    page: str = "p. 1",
) -> dict[str, Any]:
    """One valid knowledge-table row (DC-000-02)."""
    out: dict[str, Any] = {
        "id": row_id,
        "quantity": f"quantity of {row_id}",
        "value": value,
        "units": units,
        "role": role,
        "citation": citation,
        "page": page,
        "verification": verification,
        "symbol": symbol,
    }
    if verification == "verified":
        out["verified_on"] = "2026-10-06"
    return out


def table(name: str, rows: list[dict[str, Any]], *, licence: str = "CC-BY-4.0") -> dict[str, Any]:
    return {"schema_version": 1, "table": name, "title": f"{name} table", "licence": licence, "rows": rows}


def write_repo(
    root: Path,
    *,
    tables: dict[str, dict[str, Any]] | None = None,
    share_alike_tables: dict[str, dict[str, Any]] | None = None,
    bib: str = GOOD_BIB,
    src_files: dict[str, str] | None = None,
    test_files: dict[str, str] | None = None,
) -> Path:
    """Write `src/minephys/knowledge/*.yaml`, `references.bib`, source files and test files under `root`.

    `src_files` and `test_files` map a path relative to `src/minephys/` and `tests/` to its text.
    """
    kdir = root / "src" / "minephys" / "knowledge"
    kdir.mkdir(parents=True, exist_ok=True)
    (root / "src" / "minephys" / "__init__.py").write_text("__all__: list[str] = []\n", encoding="utf-8")
    for stem, doc in (tables or {}).items():
        (kdir / f"{stem}.yaml").write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    if share_alike_tables:
        sdir = kdir / "share-alike"
        sdir.mkdir(parents=True, exist_ok=True)
        for stem, doc in share_alike_tables.items():
            (sdir / f"{stem}.yaml").write_text(
                yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8"
            )
    (kdir / "references.bib").write_text(bib, encoding="utf-8")
    for rel, text in (src_files or {}).items():
        p = root / "src" / "minephys" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    for rel, text in (test_files or {}).items():
        p = root / "tests" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root


def run_tool(
    script: str, *args: str, cwd: Path | None = None, timeout: float = 120.0
) -> subprocess.CompletedProcess[str]:
    """Run `python tools/<script> <args>` from the real repository and capture text output."""
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd or REPO_ROOT),
        timeout=timeout,
        check=False,
    )

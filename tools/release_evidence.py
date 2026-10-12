"""Release evidence report: knowledge honesty and portability summary (spec 000 SC-000-03, SC-000-04).

Usage:  python tools/release_evidence.py [--root PATH] --matrix FILE [--json]
`--matrix` is the JSON written by the CI matrix: {"smoke": {"<runtime>": "pass" | "fail" | "not_run", ...}}.
Exit 0 when the report is ok, 1 when it is not, 2 for usage errors (the offending path is named, no traceback).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import _knowledge_io as kio

HERE = Path(__file__).resolve().parents[1]
REQUIRED = ["3.12", "3.13", "3.14", "wheel", "pyodide"]
STATUSES = ("pass", "fail", "not_run")


def load_matrix(path: Path) -> dict[str, str]:
    """The smoke mapping of the matrix file; ValueError carries a message naming the file."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except OSError as err:
        raise ValueError(f"{path}: cannot read the matrix: {err.strerror}") from None
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ValueError(f"{path}: not valid JSON: {err}") from None
    smoke = doc.get("smoke") if isinstance(doc, dict) else None
    if not isinstance(smoke, dict):
        raise ValueError(f"{path}: the matrix must be an object with a 'smoke' mapping")
    for runtime, status in smoke.items():
        if status not in STATUSES:
            raise ValueError(f"{path}: runtime {runtime!r} has status {status!r}; expected one of {', '.join(STATUSES)}")
    return smoke


def honesty(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for tf in kio.table_files(root):
        rows.extend(kio.rows_of(kio.read_table(tf)))
    unverified_parameters = {r["id"] for r in rows if r.get("role") == "parameter" and r.get("verification") != "verified"}
    defaults = [
        {"function": name, "row": word}
        for _, name, words in kio.knowledge_rows_of_functions(root)
        for word in dict.fromkeys(words)
        if word in unverified_parameters
    ]
    verified = [r["id"] for r in rows if r.get("verification") == "verified"]
    pinned = kio.pinned_rows(root)
    unpinned = [i for i in verified if i not in pinned]
    done = len(verified) - len(unpinned)
    pct = 100.0 if not verified else 100.0 * done / len(verified)
    return {
        "unverified_parameter_defaults": defaults,
        "verified_rows": len(verified),
        "verified_rows_pinned": done,
        "pinned_pct": pct,
        "unpinned": unpinned,
    }


def portability(smoke: dict[str, str]) -> dict[str, Any]:
    return {
        "required": REQUIRED,
        "passed": [r for r in REQUIRED if smoke.get(r) == "pass"],
        "failed": [r for r in REQUIRED if smoke.get(r) == "fail"],
        "missing": [r for r in REQUIRED if smoke.get(r) not in ("pass", "fail")],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=HERE)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)
    try:
        smoke = load_matrix(args.matrix)
    except ValueError as err:
        print(str(err), file=sys.stderr)
        return 2
    h, p = honesty(args.root), portability(smoke)
    ok = not h["unverified_parameter_defaults"] and not h["unpinned"] and not p["failed"] and not p["missing"]
    report = {"honesty": h, "portability": p, "ok": ok}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"honesty: {h['verified_rows_pinned']}/{h['verified_rows']} verified rows pinned ({h['pinned_pct']:.1f} %)")
        for d in h["unverified_parameter_defaults"]:
            print(f"  UNVERIFIED parameter {d['row']} listed by {d['function']}")
        print(f"portability: passed {p['passed']}, failed {p['failed']}, missing {p['missing']}")
        print("OK" if ok else "NOT OK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

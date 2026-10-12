"""Oracle-marker inventory and report (spec 000 FR-000-33, SC-000-02).

Usage:  python tools/oracle_inventory.py [--root PATH] [--json] [--strict] [--release]
Scans `<root>/tests/**/*.py` with the AST (a test is a function named `test_*` at module level or in a class; a
parametrised test counts once) and reports, as one JSON object with `--json`:
  tests, kinds (counts of analytical, worked-example, reference-implementation, hand-calculation), unmarked (a `req`
  marker but no `oracle` marker), violations ({test, message}), functions (exported model functions with their test
  counts) and uncovered (functions with no test carrying a non-hand-calculation oracle and no documented exception).
Rules (FR-000-33): `@pytest.mark.oracle(kind, reference)` takes two positional string literals; `kind` is one of the
four kinds and `reference` is non-empty; for a worked example it reads `<BibTeX key> <page locator>` and the key
exists in `<root>/src/minephys/knowledge/references.bib`. A violation makes the exit status 1; unmarked tests do so
only with `--strict`; a non-empty `uncovered` only with `--release` (SC-000-02). Exceptions are documented in
`<root>/specs/000-foundation/oracle-exceptions.yaml` as `function: reason`.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

import _knowledge_io as kio
import yaml

HERE = Path(__file__).resolve().parents[1]
KINDS = ("analytical", "worked-example", "reference-implementation", "hand-calculation")


def marker_calls(node: ast.FunctionDef | ast.AsyncFunctionDef, name: str) -> list[ast.Call]:
    return [
        d
        for d in node.decorator_list
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == name
    ]


def check_oracle(call: ast.Call, keys: set[str]) -> tuple[str | None, list[str]]:
    """The kind of a well-formed oracle marker (None if unusable) and the messages of its defects."""
    if call.keywords:
        return None, ["oracle arguments must be positional (kind, reference); keyword arguments are not audited"]
    if len(call.args) > 2:
        return None, [f"wrong number of arguments: {len(call.args)} given, expected kind and reference"]
    args = []
    for a in call.args:
        if not (isinstance(a, ast.Constant) and isinstance(a.value, str)):
            return None, ["the arguments of an oracle marker must be string literals (a non-literal cannot be audited)"]
        args.append(a.value)
    if not args:
        return None, ["oracle marker without kind and reference"]
    kind = args[0]
    problems: list[str] = []
    if kind not in KINDS:
        problems.append(f"unknown oracle kind {kind!r}; the kinds are {', '.join(KINDS)}")
    if len(args) < 2:
        problems.append("oracle marker without a reference")
    elif not args[1].strip():
        problems.append("oracle reference is empty")
    elif kind == "worked-example":
        parts = args[1].split(None, 1)
        if not kio.BIB_KEY.match(parts[0]):
            problems.append(f"worked-example reference must read '<BibTeX key> <page locator>', got {args[1]!r}")
        elif len(parts) < 2:
            problems.append(f"worked-example reference names only the key {parts[0]!r}: a page locator is required")
        elif parts[0] not in keys:
            problems.append(f"worked-example reference: unknown BibTeX key {parts[0]!r} (not in references.bib)")
    return (kind if not problems else None), problems


def referenced_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            names.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            names.add(sub.attr)
    return names


def exported_functions(root: Path) -> list[str]:
    """Function-like names (lower case) of the `__all__` of every `src/minephys/<sub>/__init__.py`."""
    base = root / "src" / "minephys"
    found: set[str] = set()
    if base.is_dir():
        for init in sorted(base.glob("*/__init__.py")):
            if init.parent.name.startswith("_"):
                continue
            names = kio.exported_names(root, init.parent.name) or set()
            found |= {n for n in names if re.fullmatch(r"[a-z][a-z0-9_]*", n)}
    return sorted(found)


def inventory(root: Path) -> dict[str, Any]:
    keys = set(kio.read_bibliography(root)[0])
    functions = {name: {"tests": 0, "non_hand_calculation": 0} for name in exported_functions(root)}
    kinds = dict.fromkeys(KINDS, 0)
    unmarked: list[str] = []
    violations: list[dict[str, str]] = []
    total = 0
    tests_dir = root / "tests"
    for path in sorted(tests_dir.rglob("*.py")) if tests_dir.is_dir() else []:
        rel = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, ValueError) as err:
            violations.append({"test": rel, "message": f"{rel}: cannot be parsed: {err}"})
            continue
        stack: list[tuple[str, ast.AST]] = [("", tree)]
        while stack:
            prefix, parent = stack.pop(0)
            for node in ast.iter_child_nodes(parent):
                if isinstance(node, ast.ClassDef):
                    stack.append((f"{prefix}{node.name}::", node))
                elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test_"):
                    total += 1
                    test_id = f"{rel}::{prefix}{node.name}"
                    good_kinds: list[str] = []
                    oracles = marker_calls(node, "oracle")
                    for call in oracles:
                        kind, problems = check_oracle(call, keys)
                        violations += [{"test": test_id, "message": m} for m in problems]
                        if kind:
                            kinds[kind] += 1
                            good_kinds.append(kind)
                    if marker_calls(node, "req") and not oracles:
                        unmarked.append(test_id)
                    used = referenced_names(node)
                    for name, counts in functions.items():
                        if name in used:
                            counts["tests"] += 1
                            if any(k != "hand-calculation" for k in good_kinds):
                                counts["non_hand_calculation"] += 1
    exceptions = _exceptions(root)
    uncovered = sorted(n for n, c in functions.items() if c["non_hand_calculation"] == 0 and not exceptions.get(n))
    return {
        "tests": total,
        "kinds": kinds,
        "unmarked": unmarked,
        "violations": violations,
        "functions": functions,
        "uncovered": uncovered,
    }


def _exceptions(root: Path) -> dict[str, str]:
    path = root / "specs" / "000-foundation" / "oracle-exceptions.yaml"
    if not path.is_file():
        return {}
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError, OSError):
        return {}
    if not isinstance(doc, dict):
        return {}
    return {str(k): v for k, v in doc.items() if isinstance(v, str) and v.strip()}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=HERE)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="unmarked tests are violations")
    ap.add_argument("--release", action="store_true", help="uncovered functions are violations")
    args = ap.parse_args(argv[1:])
    report = inventory(args.root.resolve())
    failed = bool(report["violations"]) or (args.strict and bool(report["unmarked"]))
    failed = failed or (args.release and bool(report["uncovered"]))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"tests {report['tests']}; oracle kinds {report['kinds']}")
        for label in ("violations", "unmarked", "uncovered"):
            for item in report[label]:
                print(f"{label}: {item if isinstance(item, str) else item['test'] + ': ' + item['message']}")
    if report["violations"] and args.json:
        for item in report["violations"]:
            print(f"{item['test']}: {item['message']}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

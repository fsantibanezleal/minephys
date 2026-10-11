"""T-000-013 (FR-000-19): literal audit with `tools/literal_allowlist.txt`.

Expected deliverable: `tools/literal_allowlist.txt`, one entry per non-blank line that is not a `#` comment, in the
form `<literal> | <one-line reason>` where `<literal>` is a Python numeric literal (for example `0.5`, `1e-12`). The
audit below fails on

* a missing allowlist, an entry without a reason, an unparsable or duplicated literal;
* an entry outside the four permitted categories (spec 000 FR-000-19): a structural constant of a formula (a small
  exact integer or simple fraction: p/q with |p| <= 10 and 1 <= q <= 10), a decimal SI prefix (10**k, k in
  {-24, -21, ..., -3, -2, -1, 1, 2, 3, ..., 24}), an exact mathematical constant (pi, e, sqrt 2 and rational multiples
  p/q of them with |p| <= 10, q <= 10, equal to float64 rounding), or a numerical tolerance or tiny guard
  (0 < v <= 1e-6);
* an entry equal to a physical or empirical constant of the specs (9.80665, 0.0254, 0.3048, 0.45359237, 3.6e6, 10.21,
  3.785411784e-3, 0.06, 0.025, 0.693, 0.72, 0.91, 0.47, 0.94, 0.015, 115, 260, 2.2, ...): those live in knowledge rows;
* any floating-point literal under `src/minephys/` that is not listed (an AST audit; integer literals are not audited).

Oracle: hand-written rules and constants of FR-000-19 (hand calculation); the AST of the real source tree; fixture
sources for the failure branches of the auditor.
"""

# ruff: noqa: PERF401
from __future__ import annotations

import ast
import math
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = ROOT / "tools" / "literal_allowlist.txt"
SRC = ROOT / "src" / "minephys"

PHYSICAL = [
    9.80665,
    9.81,
    0.0254,
    0.3048,
    0.45359237,
    3.6e6,
    10.21,
    3.785411784e-3,
    0.06,
    0.025,
    0.693,
    0.72,
    0.91,
    0.47,
    0.94,
    0.015,
    115.0,
    260.0,
    2.2,
    0.8,
    0.35,
]


def parse_allowlist(text: str) -> tuple[list[float], list[str]]:
    values: list[float] = []
    errors: list[str] = []
    for n, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            errors.append(f"line {n}: no '|' separating the literal from its reason")
            continue
        lit, reason = (p.strip() for p in line.split("|", 1))
        if not reason:
            errors.append(f"line {n}: empty reason for {lit!r}")
        try:
            tree = ast.parse(lit, mode="eval").body
            v = float(ast.literal_eval(tree))
        except (SyntaxError, ValueError):
            errors.append(f"line {n}: {lit!r} is not a numeric literal")
            continue
        if v in values:
            errors.append(f"line {n}: duplicate literal {lit!r}")
        values.append(v)
    return values, errors


def _is_simple_fraction(v: float) -> bool:
    f = Fraction(v).limit_denominator(10)
    return abs(f.numerator) <= 10 and f.denominator <= 10 and math.isclose(float(f), v, rel_tol=1e-15, abs_tol=0.0)


def category(v: float) -> str | None:
    if v == 0.0 or _is_simple_fraction(v):
        return "structural"
    a = abs(v)
    if a > 0 and any(math.isclose(a, 10.0**k, rel_tol=1e-15) for k in [*range(-24, 25, 3), -2, -1, 1, 2]):
        return "si-prefix"
    for const in (math.pi, math.e, math.sqrt(2.0)):
        for p in range(1, 11):
            for q in range(1, 11):
                if math.isclose(a, const * p / q, rel_tol=4e-16, abs_tol=0.0):
                    return "math-constant"
    if 0.0 < a <= 1e-6:
        return "tolerance"
    return None


def audit_source(text: str, allowed: set[float]) -> list[tuple[int, float]]:
    """Float literals of one module that are not allowlisted (line, value)."""
    bad: list[tuple[int, float]] = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Constant) and isinstance(node.value, float) and node.value not in allowed:
            bad.append((node.lineno, node.value))
    return bad


# ------------------------------------------------------------ the auditor on fixtures (hand-written)


@pytest.mark.req("FR-000-19")
@pytest.mark.oracle("hand-calculation", "FR-000-19 categories on hand-picked members and non-members")
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.0, "structural"),
        (0.5, "structural"),
        (2.0, "structural"),
        (0.25, "structural"),
        (1e-10, "tolerance"),
        (1e-300, "tolerance"),
        (1e-12, "si-prefix"),
        (1e3, "si-prefix"),
        (1e-3, "si-prefix"),
        (0.01, "si-prefix"),
        (math.pi, "math-constant"),
        (math.pi / 2, "math-constant"),
        (2 * math.pi, "math-constant"),
        (math.e, "math-constant"),
        (math.sqrt(2.0), "math-constant"),
        (9.80665, None),
        (0.0254, None),
        (0.3048, None),
        (3.6e6, None),
        (10.21, None),
        (0.015, None),
        (0.72, None),
        (2.2, None),
        (115.0, None),
        (0.693, None),
    ],
)
def test_category_rule(value: float, expected: str | None) -> None:
    assert category(value) == expected


@pytest.mark.req("FR-000-19")
@pytest.mark.oracle("hand-calculation", "the AST audit reports exactly the unlisted float literals")
def test_ast_audit_on_a_fixture_module() -> None:
    src = "import math\nA = 0.5\nB = 9.80665 * 2.0\nC = [1e-12, 3, 1.0]\n"
    assert audit_source(src, {0.5, 1e-12}) == [(3, 9.80665), (3, 2.0), (4, 1.0)]
    assert audit_source(src, {0.5, 1e-12, 9.80665, 2.0, 1.0}) == []
    assert audit_source("x = 100\ny = 'a 1.5 inside a string'\n", set()) == []


@pytest.mark.req("FR-000-19")
@pytest.mark.oracle("hand-calculation", "allowlist grammar: literal | reason")
def test_allowlist_parser_reports_malformed_lines() -> None:
    text = "# comment\n0.5 | structural half\n1e-12 |\nabc | not a number\n0.5 | duplicate\n9.80665\n"
    values, errors = parse_allowlist(text)
    assert values == [0.5, 1e-12, 0.5]
    assert len(errors) == 4
    assert any("empty reason" in e for e in errors)
    assert any("not a numeric literal" in e for e in errors)
    assert any("duplicate" in e for e in errors)
    assert any("no '|'" in e for e in errors)


# ------------------------------------------------------------ the real allowlist and source tree


@pytest.mark.req("FR-000-19")
@pytest.mark.oracle("hand-calculation", "FR-000-19: an allowlist exists and is well formed")
def test_allowlist_exists_and_is_well_formed() -> None:
    assert ALLOWLIST.is_file(), "missing tools/literal_allowlist.txt"
    values, errors = parse_allowlist(ALLOWLIST.read_text(encoding="utf-8"))
    assert errors == []
    assert values, "the allowlist is empty; at least the structural constants of the formulas are expected"


@pytest.mark.req("FR-000-19")
@pytest.mark.oracle("hand-calculation", "FR-000-19: only the four permitted categories may be listed")
def test_every_allowlist_entry_is_in_a_permitted_category() -> None:
    assert ALLOWLIST.is_file(), "missing tools/literal_allowlist.txt"
    values, _ = parse_allowlist(ALLOWLIST.read_text(encoding="utf-8"))
    outside = [v for v in values if category(v) is None]
    assert outside == [], f"entries outside the permitted categories: {outside}"


@pytest.mark.req("FR-000-19")
@pytest.mark.oracle("hand-calculation", "physical and empirical constants are knowledge rows, never allowlisted")
def test_no_physical_constant_is_allowlisted() -> None:
    assert ALLOWLIST.is_file(), "missing tools/literal_allowlist.txt"
    values, _ = parse_allowlist(ALLOWLIST.read_text(encoding="utf-8"))
    banned = [v for v in values if any(math.isclose(v, p, rel_tol=1e-12) for p in PHYSICAL)]
    assert banned == []


@pytest.mark.req("FR-000-19")
@pytest.mark.oracle("hand-calculation", "FR-000-19: the model code holds no unlisted floating-point literal")
def test_source_tree_has_no_unlisted_float_literals() -> None:
    assert ALLOWLIST.is_file(), "missing tools/literal_allowlist.txt"
    values, errors = parse_allowlist(ALLOWLIST.read_text(encoding="utf-8"))
    assert errors == []
    allowed = set(values)
    offenders: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        for line, value in audit_source(path.read_text(encoding="utf-8"), allowed):
            offenders.append(f"{path.relative_to(ROOT).as_posix()}:{line}: {value!r}")
    assert offenders == [], "unlisted floating-point literals:\n" + "\n".join(offenders)

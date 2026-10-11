"""T-007-053 (NFR-007-04, FR-000-08, FR-000-09): every public function of `minephys.planning` has a model card.

Expected: every function exported in `minephys.planning.__all__` has a numpydoc docstring with the sections `Parameters`, `Returns`,
`Equation`, `Source`, `Validity` and `Knowledge rows`, where
- `Parameters` names every parameter of the signature as `name : type [unit]` (flags, patterns and options need no unit but must be
  named) and `Returns` states the unit of the result in square brackets (or "dimensionless");
- `Source` cites at least one key of `knowledge/references.bib` and a locator;
- `Validity` is non-empty; for `ultimate_pit_mincut`, `nested_pits` and `regular_grid_precedence` it states the instance-size limits
  (100,000 blocks, 2,000,000 arcs) and for `ultimate_pit_mincut` the oracle used in the tests (exhaustive enumeration and networkx);
- `Knowledge rows` is `none`: the planning models have no published constants and ship no knowledge table (spec 007 section 7).
A numpydoc section is a title line followed by a line of dashes. This is the module's own check; the repository-wide audit is
foundation task T-000-012.

Oracle: hand-written rules of FR-000-08/09 and NFR-007-04.
"""

from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BIB = ROOT / "src" / "minephys" / "knowledge" / "references.bib"
SECTIONS = ["Parameters", "Returns", "Equation", "Source", "Validity", "Knowledge rows"]
EXPECTED = [
    "block_economic_value",
    "breakeven_cutoff_grade",
    "regular_grid_precedence",
    "ultimate_pit_mincut",
    "nested_pits",
    "strip_ratio",
    "npv",
    "schedule_npv",
    "lane_cutoff_grades",
]


def _functions() -> dict[str, object]:
    m = importlib.import_module("minephys.planning")
    assert getattr(m, "__all__", None), "minephys.planning must define __all__"
    return {n: getattr(m, n) for n in m.__all__ if inspect.isfunction(getattr(m, n))}


def _sections(doc: str) -> dict[str, str]:
    lines = doc.splitlines()
    out: dict[str, str] = {}
    current: str | None = None
    for i, line in enumerate(lines):
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if line.strip() and re.fullmatch(r"-{3,}", nxt):
            current = line.strip()
            out[current] = ""
        elif re.fullmatch(r"-{3,}", line.strip()):
            continue
        elif current is not None:
            out[current] += line + "\n"
    return out


def _bib_keys() -> set[str]:
    assert BIB.is_file(), "missing src/minephys/knowledge/references.bib"
    return set(re.findall(r"(?m)^@\w+\{([^,\s]+),", BIB.read_text(encoding="utf-8")))


@pytest.mark.req("NFR-007-04")
@pytest.mark.oracle("hand-calculation", "FR-000-09 section list")
def test_nfr_007_04_every_function_has_the_model_card_sections() -> None:
    funcs = _functions()
    assert set(EXPECTED) <= set(funcs), f"missing exports: {sorted(set(EXPECTED) - set(funcs))}"
    for name, fn in funcs.items():
        missing = [s for s in SECTIONS if s not in _sections(inspect.getdoc(fn) or "")]
        assert not missing, f"{name}: missing sections {missing}"


@pytest.mark.req("NFR-007-04")
@pytest.mark.req("FR-000-08")
def test_nfr_007_04_every_parameter_is_documented_with_a_unit() -> None:
    for name, fn in _functions().items():
        secs = _sections(inspect.getdoc(fn) or "")
        params = secs.get("Parameters", "")
        for p in inspect.signature(fn).parameters:
            assert re.search(rf"(?m)^\s*{re.escape(p)}\s*:\s*(.+)$", params), f"{name}: parameter {p} is not documented"
        assert re.search(r"\[[^\]]+\]", params), f"{name}: no unit in square brackets in Parameters"
        assert re.search(r"\[[^\]]+\]|dimensionless|fraction|mask|boolean|arc", secs.get("Returns", ""), re.I), f"{name}: Returns states no unit"


@pytest.mark.req("NFR-007-04")
def test_nfr_007_04_source_cites_a_bibliography_key_and_a_locator() -> None:
    funcs = _functions()
    keys = _bib_keys()
    for name, fn in funcs.items():
        source = _sections(inspect.getdoc(fn) or "").get("Source", "")
        assert any(k in source for k in keys) or re.search(r"derived|hand calculation|definition", source, re.I), f"{name}: Source cites no key of references.bib"
        assert source.strip(), f"{name}: empty Source"


@pytest.mark.req("NFR-007-04")
def test_nfr_007_04_validity_states_the_instance_size_limits_and_the_test_oracle() -> None:
    funcs = _functions()
    for name in ("ultimate_pit_mincut", "nested_pits", "regular_grid_precedence"):
        validity = _sections(inspect.getdoc(funcs[name]) or "")["Validity"]
        assert re.search(r"100,?000|10\^5|1e5|10⁵", validity), f"{name}: the 100,000-block limit is not stated"
    validity = _sections(inspect.getdoc(funcs["ultimate_pit_mincut"]) or "")["Validity"]
    assert re.search(r"2,?000,?000|2e6|2 x 10\^6", validity), "the 2,000,000-arc limit is not stated"
    assert re.search(r"networkx|enumeration", validity, re.I), "the oracle used in the tests is not named"
    for name, fn in funcs.items():
        assert _sections(inspect.getdoc(fn) or "")["Validity"].strip(), f"{name}: empty Validity"


@pytest.mark.req("NFR-007-04")
def test_nfr_007_04_knowledge_rows_section_is_none() -> None:
    for name, fn in _functions().items():
        text = _sections(inspect.getdoc(fn) or "").get("Knowledge rows", "")
        assert re.search(r"\bnone\b", text, re.I), f"{name}: planning models read no knowledge row, the section must say 'none'"

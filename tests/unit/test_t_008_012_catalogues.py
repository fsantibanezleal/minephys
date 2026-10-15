"""T-008-012 (FR-008-04): equation and glossary catalogue rules.

Expected public API (`minephys.knowledge`):
    equations(domain=None) -> tuple of frozen `Equation` (id, title, domain, latex, symbols, function, citation, page, verification,
                              verified_on, rows, notes; `symbols` a tuple of mappings with symbol, meaning, units)
    glossary(domain=None)  -> tuple of frozen `Term` (id, domain, term_en, term_es, definition_en, definition_es, citation, see_also)
    validate_tables(folder).errors for the catalogue files `catalogue/equations.yaml` and `catalogue/glossary.yaml` (`file` ending in the
    file name, `index` the 1-based entry number, `field` the offending field, as in tests/unit/test_t_008_010_tables.py).
Rules: spec 008 section 7 (DC-008-01 and DC-008-02), exactly the rules of the JSON Schemas of `contracts/`: the equation fields
(`id` identifier, `title`, `domain` among the seven module domains, `latex` non-empty, `symbols` list >= 1 of {symbol, meaning, units},
`function` dotted path `minephys.<module>.<name>`, `citation`, `page`, `verification`, `verified_on` exactly when verified, optional
`rows` and `notes`); the glossary fields (`id`, `domain` among the seven or `general`, `term_en`, `term_es`, `definition_en`,
`definition_es` non-empty and at most 1,000 characters, optional `citation` and `see_also`).

Oracles: hand-written valid catalogues and one-mutation catalogues, each with the expected (file, index, field).
"""

from __future__ import annotations

import copy
import importlib
from pathlib import Path
from typing import Any

import _knowledge_fixtures as fx
import pytest


def _k():
    return importlib.import_module("minephys.knowledge")


def _errors(tmp_path: Path, **kw: Any):
    return list(_k().validate_tables(fx.write_tree(tmp_path / "k", **kw)).errors)


def _on(errors, stem: str, field=None, index=...):
    out = []
    for e in errors:
        if not str(e.file).replace("\\", "/").endswith(f"{stem}.yaml"):
            continue
        if field is not None and e.field not in (field if isinstance(field, tuple) else (field,)):
            continue
        if index is not ... and e.index != index:
            continue
        out.append(e)
    return out


def _eq(index: int, **over: Any):
    def mutate(doc: dict[str, Any]) -> None:
        for k, v in over.items():
            if v is fx.DROP:
                doc["equations"][index].pop(k, None)
            else:
                doc["equations"][index][k] = v

    return mutate


def _term(index: int, **over: Any):
    def mutate(doc: dict[str, Any]) -> None:
        for k, v in over.items():
            if v is fx.DROP:
                doc["terms"][index].pop(k, None)
            else:
                doc["terms"][index][k] = v

    return mutate


EQ_CASES: list[tuple[str, Any, int, tuple[str, ...]]] = [
    ("missing-id", _eq(1, id=fx.DROP), 2, ("id",)),
    ("missing-title", _eq(1, title=fx.DROP), 2, ("title",)),
    ("missing-domain", _eq(1, domain=fx.DROP), 2, ("domain",)),
    ("missing-latex", _eq(1, latex=fx.DROP), 2, ("latex",)),
    ("missing-symbols", _eq(1, symbols=fx.DROP), 2, ("symbols",)),
    ("missing-function", _eq(1, function=fx.DROP), 2, ("function",)),
    ("missing-citation", _eq(1, citation=fx.DROP), 2, ("citation",)),
    ("missing-page", _eq(1, page=fx.DROP), 2, ("page",)),
    ("missing-verification", _eq(1, verification=fx.DROP), 2, ("verification",)),
    ("unknown-field", _eq(0, color="red"), 1, ("color",)),
    ("unknown-domain", _eq(1, domain="astrology"), 2, ("domain",)),
    ("general-is-not-an-equation-domain", _eq(1, domain="general"), 2, ("domain",)),
    ("empty-latex", _eq(0, latex=""), 1, ("latex",)),
    ("latex-too-long", _eq(0, latex="x" * 2001), 1, ("latex",)),
    ("empty-symbols", _eq(0, symbols=[]), 1, ("symbols",)),
    ("symbol-without-units", _eq(0, symbols=[{"symbol": "m", "meaning": "mass"}]), 1, ("units", "symbols")),
    ("symbol-units-na", _eq(0, symbols=[{"symbol": "m", "meaning": "mass", "units": "n/a"}]), 1, ("units", "symbols")),
    (
        "symbol-unknown-key",
        _eq(0, symbols=[{"symbol": "m", "meaning": "mass", "units": "kg", "extra": 1}]),
        1,
        ("extra", "symbols"),
    ),
    ("function-not-dotted", _eq(0, function="co2_from_diesel"), 1, ("function",)),
    ("function-wrong-root", _eq(0, function="haulage.co2"), 1, ("function",)),
    ("verified-without-date", _eq(0, verified_on=fx.DROP), 1, ("verified_on",)),
    ("unverified-with-date", _eq(1, verified_on="2026-10-06"), 2, ("verified_on",)),
    ("bad-verification", _eq(1, verification="maybe"), 2, ("verification",)),
    ("bad-date", _eq(0, verified_on="2026-02-45"), 1, ("verified_on",)),
    ("rows-empty", _eq(0, rows=[]), 1, ("rows",)),
    ("rows-duplicate", _eq(0, rows=["diesel_co2_factor", "diesel_co2_factor"]), 1, ("rows",)),
    ("rows-bad-id", _eq(0, rows=["Bad Row"]), 1, ("rows",)),
    ("id-bad-pattern", _eq(1, id="Powder-Factor"), 2, ("id",)),
    ("page-padded", _eq(1, page=" p. 12"), 2, ("page",)),
    ("notes-empty", _eq(1, notes=""), 2, ("notes",)),
]
EQ_TOP = [
    ("schema-version", {"schema_version": 2}, ("schema_version",)),
    ("licence-share-alike", {"licence": "CC-BY-SA-4.0"}, ("licence",)),
    ("licence-missing", {"licence": fx.DROP}, ("licence",)),
    ("title-missing", {"title": fx.DROP}, ("title",)),
    ("equations-empty", {"equations": []}, ("equations",)),
    ("equations-missing", {"equations": fx.DROP}, ("equations",)),
    ("unknown-top-field", {"extra": 1}, ("extra",)),
]
GL_CASES: list[tuple[str, Any, int, tuple[str, ...]]] = [
    ("missing-id", _term(1, id=fx.DROP), 2, ("id",)),
    ("missing-domain", _term(1, domain=fx.DROP), 2, ("domain",)),
    ("missing-term-en", _term(1, term_en=fx.DROP), 2, ("term_en",)),
    ("missing-term-es", _term(1, term_es=fx.DROP), 2, ("term_es",)),
    ("missing-definition-en", _term(1, definition_en=fx.DROP), 2, ("definition_en",)),
    ("missing-definition-es", _term(1, definition_es=fx.DROP), 2, ("definition_es",)),
    ("unknown-field", _term(0, color="red"), 1, ("color",)),
    ("unknown-domain", _term(1, domain="astrology"), 2, ("domain",)),
    ("blank-term", _term(1, term_en="   "), 2, ("term_en",)),
    ("padded-term", _term(1, term_es=" banco"), 2, ("term_es",)),
    ("multi-line-term", _term(1, term_en="two\nlines"), 2, ("term_en",)),
    ("empty-definition", _term(1, definition_es=""), 2, ("definition_es",)),
    ("definition-too-long", _term(1, definition_en="d" * 1001), 2, ("definition_en",)),
    ("see-also-empty", _term(0, see_also=[]), 1, ("see_also",)),
    ("see-also-duplicate", _term(0, see_also=["bench", "bench"]), 1, ("see_also",)),
    ("see-also-too-many", _term(0, see_also=[f"t_{i}" for i in range(17)]), 1, ("see_also",)),
    ("see-also-bad-id", _term(0, see_also=["Bad Id"]), 1, ("see_also",)),
    ("citation-bad-pattern", _term(0, citation="Bad Key"), 1, ("citation",)),
    ("id-bad-pattern", _term(1, id="Bad-Id"), 2, ("id",)),
]
GL_TOP = [
    ("schema-version", {"schema_version": 0}, ("schema_version",)),
    ("licence-wrong", {"licence": "MIT"}, ("licence",)),
    ("title-missing", {"title": fx.DROP}, ("title",)),
    ("terms-empty", {"terms": []}, ("terms",)),
    ("terms-missing", {"terms": fx.DROP}, ("terms",)),
    ("unknown-top-field", {"extra": 1}, ("extra",)),
]


@pytest.mark.req("FR-008-04")
@pytest.mark.oracle("hand-calculation", "the valid fixture catalogues load without error")
def test_fr_008_04_valid_catalogues_validate_cleanly(tmp_path: Path) -> None:
    assert _errors(tmp_path) == []


@pytest.mark.req("FR-008-04")
@pytest.mark.oracle("hand-calculation", "one DC-008-01 rule broken per equation entry")
@pytest.mark.parametrize(("name", "mutate", "index", "fields"), EQ_CASES, ids=[c[0] for c in EQ_CASES])
def test_fr_008_04_equation_rule_violations(
    tmp_path: Path, name: str, mutate: Any, index: int, fields: tuple[str, ...]
) -> None:
    doc = fx.good_equations()
    mutate(doc)
    errors = _errors(tmp_path, equations=doc)
    assert _on(errors, "equations", fields, index), [(str(e.file), e.index, e.field) for e in errors]


@pytest.mark.req("FR-008-04")
@pytest.mark.parametrize(("name", "over", "fields"), EQ_TOP, ids=[c[0] for c in EQ_TOP])
def test_fr_008_04_equation_file_violations(
    tmp_path: Path, name: str, over: dict[str, Any], fields: tuple[str, ...]
) -> None:
    doc = fx.good_equations()
    for k, v in over.items():
        if v is fx.DROP:
            doc.pop(k, None)
        else:
            doc[k] = v
    errors = _errors(tmp_path, equations=doc)
    assert _on(errors, "equations", fields), [(str(e.file), e.index, e.field) for e in errors]


@pytest.mark.req("FR-008-04")
@pytest.mark.oracle("hand-calculation", "one DC-008-02 rule broken per glossary term")
@pytest.mark.parametrize(("name", "mutate", "index", "fields"), GL_CASES, ids=[c[0] for c in GL_CASES])
def test_fr_008_04_glossary_rule_violations(
    tmp_path: Path, name: str, mutate: Any, index: int, fields: tuple[str, ...]
) -> None:
    doc = fx.good_glossary()
    mutate(doc)
    errors = _errors(tmp_path, glossary=doc)
    assert _on(errors, "glossary", fields, index), [(str(e.file), e.index, e.field) for e in errors]


@pytest.mark.req("FR-008-04")
@pytest.mark.parametrize(("name", "over", "fields"), GL_TOP, ids=[c[0] for c in GL_TOP])
def test_fr_008_04_glossary_file_violations(
    tmp_path: Path, name: str, over: dict[str, Any], fields: tuple[str, ...]
) -> None:
    doc = fx.good_glossary()
    for k, v in over.items():
        if v is fx.DROP:
            doc.pop(k, None)
        else:
            doc[k] = v
    errors = _errors(tmp_path, glossary=doc)
    assert _on(errors, "glossary", fields), [(str(e.file), e.index, e.field) for e in errors]


@pytest.mark.req("FR-008-04")
@pytest.mark.oracle(
    "hand-calculation", "boundary values that are valid: 1,000-character definitions, 16 see_also ids, every domain"
)
def test_fr_008_04_valid_boundaries(tmp_path: Path) -> None:
    eq = fx.good_equations()
    for i, domain in enumerate(("haulage", "blasting", "geotech", "bulk", "comminution", "environment", "planning")):
        e = copy.deepcopy(eq["equations"][1])
        e["id"] = f"eq_domain_{i}"
        e["domain"] = domain
        eq["equations"].append(e)
    eq["equations"][1]["latex"] = "x" * 2000
    gl = fx.good_glossary()
    gl["terms"][1]["definition_es"] = "\u00e1" * 1000  # the cap, in characters (accents count once)
    gl["terms"].extend(dict(copy.deepcopy(gl["terms"][2]), id=f"t_{i}") for i in range(1, 16))
    gl["terms"][0]["see_also"] = ["bench"] + [f"t_{i}" for i in range(1, 16)]  # 16 ids, the cap
    assert _errors(tmp_path, equations=eq, glossary=gl) == []


@pytest.mark.req("FR-008-04")
@pytest.mark.oracle(
    "hand-calculation", "loader output for the fixture catalogues: counts, filters, immutability, Spanish accents"
)
def test_fr_008_04_loader_returns_the_catalogues(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg")
    got = fx.run_api(
        base,
        """
import dataclasses
eqs, gls = K.equations(), K.glossary()
def frozen(obj):
    try:
        obj.id = "x"
    except dataclasses.FrozenInstanceError:
        return True
    except Exception:
        return False
    return False
print(json.dumps({
    "eq_ids": sorted(e.id for e in eqs), "gl_ids": sorted(t.id for t in gls),
    "eq_blasting": [e.id for e in K.equations(domain="blasting")], "eq_none": [e.id for e in K.equations(domain="planning")],
    "gl_haulage": [t.id for t in K.glossary(domain="haulage")], "gl_general": [t.id for t in K.glossary(domain="general")],
    "types": [type(eqs).__name__, type(gls).__name__], "frozen": [frozen(eqs[0]), frozen(gls[0])],
    "same": K.equations() is K.equations() or K.equations() == K.equations(),
    "es": {t.id: t.term_es for t in gls}, "def_es": {t.id: t.definition_es for t in gls},
    "first_eq": {"latex": eqs[0].latex, "function": eqs[0].function, "verification": eqs[0].verification,
                 "symbols": [dict(s) for s in eqs[0].symbols]},
}))
""",
    )
    assert got["eq_ids"] == ["co2_from_diesel", "powder_factor"] and got["gl_ids"] == [
        "bench",
        "haul_truck",
        "powder_factor_term",
    ]
    assert got["eq_blasting"] == ["powder_factor"] and got["eq_none"] == []
    assert got["gl_haulage"] == ["haul_truck"] and got["gl_general"] == ["bench"]
    assert got["types"] == ["tuple", "tuple"] and got["frozen"] == [True, True] and got["same"]
    assert got["es"]["powder_factor_term"] == "factor de carga" and got["es"]["haul_truck"] == "camión de extracción"
    assert "ángulo, aceleración, tamaño" in got["def_es"]["bench"]
    assert got["first_eq"]["verification"] in {"verified", "UNVERIFIED"}
    assert {s["symbol"] for s in got["first_eq"]["symbols"]} in ({"m", "f", "V"}, {"q"})

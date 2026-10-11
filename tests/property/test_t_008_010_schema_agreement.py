"""T-008-010 (P-008-01, P-008-02): the pure-Python validator agrees with the JSON Schemas; tables survive a YAML round trip bit for bit.

Public API under test (`minephys.knowledge`): `validate_tables(path)` returning a report with `.errors` (see
tests/unit/test_t_008_010_tables.py), `export()` / `export_json()` and the loader (round trip through a fixture package tree).

P-008-01 (200 examples): documents are generated from the rules (rows with unicode text, finite floats including subnormals and
+-1e300, rational strings, ranges) and invalid ones are made by ONE mutation of a valid one (drop, retype or rename a field,
non-finite number, min > max, wrong enum literal, unknown key, `verified_on` on an UNVERIFIED row). The decision of
`validate_tables` on a folder holding the document equals the decision of the reference: the JSON Schema of `contracts/` (the
`jsonschema` Draft 2020-12 validator) AND the rules of the data model that a schema cannot express (finite numbers, min <= max);
cross-file rules are kept satisfied by construction (unique ids, citation keys present in the bibliography). Tables, equations
catalogues, glossaries and bibliography entries are covered.

P-008-02 (25 examples, one interpreter each): a generated valid table written to YAML, loaded and exported returns the same field
values; floats are bit-identical and rational strings unchanged.
Oracle: `jsonschema` (reference implementation) and the generators themselves.
"""

from __future__ import annotations

import copy
import importlib
import json
import math
import string
import struct
import tempfile
from pathlib import Path
from typing import Any

import _knowledge_fixtures as fx
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[2]
SEEDS = st.integers(0, 2**32 - 1)
TEXT = (
    st.text(alphabet=string.ascii_letters + string.digits + " áéíóúñÁÉÍÓÚÑüµ-_/.,()", min_size=1, max_size=40)
    .map(str.strip)
    .filter(bool)
)
KEYS = ["doe2020", "agency2025", "epa2025ghghub"]
UNITS = ["m", "kg/m3", "1", "kg CO2 / US gal", "kPa", "J/kg", "µm"]
FINITE = st.floats(allow_nan=False, allow_infinity=False)
RATIONAL = st.builds(lambda p, q: f"{p}/{q}", st.integers(-(10**6), 10**6), st.integers(1, 10**6))


def _k():
    return importlib.import_module("minephys.knowledge")


def _schema_validator(name: str):
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    registry = Registry()
    names = ["knowledge-table", "bibliography-entry", "knowledge-equations", "knowledge-glossary", "knowledge-export"]
    for other in names:
        for base in (
            ROOT / "contracts",
            ROOT / "specs" / "000-foundation" / "contracts",
            ROOT / "specs" / "008-knowledge" / "contracts",
        ):
            path = base / f"{other}.schema.json"
            if path.is_file():
                doc = json.loads(path.read_text(encoding="utf-8"))
                registry = registry.with_resource(
                    doc["$id"], Resource.from_contents(doc, default_specification=DRAFT202012)
                )
                break
    for base in (
        ROOT / "contracts",
        ROOT / "specs" / "000-foundation" / "contracts",
        ROOT / "specs" / "008-knowledge" / "contracts",
    ):
        path = base / f"{name}.schema.json"
        if path.is_file():
            return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")), registry=registry)
    raise AssertionError(f"no schema {name}")


def numbers(obj: Any):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from numbers(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from numbers(v)


def table_reference(doc: Any) -> bool:
    """The schema plus the data-model rules a schema cannot express: finite numbers and min <= max."""
    if not _schema_validator("knowledge-table").is_valid(doc):
        return False
    if any(isinstance(n, float) and not math.isfinite(n) for n in numbers(doc)):
        return False
    for r in doc["rows"]:
        rng = r.get("range")
        if isinstance(rng, dict) and rng["min"] > rng["max"]:
            return False
    return True


# ----------------------------------------------------------------------------------------------- generators


@st.composite
def table_doc(draw: Any) -> dict[str, Any]:
    n = draw(st.integers(1, 6))
    rows = []
    for i in range(n):
        verified = draw(st.booleans())
        r: dict[str, Any] = {
            "id": f"r_{i}",
            "quantity": draw(TEXT),
            "units": draw(st.sampled_from(UNITS)),
            "role": draw(st.sampled_from(["model_constant", "parameter", "limit", "conversion"])),
            "citation": draw(st.sampled_from(KEYS)),
            "page": draw(TEXT),
            "verification": "verified" if verified else "UNVERIFIED",
            "symbol": draw(st.sampled_from(["minephys.haulage.fn", ["minephys.haulage.a", "minephys.blasting.b"]])),
        }
        if verified:
            r["verified_on"] = draw(
                st.dates(
                    min_value=__import__("datetime").date(2000, 1, 1),
                    max_value=__import__("datetime").date(2099, 12, 31),
                )
            ).isoformat()
        kind = draw(st.sampled_from(["float", "rational", "range"]))
        if kind == "float":
            r["value"] = draw(FINITE)
        elif kind == "rational":
            r["value"] = draw(RATIONAL)
        else:
            a, b = sorted((draw(FINITE), draw(FINITE)))
            r["range"] = {"min": a, "max": b}
        if draw(st.booleans()):
            r["notes"] = draw(TEXT)
        rows.append(r)
    return {"schema_version": 1, "table": "haulage", "title": draw(TEXT), "licence": "CC-BY-4.0", "rows": rows}


def mutate_table(doc: dict[str, Any], pick: int, which: int) -> dict[str, Any]:
    d = copy.deepcopy(doc)
    r = d["rows"][pick % len(d["rows"])] if isinstance(d.get("rows"), list) and d["rows"] else None
    ops = [
        lambda: d.pop(["schema_version", "table", "title", "licence", "rows"][pick % 5]),
        lambda: r.pop(["id", "quantity", "units", "role", "citation", "page", "verification", "symbol"][pick % 8]),
        lambda: d.__setitem__("extra_field", 1),
        lambda: r.__setitem__("extra_field", 1),
        lambda: r.__setitem__("role", "bogus"),
        lambda: r.__setitem__("verification", "maybe"),
        lambda: d.__setitem__("licence", "MIT"),
        lambda: d.__setitem__("schema_version", 2),
        lambda: r.__setitem__("value", "1/0"),
        lambda: r.__setitem__("value", "ten"),
        lambda: r.__setitem__("value", float("inf")),
        lambda: r.__setitem__("value", float("nan")),
        lambda: (r.pop("range", None), r.__setitem__("value", True)),
        lambda: r.__setitem__("range", {"min": 2.0, "max": 1.0}),
        lambda: r.__setitem__("range", {"min": 1.0}),
        lambda: (r.__setitem__("value", 1.0), r.__setitem__("range", {"min": 0.0, "max": 2.0})),
        lambda: (r.pop("value", None), r.pop("range", None)),
        lambda: (
            r.__setitem__("verified_on", "2026-10-06")
            if r["verification"] == "UNVERIFIED"
            else r.pop("verified_on", None)
        ),
        lambda: r.__setitem__("verified_on", "2026-02-31x"),
        lambda: r.__setitem__("units", "dimensionless"),
        lambda: r.__setitem__("id", "Bad_Id"),
        lambda: r.__setitem__("symbol", "nodots"),
        lambda: r.__setitem__("page", ""),
        lambda: r.__setitem__("notes", ""),
        lambda: r.__setitem__("citation", "Bad Key"),
        lambda: d.__setitem__("rows", []),
        lambda: d.__setitem__("title", ""),
    ]
    ops[which % len(ops)]()
    return d


def _decision(
    doc: Any,
    *,
    tables: dict[str, Any] | None = None,
    equations: Any = None,
    glossary: Any = None,
    bib: str = fx.GOOD_BIB,
) -> bool:
    """True when `validate_tables` reports no error for a folder holding the document."""
    with tempfile.TemporaryDirectory(prefix="mpk-") as tmp:
        folder = fx.write_tree(
            Path(tmp) / "k",
            tables=tables if tables is not None else {},
            bib=bib,
            equations=equations,
            glossary=glossary,
        )
        return len(list(_k().validate_tables(folder).errors)) == 0


@pytest.mark.req("P-008-01")
@pytest.mark.oracle(
    "reference-implementation", "jsonschema Draft 2020-12 validator + the data-model rules a schema cannot express"
)
@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(doc=table_doc(), mutate=st.booleans(), pick=st.integers(0, 1000), which=st.integers(0, 1000))
def test_p_008_01_tables_validator_agrees_with_the_schema(
    doc: dict[str, Any], mutate: bool, pick: int, which: int
) -> None:
    candidate = mutate_table(doc, pick, which) if mutate else doc
    expected_valid = table_reference(candidate)
    if not mutate:
        assert expected_valid, "the generator must produce valid documents"
    got_valid = _decision(None, tables={"haulage": candidate})
    assert got_valid == expected_valid, json.dumps(candidate, default=repr)[:400]


# --------------------------------------------------------------------------------- equations and glossary


@st.composite
def equations_doc(draw: Any) -> dict[str, Any]:
    n = draw(st.integers(1, 4))
    eqs = []
    for i in range(n):
        verified = draw(st.booleans())
        e: dict[str, Any] = {
            "id": f"eq_{i}",
            "title": draw(TEXT),
            "domain": draw(
                st.sampled_from(["haulage", "blasting", "geotech", "bulk", "comminution", "environment", "planning"])
            ),
            "latex": draw(st.text(alphabet=string.ascii_letters + "\\{}^_= +", min_size=1, max_size=60)),
            "symbols": [
                {"symbol": "x", "meaning": draw(TEXT), "units": draw(st.sampled_from(UNITS))}
                for _ in range(draw(st.integers(1, 3)))
            ],
            "function": "minephys.haulage.fn",
            "citation": draw(st.sampled_from(KEYS)),
            "page": draw(TEXT),
            "verification": "verified" if verified else "UNVERIFIED",
        }
        if verified:
            e["verified_on"] = "2026-10-06"
        if draw(st.booleans()):
            e["notes"] = draw(TEXT)
        eqs.append(e)
    return {"schema_version": 1, "title": draw(TEXT), "licence": "CC-BY-4.0", "equations": eqs}


def mutate_equations(doc: dict[str, Any], pick: int, which: int) -> dict[str, Any]:
    d = copy.deepcopy(doc)
    e = d["equations"][pick % len(d["equations"])] if isinstance(d.get("equations"), list) and d["equations"] else None
    ops = [
        lambda: d.pop(["schema_version", "title", "licence", "equations"][pick % 4]),
        lambda: e.pop(
            ["id", "title", "domain", "latex", "symbols", "function", "citation", "page", "verification"][pick % 9]
        ),
        lambda: e.__setitem__("extra", 1),
        lambda: e.__setitem__("domain", "astrology"),
        lambda: e.__setitem__("latex", ""),
        lambda: e.__setitem__("symbols", []),
        lambda: e["symbols"][0].pop("units"),
        lambda: e["symbols"][0].__setitem__("units", "n/a"),
        lambda: e.__setitem__("function", "haulage.fn"),
        lambda: (
            e.__setitem__("verification", "UNVERIFIED")
            if "verified_on" in e
            else e.__setitem__("verified_on", "2026-10-06")
        ),
        lambda: (
            e.pop("verified_on", None) if e["verification"] == "verified" else e.__setitem__("verification", "verified")
        ),
        lambda: d.__setitem__("licence", "CC-BY-SA-4.0"),
        lambda: d.__setitem__("equations", []),
        lambda: e.__setitem__("id", "Bad-Id"),
    ]
    ops[which % len(ops)]()
    return d


@pytest.mark.req("P-008-01")
@pytest.mark.oracle("reference-implementation", "jsonschema Draft 2020-12 validator on the equations catalogue")
@settings(max_examples=120, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(doc=equations_doc(), mutate=st.booleans(), pick=st.integers(0, 1000), which=st.integers(0, 1000))
def test_p_008_01_equations_validator_agrees_with_the_schema(
    doc: dict[str, Any], mutate: bool, pick: int, which: int
) -> None:
    candidate = mutate_equations(doc, pick, which) if mutate else doc
    expected_valid = _schema_validator("knowledge-equations").is_valid(candidate)
    if not mutate:
        assert expected_valid
    # the folder needs one valid table so that the only variable is the catalogue
    got_valid = _decision(None, tables={"haulage": fx.good_tables()["haulage"]}, equations=candidate)
    assert got_valid == expected_valid, json.dumps(candidate, default=repr)[:400]


@st.composite
def glossary_doc(draw: Any) -> dict[str, Any]:
    n = draw(st.integers(1, 4))
    terms = []
    for i in range(n):
        t: dict[str, Any] = {
            "id": f"term_{i}",
            "domain": draw(st.sampled_from(["haulage", "blasting", "general", "planning"])),
            "term_en": draw(TEXT),
            "term_es": draw(TEXT),
            "definition_en": draw(st.text(alphabet=string.ascii_letters + " áéíóúñ.,-", min_size=1, max_size=100)),
            "definition_es": draw(st.text(alphabet=string.ascii_letters + " áéíóúñ.,", min_size=1, max_size=100)),
        }
        if draw(st.booleans()):
            t["citation"] = draw(st.sampled_from(KEYS))
        terms.append(t)
    return {"schema_version": 1, "title": draw(TEXT), "licence": "CC-BY-4.0", "terms": terms}


def mutate_glossary(doc: dict[str, Any], pick: int, which: int) -> dict[str, Any]:
    d = copy.deepcopy(doc)
    t = d["terms"][pick % len(d["terms"])] if isinstance(d.get("terms"), list) and d["terms"] else None
    ops = [
        lambda: d.pop(["schema_version", "title", "licence", "terms"][pick % 4]),
        lambda: t.pop(["id", "domain", "term_en", "term_es", "definition_en", "definition_es"][pick % 6]),
        lambda: t.__setitem__("extra", 1),
        lambda: t.__setitem__("domain", "astrology"),
        lambda: t.__setitem__("term_es", " padded"),
        lambda: t.__setitem__("definition_en", ""),
        lambda: t.__setitem__("definition_es", "x" * 1001),
        lambda: t.__setitem__("see_also", []),
        lambda: t.__setitem__("citation", "Bad Key"),
        lambda: d.__setitem__("licence", "MIT"),
        lambda: d.__setitem__("terms", []),
        lambda: t.__setitem__("id", "Bad Id"),
    ]
    ops[which % len(ops)]()
    return d


@pytest.mark.req("P-008-01")
@pytest.mark.oracle("reference-implementation", "jsonschema Draft 2020-12 validator on the glossary")
@settings(max_examples=120, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(doc=glossary_doc(), mutate=st.booleans(), pick=st.integers(0, 1000), which=st.integers(0, 1000))
def test_p_008_01_glossary_validator_agrees_with_the_schema(
    doc: dict[str, Any], mutate: bool, pick: int, which: int
) -> None:
    candidate = mutate_glossary(doc, pick, which) if mutate else doc
    expected_valid = _schema_validator("knowledge-glossary").is_valid(candidate)
    if not mutate:
        assert expected_valid
    got_valid = _decision(None, tables={"haulage": fx.good_tables()["haulage"]}, glossary=candidate)
    assert got_valid == expected_valid, json.dumps(candidate, default=repr)[:400]


# ------------------------------------------------------------------------------------ bibliography entries

ENTRY_TYPES = ["article", "book", "inbook", "inproceedings", "techreport", "manual", "misc"]


@st.composite
def bib_entry(draw: Any) -> dict[str, Any]:
    e: dict[str, Any] = {
        "key": draw(st.from_regex(r"[a-z][a-z0-9_:-]{0,20}", fullmatch=True)),
        "entry_type": draw(st.sampled_from(ENTRY_TYPES)),
        "title": draw(TEXT),
        "year": draw(st.integers(1800, 2100)),
        "access": draw(st.sampled_from(["open", "paywalled", "regulation", "bibliographic-only"])),
    }
    e["author" if draw(st.booleans()) else "organization"] = draw(TEXT)
    if draw(st.booleans()):
        e["doi"] = (
            "10."
            + str(draw(st.integers(1000, 99999)))
            + "/"
            + draw(st.from_regex(r"[A-Za-z0-9.()_-]{1,12}", fullmatch=True))
        )
    else:
        e["url"] = "https://example.org/" + draw(st.from_regex(r"[a-z0-9]{1,10}", fullmatch=True))
    if draw(st.booleans()):
        e["journal"] = draw(TEXT)
    if draw(st.booleans()):
        e["licence"] = draw(st.sampled_from(["CC-BY-4.0", "CC-BY-SA-4.0", "CC0-1.0"]))
    return e


def render_entry(e: dict[str, Any]) -> str:
    lines = [f"@{e['entry_type']}{{{e['key']},"]
    body = [f"  {k} = {{{v}}}" for k, v in e.items() if k not in {"key", "entry_type", "year"}]
    body.append(f"  year = {{{e['year']}}}")
    return "\n".join(lines + [",\n".join(body), "}"]) + "\n"


def mutate_entry(e: dict[str, Any], which: int) -> dict[str, Any]:
    d = copy.deepcopy(e)
    ops = [
        lambda: d.pop("title"),
        lambda: d.pop("access"),
        lambda: (d.pop("author", None), d.pop("organization", None)),
        lambda: (d.pop("doi", None), d.pop("url", None)),
        lambda: d.__setitem__("year", 1799),
        lambda: d.__setitem__("year", 2101),
        lambda: d.__setitem__("access", "secret"),
        lambda: d.__setitem__("doi", "11.1/xyz") if "doi" in d else d.__setitem__("url", "ftp://example.org/x"),
        lambda: d.__setitem__("licence", "GPL-3.0"),
        lambda: d.__setitem__("pubdate", "2020"),  # a typo-like unknown field
        lambda: d.__setitem__("entry_type", "phdthesis"),
    ]
    ops[which % len(ops)]()
    return d


def _bib_decision(e: dict[str, Any]) -> bool:
    text = fx.GOOD_BIB + "\n" + render_entry(e)
    with tempfile.TemporaryDirectory(prefix="mpk-") as tmp:
        folder = fx.write_tree(
            Path(tmp) / "k", tables={"haulage": fx.good_tables()["haulage"]}, bib=text, equations=None, glossary=None
        )
        return len(list(_k().validate_tables(folder).errors)) == 0


@pytest.mark.req("P-008-01")
@pytest.mark.oracle("reference-implementation", "jsonschema Draft 2020-12 validator on the parsed bibliography entry")
@settings(max_examples=120, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(entry=bib_entry(), mutate=st.booleans(), which=st.integers(0, 1000))
def test_p_008_01_bibliography_validator_agrees_with_the_schema(
    entry: dict[str, Any], mutate: bool, which: int
) -> None:
    if entry["key"] in {"doe2020", "agency2025", "sharealike2019", "epa2025ghghub"}:
        entry = dict(entry, key="zz" + entry["key"])  # keys of the base bibliography are taken
    candidate = mutate_entry(entry, which) if mutate else entry
    expected_valid = _schema_validator("bibliography-entry").is_valid(candidate)
    if not mutate:
        assert expected_valid
    assert _bib_decision(candidate) == expected_valid, candidate


# ------------------------------------------------------------------------------------------- round trip


@pytest.mark.req("P-008-02")
@pytest.mark.oracle("analytical", "the generated table itself: floats bit-identical, rational strings unchanged")
@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(doc=table_doc())
def test_p_008_02_yaml_round_trip_through_load_and_export(doc: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory(prefix="mpk-") as tmp:
        base = fx.write_package_tree(Path(tmp) / "pkg", tables={"haulage": doc}, equations=None, glossary=None)
        got = fx.run_api(base, "print(json.dumps(json.loads(K.export_json())))")
    exported = {t["table"]: t for t in got["tables"]}["haulage"]
    by_id = {r["id"]: r for r in exported["rows"]}
    assert set(by_id) == {r["id"] for r in doc["rows"]}
    for r in doc["rows"]:
        out = by_id[r["id"]]
        for key, value in r.items():
            if key == "range":
                assert struct.pack(">d", float(out["range"]["min"])) == struct.pack(">d", float(value["min"]))
                assert struct.pack(">d", float(out["range"]["max"])) == struct.pack(">d", float(value["max"]))
            elif isinstance(value, float):
                assert isinstance(out[key], float) and struct.pack(">d", out[key]) == struct.pack(">d", value), (
                    key,
                    value,
                    out[key],
                )
            else:
                assert out[key] == value, (key, value, out[key])
        assert set(out) == set(r), "no field is added or dropped"
    assert exported["title"] == doc["title"] and exported["licence"] == doc["licence"]

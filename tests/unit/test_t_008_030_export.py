"""T-008-030 (FR-008-15): the deterministic export, valid against the export schema.

Expected public API (`minephys.knowledge`):
    export() -> JSON-serialisable mapping valid against `contracts/knowledge-export.schema.json` holding exactly `version` (the package
                version, `VERSION`), `tables` (each table object of DC-000-02 with its rows sorted by id, the tables sorted by name),
                `equations` (sorted by id), `glossary` (sorted by id), `bibliography` (the parsed entries of DC-000-03 sorted by key) and
                `summary` (counts: `rows` and `equations` as {total, unverified}, `terms`, `references`, `per_table` {name: {total,
                unverified}} and `per_role` with the four roles)
    export_json() -> str: `export()` serialised with sorted keys, two-space indent, UTF-8 characters (not \\u escapes), LF line ends, a
                trailing newline and no timestamps.

Oracles
- the hand-written golden export of the fixture knowledge (tests/_knowledge_fixtures.py): the tables and the catalogues are the
  fixture documents themselves (rows sorted by id), the bibliography entries are the four entries of GOOD_BIB parsed by hand, the summary
  counts are counted by hand (6 rows of which 4 UNVERIFIED; per role 1/0, 3/3, 1/1, 1/0; 2 equations of which 1 UNVERIFIED; 3 terms; 4
  references);
- `jsonschema` (reference implementation) validating the export against the promoted schemas.

Everything runs in a fresh interpreter served a fixture package tree.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import _knowledge_fixtures as fx
import pytest

ROOT = Path(__file__).resolve().parents[2]


def _expected_tables() -> list[dict[str, Any]]:
    docs = {**fx.good_tables(), **fx.good_share_alike()}
    out = []
    for name in sorted(docs):
        d = json.loads(json.dumps(docs[name]))
        d["rows"] = sorted(d["rows"], key=lambda r: r["id"])
        out.append(d)
    return out


EXPECTED_BIB = [
    {
        "key": "agency2025",
        "entry_type": "techreport",
        "organization": "Example Agency",
        "title": "Emission factors",
        "year": 2025,
        "url": "https://example.org/factors.pdf",
        "access": "regulation",
    },
    {
        "key": "doe2020",
        "entry_type": "article",
        "author": "Doe, Jane and Munoz, Maria",
        "title": "A Sourced Model of Comminution Energy",
        "journal": "Journal of Tests",
        "year": 2020,
        "doi": "10.1000/xyz123",
        "access": "open",
    },
    {
        "key": "epa2025ghghub",
        "entry_type": "misc",
        "organization": "US EPA",
        "title": "GHG Emission Factors Hub",
        "year": 2025,
        "url": "https://www.epa.gov/climateleadership/ghg-emission-factors-hub",
        "access": "regulation",
    },
    {
        "key": "sharealike2019",
        "entry_type": "book",
        "author": "Roe, Richard",
        "title": "A share-alike handbook",
        "publisher": "Open Press",
        "year": 2019,
        "url": "https://example.org/handbook",
        "access": "open",
        "licence": "CC-BY-SA-4.0",
    },
]

EXPECTED_SUMMARY = {
    "rows": {"total": 6, "unverified": 4},
    "equations": {"total": 2, "unverified": 1},
    "terms": 3,
    "references": 4,
    "per_table": {
        "blasting": {"total": 2, "unverified": 1},
        "geotech_sa": {"total": 1, "unverified": 1},
        "haulage": {"total": 3, "unverified": 2},
    },
    "per_role": {
        "model_constant": {"total": 1, "unverified": 0},
        "parameter": {"total": 3, "unverified": 3},
        "limit": {"total": 1, "unverified": 1},
        "conversion": {"total": 1, "unverified": 0},
    },
}

SCRIPT = """
print(json.dumps({"export": K.export(), "text": K.export_json()}))
"""


def _run(base: Path) -> dict[str, Any]:
    return fx.run_api(base, SCRIPT)


def _base(tmp_path: Path) -> Path:
    return fx.write_package_tree(tmp_path / "pkg", share_alike=fx.good_share_alike())


@pytest.mark.req("FR-008-15")
@pytest.mark.oracle("hand-calculation", "the golden export of the fixture knowledge")
def test_fr_008_15_export_equals_the_hand_written_golden(tmp_path: Path) -> None:
    got = _run(_base(tmp_path))["export"]
    assert set(got) == {"version", "tables", "equations", "glossary", "bibliography", "summary"}
    assert got["version"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert got["tables"] == _expected_tables()
    assert got["equations"] == sorted(fx.good_equations()["equations"], key=lambda e: e["id"])
    assert got["glossary"] == sorted(fx.good_glossary()["terms"], key=lambda t: t["id"])
    assert got["bibliography"] == EXPECTED_BIB
    assert got["summary"] == EXPECTED_SUMMARY


@pytest.mark.req("FR-008-15")
@pytest.mark.oracle(
    "reference-implementation",
    "jsonschema Draft 2020-12 validation of the export against contracts/knowledge-export.schema.json",
)
def test_fr_008_15_export_is_valid_against_the_export_schema(tmp_path: Path) -> None:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    registry = Registry()
    chosen = None
    for name in (
        "knowledge-table",
        "bibliography-entry",
        "knowledge-equations",
        "knowledge-glossary",
        "knowledge-export",
    ):
        doc = None
        for base in (
            ROOT / "contracts",
            ROOT / "specs" / "000-foundation" / "contracts",
            ROOT / "specs" / "008-knowledge" / "contracts",
        ):
            if (base / f"{name}.schema.json").is_file():
                doc = json.loads((base / f"{name}.schema.json").read_text(encoding="utf-8"))
                break
        assert doc is not None, name
        registry = registry.with_resource(doc["$id"], Resource.from_contents(doc, default_specification=DRAFT202012))
        if name == "knowledge-export":
            chosen = doc
    got = _run(_base(tmp_path))["export"]
    errors = list(Draft202012Validator(chosen, registry=registry).iter_errors(got))
    assert errors == [], [e.message for e in errors[:3]]


@pytest.mark.req("FR-008-15")
@pytest.mark.oracle("hand-calculation", "sorted keys, two-space indent, UTF-8, LF, trailing newline, no timestamp")
def test_fr_008_15_export_json_format(tmp_path: Path) -> None:
    got = _run(_base(tmp_path))
    text = got["text"]
    assert text.endswith("\n") and not text.endswith("\n\n") and "\r" not in text
    assert json.loads(text) == got["export"]
    lines = text.split("\n")
    assert lines[0] == "{" and lines[1].startswith('  "') and not lines[1].startswith("   "), lines[
        :3
    ]  # two-space indent
    assert text == json.dumps(json.loads(text), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    assert "camión de extracción" in text and "\\u00f3" not in text  # UTF-8 characters, not escapes
    top_keys = [k for k, _ in json.loads(text, object_pairs_hook=lambda p: p)]
    assert top_keys == sorted(top_keys)
    for word in ("generated", "timestamp", "date_created"):
        assert word not in text


@pytest.mark.req("FR-008-15")
@pytest.mark.req("P-008-03")
@pytest.mark.oracle(
    "hand-calculation", "two calls and two fresh interpreters with different PYTHONHASHSEED give the same bytes"
)
def test_fr_008_15_export_is_deterministic(tmp_path: Path) -> None:
    base = _base(tmp_path)
    twice = fx.run_api(
        base, "print(json.dumps([K.export_json(), K.export_json(), K.export_json() == K.export_json()]))"
    )
    assert twice[0] == twice[1] and twice[2] is True
    texts = []
    for seed in ("0", "1", "12345"):
        proc = fx.run_script(
            base, "sys.stdout.buffer.write(K.export_json().encode('utf-8'))", env={"PYTHONHASHSEED": seed}
        )
        assert proc.returncode == 0, proc.stderr[-1500:]
        texts.append(proc.stdout)
    assert texts[0] == texts[1] == texts[2]


@pytest.mark.req("FR-008-15")
@pytest.mark.oracle(
    "hand-calculation", "the export carries every row, UNVERIFIED ones included, with units as published"
)
def test_fr_008_15_export_keeps_values_units_and_status(tmp_path: Path) -> None:
    tables = {t["table"]: t for t in _run(_base(tmp_path))["export"]["tables"]}
    rows = {r["id"]: r for t in tables.values() for r in t["rows"]}
    assert (
        rows["rolling_resistance_default"]["value"] == "19/30"
        and rows["rolling_resistance_default"]["verification"] == "UNVERIFIED"
    )
    assert rows["max_grade"]["range"] == {"min": 0.0, "max": 0.15}
    assert (
        rows["diesel_co2_factor"]["units"] == "kg CO2 / US gal"
        and rows["diesel_co2_factor"]["verified_on"] == "2026-10-06"
    )
    assert tables["geotech_sa"]["licence"] == "CC-BY-SA-4.0"  # share-alike tables keep their licence


@pytest.mark.req("FR-008-15")
def test_fr_008_15_the_export_command_writes_the_same_text(tmp_path: Path) -> None:
    base = _base(tmp_path)
    expected = _run(base)["text"]
    proc = fx.run_cli(["export"], base)
    assert proc.returncode == 0, proc.stderr[-1500:]
    assert proc.stdout == expected
    out = tmp_path / "export.json"
    proc = fx.run_cli(["export", "--out", str(out)], base)
    assert proc.returncode == 0, proc.stderr[-1500:]
    assert out.read_bytes() == expected.encode("utf-8")

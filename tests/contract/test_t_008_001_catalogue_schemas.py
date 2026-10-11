"""T-008-001 (DC-008-01, DC-008-02, DC-008-03): the three catalogue JSON Schemas promoted to `contracts/`.

Expected deliverable: `contracts/knowledge-equations.schema.json`, `contracts/knowledge-glossary.schema.json` and
`contracts/knowledge-export.schema.json` (JSON Schema 2020-12; the drafts live in `specs/008-knowledge/contracts/`), together with
their valid and hostile fixtures (`examples/index.json`, read from `contracts/examples/` once promoted, or from the draft folder
`specs/008-knowledge/contracts/examples/`). No catalogue file is created by this task (spec 008 FR-008-22): the test checks that
`src/minephys/knowledge/catalogue/` holds no empty catalogue.
The export schema references the foundation schemas by relative URI (`knowledge-table.schema.json`,
`bibliography-entry.schema.json`) and the two catalogue schemas; the test resolves them through a registry built from `contracts/`
(or the draft folders while the foundation schemas are not promoted yet).

Oracle: the JSON Schema 2020-12 reference validator (`jsonschema`, a reference implementation, a dev-only dependency imported inside
the tests after the artefact under test has been looked up, so the failure reason is the missing schema file) and the hand-written
fixture index, which names for every hostile fixture the JSON pointer and the keyword that must be reported (spec 008
section 7 and the data-contract rules); plus hand-written boundary cases (caps, required fields, the licence constant).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "contracts"
DRAFTS = [ROOT / "specs" / "008-knowledge" / "contracts", ROOT / "specs" / "000-foundation" / "contracts"]
SCHEMAS = {
    "DC-008-01": "knowledge-equations.schema.json",
    "DC-008-02": "knowledge-glossary.schema.json",
    "DC-008-03": "knowledge-export.schema.json",
}
ALL_SCHEMAS = [*SCHEMAS.values(), "knowledge-table.schema.json", "bibliography-entry.schema.json"]
DIALECT = "https://json-schema.org/draft/2020-12/schema"


def _promoted(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    assert path.is_file(), f"missing promoted schema {path.relative_to(ROOT)}"
    return json.loads(path.read_text(encoding="utf-8"))


def _any_schema(name: str) -> dict[str, Any]:
    for base in (SCHEMA_DIR, *DRAFTS):
        if (base / name).is_file():
            return json.loads((base / name).read_text(encoding="utf-8"))
    raise AssertionError(f"schema {name} found nowhere")


def _validator(name: str):
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    registry = Registry()
    for other in ALL_SCHEMAS:
        doc = _any_schema(other)
        registry = registry.with_resource(doc["$id"], Resource.from_contents(doc, default_specification=DRAFT202012))
    return Draft202012Validator(_promoted(name), registry=registry)


def _pointer(parts: Any) -> str:
    return "".join("/" + str(p).replace("~", "~0").replace("/", "~1") for p in parts)


def _errors(schema_name: str, instance: Any) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    stack = list(_validator(schema_name).iter_errors(instance))
    while stack:  # anyOf / oneOf report their branch errors in `context`
        e = stack.pop()
        out.append((_pointer(e.absolute_path), e.validator))  # type: ignore[arg-type]
        stack.extend(e.context or [])
    return out


def _examples() -> list[tuple[Path, dict[str, Any]]]:
    out: dict[str, tuple[Path, dict[str, Any]]] = {}
    for base in (SCHEMA_DIR / "examples", DRAFTS[0] / "examples"):
        index = base / "index.json"
        if index.is_file():
            for ex in json.loads(index.read_text(encoding="utf-8"))["examples"]:
                if ex["schema"] in SCHEMAS.values() and (base / ex["file"]).is_file():
                    out.setdefault(ex["file"], (base, ex))
    return sorted(out.values(), key=lambda t: t[1]["file"])


EXAMPLES = _examples()


def _load(base: Path, ex: dict[str, Any]) -> Any:
    return json.loads((base / ex["file"]).read_text(encoding="utf-8"))


def _valid(schema: str) -> Any:
    base, ex = next((b, e) for b, e in EXAMPLES if e["schema"] == schema and e["valid"])
    return _load(base, ex)


@pytest.mark.req("DC-008-01")
@pytest.mark.req("DC-008-02")
@pytest.mark.req("DC-008-03")
@pytest.mark.oracle("reference-implementation", "jsonschema Draft202012Validator.check_schema")
@pytest.mark.parametrize("dc", sorted(SCHEMAS))
def test_schema_is_promoted_and_is_a_valid_2020_12_schema(dc: str) -> None:
    schema = _promoted(SCHEMAS[dc])
    from jsonschema import Draft202012Validator

    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == DIALECT
    assert schema["type"] == "object" and schema["additionalProperties"] is False
    assert schema["$id"].endswith("/contracts/" + SCHEMAS[dc])


@pytest.mark.req("DC-008-01")
@pytest.mark.req("DC-008-02")
@pytest.mark.req("DC-008-03")
@pytest.mark.oracle("hand-calculation", "FR-008-22: the first catalogue entries are written by module tasks, not here")
def test_no_empty_catalogue_file_is_shipped() -> None:
    _promoted(SCHEMAS["DC-008-01"])  # the promoted schemas must exist before this check is meaningful
    catalogue = ROOT / "src" / "minephys" / "knowledge" / "catalogue"
    for name, key in (("equations.yaml", "equations"), ("glossary.yaml", "terms")):
        path = catalogue / name
        if path.is_file():
            import yaml

            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            assert isinstance(doc, dict) and doc.get(key), (
                f"{name} is present but holds no entry (empty files are rejected)"
            )


@pytest.mark.req("DC-008-01")
@pytest.mark.req("DC-008-02")
@pytest.mark.req("DC-008-03")
def test_the_fixture_index_covers_all_three_schemas() -> None:
    _promoted(SCHEMAS["DC-008-01"])
    assert {e["schema"] for _, e in EXAMPLES} == set(SCHEMAS.values())
    for schema in SCHEMAS.values():
        assert any(e["valid"] for _, e in EXAMPLES if e["schema"] == schema)
        assert sum(1 for _, e in EXAMPLES if e["schema"] == schema and not e["valid"]) >= 8


@pytest.mark.req("DC-008-01")
@pytest.mark.req("DC-008-02")
@pytest.mark.req("DC-008-03")
@pytest.mark.oracle("reference-implementation", "jsonschema validation of the hand-written fixture index")
def test_every_valid_fixture_is_accepted() -> None:
    _promoted(SCHEMAS["DC-008-01"])
    assert EXAMPLES, "no fixture index found"
    valid = [(b, e) for b, e in EXAMPLES if e["valid"]]
    assert {e["schema"] for _, e in valid} == set(SCHEMAS.values())
    for base, entry in valid:
        assert _errors(entry["schema"], _load(base, entry)) == [], entry["file"]


@pytest.mark.req("DC-008-01")
@pytest.mark.req("DC-008-02")
@pytest.mark.req("DC-008-03")
@pytest.mark.oracle("reference-implementation", "jsonschema reports the pointer and keyword named in the index")
def test_every_hostile_fixture_is_rejected_at_the_stated_pointer_and_keyword() -> None:
    _promoted(SCHEMAS["DC-008-01"])
    assert EXAMPLES, "no fixture index found"
    for base, entry in EXAMPLES:
        found = _errors(entry["schema"], _load(base, entry))
        if entry["valid"]:
            assert found == [], entry["file"]
        else:
            assert found, f"{entry['file']} ({entry['class']}) was accepted"
            assert (entry["pointer"], entry["keyword"]) in found, (
                f"{entry['file']}: expected {(entry['pointer'], entry['keyword'])} in {found}"
            )


@pytest.mark.req("DC-008-01")
@pytest.mark.oracle("hand-calculation", "spec 008 section 7: equation entry fields")
@pytest.mark.parametrize(
    "key", ["id", "title", "domain", "latex", "symbols", "function", "citation", "page", "verification"]
)
def test_equation_rejects_removal_of_any_required_field(key: str) -> None:
    doc = _valid("knowledge-equations.schema.json")
    for i in range(len(doc["equations"])):
        broken = copy.deepcopy(doc)
        del broken["equations"][i][key]
        assert any(v == "required" for _, v in _errors("knowledge-equations.schema.json", broken)), (i, key)


@pytest.mark.req("DC-008-01")
@pytest.mark.oracle("hand-calculation", "spec 008 section 7: caps and conditionals of an equation entry")
def test_equation_caps_conditionals_and_licence() -> None:
    schema = "knowledge-equations.schema.json"
    doc = _valid(schema)
    assert _errors(schema, doc) == []
    eq = doc["equations"][0]

    def broken(mutate: Any) -> list[tuple[str, str]]:
        d = copy.deepcopy(doc)
        mutate(d["equations"][0])
        return _errors(schema, d)

    assert broken(lambda e: e.update(latex="x" * 2000)) == []  # the cap itself is valid
    assert broken(lambda e: e.update(latex="x" * 2001))
    assert broken(lambda e: e.update(symbols=[copy.deepcopy(e["symbols"][0]) for _ in range(64)])) == []
    assert broken(lambda e: e.update(symbols=[copy.deepcopy(e["symbols"][0]) for _ in range(65)]))
    assert broken(lambda e: e.update(verification="UNVERIFIED"))  # UNVERIFIED with verified_on is rejected
    assert broken(lambda e: e.update(rows=[]))  # rows, when present, are non-empty
    assert broken(lambda e: e.update(rows=["a_row", "a_row"]))  # and unique
    assert broken(lambda e: e.update(id="Bad-Id"))
    assert broken(lambda e: e.update(function="haulage.co2")) and broken(
        lambda e: e.update(function="minephys.haulage")
    )
    assert broken(lambda e: e.update(page=" p. 3"))  # text lines are trimmed
    assert eq["verification"] in {"verified", "UNVERIFIED"}
    many = copy.deepcopy(doc)
    many["equations"] = [dict(copy.deepcopy(doc["equations"][0]), id=f"eq_{i}") for i in range(500)]
    assert _errors(schema, many) == []
    many["equations"].append(dict(copy.deepcopy(doc["equations"][0]), id="eq_500"))
    assert _errors(schema, many)
    wrong = copy.deepcopy(doc)
    wrong["licence"] = "CC-BY-SA-4.0"
    assert ("/licence", "const") in _errors(schema, wrong)
    for domain in ("haulage", "blasting", "geotech", "bulk", "comminution", "environment", "planning"):
        assert broken(lambda e, d=domain: e.update(domain=d)) == []
    assert broken(lambda e: e.update(domain="general"))  # `general` belongs to the glossary only


@pytest.mark.req("DC-008-02")
@pytest.mark.oracle("hand-calculation", "spec 008 section 7: glossary term fields")
@pytest.mark.parametrize("key", ["id", "domain", "term_en", "term_es", "definition_en", "definition_es"])
def test_glossary_rejects_removal_of_any_required_field(key: str) -> None:
    doc = _valid("knowledge-glossary.schema.json")
    for i in range(len(doc["terms"])):
        broken = copy.deepcopy(doc)
        del broken["terms"][i][key]
        assert any(v == "required" for _, v in _errors("knowledge-glossary.schema.json", broken)), (i, key)


@pytest.mark.req("DC-008-02")
@pytest.mark.oracle("hand-calculation", "spec 008 section 7: glossary caps, Spanish text and see_also rules")
def test_glossary_caps_languages_and_see_also() -> None:
    schema = "knowledge-glossary.schema.json"
    doc = _valid(schema)

    def broken(mutate: Any) -> list[tuple[str, str]]:
        d = copy.deepcopy(doc)
        mutate(d["terms"][0])
        return _errors(schema, d)

    assert (
        broken(lambda t: t.update(definition_es="á" * 1000)) == []
    )  # 1,000 characters is the cap (accents count as one)
    assert broken(lambda t: t.update(definition_es="á" * 1001))
    assert broken(lambda t: t.update(term_es="Ángulo de reposo")) == []
    assert broken(lambda t: t.update(term_es=" ángulo"))  # not trimmed
    assert broken(lambda t: t.update(term_en="two\nlines"))  # single-line
    assert broken(lambda t: t.update(see_also=[f"t_{i}" for i in range(16)])) == []
    assert broken(lambda t: t.update(see_also=[f"t_{i}" for i in range(17)]))
    assert broken(lambda t: t.update(see_also=["a_term", "a_term"]))
    assert broken(lambda t: t.update(see_also=[]))
    assert broken(lambda t: t.update(domain="general")) == [] and broken(lambda t: t.update(domain="astrology"))
    many = copy.deepcopy(doc)
    many["terms"] = [dict(copy.deepcopy(doc["terms"][0]), id=f"term_{i}") for i in range(1000)]
    assert _errors(schema, many) == []
    many["terms"].append(dict(copy.deepcopy(doc["terms"][0]), id="term_1000"))
    assert _errors(schema, many)
    wrong = copy.deepcopy(doc)
    wrong["licence"] = "CC-BY-SA-4.0"
    assert ("/licence", "const") in _errors(schema, wrong)


@pytest.mark.req("DC-008-03")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 008 clarifications: the export holds exactly version, tables, equations, glossary, bibliography, summary",
)
def test_export_structure_and_summary_rules() -> None:
    schema = "knowledge-export.schema.json"
    doc = _valid(schema)
    assert _errors(schema, doc) == []
    assert set(doc) == {"version", "tables", "equations", "glossary", "bibliography", "summary"}
    for key in doc:
        broken = copy.deepcopy(doc)
        del broken[key]
        assert ("", "required") in _errors(schema, broken), key
    extra = copy.deepcopy(doc)
    extra["generated_at"] = "2026-10-11T00:00:00Z"  # no timestamps or other fields
    assert ("", "additionalProperties") in _errors(schema, extra)
    for bad in ("1.0.0", "1.2.3", "1.00.00", "v1.00.000", "1.00.000-rc1", ""):
        broken = copy.deepcopy(doc)
        broken["version"] = bad
        assert ("/version", "pattern") in _errors(schema, broken), bad
    for role in ("model_constant", "parameter", "limit", "conversion"):
        broken = copy.deepcopy(doc)
        del broken["summary"]["per_role"][role]
        assert any(v == "required" for _, v in _errors(schema, broken)), role
    broken = copy.deepcopy(doc)
    broken["summary"]["rows"]["total"] = -1
    assert any(v == "minimum" for _, v in _errors(schema, broken))
    broken = copy.deepcopy(doc)
    broken["summary"]["per_table"] = {}
    assert any(v == "minProperties" for _, v in _errors(schema, broken))

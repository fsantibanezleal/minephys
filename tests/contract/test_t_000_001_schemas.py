"""T-000-001 (DC-000-02, DC-000-03, DC-000-04): the three JSON Schemas promoted to `contracts/`.

Expected deliverable: `contracts/knowledge-table.schema.json`, `contracts/bibliography-entry.schema.json` and
`contracts/api-snapshot.schema.json` (JSON Schema 2020-12), together with the valid and hostile fixtures indexed by
`examples/index.json`. The fixtures are read from `contracts/examples/` once promoted, or from the draft folder
`specs/000-foundation/contracts/examples/` while the drafts are still there.

Oracle: the JSON Schema 2020-12 reference validator (`jsonschema`, a reference implementation) and the hand-written
fixture index, which names for every hostile fixture the JSON pointer and the schema keyword that must be reported.
`jsonschema` is a dev-only dependency (spec 000 plan, technical context); it is imported inside the test functions,
after the first-party artefact under test has been looked up, so the failure reason is the missing schema file.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "contracts"
EXAMPLE_DIRS = [ROOT / "contracts" / "examples", ROOT / "specs" / "000-foundation" / "contracts" / "examples"]
SCHEMAS = {
    "DC-000-02": "knowledge-table.schema.json",
    "DC-000-03": "bibliography-entry.schema.json",
    "DC-000-04": "api-snapshot.schema.json",
}
DIALECT = "https://json-schema.org/draft/2020-12/schema"


def _example_dir() -> Path:
    for d in EXAMPLE_DIRS:
        if (d / "index.json").is_file():
            return d
    raise AssertionError("no examples/index.json found under contracts/ or specs/000-foundation/contracts/")


def _index() -> list[dict[str, Any]]:
    path = _example_dir() / "index.json"
    return json.loads(path.read_text(encoding="utf-8"))["examples"]


def _load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    assert path.is_file(), f"missing promoted schema {path.relative_to(ROOT)}"
    return json.loads(path.read_text(encoding="utf-8"))


def _pointer(parts: Any) -> str:
    return "".join("/" + str(p).replace("~", "~0").replace("/", "~1") for p in parts)


def _errors(schema_name: str, instance: Any) -> list[tuple[str, str]]:
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(_load_schema(schema_name))
    out: list[tuple[str, str]] = []
    stack = list(validator.iter_errors(instance))
    while stack:  # anyOf / oneOf report their branch errors in `context`
        e = stack.pop()
        out.append((_pointer(e.absolute_path), e.validator))  # type: ignore[arg-type]
        stack.extend(e.context or [])
    return out


@pytest.mark.req("DC-000-02")
@pytest.mark.req("DC-000-03")
@pytest.mark.req("DC-000-04")
@pytest.mark.oracle("reference-implementation", "jsonschema Draft202012Validator.check_schema")
@pytest.mark.parametrize("dc", sorted(SCHEMAS))
def test_schema_is_promoted_and_is_a_valid_2020_12_schema(dc: str) -> None:
    schema = _load_schema(SCHEMAS[dc])
    from jsonschema import Draft202012Validator

    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == DIALECT
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False, "no other field is allowed (data-model.md)"
    assert schema["$id"].endswith("/contracts/" + SCHEMAS[dc])


_EXAMPLES = _index()


@pytest.mark.req("DC-000-02")
@pytest.mark.req("DC-000-03")
@pytest.mark.req("DC-000-04")
@pytest.mark.oracle("reference-implementation", "jsonschema validation of the hand-written fixture index")
@pytest.mark.parametrize("ex", [e for e in _EXAMPLES if e["valid"]], ids=lambda e: e["file"])
def test_valid_fixture_is_accepted(ex: dict[str, Any]) -> None:
    instance = json.loads((_example_dir() / ex["file"]).read_text(encoding="utf-8"))
    assert _errors(ex["schema"], instance) == []


@pytest.mark.req("DC-000-02")
@pytest.mark.req("DC-000-03")
@pytest.mark.req("DC-000-04")
@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("reference-implementation", "jsonschema reports the pointer and keyword named in the index")
@pytest.mark.parametrize("ex", [e for e in _EXAMPLES if not e["valid"]], ids=lambda e: e["file"])
def test_hostile_fixture_is_rejected_at_the_stated_pointer_and_keyword(ex: dict[str, Any]) -> None:
    instance = json.loads((_example_dir() / ex["file"]).read_text(encoding="utf-8"))
    found = _errors(ex["schema"], instance)
    assert found, f"{ex['file']} ({ex['class']}) was accepted"
    assert (ex["pointer"], ex["keyword"]) in found, f"expected {(ex['pointer'], ex['keyword'])} in {found}"


def _valid_instances(schema_file: str) -> list[tuple[str, Any]]:
    return [
        (e["file"], json.loads((_example_dir() / e["file"]).read_text(encoding="utf-8")))
        for e in _EXAMPLES
        if e["valid"] and e["schema"] == schema_file
    ]


@pytest.mark.req("DC-000-02")
@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("hand-calculation", "data-model.md section 1: required fields of the table and of a row")
@pytest.mark.parametrize("key", ["schema_version", "table", "title", "licence", "rows"])
def test_knowledge_table_rejects_removal_of_any_required_table_field(key: str) -> None:
    for name, doc in _valid_instances("knowledge-table.schema.json"):
        broken = copy.deepcopy(doc)
        del broken[key]
        assert ("", "required") in _errors("knowledge-table.schema.json", broken), name


@pytest.mark.req("DC-000-02")
@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("hand-calculation", "data-model.md section 1: required fields of a row")
@pytest.mark.parametrize("key", ["id", "quantity", "units", "role", "citation", "page", "verification", "symbol"])
def test_knowledge_table_rejects_removal_of_any_required_row_field(key: str) -> None:
    for name, doc in _valid_instances("knowledge-table.schema.json"):
        for i in range(len(doc["rows"])):
            broken = copy.deepcopy(doc)
            del broken["rows"][i][key]
            assert any(v == "required" for _, v in _errors("knowledge-table.schema.json", broken)), (name, i)


@pytest.mark.req("DC-000-02")
@pytest.mark.req("DC-000-03")
@pytest.mark.req("DC-000-04")
@pytest.mark.oracle("hand-calculation", "data-model.md: additionalProperties false so that a typo cannot hide a field")
@pytest.mark.parametrize("schema_file", sorted(SCHEMAS.values()))
def test_an_unknown_top_level_field_is_rejected(schema_file: str) -> None:
    for name, doc in _valid_instances(schema_file):
        broken = copy.deepcopy(doc)
        broken["sneaky_extra_field"] = 1
        assert ("", "additionalProperties") in _errors(schema_file, broken), name


@pytest.mark.req("DC-000-02")
@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("hand-calculation", "data-model.md: exactly one of value and range; verified_on iff verified")
def test_knowledge_row_value_range_and_verified_on_exclusivity() -> None:
    (_, doc) = next(x for x in _valid_instances("knowledge-table.schema.json") if x[0] == "knowledge-table.valid.json")
    both = copy.deepcopy(doc)
    both["rows"][0]["range"] = {"min": 1.0, "max": 2.0}
    assert _errors("knowledge-table.schema.json", both), "value and range together must be rejected"
    neither = copy.deepcopy(doc)
    del neither["rows"][0]["value"]
    assert _errors("knowledge-table.schema.json", neither), "neither value nor range must be rejected"
    as_range = copy.deepcopy(doc)
    del as_range["rows"][0]["value"]
    as_range["rows"][0]["range"] = {"min": 9.5, "max": 10.5}
    assert _errors("knowledge-table.schema.json", as_range) == []
    unverified_with_date = copy.deepcopy(doc)
    unverified_with_date["rows"][1]["verified_on"] = "2026-10-06"
    assert _errors("knowledge-table.schema.json", unverified_with_date)
    verified_without_date = copy.deepcopy(doc)
    del verified_without_date["rows"][0]["verified_on"]
    assert _errors("knowledge-table.schema.json", verified_without_date)


@pytest.mark.req("DC-000-02")
@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("hand-calculation", "data-model.md: a value is a finite number or an exact p/q string")
@pytest.mark.parametrize(
    ("value", "ok"),
    [
        (19, True),
        (-0.5, True),
        ("19/30", True),
        ("-7/3", True),
        ("1/0", False),
        ("0.6333", False),
        ("1/2/3", False),
        (True, False),
        (None, False),
        ([1], False),
    ],
)
def test_knowledge_value_forms(value: Any, ok: bool) -> None:
    (_, doc) = next(x for x in _valid_instances("knowledge-table.schema.json") if x[0] == "knowledge-table.valid.json")
    doc = copy.deepcopy(doc)
    doc["rows"][0]["value"] = value
    assert (_errors("knowledge-table.schema.json", doc) == []) is ok


@pytest.mark.req("DC-000-03")
@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("hand-calculation", "data-model.md section 2: DOI and URL patterns, year range")
@pytest.mark.parametrize(
    ("field", "value", "ok"),
    [
        ("doi", "10.1000/xyz123", True),
        ("doi", "https://doi.org/10.1000/xyz123", False),
        ("doi", "10.1/short", False),
        ("url", "https://example.org/a", True),
        ("url", "http://example.org/a", True),
        ("url", "ftp://example.org/a", False),
        ("url", "https://user:pw@example.org/a", False),
        ("year", 1800, True),
        ("year", 2100, True),
        ("year", 1799, False),
        ("year", 2101, False),
        ("year", "2020", False),
        ("access", "open", True),
        ("access", "secret", False),
    ],
)
def test_bibliography_field_rules(field: str, value: Any, ok: bool) -> None:
    (_, doc) = next(
        x for x in _valid_instances("bibliography-entry.schema.json") if x[0] == "bibliography-entry.valid.json"
    )
    doc = copy.deepcopy(doc)
    doc[field] = value
    assert (_errors("bibliography-entry.schema.json", doc) == []) is ok


@pytest.mark.req("DC-000-04")
@pytest.mark.req("FR-000-28")
@pytest.mark.oracle("hand-calculation", "data-model.md section 3: snapshot version pattern X.YY.ZZZ")
@pytest.mark.parametrize(
    ("version", "ok"),
    [("0.01.000", True), ("12.34.567", True), ("0.1.0", False), ("1.00", False), ("v1.00.000", False)],
)
def test_api_snapshot_version_pattern(version: str, ok: bool) -> None:
    (_, doc) = next(x for x in _valid_instances("api-snapshot.schema.json") if x[0] == "api-snapshot.valid.json")
    doc = copy.deepcopy(doc)
    doc["version"] = version
    assert (_errors("api-snapshot.schema.json", doc) == []) is ok


@pytest.mark.req("DC-000-02")
@pytest.mark.req("DC-000-03")
@pytest.mark.req("DC-000-04")
@pytest.mark.oracle("hand-calculation", "index.json lists every hostile class with its pointer and keyword")
def test_every_fixture_in_the_index_exists_and_is_utf8_json() -> None:
    d = _example_dir()
    assert len(_EXAMPLES) >= 50
    for e in _EXAMPLES:
        path = d / e["file"]
        assert path.is_file(), e["file"]
        json.loads(path.read_text(encoding="utf-8"))
        assert (SCHEMA_DIR / e["schema"]).is_file(), f"{e['schema']} is not promoted to contracts/"

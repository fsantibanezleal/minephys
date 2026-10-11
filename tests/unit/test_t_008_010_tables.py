"""T-008-010 (FR-008-01, FR-008-02, FR-008-05, FR-008-09): table loading, DC-000-02 rules, cross-file integrity, cached immutable API.

Expected public API (`minephys.knowledge`; the field names of the frozen dataclasses are the YAML keys):
    list_tables() -> tuple of table names (file stems of `knowledge/*.yaml` and `knowledge/share-alike/*.yaml`), sorted
    load_table(table) -> Table(table, title, licence, rows)       rows: tuple of Row(id, quantity, value, range, units, role, citation,
                                                                   page, verification, verified_on, symbol, notes)
    get_parameter(id) -> Row ; list_parameters(table=None, role=None, verification=None) -> tuple of Row
    validate_tables(path=None) -> report with `.errors` (every error, not only the first: objects with `file`, `index` (1-based row
                                  or entry, None or 0 for a table-level error), `field` and a message), `.rows` (row count) and
                                  `.unverified` (UNVERIFIED row count); `path` is a knowledge folder with the package layout
    KnowledgeSchemaError(ValueError) with `file`, `index`, `field`
Everything is read through `importlib.resources` (FR-008-01): the loader tests run in a fresh interpreter in which
`importlib.resources.files` is redirected to a fixture tree (tests/_knowledge_fixtures.py), the validation tests call
`validate_tables(folder)` on hand-written folders. Assumptions recorded in the red-phase report: the report attribute names above,
that the loader does not resolve `symbol` / `function` paths to objects (a repository check does, FR-000-21 and T-008-070), and that the
stem and licence-folder rules are file-level rules checked next to the schema rules.

Oracles: hand-written valid fixtures and one-mutation fixtures, each paired with the expected (file, index, field) of its error (plan
008 test strategy); hand-counted rows.
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


def _validate(folder: Path):
    return _k().validate_tables(folder)


def _has(report: Any, stem: str, field: Any, index: Any = ..., *, fields: tuple[str, ...] | None = None) -> bool:
    for e in report.errors:
        name = str(getattr(e, "file", "")).replace("\\", "/")
        if not name.endswith(f"{stem}.yaml") and not name.endswith(stem):
            continue
        ok_field = (getattr(e, "field", None) in fields) if fields else (getattr(e, "field", None) == field)
        if not ok_field:
            continue
        if index is ... or getattr(e, "index", None) == index:
            return True
    return False


def _table_error_index(e: Any) -> bool:
    return getattr(e, "index", None) in (None, 0)


@pytest.mark.req("FR-008-01")
@pytest.mark.oracle("hand-calculation", "fixture tree: haulage, blasting and the share-alike table geotech_sa")
def test_fr_008_01_tables_are_read_through_importlib_resources(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", share_alike=fx.good_share_alike())
    got = fx.run_api(
        base,
        """
print(json.dumps({"tables": list(K.list_tables()), "licences": {t: K.load_table(t).licence for t in K.list_tables()},
                  "rows": {t: [r.id for r in K.load_table(t).rows] for t in K.list_tables()}}))
""",
    )
    assert got["tables"] == ["blasting", "geotech_sa", "haulage"]  # sorted, share-alike tables included
    assert got["licences"] == {"blasting": "CC-BY-4.0", "geotech_sa": "CC-BY-SA-4.0", "haulage": "CC-BY-4.0"}
    assert got["rows"]["haulage"] == ["diesel_co2_factor", "rolling_resistance_default", "max_grade"]
    assert got["rows"]["blasting"] == ["inch", "powder_factor_typical"]
    assert got["rows"]["geotech_sa"] == ["sa_cohesion_default"]


@pytest.mark.req("FR-008-09")
@pytest.mark.oracle("hand-calculation", "frozen dataclasses, tuples, identity of cached objects, files opened once")
def test_fr_008_09_objects_are_immutable_and_cached(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg")
    got = fx.run_api(
        base,
        """
import dataclasses
events = []
sys.addaudithook(lambda ev, args: events.append((ev, str(args[0]))) if ev == "open" else None)
t1 = K.load_table("haulage")
first_opens = [p for ev, p in events if p.endswith(".yaml") or p.endswith(".bib")]
t2 = K.load_table("haulage")
p1 = K.get_parameter("diesel_co2_factor")
p2 = K.get_parameter("diesel_co2_factor")
second_opens = [p for ev, p in events if p.endswith(".yaml") or p.endswith(".bib")]
def raises_frozen(obj, name):
    try:
        setattr(obj, name, "x")
    except dataclasses.FrozenInstanceError:
        return True
    except Exception as e:
        return type(e).__name__
    return False
print(json.dumps({
    "same_table": t1 is t2, "same_row": p1 is p2, "row_in_table": any(r is p1 for r in t1.rows),
    "rows_is_tuple": type(t1.rows).__name__, "tables_tuple": type(K.list_tables()).__name__,
    "params_tuple": type(K.list_parameters()).__name__,
    "table_frozen": raises_frozen(t1, "title"), "row_frozen": raises_frozen(p1, "page"),
    "dataclass": dataclasses.is_dataclass(t1) and dataclasses.is_dataclass(p1),
    "no_extra_opens": second_opens == first_opens, "opened_something": len(first_opens) > 0,
}))
""",
    )
    assert got["same_table"] and got["same_row"] and got["row_in_table"]
    assert got["rows_is_tuple"] == "tuple" and got["tables_tuple"] == "tuple" and got["params_tuple"] == "tuple"
    assert got["table_frozen"] is True and got["row_frozen"] is True and got["dataclass"]
    assert got["opened_something"] and got["no_extra_opens"], (
        "files are loaded and validated once; later calls hit the cache"
    )


@pytest.mark.req("FR-008-09")
@pytest.mark.oracle("hand-calculation", "list_parameters filters over the hand-counted fixture rows")
def test_fr_008_09_lookup_and_filters(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", share_alike=fx.good_share_alike())
    got = fx.run_api(
        base,
        """
ids = lambda rows: sorted(r.id for r in rows)
print(json.dumps({
    "all": ids(K.list_parameters()),
    "haulage": ids(K.list_parameters(table="haulage")),
    "param": ids(K.list_parameters(role="parameter")),
    "unverified": ids(K.list_parameters(verification="UNVERIFIED")),
    "verified": ids(K.list_parameters(verification="verified")),
    "combo": ids(K.list_parameters(table="blasting", role="parameter", verification="UNVERIFIED")),
    "none": ids(K.list_parameters(table="haulage", role="conversion")),
    "row": [K.get_parameter("inch").units, K.get_parameter("inch").role, K.get_parameter("inch").citation],
}))
""",
    )
    assert got["all"] == sorted(
        [
            "diesel_co2_factor",
            "rolling_resistance_default",
            "max_grade",
            "inch",
            "powder_factor_typical",
            "sa_cohesion_default",
        ]
    )
    assert got["haulage"] == ["diesel_co2_factor", "max_grade", "rolling_resistance_default"]
    assert got["param"] == ["powder_factor_typical", "rolling_resistance_default", "sa_cohesion_default"]
    assert got["unverified"] == [
        "max_grade",
        "powder_factor_typical",
        "rolling_resistance_default",
        "sa_cohesion_default",
    ]
    assert got["verified"] == ["diesel_co2_factor", "inch"]
    assert got["combo"] == ["powder_factor_typical"] and got["none"] == []
    assert got["row"] == ["m", "conversion", "agency2025"]


@pytest.mark.req("FR-008-02")
@pytest.mark.oracle("hand-calculation", "a valid fixture folder: no error, 6 rows, 4 UNVERIFIED")
def test_fr_008_02_valid_folder_validates_cleanly(tmp_path: Path) -> None:
    folder = fx.write_tree(tmp_path / "k", share_alike=fx.good_share_alike())
    report = _validate(folder)
    assert list(report.errors) == []
    assert report.rows == 6 and report.unverified == 4


def _row_edit(index: int, **over: Any):
    """Mutation of row `index` (0-based) of the haulage table: set keys, or delete them when the value is fx.DROP."""

    def mutate(table: dict[str, Any]) -> None:
        for k, v in over.items():
            if v is fx.DROP:
                table["rows"][index].pop(k, None)
            else:
                table["rows"][index][k] = v

    return mutate


def _top(**over: Any):
    def mutate(table: dict[str, Any]) -> None:
        for k, v in over.items():
            if v is fx.DROP:
                table.pop(k, None)
            else:
                table[k] = v

    return mutate


# (id, mutation of the haulage table, expected row index (1-based) or None for a table-level error, accepted `field` values)
ROW_CASES: list[tuple[str, Any, int, tuple[str, ...]]] = [
    ("missing-id", _row_edit(1, id=fx.DROP), 2, ("id",)),
    ("missing-quantity", _row_edit(1, quantity=fx.DROP), 2, ("quantity",)),
    ("missing-units", _row_edit(1, units=fx.DROP), 2, ("units",)),
    ("missing-role", _row_edit(1, role=fx.DROP), 2, ("role",)),
    ("missing-citation", _row_edit(1, citation=fx.DROP), 2, ("citation",)),
    ("missing-page", _row_edit(1, page=fx.DROP), 2, ("page",)),
    ("missing-verification", _row_edit(1, verification=fx.DROP), 2, ("verification",)),
    ("missing-symbol", _row_edit(1, symbol=fx.DROP), 2, ("symbol",)),
    ("bad-role", _row_edit(1, role="constant"), 2, ("role",)),
    ("bad-verification-case", _row_edit(1, verification="unverified"), 2, ("verification",)),
    ("unknown-field", _row_edit(1, foo=1), 2, ("foo",)),
    ("value-and-range", _row_edit(0, range={"min": 1.0, "max": 2.0}), 1, ("value", "range", "value/range")),
    ("neither-value-nor-range", _row_edit(0, value=fx.DROP), 1, ("value", "range", "value/range")),
    ("range-min-above-max", _row_edit(2, range={"min": 1.0, "max": 0.5}), 3, ("range",)),
    ("range-missing-max", _row_edit(2, range={"min": 0.0}), 3, ("range", "max")),
    ("range-extra-key", _row_edit(2, range={"min": 0.0, "max": 1.0, "step": 0.1}), 3, ("range", "step")),
    ("value-inf", _row_edit(0, value=float("inf")), 1, ("value",)),
    ("value-nan", _row_edit(0, value=float("nan")), 1, ("value",)),
    ("value-minus-inf", _row_edit(0, value=float("-inf")), 1, ("value",)),
    ("value-text", _row_edit(0, value="ten"), 1, ("value",)),
    ("value-decimal-string", _row_edit(0, value="0.6333"), 1, ("value",)),
    ("value-zero-denominator", _row_edit(0, value="1/0"), 1, ("value",)),
    ("value-bool", _row_edit(0, value=True), 1, ("value",)),
    ("verified-without-date", _row_edit(0, verified_on=fx.DROP), 1, ("verified_on",)),
    ("unverified-with-date", _row_edit(1, verified_on="2026-10-06"), 2, ("verified_on",)),
    ("bad-date-month", _row_edit(0, verified_on="2026-13-01"), 1, ("verified_on",)),
    ("bad-date-format", _row_edit(0, verified_on="06/10/2026"), 1, ("verified_on",)),
    ("id-uppercase", _row_edit(1, id="Bad_Id"), 2, ("id",)),
    ("id-leading-digit", _row_edit(1, id="1abc"), 2, ("id",)),
    ("id-too-long", _row_edit(1, id="a" * 65), 2, ("id",)),
    ("units-dimensionless", _row_edit(1, units="dimensionless"), 2, ("units",)),
    ("units-dash", _row_edit(1, units="-"), 2, ("units",)),
    ("units-none", _row_edit(1, units="none"), 2, ("units",)),
    ("units-na", _row_edit(1, units="n/a"), 2, ("units",)),
    ("units-empty", _row_edit(1, units=""), 2, ("units",)),
    ("units-padded", _row_edit(1, units=" m"), 2, ("units",)),
    ("quantity-blank", _row_edit(1, quantity="   "), 2, ("quantity",)),
    ("quantity-too-long", _row_edit(1, quantity="q" * 201), 2, ("quantity",)),
    ("page-empty", _row_edit(1, page=""), 2, ("page",)),
    ("notes-empty", _row_edit(0, notes=""), 1, ("notes",)),
    ("notes-too-long", _row_edit(0, notes="n" * 1001), 1, ("notes",)),
    ("symbol-not-dotted", _row_edit(0, symbol="co2_from_diesel"), 1, ("symbol",)),
    ("symbol-wrong-root", _row_edit(0, symbol="haulage.module.function"), 1, ("symbol",)),
    ("symbol-too-short", _row_edit(0, symbol="minephys.haulage"), 1, ("symbol",)),
    ("symbol-empty-list", _row_edit(0, symbol=[]), 1, ("symbol",)),
    ("symbol-duplicates", _row_edit(1, symbol=["minephys.haulage.a", "minephys.haulage.a"]), 2, ("symbol",)),
    ("citation-bad-pattern", _row_edit(0, citation="Bad Key"), 1, ("citation",)),
]
TABLE_CASES: list[tuple[str, Any, tuple[str, ...]]] = [
    ("schema-version-2", _top(schema_version=2), ("schema_version",)),
    ("schema-version-missing", _top(schema_version=fx.DROP), ("schema_version",)),
    ("table-name-differs-from-stem", _top(table="other"), ("table",)),
    ("table-name-invalid", _top(table="Haulage"), ("table",)),
    ("title-missing", _top(title=fx.DROP), ("title",)),
    ("title-empty", _top(title=""), ("title",)),
    ("licence-unknown", _top(licence="MIT"), ("licence",)),
    ("licence-share-alike-in-main-folder", _top(licence="CC-BY-SA-4.0"), ("licence",)),
    ("licence-missing", _top(licence=fx.DROP), ("licence",)),
    ("extra-top-level-field", _top(sneaky=1), ("sneaky",)),
    ("rows-empty", _top(rows=[]), ("rows",)),
    ("rows-missing", _top(rows=fx.DROP), ("rows",)),
    ("rows-not-a-list", _top(rows={"a": 1}), ("rows",)),
]


@pytest.mark.req("FR-008-02")
@pytest.mark.oracle("hand-calculation", "one mutation per DC-000-02 rule, each with its expected (file, index, field)")
@pytest.mark.parametrize(("name", "mutate", "index", "fields"), ROW_CASES, ids=[c[0] for c in ROW_CASES])
def test_fr_008_02_row_rule_violations(
    tmp_path: Path, name: str, mutate: Any, index: int, fields: tuple[str, ...]
) -> None:
    table = copy.deepcopy(fx.good_tables()["haulage"])
    mutate(table)
    tables = fx.good_tables()
    tables["haulage"] = table
    report = _validate(fx.write_tree(tmp_path / "k", tables=tables))
    assert _has(report, "haulage", None, index, fields=fields), [(str(e.file), e.index, e.field) for e in report.errors]


@pytest.mark.req("FR-008-02")
@pytest.mark.parametrize(("name", "mutate", "fields"), TABLE_CASES, ids=[c[0] for c in TABLE_CASES])
def test_fr_008_02_table_rule_violations(tmp_path: Path, name: str, mutate: Any, fields: tuple[str, ...]) -> None:
    table = copy.deepcopy(fx.good_tables()["haulage"])
    mutate(table)
    tables = fx.good_tables()
    tables["haulage"] = table
    report = _validate(fx.write_tree(tmp_path / "k", tables=tables))
    assert any(
        str(e.file).replace("\\", "/").endswith("haulage.yaml") and e.field in fields and _table_error_index(e)
        for e in report.errors
    ), [(str(e.file), e.index, e.field) for e in report.errors]


@pytest.mark.req("FR-008-02")
@pytest.mark.oracle(
    "hand-calculation", "the valid forms next to the invalid ones: rationals, negative rationals, ranges, symbol lists"
)
def test_fr_008_02_valid_variants_are_accepted(tmp_path: Path) -> None:
    table = copy.deepcopy(fx.good_tables()["haulage"])
    table["rows"][0]["value"] = "-7/3"
    table["rows"][1]["value"] = 19
    table["rows"][2]["range"] = {"min": -1e300, "max": 1e300}
    table["rows"].append(
        fx.row(id="subnormal", value=5e-324, symbol=["minephys.haulage.a", "minephys.haulage.b"], notes=fx.DROP)
    )
    table["rows"].append(fx.row(id="x" * 64, value=0, notes=fx.DROP))
    tables = fx.good_tables()
    tables["haulage"] = table
    report = _validate(fx.write_tree(tmp_path / "k", tables=tables))
    assert list(report.errors) == []


@pytest.mark.req("FR-008-02")
@pytest.mark.req("FR-008-06")
@pytest.mark.oracle(
    "hand-calculation", "a share-alike table must carry a share-alike licence and the main folder must not"
)
def test_fr_008_02_share_alike_licence_rule(tmp_path: Path) -> None:
    bad = fx.good_share_alike()
    bad["geotech_sa"]["licence"] = "CC-BY-4.0"  # a share-alike table with the main licence
    report = _validate(fx.write_tree(tmp_path / "k", share_alike=bad))
    assert any(e.field == "licence" and "geotech_sa" in str(e.file) for e in report.errors)


@pytest.mark.req("FR-008-05")
@pytest.mark.oracle(
    "hand-calculation", "duplicate row ids, unknown citation keys, dangling equation rows and glossary links"
)
def test_fr_008_05_duplicate_row_ids_across_and_within_tables(tmp_path: Path) -> None:
    tables = fx.good_tables()
    tables["blasting"]["rows"][0]["id"] = "diesel_co2_factor"  # also in haulage
    report = _validate(fx.write_tree(tmp_path / "a", tables=tables))
    assert any(e.field == "id" and "diesel_co2_factor" in str(e) for e in report.errors), [
        (str(e.file), e.index, e.field) for e in report.errors
    ]
    tables = fx.good_tables()
    tables["haulage"]["rows"][2]["id"] = "max_grade"
    tables["haulage"]["rows"].append(copy.deepcopy(tables["haulage"]["rows"][2]))  # the same id twice in one table
    report = _validate(fx.write_tree(tmp_path / "b", tables=tables))
    assert any(e.field == "id" and e.index == 4 for e in report.errors)


@pytest.mark.req("FR-008-05")
def test_fr_008_05_citation_must_be_in_the_bibliography(tmp_path: Path) -> None:
    tables = fx.good_tables()
    tables["haulage"]["rows"][1]["citation"] = "nobody1999"  # well formed but absent from references.bib
    report = _validate(fx.write_tree(tmp_path / "k", tables=tables))
    assert _has(report, "haulage", "citation", 2)
    no_bib = fx.write_tree(tmp_path / "nobib", bib=None)
    report = _validate(no_bib)
    assert any(e.field == "citation" for e in report.errors) or any(
        "references.bib" in str(e.file) for e in report.errors
    )


@pytest.mark.req("FR-008-05")
def test_fr_008_05_equation_and_glossary_references(tmp_path: Path) -> None:
    eq = fx.good_equations()
    eq["equations"][0]["rows"] = ["diesel_co2_factor", "no_such_row"]
    report = _validate(fx.write_tree(tmp_path / "e1", equations=eq))
    assert _has(report, "equations", "rows", 1)
    eq = fx.good_equations()
    eq["equations"][1]["id"] = eq["equations"][0]["id"]  # duplicate equation id
    report = _validate(fx.write_tree(tmp_path / "e2", equations=eq))
    assert _has(report, "equations", "id", 2)
    eq = fx.good_equations()
    eq["equations"][1]["citation"] = "ghost2001"
    report = _validate(fx.write_tree(tmp_path / "e3", equations=eq))
    assert _has(report, "equations", "citation", 2)
    gl = fx.good_glossary()
    gl["terms"][0]["see_also"] = ["bench", "no_such_term"]
    report = _validate(fx.write_tree(tmp_path / "g1", glossary=gl))
    assert _has(report, "glossary", "see_also", 1)
    gl = fx.good_glossary()
    gl["terms"][2]["id"] = "bench"  # duplicate term id
    report = _validate(fx.write_tree(tmp_path / "g2", glossary=gl))
    assert _has(report, "glossary", "id", 3)
    gl = fx.good_glossary()
    gl["terms"][0]["citation"] = "ghost2001"
    report = _validate(fx.write_tree(tmp_path / "g3", glossary=gl))
    assert _has(report, "glossary", "citation", 1)
    # equation ids and glossary ids are separate namespaces: the same id in both is fine
    eq = fx.good_equations()
    gl = fx.good_glossary()
    gl["terms"][2]["id"] = eq["equations"][0]["id"]  # a term (not the one `see_also` points to) reuses an equation id
    assert list(_validate(fx.write_tree(tmp_path / "ns", equations=eq, glossary=gl)).errors) == []


@pytest.mark.req("FR-008-05")
@pytest.mark.oracle("hand-calculation", "row ids are unique across plain and share-alike tables")
def test_fr_008_05_share_alike_ids_are_part_of_the_same_namespace(tmp_path: Path) -> None:
    sa = fx.good_share_alike()
    sa["geotech_sa"]["rows"][0]["id"] = "inch"
    report = _validate(fx.write_tree(tmp_path / "k", share_alike=sa))
    assert any(e.field == "id" and "inch" in str(e) for e in report.errors)

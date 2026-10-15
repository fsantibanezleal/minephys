"""T-008-042 (FR-008-20): `knowledge_changes(old_dir, new_dir)` for the foundation's release check.

Expected behaviour (`minephys.knowledge.knowledge_changes`): given two knowledge folders with the layout of FR-008-01 it returns the ids of
the rows whose `value`, `range` or `verification` differ between the two folders, including rows that exist in only one of them (added or
removed rows, in an existing table or in a whole added or removed table, share-alike tables included), sorted in ascending order
(a sequence of `str`: the tests compare `list(result)`), and nothing else: a change of quantity, units, role, citation, page, symbol,
notes, `verified_on`, a table title, the order of the rows, the equations catalogue, the glossary or the bibliography is not a change.
Identical folders give an empty sequence. A folder argument that is not an existing directory raises `minephys.InputError`
(`argument` "old_dir" or "new_dir"; the error of a missing directory is also pinned in T-008-032).

Not pinned (the specification does not define them): whether the integer 2 and the float 2.0, or the rational "1/2" and 0.5, count as the
same value.

Oracle: hand-made pairs of fixture folders (tests/_knowledge_fixtures.py) in which exactly the named rows are edited.
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


def _pair(
    tmp_path: Path, edit: Any = None, *, old_kw: dict[str, Any] | None = None, new_kw: dict[str, Any] | None = None
) -> list[str]:
    """Write the fixture twice (the second one edited by `edit(tables, share_alike)`) and return `list(knowledge_changes(old, new))`."""
    old_tables, old_sa = fx.good_tables(), fx.good_share_alike()
    new_tables, new_sa = copy.deepcopy(old_tables), copy.deepcopy(old_sa)
    if edit is not None:
        edit(new_tables, new_sa)
    old = fx.write_tree(tmp_path / "old", tables=old_tables, share_alike=old_sa, **(old_kw or {}))
    new = fx.write_tree(tmp_path / "new", tables=new_tables, share_alike=new_sa, **(new_kw or {}))
    result = _k().knowledge_changes(old, new)
    assert not isinstance(result, str)
    ids = list(result)
    assert all(isinstance(i, str) for i in ids)
    return ids


def _row(tables: dict[str, Any], table: str, row_id: str) -> dict[str, Any]:
    return next(r for r in tables[table]["rows"] if r["id"] == row_id)


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle("hand-calculation", "identical folders have no change")
def test_fr_008_20_identical_folders_have_no_changes(tmp_path: Path) -> None:
    assert _pair(tmp_path) == []


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle("hand-calculation", "a changed value, rational value, range end or status is listed")
@pytest.mark.parametrize(
    ("table", "row_id", "change"),
    [
        ("haulage", "diesel_co2_factor", {"value": 10.5}),
        ("haulage", "rolling_resistance_default", {"value": "5/8"}),
        ("haulage", "max_grade", {"range": {"min": 0.0, "max": 0.2}}),
        ("haulage", "max_grade", {"range": {"min": 0.01, "max": 0.15}}),
        ("blasting", "inch", {"verification": "UNVERIFIED", "verified_on": None}),
        ("haulage", "rolling_resistance_default", {"verification": "verified", "verified_on": "2026-10-09"}),
        ("blasting", "powder_factor_typical", {"value": 0.36}),
    ],
    ids=[
        "value",
        "rational",
        "range-max",
        "range-min",
        "verified-to-unverified",
        "unverified-to-verified",
        "value-in-second-table",
    ],
)
def test_fr_008_20_a_change_of_value_range_or_status_is_listed(
    tmp_path: Path, table: str, row_id: str, change: dict[str, Any]
) -> None:
    def edit(tables: dict[str, Any], _sa: dict[str, Any]) -> None:
        r = _row(tables, table, row_id)
        for k, v in change.items():
            if v is None:
                r.pop(k, None)
            else:
                r[k] = v

    assert _pair(tmp_path, edit) == [row_id]


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle("hand-calculation", "a row switching between a value and a range is a change")
def test_fr_008_20_switching_between_value_and_range_is_a_change(tmp_path: Path) -> None:
    def edit(tables: dict[str, Any], _sa: dict[str, Any]) -> None:
        r = _row(tables, "blasting", "powder_factor_typical")
        del r["value"]
        r["range"] = {"min": 0.35, "max": 0.35}

    assert _pair(tmp_path, edit) == ["powder_factor_typical"]


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle("hand-calculation", "added and removed rows and tables are listed")
def test_fr_008_20_added_and_removed_rows_and_tables_are_listed(tmp_path: Path) -> None:
    def edit(tables: dict[str, Any], sa: dict[str, Any]) -> None:
        tables["haulage"]["rows"].append(fx.row(id="zz_new_row", symbol="minephys.haulage.f", notes=fx.DROP))
        tables["blasting"]["rows"] = [r for r in tables["blasting"]["rows"] if r["id"] != "inch"]  # removed
        sa.clear()  # the whole share-alike table is removed

    assert _pair(tmp_path, edit) == ["inch", "sa_cohesion_default", "zz_new_row"]


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle("hand-calculation", "a whole table added in the new folder lists all its rows")
def test_fr_008_20_a_new_table_lists_all_its_rows(tmp_path: Path) -> None:
    def edit(tables: dict[str, Any], _sa: dict[str, Any]) -> None:
        extra = copy.deepcopy(tables["blasting"])
        extra["table"] = "extra"
        extra["rows"] = [
            fx.row(id="extra_one", symbol="minephys.haulage.f", notes=fx.DROP),
            fx.row(id="extra_two", symbol="minephys.haulage.f", notes=fx.DROP),
        ]
        tables["extra"] = extra

    assert _pair(tmp_path, edit) == ["extra_one", "extra_two"]


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle(
    "hand-calculation", "several changes are returned sorted in ascending order whatever the table order"
)
def test_fr_008_20_result_is_sorted(tmp_path: Path) -> None:
    def edit(tables: dict[str, Any], sa: dict[str, Any]) -> None:
        _row(tables, "haulage", "max_grade")["range"] = {"min": 0.0, "max": 0.3}
        _row(tables, "blasting", "powder_factor_typical")["value"] = 0.4
        _row(tables, "haulage", "diesel_co2_factor")["value"] = 11.0
        sa["geotech_sa"]["rows"][0]["value"] = 26.0
        _row(tables, "blasting", "inch")["value"] = 0.0255

    got = _pair(tmp_path, edit)
    assert got == sorted(["diesel_co2_factor", "inch", "max_grade", "powder_factor_typical", "sa_cohesion_default"])


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle("hand-calculation", "changes of any other field are not changes")
@pytest.mark.parametrize(
    ("field", "new_value"),
    [
        ("quantity", "a reworded quantity"),
        ("units", "kg CO2 / L"),
        ("role", "parameter"),
        ("citation", "agency2025"),
        ("page", "Table 9, p. 99"),
        ("symbol", "minephys.haulage.other"),
        ("notes", "a different note"),
        ("verified_on", "2026-10-09"),
    ],
)
def test_fr_008_20_changes_of_other_fields_are_not_changes(tmp_path: Path, field: str, new_value: str) -> None:
    def edit(tables: dict[str, Any], _sa: dict[str, Any]) -> None:
        _row(tables, "haulage", "diesel_co2_factor")[field] = new_value

    assert _pair(tmp_path, edit) == []


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle("hand-calculation", "titles, row order, the catalogues and the bibliography are not row changes")
def test_fr_008_20_titles_row_order_catalogues_and_bibliography_are_not_changes(tmp_path: Path) -> None:
    def edit(tables: dict[str, Any], _sa: dict[str, Any]) -> None:
        tables["haulage"]["title"] = "A new title"
        tables["haulage"]["rows"].reverse()

    eq = fx.good_equations()
    eq["equations"][0]["latex"] = "z = 1"
    gl = fx.good_glossary()
    gl["terms"][0]["definition_en"] = "a changed definition"
    bib = fx.GOOD_BIB.replace("Emission factors", "Emission factors, second edition")
    assert _pair(tmp_path, edit, new_kw={"equations": eq, "glossary": gl, "bib": bib}) == []


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle("hand-calculation", "folders without catalogues are compared on their rows")
def test_fr_008_20_folders_without_catalogues_are_compared_on_rows(tmp_path: Path) -> None:
    def edit(tables: dict[str, Any], _sa: dict[str, Any]) -> None:
        _row(tables, "blasting", "inch")["value"] = 0.0255

    assert _pair(
        tmp_path, edit, old_kw={"equations": None, "glossary": None}, new_kw={"equations": None, "glossary": None}
    ) == ["inch"]


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle("hand-calculation", "the argument order matters only for added and removed, not for the id set")
def test_fr_008_20_is_symmetric_in_its_arguments(tmp_path: Path) -> None:
    def edit(tables: dict[str, Any], _sa: dict[str, Any]) -> None:
        _row(tables, "haulage", "max_grade")["range"] = {"min": 0.0, "max": 0.3}
        tables["haulage"]["rows"].append(fx.row(id="zz_new_row", symbol="minephys.haulage.f", notes=fx.DROP))

    old_tables, sa = fx.good_tables(), fx.good_share_alike()
    new_tables = copy.deepcopy(old_tables)
    edit(new_tables, sa)
    old = fx.write_tree(tmp_path / "old", tables=old_tables, share_alike=sa)
    new = fx.write_tree(tmp_path / "new", tables=new_tables, share_alike=sa)
    forward = list(_k().knowledge_changes(old, new))
    backward = list(_k().knowledge_changes(new, old))
    assert forward == backward == ["max_grade", "zz_new_row"]


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle("hand-calculation", "hostile arguments raise InputError")
@pytest.mark.parametrize("bad", [None, 42, "no/such/folder", b"bytes"], ids=["none", "int", "missing", "bytes"])
def test_fr_008_20_bad_arguments_raise_input_error(tmp_path: Path, bad: Any) -> None:
    import minephys

    good = fx.write_tree(tmp_path / "good")
    with pytest.raises((minephys.InputError, minephys.InputTypeError)) as e1:
        _k().knowledge_changes(bad, good)
    assert e1.value.argument in {"old_dir", "old"}
    with pytest.raises((minephys.InputError, minephys.InputTypeError)) as e2:
        _k().knowledge_changes(good, bad)
    assert e2.value.argument in {"new_dir", "new"}


@pytest.mark.req("FR-008-20")
@pytest.mark.oracle("hand-calculation", "it reads the folders it is given and writes nothing")
def test_fr_008_20_leaves_both_folders_untouched(tmp_path: Path) -> None:
    old = fx.write_tree(tmp_path / "old")
    new = fx.write_tree(tmp_path / "new")

    def snapshot(d: Path) -> dict[str, bytes]:
        return {str(p.relative_to(d)): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file()}

    before = (snapshot(old), snapshot(new))
    _k().knowledge_changes(old, new)
    assert (snapshot(old), snapshot(new)) == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["new", "old"]

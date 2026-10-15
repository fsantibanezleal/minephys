"""T-008-020 (FR-008-11, FR-008-12, FR-008-13): `get_value` kinds, `UnverifiedParameterWarning` by role, no default filtering.

Expected behaviour (`minephys.knowledge`):
- `get_value(id)` returns a `value` row as a float (a `"p/q"` string is evaluated as p / q in float64) and a `range` row as the tuple
  `(min, max)` of floats;
- when `get_value` is called for an UNVERIFIED row whose `role` is `model_constant` or `parameter`, it emits
  `UnverifiedParameterWarning` (a `UserWarning` subclass, importable from `minephys.knowledge`) naming the row id and its citation
  key; rows of role `limit` and `conversion` do not warn, and neither do verified rows;
- `list_parameters()` without filters, `export()` and the rendered pages include every row, UNVERIFIED ones included, each carrying its
  verification status.
Run in a fresh interpreter served a fixture package tree (tests/_knowledge_fixtures.py).

Oracle: fixture rows with hand-known values (`19/30` is evaluated by plain Python division and compared bit for bit with `float.hex`),
and hand-counted rows per status and role.
"""

from __future__ import annotations

import copy
from pathlib import Path

import _knowledge_fixtures as fx
import pytest


def _tables() -> dict[str, dict]:
    t = copy.deepcopy(fx.good_tables())
    rows = t["haulage"]["rows"]
    rows[1]["role"] = "model_constant"  # UNVERIFIED model_constant (rational value)
    rows.append(
        fx.row(
            id="unv_parameter",
            quantity="an unverified parameter",
            value=2.5,
            units="m",
            role="parameter",
            citation="doe2020",
            page="p. 9",
            verification="UNVERIFIED",
            verified_on=fx.DROP,
            symbol="minephys.haulage.a",
            notes=fx.DROP,
        )
    )
    rows.append(
        fx.row(
            id="unv_limit",
            quantity="an unverified limit",
            value=70,
            units="um",
            role="limit",
            citation="doe2020",
            page="p. 1",
            verification="UNVERIFIED",
            verified_on=fx.DROP,
            symbol="minephys.haulage.b",
            notes=fx.DROP,
        )
    )
    rows.append(
        fx.row(
            id="unv_conversion",
            quantity="an unverified conversion",
            value=3.6e6,
            units="J",
            role="conversion",
            citation="doe2020",
            page="p. 2",
            verification="UNVERIFIED",
            verified_on=fx.DROP,
            symbol="minephys.haulage.c",
            notes=fx.DROP,
        )
    )
    rows.append(
        fx.row(
            id="ver_parameter",
            quantity="a verified parameter",
            value=4,
            units="m",
            role="parameter",
            citation="doe2020",
            page="p. 3",
            symbol="minephys.haulage.d",
            notes=fx.DROP,
        )
    )
    rows.append(
        fx.row(
            id="unv_range_const",
            quantity="an unverified ranged constant",
            value=fx.DROP,
            range={"min": 0.5, "max": 1.5},
            units="1",
            role="model_constant",
            citation="agency2025",
            page="p. 4",
            verification="UNVERIFIED",
            verified_on=fx.DROP,
            symbol="minephys.haulage.e",
            notes=fx.DROP,
        )
    )
    return t


@pytest.mark.req("FR-008-11")
@pytest.mark.oracle(
    "hand-calculation", "19/30 evaluated in float64 by plain division; ranges as (min, max); plain numbers as floats"
)
def test_fr_008_11_get_value_kinds(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", tables=_tables())
    got = fx.run_api(
        base,
        """
warnings.simplefilter("ignore")
r = K.get_value("rolling_resistance_default")
rng = K.get_value("max_grade")
print(json.dumps({"rational": [type(r).__name__, r.hex()], "float": [type(K.get_value("diesel_co2_factor")).__name__, K.get_value("diesel_co2_factor")],
                  "int_value": [type(K.get_value("unv_limit")).__name__, K.get_value("unv_limit")],
                  "range": [type(rng).__name__, [type(x).__name__ for x in rng], list(rng)],
                  "range2": list(K.get_value("unv_range_const")), "sci": K.get_value("unv_conversion"), "inch": K.get_value("inch")}))
""",
    )
    assert got["rational"] == ["float", (19 / 30).hex()]  # bit-equal to 19/30
    assert got["float"] == ["float", 10.21] and got["int_value"] == ["float", 70.0]
    assert got["range"] == ["tuple", ["float", "float"], [0.0, 0.15]] and got["range2"] == [0.5, 1.5]
    assert got["sci"] == 3.6e6 and got["inch"] == 0.0254


@pytest.mark.req("FR-008-12")
@pytest.mark.oracle(
    "hand-calculation",
    "FR-008-12: warn for UNVERIFIED model_constant and parameter only, naming the id and the citation key",
)
def test_fr_008_12_warnings_by_role_and_status(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", tables=_tables())
    got = fx.run_api(
        base,
        """
from minephys.knowledge import UnverifiedParameterWarning
ids = ["rolling_resistance_default", "unv_parameter", "unv_range_const", "unv_limit", "unv_conversion", "ver_parameter", "diesel_co2_factor", "inch", "max_grade"]
out = {}
for rid in ids:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        K.get_value(rid)
    out[rid] = [[w.category.__name__, str(w.message)] for w in rec if issubclass(w.category, UnverifiedParameterWarning)]
with warnings.catch_warnings(record=True) as rec:  # each call warns again
    warnings.simplefilter("always")
    K.get_value("unv_parameter"); K.get_value("unv_parameter")
print(json.dumps({"out": out, "twice": len(rec), "is_user_warning": issubclass(UnverifiedParameterWarning, UserWarning),
                  "exported": "UnverifiedParameterWarning" in dir(K)}))
""",
    )
    assert got["is_user_warning"] and got["exported"]
    for rid, citation in (
        ("rolling_resistance_default", "doe2020"),
        ("unv_parameter", "doe2020"),
        ("unv_range_const", "agency2025"),
    ):
        warns = got["out"][rid]
        assert len(warns) == 1 and warns[0][0] == "UnverifiedParameterWarning", (rid, warns)
        assert rid in warns[0][1] and citation in warns[0][1], warns
    for rid in ("unv_limit", "unv_conversion", "ver_parameter", "diesel_co2_factor", "inch", "max_grade"):
        assert got["out"][rid] == [], rid  # limits and conversions never warn; verified rows never warn
    assert got["twice"] == 2


@pytest.mark.req("FR-008-12")
def test_fr_008_12_other_lookups_do_not_warn(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", tables=_tables())
    got = fx.run_api(
        base,
        """
with warnings.catch_warnings(record=True) as rec:
    warnings.simplefilter("always")
    K.get_parameter("unv_parameter"); K.list_parameters(verification="UNVERIFIED"); K.load_table("haulage"); K.export(); K.export_json()
print(json.dumps(len(rec)))
""",
    )
    assert got == 0, (
        "only get_value warns about UNVERIFIED constants (the other accessors are how a reader surfaces them)"
    )


@pytest.mark.req("FR-008-13")
@pytest.mark.oracle("hand-calculation", "no default filtering: every row is listed and exported with its status")
def test_fr_008_13_unverified_rows_are_never_hidden(tmp_path: Path) -> None:
    tables = _tables()
    base = fx.write_package_tree(tmp_path / "pkg", tables=tables, share_alike=fx.good_share_alike())
    got = fx.run_api(
        base,
        """
rows = K.list_parameters()
exp = K.export()
exported = {r["id"]: r["verification"] for t in exp["tables"] for r in t["rows"]}
print(json.dumps({"listed": sorted((r.id, r.verification) for r in rows), "exported": sorted(exported.items()),
                  "summary": exp["summary"]["rows"], "per_role": exp["summary"]["per_role"]}))
""",
    )
    expected = sorted(
        (r["id"], r["verification"]) for t in (*tables.values(), *fx.good_share_alike().values()) for r in t["rows"]
    )
    assert [tuple(x) for x in got["listed"]] == expected
    assert [tuple(x) for x in got["exported"]] == expected
    unverified = sum(1 for _, v in expected if v == "UNVERIFIED")
    assert got["summary"] == {"total": len(expected), "unverified": unverified}
    roles = {}
    for t in (*tables.values(), *fx.good_share_alike().values()):
        for r in t["rows"]:
            c = roles.setdefault(r["role"], {"total": 0, "unverified": 0})
            c["total"] += 1
            c["unverified"] += r["verification"] == "UNVERIFIED"
    assert {k: got["per_role"][k] for k in roles} == roles

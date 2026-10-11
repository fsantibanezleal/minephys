"""T-008-015 (FR-008-10): hostile table names and unknown ids (path traversal, no file opened).

Expected behaviour (`minephys.knowledge`): `load_table(table)` with a name that is not one of `list_tables()` (including names containing
`/`, `\\`, `..`, a drive or an absolute path, and the empty string), and `get_parameter(id)` / `get_value(id)` with an unknown id, raise
`minephys.InputError` naming the argument (`table` or `id`) without opening any file; a non-string argument raises
`minephys.InputTypeError`. "Without opening any file" is checked with an audit hook installed after the knowledge has been loaded once
(a warm-up call opens the package data): the hostile calls must raise no `open` audit event at all.

Oracle: the hand-written hostile names of spec 008 plan (`../haulage`, `a/b`, `C:\\x`, `/etc/x`, `""`, `None`, `3`) and more.
"""

from __future__ import annotations

from pathlib import Path

import _knowledge_fixtures as fx
import pytest

HOSTILE_NAMES = [
    "../haulage",
    "..\\haulage",
    "..",
    "...",
    "a/b",
    "a\\b",
    "haulage/",
    "/haulage",
    "/etc/passwd",
    "C:\\x",
    "C:/Windows/win.ini",
    "\\\\server\\share\\x",
    "haulage.yaml",
    "haulage\x00",
    "haulage\n",
    " haulage",
    "HAULAGE",
    "Haulage",
    "no_such_table",
    "",
    " ",
    "h\u202eaulage",
    "haulage" * 300,
    "../" * 50 + "etc/passwd",
    "share-alike/geotech_sa",
    "catalogue/equations",
    "references",
    "%2e%2e%2fhaulage",
]
NON_STRINGS = [
    "None",
    "3",
    "3.5",
    "True",
    "b'haulage'",
    "['haulage']",
    "('haulage',)",
    "{'t': 1}",
    "object()",
    "complex(1, 2)",
]
UNKNOWN_IDS = [
    "",
    "no_such_row",
    "DIESEL_CO2_FACTOR",
    " diesel_co2_factor",
    "diesel_co2_factor ",
    "../diesel_co2_factor",
    "a/b",
    "diesel\x00",
    "x" * 5000,
]


@pytest.mark.req("FR-008-10")
@pytest.mark.oracle("hand-calculation", "hostile table names raise InputError('table') and open no file")
def test_fr_008_10_hostile_table_names(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg")
    script = f"""
K.load_table("haulage"); K.get_parameter("diesel_co2_factor"); K.list_parameters()
events = []
sys.addaudithook(lambda ev, args: events.append((ev, str(args[0])[:80])) if ev == "open" else None)
names = {HOSTILE_NAMES!r}
out = []
for value in names:
    try:
        K.load_table(value)
        out.append({{"ok": True}})
    except BaseException as e:
        out.append(_err(e))
print(json.dumps({{"results": out, "opens": events}}))
"""
    got = fx.run_api(base, script)
    assert got["opens"] == [], f"files were opened: {got['opens']}"
    for name, res in zip(HOSTILE_NAMES, got["results"], strict=True):
        assert res.get("ok") is not True, f"{name!r} was accepted"
        assert res["type"] == "InputError" and res["argument"] == "table" and res["is_value_error"], (name[:40], res)


@pytest.mark.req("FR-008-10")
@pytest.mark.oracle("hand-calculation", "non-string table names and ids raise InputTypeError and open no file")
def test_fr_008_10_non_string_arguments(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg")
    for fn, arg in (("load_table", "table"), ("get_parameter", "id"), ("get_value", "id")):
        script = f"""
K.load_table("haulage"); K.get_parameter("diesel_co2_factor")
events = []
sys.addaudithook(lambda ev, args: events.append((ev, str(args[0])[:80])) if ev == "open" else None)
out = []
for value in [{", ".join(NON_STRINGS)}]:
    try:
        K.{fn}(value)
        out.append({{"ok": True}})
    except BaseException as e:
        out.append(_err(e))
print(json.dumps({{"results": out, "opens": events}}))
"""
        got = fx.run_api(base, script)
        assert got["opens"] == []
        for src, res in zip(NON_STRINGS, got["results"], strict=True):
            assert res.get("ok") is not True, (fn, src)
            assert res["type"] == "InputTypeError" and res["argument"] == arg and res["is_type_error"], (fn, src, res)


@pytest.mark.req("FR-008-10")
@pytest.mark.oracle("hand-calculation", "unknown ids raise InputError('id') and open no file")
@pytest.mark.parametrize("fn", ["get_parameter", "get_value"])
def test_fr_008_10_unknown_ids(tmp_path: Path, fn: str) -> None:
    base = fx.write_package_tree(tmp_path / "pkg")
    script = f"""
K.load_table("haulage"); K.get_parameter("diesel_co2_factor")
events = []
sys.addaudithook(lambda ev, args: events.append((ev, str(args[0])[:80])) if ev == "open" else None)
ids = {UNKNOWN_IDS!r}
out = []
for value in ids:
    try:
        K.{fn}(value)
        out.append({{"ok": True}})
    except BaseException as e:
        out.append(_err(e))
print(json.dumps({{"results": out, "opens": events}}))
"""
    got = fx.run_api(base, script)
    assert got["opens"] == [], f"files were opened: {got['opens']}"
    for name, res in zip(UNKNOWN_IDS, got["results"], strict=True):
        assert res.get("ok") is not True, f"{name[:30]!r} was accepted"
        assert res["type"] == "InputError" and res["argument"] == "id" and res["is_value_error"], (name[:30], res)


@pytest.mark.req("FR-008-10")
def test_fr_008_10_valid_names_still_work_and_share_alike_names_are_plain_stems(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", share_alike=fx.good_share_alike())
    got = fx.run_api(
        base,
        """
print(json.dumps({"tables": list(K.list_tables()), "sa": K.load_table("geotech_sa").licence, "row": K.get_parameter("sa_cohesion_default").units,
                  "value": K.get_value("diesel_co2_factor")}))
""",
    )
    assert got["tables"] == ["blasting", "geotech_sa", "haulage"] and got["sa"] == "CC-BY-SA-4.0"
    assert got["row"] == "kPa" and got["value"] == 10.21

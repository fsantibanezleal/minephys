"""T-008-013 (FR-008-06, FR-008-07): schema errors and hostile YAML (size, encoding, tags, aliases, duplicates, depth).

Expected behaviour (`minephys.knowledge`):
- FR-008-06: when a packaged or user-supplied knowledge file violates FR-008-02 to FR-008-05, the LOADER (`list_tables()`, `load_table`,
  `get_parameter`, ... on first use) raises `KnowledgeSchemaError` (a `ValueError` with `file`, `index` and `field` attributes) whose message
  names the file, the 1-based row or entry index and the field, and returns no partially validated data (every later call raises too,
  even for the files that were valid); `validate_tables(folder)` lists every error instead of raising.
- FR-008-07: a YAML file larger than 1 MiB, not valid UTF-8, using a tag outside the YAML core schema (for example
  `!!python/object/apply:...`), an anchor or alias, a repeated mapping key, nesting deeper than 8 levels, or whose top level is not
  a mapping is rejected with `KnowledgeSchemaError` without constructing arbitrary objects or expanding aliases (a payload that would
  create a marker file when executed is used to prove that nothing is executed).
The loader tests run in a fresh interpreter served a fixture package tree (tests/_knowledge_fixtures.py).

Oracle: hand-written hostile files, each with the rule it violates (spec 008 section 7 "Hardened YAML"), and a marker file as the
witness that no constructor ran.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import _knowledge_fixtures as fx
import pytest

GOOD_HAULAGE = fx.dump(fx.good_tables()["haulage"])


def _k():
    return importlib.import_module("minephys.knowledge")


def _hostile_cases(marker: Path) -> dict[str, bytes | str]:
    m = str(marker).replace("\\", "/")
    base = GOOD_HAULAGE
    replace_title = lambda new: base.replace("title: Haulage constants and parameters", new, 1)  # noqa: E731
    pad = 1_048_577 - len(base.encode("utf-8")) - 2  # the file is exactly 1 MiB + 1 byte
    cases: dict[str, bytes | str] = {
        "oversized": (base + "\n#" + "x" * pad).encode("utf-8"),
        "invalid-utf8": base.encode("utf-8") + b"\n# \xff\xfe\n",
        "utf16-bom": b"\xff\xfe" + base.encode("utf-16-le"),
        "python-object-apply": replace_title(f'title: !!python/object/apply:builtins.open ["{m}", "w"]'),
        "python-name": replace_title("title: !!python/name:os.system"),
        "python-object-new": replace_title(f'title: !!python/object/new:builtins.open ["{m}", "w"]'),
        "custom-tag": replace_title("title: !custom value"),
        "set-tag": replace_title("title: !!set {a, b}"),
        "binary-tag": replace_title("title: !!binary aGVsbG8="),
        "anchor": replace_title("title: &t Haulage constants"),
        "alias": replace_title("title: &t Haulage constants\nsubtitle: *t"),
        "alias-bomb": (
            "title: Haulage\nlicence: CC-BY-4.0\ntable: haulage\nschema_version: 1\n"
            "a: &a [x, x, x, x, x, x, x, x, x]\nb: &b [*a, *a, *a, *a, *a, *a, *a, *a, *a]\n"
            "c: &c [*b, *b, *b, *b, *b, *b, *b, *b, *b]\nd: &d [*c, *c, *c, *c, *c, *c, *c, *c, *c]\nrows: []\n"
        ),
        "merge-key": base + "\nbase: &b {x: 1}\nother:\n  <<: *b\n",
        "duplicate-top-key": base + "\ntitle: Another title\n",
        "duplicate-row-key": "schema_version: 1\ntable: haulage\ntitle: T\nlicence: CC-BY-4.0\nrows:\n  - id: a\n    page: x\n    page: y\n",
        "duplicate-flow-key": "schema_version: 1\ntable: haulage\ntitle: T\nlicence: CC-BY-4.0\nrows: [{id: a, id: b}]\n",
        "depth-9": base + "\ndeep: {a: {a: {a: {a: {a: {a: {a: {a: 1}}}}}}}}\n",
        "depth-9-sequences": base + "\ndeep: [[[[[[[[1]]]]]]]]\n",
        "top-level-list": "- a\n- b\n",
        "top-level-scalar": "just some text\n",
        "top-level-null": "null\n",
        "empty-file": "",
        "comment-only": "# nothing here\n",
        "two-documents": base + "\n---\n" + base,
    }
    return cases


CASE_NAMES = list(_hostile_cases(Path("marker.txt")))


def _tree(tmp_path: Path, content: bytes | str) -> Path:
    tables = fx.good_tables()
    root = fx.write_package_tree(
        tmp_path / "pkg", tables={"blasting": tables["blasting"]}, equations=None, glossary=None
    )
    target = root / "knowledge" / "haulage.yaml"
    target.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    return root


@pytest.mark.req("FR-008-07")
@pytest.mark.oracle(
    "hand-calculation", "FR-008-07 hostile YAML classes: validate_tables lists the file, nothing is executed"
)
@pytest.mark.parametrize("name", CASE_NAMES)
def test_fr_008_07_validate_tables_rejects_hostile_yaml(tmp_path: Path, name: str) -> None:
    marker = tmp_path / "marker.txt"
    root = _tree(tmp_path, _hostile_cases(marker)[name])
    report = _k().validate_tables(root / "knowledge")
    assert any(str(e.file).replace("\\", "/").endswith("haulage.yaml") for e in report.errors), [
        (str(e.file), e.field) for e in report.errors
    ]
    assert not marker.exists(), "a YAML constructor was executed"


@pytest.mark.req("FR-008-07")
@pytest.mark.req("FR-008-06")
@pytest.mark.parametrize("name", CASE_NAMES)
def test_fr_008_07_loader_raises_knowledge_schema_error_and_returns_no_partial_data(tmp_path: Path, name: str) -> None:
    marker = tmp_path / "marker.txt"
    root = _tree(tmp_path, _hostile_cases(marker)[name])
    got = fx.run_api(
        root,
        """
outcome = {}
for label, call in (("list_tables", lambda: K.list_tables()), ("again", lambda: K.list_tables()),
                    ("valid_table_row", lambda: K.get_parameter("inch")), ("load_valid", lambda: K.load_table("blasting"))):
    try:
        outcome[label] = {"ok": True, "value": repr(call())[:60]}
    except BaseException as e:
        outcome[label] = {"ok": False, **_err(e)}
print(json.dumps(outcome))
""",
    )
    first = got["list_tables"]
    assert first["ok"] is False and first["type"] == "KnowledgeSchemaError" and first["is_value_error"], first
    assert "haulage" in str(first["file"]) or "haulage" in first["msg"]
    for label in (
        "again",
        "valid_table_row",
        "load_valid",
    ):  # no partially validated data: the valid file is not served either
        assert got[label]["ok"] is False and got[label]["type"] == "KnowledgeSchemaError", (label, got[label])
    assert not marker.exists(), "a YAML constructor was executed"


@pytest.mark.req("FR-008-06")
@pytest.mark.oracle("hand-calculation", "the error names the file, the 1-based row index and the field")
def test_fr_008_06_the_loader_error_names_file_row_and_field(tmp_path: Path) -> None:
    tables = fx.good_tables()
    del tables["haulage"]["rows"][1]["page"]  # row 2 of haulage
    base = fx.write_package_tree(tmp_path / "pkg", tables=tables)
    got = fx.run_api(
        base,
        """
try:
    K.load_table("haulage")
    print(json.dumps({"ok": True}))
except BaseException as e:
    print(json.dumps({"ok": False, **_err(e)}))
""",
    )
    assert got["ok"] is False and got["type"] == "KnowledgeSchemaError" and got["is_value_error"]
    assert str(got["file"]).replace("\\", "/").endswith("haulage.yaml")
    assert got["index"] == 2 and got["field"] == "page"
    assert "haulage" in got["msg"] and "2" in got["msg"] and "page" in got["msg"]


@pytest.mark.req("FR-008-06")
@pytest.mark.parametrize(
    ("kind", "mutate", "stem", "index", "field"),
    [
        ("equation", lambda eq, gl, t: eq["equations"][1].update(domain="astrology"), "equations", 2, "domain"),
        ("glossary", lambda eq, gl, t: gl["terms"][2].pop("term_es"), "glossary", 3, "term_es"),
        (
            "cross-file",
            lambda eq, gl, t: t["haulage"]["rows"][1].update(citation="ghost2001"),
            "haulage",
            2,
            "citation",
        ),
    ],
    ids=["equation", "glossary", "cross-file"],
)
def test_fr_008_06_errors_in_catalogues_and_cross_file_rules(
    tmp_path: Path, kind: str, mutate: Any, stem: str, index: int, field: str
) -> None:
    eq, gl, tables = fx.good_equations(), fx.good_glossary(), fx.good_tables()
    mutate(eq, gl, tables)
    base = fx.write_package_tree(tmp_path / "pkg", tables=tables, equations=eq, glossary=gl)
    got = fx.run_api(
        base,
        """
try:
    K.list_tables()
    print(json.dumps({"ok": True}))
except BaseException as e:
    print(json.dumps({"ok": False, **_err(e)}))
""",
    )
    assert got["ok"] is False and got["type"] == "KnowledgeSchemaError"
    assert (
        str(got["file"]).replace("\\", "/").endswith(f"{stem}.yaml") and got["index"] == index and got["field"] == field
    )


@pytest.mark.req("FR-008-06")
@pytest.mark.req("FR-008-19")
@pytest.mark.oracle("hand-calculation", "three independent errors: exactly three are listed (not only the first)")
def test_fr_008_06_validate_lists_every_error(tmp_path: Path) -> None:
    tables = fx.good_tables()
    del tables["haulage"]["rows"][1]["page"]  # error 1
    tables["haulage"]["rows"][2]["role"] = "bogus"  # error 2
    eq = fx.good_equations()
    eq["equations"][1]["domain"] = "astrology"  # error 3
    report = _k().validate_tables(fx.write_tree(tmp_path / "k", tables=tables, equations=eq))
    found = sorted((Path(str(e.file)).name, e.index, e.field) for e in report.errors)
    assert found == [("equations.yaml", 2, "domain"), ("haulage.yaml", 2, "page"), ("haulage.yaml", 3, "role")], found
    assert len(report.errors) == 3

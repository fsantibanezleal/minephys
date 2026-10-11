"""T-008-016 (FR-008-22): an absent catalogue reads as empty; a present table or catalogue file with no row or entry is rejected.

Expected behaviour (`minephys.knowledge`): where `catalogue/equations.yaml` or `catalogue/glossary.yaml` is absent because no entry has
been written yet, the loader treats that catalogue as empty (`equations()` and `glossary()` return an empty tuple and the export lists
no entry of it); no knowledge table or catalogue file is shipped without at least one row or entry, so an empty file that is present
is rejected (`KnowledgeSchemaError` from the loader, an error in `validate_tables`).

Oracle: hand-written package trees with no catalogue files, with only one of them, and with empty files (spec 008 FR-008-22).
"""

from __future__ import annotations

import importlib
from pathlib import Path

import _knowledge_fixtures as fx
import pytest


def _k():
    return importlib.import_module("minephys.knowledge")


@pytest.mark.req("FR-008-22")
@pytest.mark.oracle("hand-calculation", "a package tree with no catalogue files reads as empty tuples")
def test_fr_008_22_absent_catalogues_read_as_empty(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", equations=None, glossary=None)
    assert not (base / "knowledge" / "catalogue").exists()
    got = fx.run_api(
        base,
        """
exp = K.export()
print(json.dumps({"eq": [type(K.equations()).__name__, len(K.equations())], "gl": [type(K.glossary()).__name__, len(K.glossary())],
                  "eq_dom": len(K.equations(domain="blasting")), "gl_dom": len(K.glossary(domain="general")),
                  "export_eq": exp["equations"], "export_gl": exp["glossary"], "summary": [exp["summary"]["equations"], exp["summary"]["terms"]],
                  "tables": list(K.list_tables())}))
""",
    )
    assert got["eq"] == ["tuple", 0] and got["gl"] == ["tuple", 0] and got["eq_dom"] == 0 and got["gl_dom"] == 0
    assert got["export_eq"] == [] and got["export_gl"] == []
    assert got["summary"] == [{"total": 0, "unverified": 0}, 0]
    assert got["tables"] == ["blasting", "haulage"]


@pytest.mark.req("FR-008-22")
def test_fr_008_22_absent_catalogues_are_not_validation_errors(tmp_path: Path) -> None:
    for name, kw in (
        ("none", {"equations": None, "glossary": None}),
        ("only-equations", {"glossary": None}),
        ("only-glossary", {"equations": None}),
    ):
        report = _k().validate_tables(fx.write_tree(tmp_path / name, **kw))
        assert list(report.errors) == [], name


@pytest.mark.req("FR-008-22")
@pytest.mark.oracle("hand-calculation", "one catalogue present, the other absent")
def test_fr_008_22_one_present_one_absent(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", glossary=None)
    got = fx.run_api(base, "print(json.dumps([sorted(e.id for e in K.equations()), len(K.glossary())]))")
    assert got == [["co2_from_diesel", "powder_factor"], 0]


@pytest.mark.req("FR-008-22")
@pytest.mark.req("FR-008-04")
@pytest.mark.parametrize(
    ("which", "content"),
    [
        ("equations", {"schema_version": 1, "title": "Equations", "licence": "CC-BY-4.0", "equations": []}),
        ("equations", "schema_version: 1\ntitle: Equations\nlicence: CC-BY-4.0\nequations:\n"),  # null list
        ("equations", ""),  # an empty file
        ("equations", "# only a comment\n"),
        ("glossary", {"schema_version": 1, "title": "Glossary", "licence": "CC-BY-4.0", "terms": []}),
        ("glossary", "schema_version: 1\ntitle: Glossary\nlicence: CC-BY-4.0\nterms: []\n"),
        ("glossary", ""),
        ("glossary", "---\n"),
    ],
    ids=[
        "eq-empty-list",
        "eq-null-list",
        "eq-empty-file",
        "eq-comment-only",
        "gl-empty-list",
        "gl-flow-empty-list",
        "gl-empty-file",
        "gl-document-marker",
    ],
)
def test_fr_008_22_a_present_empty_catalogue_is_rejected(tmp_path: Path, which: str, content: object) -> None:
    kw = {"equations": "default", "glossary": "default"}
    kw[which] = content
    folder = fx.write_tree(tmp_path / "k", **kw)
    report = _k().validate_tables(folder)
    assert any(str(e.file).replace("\\", "/").endswith(f"{which}.yaml") for e in report.errors), [
        (str(e.file), e.field) for e in report.errors
    ]
    base = fx.write_package_tree(tmp_path / "pkg", **kw)
    got = fx.run_api(
        base,
        """
try:
    K.equations() if %r == "equations" else K.glossary()
    print(json.dumps({"ok": True}))
except BaseException as e:
    print(json.dumps({"ok": False, **_err(e)}))
"""
        % which,
    )
    assert got["ok"] is False and got["type"] == "KnowledgeSchemaError"


@pytest.mark.req("FR-008-22")
@pytest.mark.req("FR-008-02")
@pytest.mark.parametrize(
    "content",
    [
        {"schema_version": 1, "table": "haulage", "title": "T", "licence": "CC-BY-4.0", "rows": []},
        "schema_version: 1\ntable: haulage\ntitle: T\nlicence: CC-BY-4.0\nrows:\n",
        "",
        "# nothing\n",
    ],
    ids=["empty-rows", "null-rows", "empty-file", "comment-only"],
)
def test_fr_008_22_a_table_file_without_rows_is_rejected(tmp_path: Path, content: object) -> None:
    tables = fx.good_tables()
    tables["haulage"] = content  # type: ignore[assignment]
    folder = fx.write_tree(tmp_path / "k", tables=tables)
    report = _k().validate_tables(folder)
    assert any(str(e.file).replace("\\", "/").endswith("haulage.yaml") for e in report.errors)
    base = fx.write_package_tree(tmp_path / "pkg", tables=tables)
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


@pytest.mark.req("FR-008-22")
@pytest.mark.oracle(
    "hand-calculation", "a package with no table at all, or only an empty tables folder, ships nothing to list"
)
def test_fr_008_22_no_table_files_means_no_tables(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", tables={}, equations=None, glossary=None)
    got = fx.run_api(base, "print(json.dumps(list(K.list_tables())))")
    assert got == []

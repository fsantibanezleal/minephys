"""T-008-032 (FR-008-17): hostile output paths and CLI usage errors.

Expected behaviour (`minephys.knowledge`): if `render_pages`, `validate_tables` or `knowledge_changes` gets a directory argument that is not an
existing directory, if the export command gets an output path that is an existing directory or whose parent does not exist, or if the CLI
gets an unknown subcommand or option, then the function raises `minephys.InputError` (CLI: exit code 2) and writes nothing; no function
writes a file whose name comes from knowledge data other than a table stem that passed FR-008-02 (a table whose stem or `table` field is not a
valid identifier is rejected, and no page is written for it).

Oracle: hand-written hostile paths and fixture trees; "writes nothing" is checked by listing the target folders before and after.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import _knowledge_fixtures as fx
import pytest


def _k():
    return importlib.import_module("minephys.knowledge")


def _errors():
    importlib.import_module("minephys.knowledge")
    import minephys

    return minephys.InputError, minephys.InputTypeError


@pytest.mark.req("FR-008-17")
@pytest.mark.oracle("hand-calculation", "a directory argument that is not an existing directory raises InputError")
def test_fr_008_17_directory_arguments_must_exist(tmp_path: Path) -> None:
    input_error, _ = _errors()
    k = _k()
    a_file = tmp_path / "a_file.txt"
    a_file.write_text("x", encoding="utf-8")
    missing = tmp_path / "missing"
    base = fx.write_package_tree(tmp_path / "pkg")
    for bad in (a_file, missing, tmp_path / "a_file.txt" / "sub"):
        with pytest.raises(input_error) as exc:
            k.validate_tables(bad)
        assert exc.value.argument == "path"
        with pytest.raises(input_error) as exc:
            k.knowledge_changes(bad, base / "knowledge")
        assert exc.value.argument in {"old_dir", "old"}
        with pytest.raises(input_error) as exc:
            k.knowledge_changes(base / "knowledge", bad)
        assert exc.value.argument in {"new_dir", "new"}
    got = fx.run_api(
        base,
        """
out = {}
for label, target in (("file", %r), ("missing", %r)):
    try:
        K.render_pages(target)
        out[label] = {"ok": True}
    except BaseException as e:
        out[label] = _err(e)
print(json.dumps(out))
"""
        % (str(a_file), str(missing)),
    )
    for label in ("file", "missing"):
        assert got[label]["type"] == "InputError" and got[label]["argument"] in {"out_dir", "directory", "path"}, got[
            label
        ]
    assert not missing.exists() and a_file.read_text(encoding="utf-8") == "x"


@pytest.mark.req("FR-008-17")
@pytest.mark.oracle(
    "hand-calculation", "the export command: an output path that is a directory, or whose parent is missing, exits 2"
)
def test_fr_008_17_export_output_paths(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg")
    a_dir = tmp_path / "a_dir"
    a_dir.mkdir()
    no_parent = tmp_path / "missing_parent" / "out.json"
    for target in (a_dir, no_parent):
        proc = fx.run_cli(["export", "--out", str(target)], base)
        assert proc.returncode == 2, (target, proc.returncode, proc.stderr[-300:])
    assert list(a_dir.iterdir()) == [] and not no_parent.parent.exists()
    ok = tmp_path / "ok.json"
    assert fx.run_cli(["export", "--out", str(ok)], base).returncode == 0 and ok.is_file()


@pytest.mark.req("FR-008-17")
def test_fr_008_17_render_and_validate_commands_reject_bad_directories(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg")
    a_file = tmp_path / "a_file.txt"
    a_file.write_text("x", encoding="utf-8")
    missing = tmp_path / "missing"
    for target in (a_file, missing):
        assert fx.run_cli(["render", "--out-dir", str(target)], base).returncode == 2, target
        assert fx.run_cli(["validate", str(target)]).returncode == 2, target
    assert not missing.exists() and a_file.read_text(encoding="utf-8") == "x"


@pytest.mark.req("FR-008-17")
@pytest.mark.oracle(
    "hand-calculation", "no file is written with a name taken from knowledge data that failed the table-stem rule"
)
@pytest.mark.parametrize(
    "stem",
    ["evil name", "Evil", "1evil", "..", "a" * 80, "café", "x;y"],
    ids=["space", "uppercase", "digit-first", "dotdot", "too-long", "non-ascii", "semicolon"],
)
def test_fr_008_17_a_bad_table_name_is_rejected_and_no_page_is_written(tmp_path: Path, stem: str) -> None:
    table = fx.good_tables()["blasting"]
    table["table"] = stem
    tables = {"haulage": fx.good_tables()["haulage"]}
    root = fx.write_package_tree(tmp_path / "pkg", tables=tables, equations=None, glossary=None)
    (root / "knowledge" / "evil.yaml").write_text(
        fx.dump(table), encoding="utf-8", newline="\n"
    )  # the stem `evil` differs from the table field
    pages = tmp_path / "pages"
    pages.mkdir()
    report = _k().validate_tables(root / "knowledge")
    assert any(e.field == "table" for e in report.errors), [(str(e.file), e.field) for e in report.errors]
    got = fx.run_api(
        root,
        """
try:
    K.render_pages(%r)
    print(json.dumps({"ok": True}))
except BaseException as e:
    print(json.dumps({"ok": False, **_err(e)}))
"""
        % str(pages),
    )
    assert got["ok"] is False and got["type"] == "KnowledgeSchemaError"
    assert list(pages.iterdir()) == [], "no page may be written when the knowledge is invalid"


@pytest.mark.req("FR-008-17")
def test_fr_008_17_valid_table_stems_produce_pages_named_after_the_stem_only(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", share_alike=fx.good_share_alike())
    pages = tmp_path / "pages"
    pages.mkdir()
    fx.run_api(base, "K.render_pages(%r); print(json.dumps(True))" % str(pages))
    names = sorted(p.name for p in pages.iterdir())
    assert names == ["bibliography.md", "blasting.md", "equations.md", "geotech_sa.md", "glossary.md", "haulage.md"]
    assert all(not p.is_dir() for p in pages.iterdir())

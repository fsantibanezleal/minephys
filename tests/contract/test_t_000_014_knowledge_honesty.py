"""T-000-014 (FR-000-20, FR-000-21, FR-000-22, FR-000-31): knowledge honesty checks, `tools/check_knowledge.py`.

Expected CLI (the file lives in the repository `tools/` folder, runs on CPython 3.12+ with NumPy-free PyYAML only):

    python tools/check_knowledge.py [--root PATH]

`--root` is a repository-like tree (default: this repository) laid out as
    src/minephys/knowledge/*.yaml                 knowledge tables (DC-000-02)
    src/minephys/knowledge/share-alike/*.yaml     share-alike-derived tables
    src/minephys/knowledge/references.bib         bibliography (DC-000-03)
    src/minephys/<module>/__init__.py             `__all__ = [...]` lists the exported objects (read statically)
    src/minephys/**/*.py                          function docstrings with a numpydoc `Knowledge rows` section
    tests/**/*.py                                 `@pytest.mark.knowledge("<row id>")` markers (found by AST)
    REUSE.toml                                    licence annotations
Exit status 0 when clean (stdout contains "OK"), 1 when violations exist. Every violation is one stdout line that
names the file (base name), the row id (or the function name) and the field or rule, for example
    knowledge/haulage.yaml: row rolling_resistance_hard_smooth: field page: missing
A symbol `minephys.<module>.<name>` resolves when `<module>` exists under src/minephys/ and `<name>` is listed in the
`__all__` of its `__init__.py` (or of `<module>.py`); a missing module is not reported (the symbol is "planned").

Oracle: hand-written fixture trees (plan 000: "hand-written fixture tables and test trees"), one defect per case.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml
from _mini_repo import GOOD_BIB, REPO_ROOT, row, run_tool, table, write_repo

REUSE_OK = """version = 1

[[annotations]]
path = ["src/minephys/knowledge/*.yaml", "src/minephys/knowledge/references.bib"]
precedence = "aggregate"
SPDX-FileCopyrightText = "2026 Example"
SPDX-License-Identifier = "CC-BY-4.0"

[[annotations]]
path = ["src/minephys/knowledge/share-alike/*.yaml"]
precedence = "aggregate"
SPDX-FileCopyrightText = "2026 Example"
SPDX-License-Identifier = "CC-BY-SA-4.0"
"""

DEMO_INIT = '__all__ = ["f"]\nfrom ._f import f\n'
DEMO_F = '''def f(x):
    """Demo.

    Parameters
    ----------
    x : float [m]

    Returns
    -------
    float [m]

    Knowledge rows
    --------------
    `verified_param`, model_const
    """
    return x
'''
TEST_PINS = (
    "import pytest\n\n"
    '@pytest.mark.knowledge("verified_param")\n'
    "def test_a():\n    assert True\n\n"
    '@pytest.mark.knowledge("verified_const")\n'
    "def test_b():\n    assert True\n"
)


def good_tables() -> dict[str, dict]:
    return {
        "demo": table(
            "demo",
            [
                row("verified_param", role="parameter", verification="verified", symbol="minephys.demo.f"),
                row("verified_const", role="model_constant", verification="verified", symbol="minephys.demo.f"),
                row("model_const", role="model_constant", verification="UNVERIFIED", symbol="minephys.demo.f"),
                row("tripwire_x", role="limit", verification="UNVERIFIED", symbol="minephys.demo.f"),
                row("raw_param", role="parameter", verification="UNVERIFIED", symbol="minephys.demo.f"),
            ],
        )
    }


def build(tmp: Path, **override) -> Path:
    kwargs = {
        "tables": good_tables(),
        "bib": GOOD_BIB,
        "src_files": {"demo/__init__.py": DEMO_INIT, "demo/_f.py": DEMO_F},
        "test_files": {"unit/test_demo.py": TEST_PINS},
    }
    reuse = override.pop("reuse", REUSE_OK)
    kwargs.update(override)
    root = write_repo(tmp, **kwargs)
    (root / "REUSE.toml").write_text(reuse, encoding="utf-8")
    return root


def check(root: Path):
    return run_tool("check_knowledge.py", "--root", str(root))


def assert_violation(root: Path, *needles: str) -> None:
    proc = check(root)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    lines = [ln for ln in proc.stdout.splitlines() if all(n in ln for n in needles)]
    assert lines, f"no violation line with {needles} in:\n{proc.stdout}"


@pytest.mark.req("SC-000-03")
@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("hand-calculation", "a clean fixture tree passes with exit 0 and prints OK")
def test_clean_tree_passes(tmp_path: Path) -> None:
    proc = check(build(tmp_path))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK" in proc.stdout


@pytest.mark.req("FR-000-20")
@pytest.mark.req("FR-000-21")
@pytest.mark.req("FR-000-22")
@pytest.mark.req("FR-000-31")
@pytest.mark.oracle("hand-calculation", "the repository's own knowledge tables are honest")
def test_the_real_repository_passes() -> None:
    proc = run_tool("check_knowledge.py", "--root", str(REPO_ROOT))
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ---------------------------------------------------------------- FR-000-20: schema agreement, reported precisely


@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("hand-calculation", "a row without its page locator is reported with file, row id and field")
def test_missing_field_is_reported_with_file_row_and_field(tmp_path: Path) -> None:
    tables = good_tables()
    del tables["demo"]["rows"][2]["page"]
    root = build(tmp_path, tables=tables)
    assert_violation(root, "demo.yaml", "model_const", "page")


@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("hand-calculation", "unknown field, bad enum, bad value form, zero denominator, verified_on rules")
@pytest.mark.parametrize(
    ("mutate", "row_id", "field"),
    [
        (lambda r: r.update(typo_field=1), "model_const", "typo_field"),
        (lambda r: r.update(verification="Verified"), "model_const", "verification"),
        (lambda r: r.update(role="constant"), "model_const", "role"),
        (lambda r: r.update(value="1/0"), "model_const", "value"),
        (lambda r: r.update(value="0.6333"), "model_const", "value"),
        (lambda r: r.update(units="none"), "model_const", "units"),
        (lambda r: r.update(verified_on="2026-10-06"), "model_const", "verified_on"),
        (lambda r: r.update(range={"min": 1.0, "max": 2.0}), "model_const", "range"),
        (lambda r: r.update(id="Bad-Id"), "Bad-Id", "id"),
        (lambda r: r.update(citation="Doe 2020"), "model_const", "citation"),
        (lambda r: r.update(symbol="haulage.f"), "model_const", "symbol"),
    ],
)
def test_each_schema_defect_is_reported(tmp_path: Path, mutate, row_id: str, field: str) -> None:
    tables = good_tables()
    mutate(tables["demo"]["rows"][2])
    root = build(tmp_path, tables=tables)
    assert_violation(root, "demo.yaml", row_id, field)


@pytest.mark.req("FR-000-20")
@pytest.mark.oracle(
    "hand-calculation", "a verified row needs its verification date; a calendar-invalid date is rejected"
)
def test_verified_date_rules(tmp_path: Path) -> None:
    tables = good_tables()
    del tables["demo"]["rows"][0]["verified_on"]
    assert_violation(build(tmp_path / "a", tables=tables), "verified_param", "verified_on")
    tables = good_tables()
    tables["demo"]["rows"][0]["verified_on"] = "2026-02-30"
    assert_violation(build(tmp_path / "b", tables=tables), "verified_param", "verified_on")


@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("hand-calculation", "table-level defects: file stem, empty table, schema_version, range order")
def test_table_level_defects(tmp_path: Path) -> None:
    tables = good_tables()
    tables["demo"]["table"] = "other"  # differs from the file stem
    assert_violation(build(tmp_path / "a", tables=tables), "demo.yaml", "table")
    tables = good_tables()
    tables["demo"]["schema_version"] = 2
    assert_violation(build(tmp_path / "b", tables=tables), "demo.yaml", "schema_version")
    tables = good_tables()
    tables["demo"]["rows"] = []
    assert_violation(build(tmp_path / "c", tables=tables), "demo.yaml", "rows")
    tables = good_tables()
    tables["demo"]["rows"][2].pop("value")
    tables["demo"]["rows"][2]["range"] = {"min": 5.0, "max": 1.0}
    assert_violation(build(tmp_path / "d", tables=tables), "model_const", "range")


@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("hand-calculation", "a row id is unique across all tables of the package")
def test_duplicate_row_id_across_tables(tmp_path: Path) -> None:
    tables = good_tables()
    tables["second"] = table("second", [row("model_const", symbol="minephys.demo.f")])
    assert_violation(build(tmp_path, tables=tables), "model_const", "duplicate")


@pytest.mark.req("FR-000-20")
@pytest.mark.oracle("hand-calculation", "hostile: malformed YAML, a non-mapping top level, an empty file")
@pytest.mark.parametrize("content", ["rows: [unclosed\n", "- just\n- a list\n", "", "\x00\x01"])
def test_malformed_yaml_is_reported_not_crashed(tmp_path: Path, content: str) -> None:
    root = build(tmp_path)
    (root / "src" / "minephys" / "knowledge" / "broken.yaml").write_text(content, encoding="utf-8")
    proc = check(root)
    assert proc.returncode == 1
    assert "broken.yaml" in proc.stdout
    assert "Traceback" not in proc.stderr


# ---------------------------------------------------------------- FR-000-21


@pytest.mark.req("FR-000-21")
@pytest.mark.oracle("hand-calculation", "a verified row nobody pins by a knowledge marker fails, naming the row")
def test_unpinned_verified_row(tmp_path: Path) -> None:
    root = build(
        tmp_path,
        test_files={"unit/test_demo.py": TEST_PINS.replace('"verified_const"', '"some_other_row"')},
    )
    assert_violation(root, "verified_const")
    proc = check(root)
    assert not any("verified_param" in ln for ln in proc.stdout.splitlines()), "a pinned row must not be reported"


@pytest.mark.req("FR-000-21")
@pytest.mark.oracle("hand-calculation", "an UNVERIFIED row needs no pin; a marker on another file counts")
def test_markers_in_any_test_file_count(tmp_path: Path) -> None:
    root = build(
        tmp_path,
        test_files={
            "unit/test_a.py": TEST_PINS.split('@pytest.mark.knowledge("verified_const")')[0],
            "property/test_b.py": (
                'import pytest\n\n@pytest.mark.knowledge("verified_const")\ndef test_c():\n    pass\n'
            ),
        },
    )
    assert check(root).returncode == 0


@pytest.mark.req("FR-000-21")
@pytest.mark.oracle("hand-calculation", "a symbol that its module does not export fails, naming the row")
def test_symbol_not_exported(tmp_path: Path) -> None:
    tables = good_tables()
    tables["demo"]["rows"][3]["symbol"] = "minephys.demo.not_exported"
    assert_violation(build(tmp_path, tables=tables), "tripwire_x", "symbol")


@pytest.mark.req("FR-000-21")
@pytest.mark.oracle("hand-calculation", "a list of symbols is checked element by element")
def test_symbol_list_is_checked_per_element(tmp_path: Path) -> None:
    tables = good_tables()
    tables["demo"]["rows"][3]["symbol"] = ["minephys.demo.f", "minephys.demo.ghost"]
    assert_violation(build(tmp_path, tables=tables), "tripwire_x", "ghost")


@pytest.mark.req("FR-000-21")
@pytest.mark.oracle("hand-calculation", "a citation absent from references.bib fails, naming the row and the key")
def test_unknown_citation(tmp_path: Path) -> None:
    tables = good_tables()
    tables["demo"]["rows"][3]["citation"] = "ghost1999"
    assert_violation(build(tmp_path, tables=tables), "tripwire_x", "citation", "ghost1999")


# ---------------------------------------------------------------- FR-000-22


@pytest.mark.req("FR-000-22")
@pytest.mark.oracle("hand-calculation", "an UNVERIFIED parameter row in a model card fails, naming function and row")
def test_unverified_parameter_listed_in_a_model_card(tmp_path: Path) -> None:
    bad = DEMO_F.replace("`verified_param`, model_const", "`verified_param`, raw_param")
    assert_violation(build(tmp_path, src_files={"demo/__init__.py": DEMO_INIT, "demo/_f.py": bad}), "raw_param", "f")


@pytest.mark.req("FR-000-22")
@pytest.mark.oracle("hand-calculation", "verified parameters, UNVERIFIED model constants and limits may be listed")
@pytest.mark.parametrize(
    "listed", ["verified_param", "model_const", "tripwire_x", "verified_param, model_const, tripwire_x", "none"]
)
def test_permitted_card_entries(tmp_path: Path, listed: str) -> None:
    doc = DEMO_F.replace("`verified_param`, model_const", listed)
    root = build(tmp_path, src_files={"demo/__init__.py": DEMO_INIT, "demo/_f.py": doc})
    proc = check(root)
    assert proc.returncode == 0, proc.stdout


# ---------------------------------------------------------------- FR-000-31


@pytest.mark.req("FR-000-31")
@pytest.mark.oracle("hand-calculation", "a CC-BY-4.0 table must not cite a share-alike bibliography entry")
def test_cc_by_table_citing_a_share_alike_source(tmp_path: Path) -> None:
    tables = good_tables()
    tables["demo"]["rows"][3]["citation"] = "sharealike2019"
    assert_violation(build(tmp_path, tables=tables), "tripwire_x", "sharealike2019")


@pytest.mark.req("FR-000-31")
@pytest.mark.oracle("hand-calculation", "licence and folder must agree; a share-alike table keeps its own licence")
def test_licence_versus_folder(tmp_path: Path) -> None:
    sa = {
        "sa": table("sa", [row("sa_row", citation="sharealike2019", symbol="minephys.demo.f")], licence="CC-BY-SA-4.0")
    }
    ok = build(tmp_path / "ok", share_alike_tables=sa)
    assert check(ok).returncode == 0, check(ok).stdout
    wrong_licence_in_sa = {"sa": table("sa", [row("sa_row", symbol="minephys.demo.f")], licence="CC-BY-4.0")}
    assert_violation(build(tmp_path / "a", share_alike_tables=wrong_licence_in_sa), "sa.yaml", "licence")
    tables = good_tables()
    tables["demo"]["licence"] = "CC-BY-SA-4.0"
    assert_violation(build(tmp_path / "b", tables=tables), "demo.yaml", "licence")
    tables = good_tables()
    tables["demo"]["licence"] = "MIT"
    assert_violation(build(tmp_path / "c", tables=tables), "demo.yaml", "licence")


@pytest.mark.req("FR-000-31")
@pytest.mark.oracle("hand-calculation", "REUSE.toml must annotate the share-alike folder separately")
def test_reuse_annotation_of_the_share_alike_folder(tmp_path: Path) -> None:
    sa = {"sa": table("sa", [row("sa_row", symbol="minephys.demo.f")], licence="CC-BY-SA-4.0")}
    no_sa_annotation = REUSE_OK.split("[[annotations]]")[0] + "[[annotations]]" + REUSE_OK.split("[[annotations]]")[1]
    assert_violation(build(tmp_path / "a", share_alike_tables=sa, reuse=no_sa_annotation), "REUSE")
    assert_violation(build(tmp_path / "b", reuse="version = 1\n"), "REUSE")


@pytest.mark.req("FR-000-31")
@pytest.mark.oracle("hand-calculation", "a table file must declare an SPDX licence")
def test_missing_licence_is_reported(tmp_path: Path) -> None:
    tables = copy.deepcopy(good_tables())
    del tables["demo"]["licence"]
    assert_violation(build(tmp_path, tables=tables), "demo.yaml", "licence")


@pytest.mark.req("FR-000-31")
@pytest.mark.oracle("hand-calculation", "the fixture YAML is what the checker sees, not Python objects")
def test_fixture_tables_are_plain_yaml(tmp_path: Path) -> None:
    root = build(tmp_path)
    loaded = yaml.safe_load((root / "src" / "minephys" / "knowledge" / "demo.yaml").read_text(encoding="utf-8"))
    assert loaded["rows"][0]["id"] == "verified_param"

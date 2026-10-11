"""T-008-031 (FR-008-18, FR-008-19): the command line and the validation report.

Expected behaviour (`python -m minephys.knowledge`, FR-008-18): the subcommands `validate [PATH]`, `export [--out FILE]` (standard output
by default) and `render --out-dir DIR`, with exit code 0 on success, 1 on validation errors (every error listed) and 2 on usage errors.
`validate_tables(path=None)` (FR-008-19) validates the packaged knowledge, or a user folder with the same layout, and returns a report
listing every error (not only the first) with the row, entry and UNVERIFIED counts (`.errors`, `.rows`, `.unverified`; the entry count
is not pinned here, the plan names it without defining which entries it counts).
`validate PATH` reads the user folder directly; `export`, `render` and a bare `validate` act on the packaged knowledge, which these tests
replace by a fixture package tree (tests/_knowledge_fixtures.py, `importlib.resources` redirected in the child interpreter).

Oracle: hand-counted fixtures (6 rows of which 4 UNVERIFIED), a fixture with exactly three independent errors, and the exit codes of
spec 008 FR-008-18.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import _knowledge_fixtures as fx
import pytest


def _k():
    return importlib.import_module("minephys.knowledge")


def _three_error_tree(tmp_path: Path) -> Path:
    tables = fx.good_tables()
    del tables["haulage"]["rows"][1]["page"]  # error 1: haulage row 2, field page
    tables["haulage"]["rows"][2]["role"] = "bogus"  # error 2: haulage row 3, field role
    eq = fx.good_equations()
    eq["equations"][1]["domain"] = "astrology"  # error 3: equations entry 2, field domain
    return fx.write_tree(tmp_path / "bad", tables=tables, equations=eq)


@pytest.mark.req("FR-008-19")
@pytest.mark.oracle(
    "hand-calculation", "valid fixture: 6 rows, 4 UNVERIFIED, no error; three-error fixture: exactly three errors"
)
def test_fr_008_19_validate_tables_report(tmp_path: Path) -> None:
    good = _k().validate_tables(fx.write_tree(tmp_path / "good", share_alike=fx.good_share_alike()))
    assert list(good.errors) == [] and good.rows == 6 and good.unverified == 4
    bad = _k().validate_tables(_three_error_tree(tmp_path))
    found = sorted((Path(str(e.file)).name, e.index, e.field) for e in bad.errors)
    assert found == [("equations.yaml", 2, "domain"), ("haulage.yaml", 2, "page"), ("haulage.yaml", 3, "role")], found
    assert len(bad.errors) == 3  # every error, not only the first


@pytest.mark.req("FR-008-19")
def test_fr_008_19_validate_tables_without_a_path_validates_the_packaged_knowledge() -> None:
    report = _k().validate_tables()
    assert list(report.errors) == [], [str(e) for e in report.errors[:3]]
    assert report.rows >= 1 and 0 <= report.unverified <= report.rows


@pytest.mark.req("FR-008-18")
@pytest.mark.oracle("hand-calculation", "exit codes: 0 valid, 1 errors listed, 2 usage")
def test_fr_008_18_validate_exit_codes_and_listing(tmp_path: Path) -> None:
    ok = fx.run_cli(["validate", str(fx.write_tree(tmp_path / "good"))])
    assert ok.returncode == 0, ok.stdout + ok.stderr
    bad = fx.run_cli(["validate", str(_three_error_tree(tmp_path))])
    assert bad.returncode == 1, bad.stdout + bad.stderr
    listing = bad.stdout + bad.stderr
    for marker in (
        "haulage.yaml",
        "equations.yaml",
        "page",
        "role",
        "domain",
    ):  # all three errors are printed, not only the first
        assert marker in listing, f"{marker!r} missing from the validation listing:\n{listing}"


@pytest.mark.req("FR-008-18")
def test_fr_008_18_validate_without_a_path_uses_the_packaged_knowledge(tmp_path: Path) -> None:
    good = fx.write_package_tree(tmp_path / "good")
    assert fx.run_cli(["validate"], good).returncode == 0
    bad = fx.write_package_tree(tmp_path / "bad", tables={**fx.good_tables(), "haulage": {"schema_version": 1}})
    assert fx.run_cli(["validate"], bad).returncode == 1


@pytest.mark.req("FR-008-18")
@pytest.mark.oracle("hand-calculation", "export to stdout and to a file, render into a directory")
def test_fr_008_18_export_and_render(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", share_alike=fx.good_share_alike())
    exported = fx.run_cli(["export"], base)
    assert exported.returncode == 0 and exported.stdout.startswith("{") and exported.stdout.endswith("\n")
    target = tmp_path / "out.json"
    assert fx.run_cli(["export", "--out", str(target)], base).returncode == 0
    assert target.read_text(encoding="utf-8") == exported.stdout
    pages = tmp_path / "pages"
    pages.mkdir()
    rendered = fx.run_cli(["render", "--out-dir", str(pages)], base)
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    names = {p.name for p in pages.iterdir()}
    assert names >= {"haulage.md", "blasting.md", "geotech_sa.md", "equations.md", "bibliography.md", "glossary.md"}


@pytest.mark.req("FR-008-18")
@pytest.mark.parametrize(
    "args",
    [
        [],
        ["frobnicate"],
        ["validate", "--no-such-option"],
        ["export", "--format", "yaml"],
        ["export", "--out"],  # missing value
        ["render"],  # --out-dir is required
        ["render", "--out-dir"],
        ["validate", "a", "b"],  # too many paths
        ["--help-me-please"],
    ],
    ids=[
        "no-subcommand",
        "unknown-subcommand",
        "unknown-option",
        "unknown-export-option",
        "out-without-value",
        "render-without-out-dir",
        "out-dir-without-value",
        "two-paths",
        "unknown-global-option",
    ],
)
def test_fr_008_18_usage_errors_exit_with_code_2(tmp_path: Path, args: list[str]) -> None:
    base = fx.write_package_tree(tmp_path / "pkg")
    proc = fx.run_cli(args, base)
    assert proc.returncode == 2, (args, proc.returncode, proc.stdout, proc.stderr[-300:])
    assert not any(p for p in tmp_path.iterdir() if p.name != "pkg"), "a usage error must not create files"

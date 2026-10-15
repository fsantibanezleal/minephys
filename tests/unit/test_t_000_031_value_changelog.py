"""T-000-031 (FR-000-30): the knowledge value-change check against the previous release.

Expected CLI (an added mode of `tools/release.py`, the release tool):

    python tools/release.py --check-knowledge --previous DIR --current DIR --changelog FILE

`DIR` holds knowledge tables (`*.yaml`, plus `share-alike/*.yaml`) in the DC-000-02 format; `--previous` is the
tables of the previous release, `--current` the working tree. For every row id present in both, the row CHANGED when
its `value`, its `range` or its `verification` differs (numbers compare as numbers: `1` equals `1.0`; a `"p/q"`
string differs from a different string). A changed row makes the check FAIL (exit 1, one line per row naming its
id) unless the text of the `## [Unreleased]` section of the changelog (up to the next `## ` heading) contains the
row id as a whole word (`rock_factor` is not named by `rock_factor_min`). `units`, `quantity`, `notes`, `page`,
`citation`, `verified_on` and `symbol` changes alone do not count; added or removed rows are not reported by this
check. Exit 0 and `OK` when every changed row is named.
A missing directory or changelog, or an unreadable table, exits 2 naming the path.

Oracle: hand-written fixture tables and changelogs (plan 000: "hand-written fixture tables and changelogs").
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from _mini_repo import REPO_ROOT, row, run_tool, table, write_repo

CHANGELOG = """# Changelog

## [Unreleased]
### Changed
{unreleased}

## [1.01.000] - 2026-09-01
### Changed
- `rock_factor` was adjusted.
"""


def tables() -> dict[str, dict]:
    return {
        "demo": table(
            "demo",
            [
                row("rock_factor", value=10.21, verification="verified"),
                row("rock_factor_min", value=0.8),
                row("exponent", value="19/30"),
                row("windowed", value=1.0),
            ],
        )
    }


def tables_range() -> dict[str, dict]:
    t = tables()
    r = t["demo"]["rows"][1]
    del r["value"]
    r["range"] = {"min": 0.8, "max": 22.0}
    return t


def release(prev: Path, cur: Path, log: Path):
    assert (REPO_ROOT / "tools" / "release.py").is_file()
    assert "--check-knowledge" in run_tool("release.py", "--help").stdout, "release.py has no --check-knowledge mode"
    return run_tool(
        "release.py", "--check-knowledge", "--previous", str(prev), "--current", str(cur), "--changelog", str(log)
    )


def knowledge(tmp: Path, name: str, content: dict[str, dict]) -> Path:
    root = write_repo(tmp / name, tables=content)
    return root / "src" / "minephys" / "knowledge"


def check(tmp: Path, previous: dict[str, dict], current: dict[str, dict], unreleased: str | None):
    prev = knowledge(tmp, "prev", previous)
    cur = knowledge(tmp, "cur", current)
    log = tmp / "CHANGELOG.md"
    log.write_text(CHANGELOG.format(unreleased=unreleased or ""), encoding="utf-8")
    return release(prev, cur, log)


def modified(mutator) -> dict[str, dict]:
    t = copy.deepcopy(tables())
    mutator(t["demo"]["rows"])
    return t


@pytest.mark.req("FR-000-30")
@pytest.mark.oracle("hand-calculation", "no change, no entry needed")
def test_unchanged_tables_pass(tmp_path: Path) -> None:
    proc = check(tmp_path, tables(), tables(), None)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK" in proc.stdout


@pytest.mark.req("FR-000-30")
@pytest.mark.oracle("hand-calculation", "a changed value without a changelog entry fails and names the row")
def test_changed_value_without_entry_fails(tmp_path: Path) -> None:
    cur = modified(lambda rows: rows[0].update(value=10.22))
    proc = check(tmp_path, tables(), cur, "- nothing about knowledge")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert any("rock_factor" in ln and "rock_factor_min" not in ln for ln in proc.stdout.splitlines())


@pytest.mark.req("FR-000-30")
@pytest.mark.oracle("hand-calculation", "naming the row in the Unreleased section is enough, in any markup")
@pytest.mark.parametrize(
    "entry",
    [
        "- `rock_factor` changed from 10.21 to 10.22 (typo in the source table)",
        "- rock_factor: 10.21 -> 10.22",
        "- Row **rock_factor** updated.",
        "* knowledge row rock_factor, see issue 12",
    ],
)
def test_entry_in_unreleased_justifies_the_change(tmp_path: Path, entry: str) -> None:
    cur = modified(lambda rows: rows[0].update(value=10.22))
    proc = check(tmp_path, tables(), cur, entry)
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.req("FR-000-30")
@pytest.mark.oracle(
    "hand-calculation", "an entry in an older release section, or for a similarly named row, does not count"
)
def test_old_entries_and_similar_names_do_not_justify(tmp_path: Path) -> None:
    cur = modified(lambda rows: rows[0].update(value=10.22))
    # CHANGELOG fixture already names `rock_factor` under [1.01.000]
    proc = check(tmp_path / "a", tables(), cur, "- unrelated")
    assert proc.returncode == 1
    similar = check(tmp_path / "b", tables(), cur, "- `rock_factor_min` was adjusted")
    assert similar.returncode == 1, "rock_factor_min is a different row"


@pytest.mark.req("FR-000-30")
@pytest.mark.oracle("hand-calculation", "value, range and verification changes all count")
@pytest.mark.parametrize(
    ("label", "mutator", "row_id"),
    [
        ("value", lambda rows: rows[2].update(value="19/20"), "exponent"),
        (
            "verification",
            lambda rows: rows[1].update(verification="verified", verified_on="2026-10-06"),
            "rock_factor_min",
        ),
        (
            "unverify",
            lambda rows: (rows[0].update(verification="UNVERIFIED"), rows[0].pop("verified_on")),
            "rock_factor",
        ),
        (
            "value_to_range",
            lambda rows: (rows[3].pop("value"), rows[3].update(range={"min": 0.0, "max": 1.0})),
            "windowed",
        ),
    ],
)
def test_each_kind_of_change_is_detected(tmp_path: Path, label: str, mutator, row_id: str) -> None:
    cur = modified(mutator)
    proc = check(tmp_path, tables(), cur, "- unrelated")
    assert proc.returncode == 1, label
    assert row_id in proc.stdout


@pytest.mark.req("FR-000-30")
@pytest.mark.oracle("hand-calculation", "a range bound change counts")
def test_range_bound_change(tmp_path: Path) -> None:
    cur = copy.deepcopy(tables_range())
    cur["demo"]["rows"][1]["range"]["max"] = 25.0
    proc = check(tmp_path, tables_range(), cur, "- unrelated")
    assert proc.returncode == 1
    assert "rock_factor_min" in proc.stdout


@pytest.mark.req("FR-000-30")
@pytest.mark.oracle("hand-calculation", "metadata-only edits are not value changes; 1 and 1.0 are the same number")
def test_non_value_edits_are_not_reported(tmp_path: Path) -> None:
    def edit(rows: list[dict]) -> None:
        rows[0].update(units="kg", notes="more context", page="p. 9", quantity="a better description")
        rows[0]["verified_on"] = "2026-11-01"
        rows[3].update(value=1)  # 1.0 -> 1
        rows[1].update(symbol="minephys.demo.g", citation="agency2025")

    proc = check(tmp_path, tables(), modified(edit), None)
    assert proc.returncode == 0, proc.stdout


@pytest.mark.req("FR-000-30")
@pytest.mark.oracle("hand-calculation", "added or removed rows are outside this check")
def test_added_and_removed_rows_are_not_reported(tmp_path: Path) -> None:
    cur = copy.deepcopy(tables())
    cur["demo"]["rows"].pop(3)
    cur["demo"]["rows"].append(row("brand_new_row", value=3.0))
    proc = check(tmp_path, tables(), cur, None)
    assert proc.returncode == 0, proc.stdout


@pytest.mark.req("FR-000-30")
@pytest.mark.oracle("hand-calculation", "several changed rows are all listed")
def test_all_changed_rows_are_listed_and_partial_entries_do_not_suffice(tmp_path: Path) -> None:
    cur = modified(lambda rows: (rows[0].update(value=11.0), rows[2].update(value="1/2")))
    proc = check(tmp_path / "a", tables(), cur, "- `rock_factor` fixed")
    assert proc.returncode == 1
    assert "exponent" in proc.stdout
    both = check(tmp_path / "b", tables(), cur, "- `rock_factor` fixed\n- `exponent` fixed")
    assert both.returncode == 0, both.stdout


@pytest.mark.req("FR-000-30")
@pytest.mark.oracle("hand-calculation", "hostile: a changelog without an Unreleased section justifies nothing")
def test_changelog_without_unreleased_section(tmp_path: Path) -> None:
    cur = modified(lambda rows: rows[0].update(value=10.22))
    prev = knowledge(tmp_path, "prev", tables())
    now = knowledge(tmp_path, "cur", cur)
    log = tmp_path / "CHANGELOG.md"
    log.write_text("# Changelog\n\n## [1.01.000]\n- `rock_factor` was adjusted.\n", encoding="utf-8")
    proc = release(prev, now, log)
    assert proc.returncode == 1


@pytest.mark.req("FR-000-30")
@pytest.mark.oracle("hand-calculation", "hostile: missing paths and malformed tables exit 2 naming the path")
def test_missing_paths_and_malformed_tables(tmp_path: Path) -> None:
    prev = knowledge(tmp_path, "prev", tables())
    log = tmp_path / "CHANGELOG.md"
    log.write_text(CHANGELOG.format(unreleased=""), encoding="utf-8")
    absent = tmp_path / "absent"
    proc = release(prev, absent, log)
    assert proc.returncode == 2
    assert "absent" in proc.stdout + proc.stderr
    proc = release(prev, prev, tmp_path / "nolog.md")
    assert proc.returncode == 2
    assert "nolog.md" in proc.stdout + proc.stderr
    broken = knowledge(tmp_path, "broken", tables())
    (broken / "demo.yaml").write_text("rows: [unclosed\n", encoding="utf-8")
    proc = release(prev, broken, log)
    assert proc.returncode == 2
    assert "demo.yaml" in proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr

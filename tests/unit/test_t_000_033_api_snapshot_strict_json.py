"""T-000-033 (FR-000-34): `tools/check_api.py` reads the API snapshot with a strict JSON reader.

Expected behaviour (CLI of T-000-030: `--previous PREV.json --current CUR.json [--changelog FILE]`):
a snapshot file that holds a DUPLICATE object key (at any depth, even with equal values), a NON-FINITE number (`NaN`,
`Infinity`, `-Infinity`) or INVALID UTF-8 makes the tool exit non-zero, name the file and the key or the JSON pointer
of the first problem on stdout or stderr, print no traceback, and compare nothing (no `OK`, no difference lines), even
when "last key wins" parsing would have produced an identical, clean comparison. Keys that merely differ in case are not
duplicates. Pathological input (a nesting depth of 100,000) is an error, not a crash.

Oracle: hand calculation. The valid fixture is the spec's own `api-snapshot.valid.json` example (DC-000-04); each defect
is spliced into its text by hand.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _mini_repo import REPO_ROOT, run_tool

VALID = REPO_ROOT / "specs" / "000-foundation" / "contracts" / "examples" / "api-snapshot.valid.json"


def valid_text() -> str:
    return VALID.read_text(encoding="utf-8")


def compare(tmp: Path, previous: bytes | str, current: bytes | str):
    assert (REPO_ROOT / "tools" / "check_api.py").is_file(), "missing tools/check_api.py"
    paths = []
    for name, content in (("prev.json", previous), ("cur.json", current)):
        p = tmp / name
        p.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        paths.append(str(p))
    return run_tool("check_api.py", "--previous", paths[0], "--current", paths[1])


def assert_rejected(proc, filename: str, *needles: str) -> None:
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0, out
    assert filename in out, out
    assert any(n in out for n in needles), f"none of {needles} in:\n{out}"
    assert "Traceback" not in proc.stderr
    assert "OK" not in proc.stdout, "nothing may be compared"


@pytest.mark.req("FR-000-34")
@pytest.mark.oracle("hand-calculation", "control: the valid fixture compared with itself is clean")
def test_clean_file_compares_clean(tmp_path: Path) -> None:
    proc = compare(tmp_path, valid_text(), valid_text())
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "OK" in proc.stdout


@pytest.mark.req("FR-000-34")
@pytest.mark.oracle("hand-calculation", "a repeated object key is rejected, in either file, even with equal values")
@pytest.mark.parametrize("which", ["prev.json", "cur.json"])
def test_duplicate_key_is_rejected(tmp_path: Path, which: str) -> None:
    text = valid_text()
    doc = json.loads(text)
    first = doc["objects"][0]["name"]
    # splice a second "name" member with the SAME value into the first object: last-wins parsing sees no change
    dup = text.replace(f'"name": "{first}"', f'"name": "{first}", "name": "{first}"', 1)
    assert dup != text, 'fixture assumption: the first object has a name member written as \'"name": "..."\''
    pair = (dup, text) if which == "prev.json" else (text, dup)
    proc = compare(tmp_path, *pair)
    assert_rejected(proc, which, "name", "/objects/0/name")


@pytest.mark.req("FR-000-34")
@pytest.mark.oracle("hand-calculation", "a duplicate at the top level and in a nested parameter are both found")
def test_duplicate_key_at_top_level_and_nested(tmp_path: Path) -> None:
    text = valid_text()
    top = text.replace('"version"', '"version": "9.99.999", "version"', 1)
    assert top != text
    for sub in "ab":
        (tmp_path / sub).mkdir()
    assert_rejected(compare(tmp_path / "a", top, text), "prev.json", "version")
    old = '"kind": "positional_or_keyword"'
    nested = text.replace(old, '"kind": "keyword_only", ' + old, 1)
    assert nested != text
    assert_rejected(compare(tmp_path / "b", text, nested), "cur.json", "kind", "parameters")


@pytest.mark.req("FR-000-34")
@pytest.mark.oracle("hand-calculation", "keys that differ in case are distinct, not duplicates")
def test_case_variants_are_not_duplicates(tmp_path: Path) -> None:
    text = valid_text()
    variant = text.replace('"version"', '"Version": "0.00.000", "version"', 1)
    proc = compare(tmp_path, text, variant)
    # an unknown extra field may be reported by the comparison, but never as a duplicate key
    assert "duplicate" not in (proc.stdout + proc.stderr).lower()


@pytest.mark.req("FR-000-34")
@pytest.mark.oracle("hand-calculation", "NaN, Infinity and -Infinity are rejected anywhere in the document")
@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_numbers_are_rejected(tmp_path: Path, literal: str) -> None:
    text = valid_text()
    bad = text.replace('"deprecated": null', f'"deprecated": null, "score": {literal}', 1)
    assert bad != text
    proc = compare(tmp_path, text, bad)
    assert_rejected(proc, "cur.json", literal, "score", "/objects/0/score")


@pytest.mark.req("FR-000-34")
@pytest.mark.oracle("hand-calculation", "invalid UTF-8 bytes are rejected naming the file")
@pytest.mark.parametrize("payload", [b"\xff", b"\xc3\x28", b"\xe2\x82", b"\xed\xa0\x80"])
def test_invalid_utf8_is_rejected(tmp_path: Path, payload: bytes) -> None:
    raw = valid_text().encode("utf-8")
    bad = raw.replace(b'"version"', b'"ver' + payload + b'sion"', 1)
    assert bad != raw
    proc = compare(tmp_path, raw, bad)
    assert_rejected(proc, "cur.json", "UTF-8", "utf-8", "utf8", "byte")


@pytest.mark.req("FR-000-34")
@pytest.mark.oracle("hand-calculation", "hostile: absurd nesting depth is an error, not a RecursionError")
def test_deeply_nested_json_is_an_error_not_a_crash(tmp_path: Path) -> None:
    deep = "[" * 100_000 + "]" * 100_000
    proc = compare(tmp_path, valid_text(), deep)
    assert proc.returncode != 0
    assert "Traceback" not in proc.stderr
    assert "cur.json" in proc.stdout + proc.stderr
    assert "OK" not in proc.stdout

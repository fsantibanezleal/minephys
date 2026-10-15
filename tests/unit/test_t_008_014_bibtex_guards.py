"""T-008-014 (FR-008-08): hostile BibTeX.

Expected behaviour (`minephys.knowledge`): a `references.bib` that is larger than 1 MiB, has unbalanced braces or quotes, repeats an
entry key or a field within an entry, or uses an unsupported entry type (including `@string`, `@preamble` and `@comment`) makes the
parser raise `KnowledgeSchemaError` (the LOADER raises on first use) naming the entry key (when known) and the 1-based LINE: the
message contains the key and the line number; `file` ends in `references.bib`. `validate_tables(folder)` lists the same error instead
of raising, and no later call returns partially validated data.

Oracle: hand-written hostile BibTeX files; the expected line is computed by counting the newlines of the fixture text.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any

import _knowledge_fixtures as fx
import pytest

ENTRY = "@article{{{key},\n  author = {{D, J}},\n  title = {{T}},\n  year = {{2020}},\n  doi = {{10.1000/x1}},\n  access = {{open}}\n}}\n"


def _k():
    return importlib.import_module("minephys.knowledge")


def _entry(key: str) -> str:
    return ENTRY.format(key=key)


def _span(text: str, needle: str) -> tuple[int, int]:
    """Lines (1-based, inclusive) of the entry or construct that starts at the LAST occurrence of `needle`."""
    start_pos = text.rindex(needle)
    start = text[:start_pos].count("\n") + 1
    nxt = text.find("\n@", start_pos + 1)
    end = (text[:nxt].count("\n") + 1) if nxt != -1 else text.count("\n") + 1
    return start, end


def _numbers_in(message: str) -> list[int]:
    return [int(m) for m in re.findall(r"(?<![\w.])(\d+)(?![\w.])", message)]


def _cases() -> dict[str, tuple[str | bytes, str | None, str | None]]:
    """name -> (bibliography text, entry key named by the error or None, text whose line number is expected or None)."""
    good = fx.GOOD_BIB
    return {
        "unbalanced-open-brace": (
            good + "\n@article{brace1,\n  author = {D, J,\n  title = {T},\n  year = {2020}\n}\n",
            "brace1",
            "@article{brace1",
        ),
        "unbalanced-close-brace": (good + "\n" + _entry("brace2") + "}\n", None, None),
        "unclosed-entry-at-eof": (
            good + "\n@article{eof1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n",
            "eof1",
            "@article{eof1",
        ),
        "unbalanced-quote": (
            good + '\n@article{quote1,\n  author = {D, J},\n  title = "T,\n  year = {2020}\n}\n',
            "quote1",
            "@article{quote1",
        ),
        "nested-brace-unbalanced": (
            good + "\n@article{nest1,\n  author = {D, {J},\n  title = {T},\n  year = {2020}\n}\n",
            "nest1",
            "@article{nest1",
        ),
        "duplicate-entry-key": (good + "\n" + _entry("doe2020"), "doe2020", "@article{doe2020"),
        "duplicate-field": (
            good
            + "\n@article{dupf1,\n  author = {D, J},\n  title = {T},\n  title = {T2},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
            "dupf1",
            "@article{dupf1",
        ),
        "duplicate-field-case-insensitive": (
            good
            + "\n@article{dupf2,\n  author = {D, J},\n  Title = {T},\n  TITLE = {T2},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
            "dupf2",
            "@article{dupf2",
        ),
        "string-macro": (good + '\n@string{jt = "Journal of Tests"}\n', None, "@string"),
        "preamble": (good + '\n@preamble{"\\newcommand{\\noop}[1]{}"}\n', None, "@preamble"),
        "comment-entry": (good + "\n@comment{hidden text}\n", None, "@comment"),
        "unsupported-type": (
            good
            + "\n@phdthesis{thesis1,\n  author = {D, J},\n  title = {T},\n  year = {2020},\n  doi = {10.1000/x1},\n  access = {open}\n}\n",
            None,
            "@phdthesis",
        ),
        "no-key": (good + "\n@article{,\n  author = {D, J},\n  title = {T},\n  year = {2020}\n}\n", None, None),
        "text-outside-entries": (good + "\nstray words here\n", None, "stray words"),
        "field-without-equals": (
            good + "\n@article{noeq1,\n  author {D, J},\n  title = {T},\n  year = {2020}\n}\n",
            "noeq1",
            "@article{noeq1",
        ),
        "oversized": (good + "\n% " + "x" * (1_048_577 - len(good.encode("utf-8")) - 4) + "\n", None, None),
        "invalid-utf8": (good.encode("utf-8") + b"\n% \xff\xfe\n", None, None),
    }


NAMES = list(_cases())


def _write(tmp_path: Path, bib: str | bytes) -> Path:
    base = fx.write_package_tree(tmp_path / "pkg", equations=None, glossary=None, bib=None)
    path = base / "knowledge" / "references.bib"
    path.write_bytes(bib if isinstance(bib, bytes) else bib.encode("utf-8"))
    return base


def _check_message(message: str, key: str | None, span: tuple[int, int] | None) -> None:
    if key is not None:
        assert key in message, f"the message must name the entry key {key!r}: {message}"
    if (
        span is not None
    ):  # the 1-based line of the entry (its first line) or of the point where parsing failed inside it
        assert any(span[0] <= n <= span[1] for n in _numbers_in(message)), (
            f"the message must give a line in {span}: {message}"
        )


@pytest.mark.req("FR-008-08")
@pytest.mark.oracle("hand-calculation", "FR-008-08 hostile BibTeX classes, with the expected entry key and line")
@pytest.mark.parametrize("name", NAMES)
def test_fr_008_08_validate_tables_lists_the_bibtex_error(tmp_path: Path, name: str) -> None:
    text, key, needle = _cases()[name]
    base = _write(tmp_path, text)
    report = _k().validate_tables(base / "knowledge")
    on_bib = [e for e in report.errors if str(e.file).replace("\\", "/").endswith("references.bib")]
    assert on_bib, f"{name}: the hostile bibliography was accepted"
    if isinstance(text, str) and needle is not None:
        span = _span(text, needle)
        assert any(
            (key is None or key in str(e))
            and (
                any(span[0] <= n <= span[1] for n in _numbers_in(str(e)))
                or span[0] <= (getattr(e, "index", None) or -1) <= span[1]
            )
            for e in on_bib
        ), (span, [str(e) for e in on_bib])


@pytest.mark.req("FR-008-08")
@pytest.mark.req("FR-008-06")
@pytest.mark.parametrize("name", NAMES)
def test_fr_008_08_loader_raises_knowledge_schema_error_naming_the_key_and_line(tmp_path: Path, name: str) -> None:
    text, key, needle = _cases()[name]
    base = _write(tmp_path, text)
    got = fx.run_api(
        base,
        """
outcome = {}
for label, call in (("bibliography", lambda: K.bibliography()), ("again", lambda: K.bibliography()),
                    ("tables", lambda: K.list_tables()), ("row", lambda: K.get_parameter("inch"))):
    try:
        outcome[label] = {"ok": True}
        call()
    except BaseException as e:
        outcome[label] = {"ok": False, **_err(e)}
print(json.dumps(outcome))
""",
    )
    first = got["bibliography"]
    assert first["ok"] is False and first["type"] == "KnowledgeSchemaError" and first["is_value_error"], first
    assert str(first["file"]).replace("\\", "/").endswith("references.bib")
    span = _span(text, needle) if isinstance(text, str) and needle is not None else None
    if span is not None or key is not None:
        _check_message(first["msg"], key, span)
    for label in ("again", "tables", "row"):  # no partially validated data (the tables themselves are valid)
        assert got[label]["ok"] is False and got[label]["type"] == "KnowledgeSchemaError", (label, got[label])


@pytest.mark.req("FR-008-08")
@pytest.mark.oracle(
    "hand-calculation", "constructs that are NOT errors: comments, blank lines, quoted and digit values, nested braces"
)
def test_fr_008_08_the_supported_subset_is_not_rejected(tmp_path: Path) -> None:
    bib = (
        fx.GOOD_BIB
        + "\n% fine\n\n\n"
        + _entry("fine1")
        + '\n@misc{fine2, author = "A, B", title = {A {nested {brace}} title}, year = 2001, url = {https://example.org/a}, access = {open}}\n'
    )
    base = _write(tmp_path, bib)
    report = _k().validate_tables(base / "knowledge")
    assert [e for e in report.errors if str(e.file).replace("\\", "/").endswith("references.bib")] == []
    keys: Any = fx.run_api(base, "print(json.dumps(sorted(r.key for r in K.bibliography())))")
    assert keys == sorted(["agency2025", "doe2020", "epa2025ghghub", "fine1", "fine2", "sharealike2019"])

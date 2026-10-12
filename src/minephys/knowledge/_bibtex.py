"""BibTeX-subset parser and the DC-000-03 entry rules (spec 008 FR-008-03, FR-008-08).

Grammar: `@type{key, field = {...} | "..." | digits, ...}` with nested braces, `%` comment lines and blank lines
between entries,
field names and entry types case-insensitive, UTF-8 text. `@string`, `@preamble` and `@comment` are rejected so that
macros
cannot hide values. A value keeps its inner braces verbatim (only the outer delimiters are removed), so parsing,
writing back
and parsing again gives the same entries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ._model import Reference

__all__ = ["BibEntry", "BibSyntaxError", "check_entry", "parse", "to_reference"]

MAX_BYTES = 1_048_576
ENTRY_TYPES = ("article", "book", "inbook", "inproceedings", "techreport", "manual", "misc")
OPTIONAL_TEXT = {
    "journal": 300,
    "booktitle": 500,
    "volume": 32,
    "number": 32,
    "pages": 32,
    "publisher": 300,
    "edition": 64,
    "note": 1000,
}
ACCESS = ("open", "paywalled", "regulation", "bibliographic-only")
SOURCE_LICENCES = (
    "CC0-1.0",
    "CC-BY-3.0",
    "CC-BY-4.0",
    "CC-BY-SA-3.0",
    "CC-BY-SA-4.0",
    "CC-BY-ND-4.0",
    "CC-BY-NC-4.0",
    "CC-BY-NC-SA-4.0",
    "CC-BY-NC-ND-4.0",
)
_ALLOWED = {"author", "organization", "title", "year", "doi", "url", "access", "licence", *OPTIONAL_TEXT}
_KEY = re.compile(r"^[a-z][a-z0-9_:-]*$")
_DOI = re.compile(r"^10\.[0-9]{4,9}/[!-~]+$")
_URL = re.compile(
    r"^https?://[A-Za-z0-9.-]+(:[0-9]{1,5})?(/[A-Za-z0-9._~%!$&'()*+,;=:@/-]*)?(\?[A-Za-z0-9._~%!$&'()*+,;=:@/?-]*)?$"
)
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_:-]*")
_DIGITS = re.compile(r"[0-9]+")


class BibSyntaxError(ValueError):
    """The file is not in the supported BibTeX subset; `key` (when known) and the 1-based `line` locate the error."""

    def __init__(self, message: str, *, line: int, key: str | None = None) -> None:
        super().__init__(message)
        self.line = line
        self.key = key


@dataclass
class BibEntry:
    key: str
    entry_type: str
    line: int
    fields: dict[str, str] = field(default_factory=dict)
    field_lines: dict[str, int] = field(default_factory=dict)


class _Scanner:
    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.line = 1

    def peek(self) -> str:
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def advance(self, count: int = 1) -> None:
        for _ in range(count):
            if self.pos < len(self.text):
                if self.text[self.pos] == "\n":
                    self.line += 1
                self.pos += 1

    def skip_space(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] in " \t\r\n":
            self.advance()

    def skip_space_and_comments(self) -> None:
        while True:
            self.skip_space()
            if self.peek() == "%":
                while self.pos < len(self.text) and self.text[self.pos] != "\n":
                    self.advance()
            else:
                return


def _read_value(sc: _Scanner, key: str) -> str:
    start_line = sc.line
    ch = sc.peek()
    if ch == "{":
        depth = 0
        begin = sc.pos + 1
        while sc.pos < len(sc.text):
            c = sc.text[sc.pos]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    value = sc.text[begin : sc.pos]
                    sc.advance()
                    return value
            sc.advance()
        raise BibSyntaxError(
            f"unbalanced braces in entry {key!r}: the value starting on line {start_line} is never closed",
            line=start_line,
            key=key,
        )
    if ch == '"':
        depth = 0
        sc.advance()
        begin = sc.pos
        while sc.pos < len(sc.text):
            c = sc.text[sc.pos]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth < 0:
                    raise BibSyntaxError(f"unbalanced braces in entry {key!r} on line {sc.line}", line=sc.line, key=key)
            elif c == '"' and depth == 0:
                value = sc.text[begin : sc.pos]
                sc.advance()
                return value
            sc.advance()
        raise BibSyntaxError(
            f"unbalanced quote in entry {key!r}: the value starting on line {start_line} is never closed",
            line=start_line,
            key=key,
        )
    m = _DIGITS.match(sc.text, sc.pos)
    if m:
        sc.advance(m.end() - sc.pos)
        return m.group(0)
    raise BibSyntaxError(
        f"unsupported value (a macro or a bare word) in entry {key!r} on line {sc.line}", line=sc.line, key=key
    )


def parse(text: str) -> list[BibEntry]:
    """Parse the BibTeX subset; raises `BibSyntaxError` at the first construct outside it."""
    sc = _Scanner(text)
    entries: list[BibEntry] = []
    seen: dict[str, int] = {}
    while True:
        sc.skip_space_and_comments()
        if sc.pos >= len(sc.text):
            return entries
        if sc.peek() != "@":
            raise BibSyntaxError(
                f"text outside an entry on line {sc.line}: {sc.text[sc.pos : sc.pos + 20].splitlines()[0]!r}",
                line=sc.line,
            )
        entry_line = sc.line
        sc.advance()
        m = re.compile(r"[A-Za-z]+").match(sc.text, sc.pos)
        if not m:
            raise BibSyntaxError(f"an entry type is missing after '@' on line {entry_line}", line=entry_line)
        entry_type = m.group(0).lower()
        sc.advance(m.end() - sc.pos)
        if entry_type in ("string", "preamble", "comment"):
            raise BibSyntaxError(f"@{entry_type} is not supported (line {entry_line})", line=entry_line)
        if entry_type not in ENTRY_TYPES:
            raise BibSyntaxError(f"unsupported entry type @{entry_type} on line {entry_line}", line=entry_line)
        sc.skip_space()
        if sc.peek() != "{":
            raise BibSyntaxError(f"a '{{' is missing after @{entry_type} on line {entry_line}", line=entry_line)
        sc.advance()
        begin = sc.pos
        while sc.pos < len(sc.text) and sc.text[sc.pos] not in ",}":
            sc.advance()
        if sc.pos >= len(sc.text):
            key_guess = sc.text[begin:].strip() or None
            raise BibSyntaxError(
                f"unclosed entry {key_guess!r} starting on line {entry_line}", line=entry_line, key=key_guess
            )
        key = sc.text[begin : sc.pos].strip()
        if not key:
            raise BibSyntaxError(f"the entry on line {entry_line} has no key", line=entry_line)
        if key in seen:
            raise BibSyntaxError(
                f"repeated entry key {key!r} on line {entry_line} (first on line {seen[key]})", line=entry_line, key=key
            )
        seen[key] = entry_line
        entry = BibEntry(key=key, entry_type=entry_type, line=entry_line)
        while True:
            c = sc.peek()
            if c == ",":
                sc.advance()
            elif c == "}":
                sc.advance()
                break
            sc.skip_space_and_comments()
            if sc.peek() == "}":
                sc.advance()
                break
            if sc.pos >= len(sc.text):
                raise BibSyntaxError(f"unclosed entry {key!r} starting on line {entry_line}", line=entry_line, key=key)
            name_line = sc.line
            nm = _NAME.match(sc.text, sc.pos)
            if not nm:
                raise BibSyntaxError(
                    f"a field name is expected in entry {key!r} on line {sc.line}", line=sc.line, key=key
                )
            name = nm.group(0).lower()
            sc.advance(nm.end() - sc.pos)
            sc.skip_space()
            if sc.peek() != "=":
                raise BibSyntaxError(
                    f"field {name!r} of entry {key!r} has no '=' on line {name_line}", line=name_line, key=key
                )
            sc.advance()
            sc.skip_space()
            value = _read_value(sc, key)
            if name in entry.fields:
                raise BibSyntaxError(
                    f"repeated field {name!r} in entry {key!r} on line {name_line}", line=name_line, key=key
                )
            entry.fields[name] = value
            entry.field_lines[name] = name_line
            sc.skip_space_and_comments()
            if sc.peek() not in (",", "}"):
                if sc.pos >= len(sc.text):
                    raise BibSyntaxError(
                        f"unclosed entry {key!r} starting on line {entry_line}", line=entry_line, key=key
                    )
                raise BibSyntaxError(
                    f"a ',' or '}}' is expected after field {name!r} of entry {key!r} on line {sc.line}",
                    line=sc.line,
                    key=key,
                )
        entries.append(entry)


def check_entry(entry: BibEntry) -> list[tuple[str, str]]:
    """The DC-000-03 rule violations of one entry as (field, message) pairs; the messages name the entry key."""
    out: list[tuple[str, str]] = []
    k = entry.key
    f = entry.fields

    def bad(name: str, why: str) -> None:
        out.append((name, f"entry {k!r} (line {entry.field_lines.get(name, entry.line)}): field {name}: {why}"))

    if len(k) > 64 or not _KEY.search(k):
        out.append(
            ("key", f"entry {k!r} (line {entry.line}): the key must match [a-z][a-z0-9_:-]* (at most 64 characters)")
        )
    for name in f:
        if name not in _ALLOWED:
            bad(name, "unknown field")
    if "author" not in f and "organization" not in f:
        out.append(("author", f"entry {k!r} (line {entry.line}): author or organization is required"))
    for name, cap in (("author", 2000), ("organization", 300), ("title", 500)):
        if name in f and not 1 <= len(f[name]) <= cap:
            bad(name, f"must have 1 to {cap} characters")
    if "title" not in f:
        out.append(("title", f"entry {k!r} (line {entry.line}): title is required"))
    if "year" not in f:
        out.append(("year", f"entry {k!r} (line {entry.line}): year is required"))
    elif not _DIGITS.fullmatch(f["year"].strip()) or not 1800 <= int(f["year"].strip()) <= 2100:
        bad("year", "must be an integer from 1800 to 2100")
    if "doi" not in f and "url" not in f:
        out.append(("doi", f"entry {k!r} (line {entry.line}): doi or url is required"))
    if "doi" in f and (len(f["doi"]) > 256 or not _DOI.search(f["doi"])):
        bad("doi", "must match 10.NNNN/suffix")
    if "url" in f and (len(f["url"]) > 2048 or not _URL.search(f["url"])):
        bad("url", "must be an http(s) URL without credentials")
    if "access" not in f:
        out.append(("access", f"entry {k!r} (line {entry.line}): access is required"))
    elif f["access"] not in ACCESS:
        bad("access", f"must be one of {', '.join(ACCESS)}")
    if "licence" in f and f["licence"] not in SOURCE_LICENCES:
        bad("licence", "must be an allowed SPDX licence identifier")
    for name, cap in OPTIONAL_TEXT.items():
        if name in f and not 1 <= len(f[name]) <= cap:
            bad(name, f"must have 1 to {cap} characters")
    return out


def to_reference(entry: BibEntry) -> Reference:
    """The `Reference` of an entry that passed `check_entry`."""
    f: dict[str, Any] = dict(entry.fields)
    return Reference(
        key=entry.key,
        entry_type=entry.entry_type,
        author=f.get("author"),
        organization=f.get("organization"),
        title=f["title"],
        year=int(f["year"].strip()),
        doi=f.get("doi"),
        url=f.get("url"),
        access=f["access"],
        licence=f.get("licence"),
        journal=f.get("journal"),
        booktitle=f.get("booktitle"),
        volume=f.get("volume"),
        number=f.get("number"),
        pages=f.get("pages"),
        publisher=f.get("publisher"),
        edition=f.get("edition"),
        note=f.get("note"),
    )

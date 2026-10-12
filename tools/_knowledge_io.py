"""Shared, dependency-light readers for the knowledge tables and the bibliography (PyYAML and the standard library).

Used by `check_knowledge.py`, `gen_knowledge_docs.py`, `release.py --check-knowledge` and `release_evidence.py`. The
rules are those of `specs/000-foundation/data-model.md` (DC-000-02, DC-000-03); the JSON Schemas under `contracts/`
are the neutral contract and a contract test proves that both agree. Every function reports problems as lines of text
that name the file, the row or entry and the field; nothing here raises for malformed user data.
"""

from __future__ import annotations

import ast
import datetime as dt
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

KNOWLEDGE = Path("src") / "minephys" / "knowledge"

IDENT = re.compile(r"^[a-z][a-z0-9_]*$")
BIB_KEY = re.compile(r"^[a-z][a-z0-9_:-]*$")
RATIONAL = re.compile(r"^-?[0-9]+/[0-9]*[1-9][0-9]*$")
TEXT_LINE = re.compile(r"^[^ \t\r\n]([^\r\n]*[^ \t\r\n])?$")
DATE = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")
SYMBOL = re.compile(r"^minephys\.[a-z][a-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$")
DOI = re.compile(r"^10\.[0-9]{4,9}/[!-~]+$")
URL = re.compile(
    r"^https?://[A-Za-z0-9.-]+(:[0-9]{1,5})?(/[A-Za-z0-9._~%!$&'()*+,;=:@/-]*)?(\?[A-Za-z0-9._~%!$&'()*+,;=:@/?-]*)?$"
)
BAD_UNITS = {"-", "none", "None", "dimensionless", "unitless", "n/a", "N/A"}
ROLES = ("model_constant", "parameter", "limit", "conversion")
VERIFICATION = ("verified", "UNVERIFIED")
TABLE_LICENCES = ("CC-BY-4.0",)
SHARE_ALIKE_LICENCES = ("CC-BY-SA-4.0", "CC-BY-SA-3.0")
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
ENTRY_TYPES = ("article", "book", "inbook", "inproceedings", "techreport", "manual", "misc")
ACCESS = ("open", "paywalled", "regulation", "bibliographic-only")
BIB_LIMITS = {
    "author": 2000,
    "organization": 300,
    "title": 500,
    "journal": 300,
    "booktitle": 500,
    "volume": 32,
    "number": 32,
    "pages": 32,
    "publisher": 300,
    "edition": 64,
    "note": 1000,
}
BIB_FIELDS = (*BIB_LIMITS, "year", "doi", "url", "access", "licence")
ROW_FIELDS = (
    "id",
    "quantity",
    "value",
    "range",
    "units",
    "role",
    "citation",
    "page",
    "verification",
    "verified_on",
    "symbol",
    "notes",
)
ROW_REQUIRED = ("id", "quantity", "units", "role", "citation", "page", "verification", "symbol")
TABLE_FIELDS = ("schema_version", "table", "title", "licence", "rows")


@dataclass
class TableFile:
    """One knowledge table file as found on disk."""

    path: Path
    label: str  # `knowledge/<stem>.yaml` or `knowledge/share-alike/<stem>.yaml`
    stem: str
    share_alike: bool
    doc: Any = None
    errors: list[str] = field(default_factory=list)


def table_files(root: Path) -> list[TableFile]:
    """Every table file of `root` (knowledge folder and its share-alike subfolder), sorted by label."""
    base = root / KNOWLEDGE
    found: list[TableFile] = []
    for shared, folder in ((False, base), (True, base / "share-alike")):
        if folder.is_dir():
            for path in sorted(folder.glob("*.yaml")):
                label = f"knowledge/{'share-alike/' if shared else ''}{path.name}"
                found.append(TableFile(path, label, path.stem, shared))
    return found


def read_table(tf: TableFile) -> TableFile:
    """Parse the YAML of `tf`; a read or parse failure becomes a one-line error, never an exception."""
    try:
        text = tf.path.read_bytes().decode("utf-8")
        tf.doc = yaml.safe_load(text)
    except UnicodeDecodeError as err:
        tf.errors.append(f"{tf.label}: not valid UTF-8: {err.reason}")
    except yaml.YAMLError as err:
        first = str(err).strip().splitlines()[0] if str(err).strip() else type(err).__name__
        tf.errors.append(f"{tf.label}: not valid YAML: {first}")
    except OSError as err:
        tf.errors.append(f"{tf.label}: unreadable: {err.strerror}")
    else:
        if not isinstance(tf.doc, dict):
            tf.errors.append(f"{tf.label}: the top level must be a mapping")
    return tf


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def _text(value: Any, limit: int = 200) -> bool:
    return isinstance(value, str) and len(value) <= limit and TEXT_LINE.match(value) is not None


def validate_row(label: str, index: int, raw: Any) -> list[str]:
    """DC-000-02 row rules; each line names the file, the row id (or its 1-based index) and the field."""
    if not isinstance(raw, dict):
        return [f"{label}: row #{index}: field row: must be a mapping"]
    row_id = raw.get("id") if isinstance(raw.get("id"), str) else f"#{index}"
    out: list[str] = []

    def bad(name: str, why: str) -> None:
        out.append(f"{label}: row {row_id}: field {name}: {why}")

    for name in raw:
        if name not in ROW_FIELDS:
            bad(str(name), "unknown field")
    for name in ROW_REQUIRED:
        if name not in raw:
            bad(name, "missing")
    if "id" in raw and not (isinstance(raw["id"], str) and IDENT.match(raw["id"]) and len(raw["id"]) <= 64):
        bad("id", "must match ^[a-z][a-z0-9_]*$ (at most 64 characters)")
    for name in ("quantity", "page"):
        if name in raw and not _text(raw[name]):
            bad(name, "must be a single trimmed non-empty line of at most 200 characters")
    if "units" in raw and not (_text(raw["units"], 64) and raw["units"] not in BAD_UNITS):
        bad("units", "must be a single trimmed line of at most 64 characters; write dimensionless as 1")
    if "role" in raw and raw["role"] not in ROLES:
        bad("role", f"must be one of {', '.join(ROLES)}")
    if "citation" in raw and not (
        isinstance(raw["citation"], str) and BIB_KEY.match(raw["citation"]) and len(raw["citation"]) <= 64
    ):
        bad("citation", "must be a BibTeX key matching ^[a-z][a-z0-9_:-]*$")
    if "verification" in raw and raw["verification"] not in VERIFICATION:
        bad("verification", "must be verified or UNVERIFIED")
    out += _value_problems(raw, bad)
    verified = raw.get("verification") == "verified"
    if verified and "verified_on" not in raw:
        bad("verified_on", "required when verification is verified")
    if "verified_on" in raw:
        if not verified:
            bad("verified_on", "allowed only when verification is verified")
        elif not _calendar_date(raw["verified_on"]):
            bad("verified_on", "must be a calendar date YYYY-MM-DD written as a string")
    if "symbol" in raw:
        symbols = raw["symbol"] if isinstance(raw["symbol"], list) else [raw["symbol"]]
        if (
            not symbols
            or len(symbols) > 32
            or len(set(map(str, symbols))) != len(symbols)
            or not all(isinstance(s, str) and SYMBOL.match(s) and len(s) <= 128 for s in symbols)
        ):
            bad("symbol", "must be minephys.<module>.<name> or a list of at most 32 distinct such names")
    if "notes" in raw and not (isinstance(raw["notes"], str) and 1 <= len(raw["notes"]) <= 1000):
        bad("notes", "must be a string of 1 to 1000 characters")
    return out


def _calendar_date(value: Any) -> bool:
    if not (isinstance(value, str) and DATE.match(value)):
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _value_problems(raw: dict[str, Any], bad: Any) -> list[str]:
    has_value, has_range = "value" in raw, "range" in raw
    if has_value == has_range:
        bad("value" if not has_range else "range", "exactly one of value and range is required")
        return []
    if has_value:
        value = raw["value"]
        ok = _is_number(value) or (isinstance(value, str) and len(value) <= 32 and RATIONAL.match(value) is not None)
        if not ok:
            bad("value", "must be a finite YAML number or an exact rational string p/q with a non-zero denominator")
        return []
    span = raw["range"]
    if not (isinstance(span, dict) and set(span) == {"min", "max"} and all(_is_number(v) for v in span.values())):
        bad("range", "must be a mapping with exactly the finite numbers min and max")
    elif span["min"] > span["max"]:
        bad("range", "min must not exceed max")
    return []


def validate_table(tf: TableFile) -> list[str]:
    """DC-000-02 table rules plus licence-versus-folder and file-stem agreement (FR-000-20, FR-000-31)."""
    doc, label = tf.doc, tf.label
    if not isinstance(doc, dict):
        return []
    out: list[str] = []

    def bad(name: str, why: str) -> None:
        out.append(f"{label}: field {name}: {why}")

    for name in doc:
        if name not in TABLE_FIELDS:
            bad(str(name), "unknown field")
    for name in TABLE_FIELDS:
        if name not in doc:
            bad(name, "missing")
    if "schema_version" in doc and not (doc["schema_version"] == 1 and not isinstance(doc["schema_version"], bool)):
        bad("schema_version", "must be 1")
    if "table" in doc and not (isinstance(doc["table"], str) and IDENT.match(doc["table"]) and doc["table"] == tf.stem):
        bad("table", f"must equal the file stem {tf.stem!r} and match ^[a-z][a-z0-9_]*$")
    if "title" in doc and not _text(doc["title"]):
        bad("title", "must be a single trimmed non-empty line")
    if "licence" in doc:
        allowed = SHARE_ALIKE_LICENCES if tf.share_alike else TABLE_LICENCES
        if doc["licence"] not in allowed:
            where = "share-alike/" if tf.share_alike else ""
            bad("licence", f"a table in knowledge/{where} must be {' or '.join(allowed)}, got {doc['licence']!r}")
    if "rows" in doc:
        rows = doc["rows"]
        if not (isinstance(rows, list) and 1 <= len(rows) <= 1000):
            bad("rows", "must be a list of 1 to 1000 rows (a table file is shipped only with at least one row)")
        else:
            for i, raw in enumerate(rows, start=1):
                out += validate_row(label, i, raw)
    return out


def rows_of(tf: TableFile) -> list[dict[str, Any]]:
    """The row mappings of a parsed table (empty when the table is unusable)."""
    doc = tf.doc
    if isinstance(doc, dict) and isinstance(doc.get("rows"), list):
        return [r for r in doc["rows"] if isinstance(r, dict) and isinstance(r.get("id"), str)]
    return []


def symbols_of(row: dict[str, Any]) -> list[str]:
    sym = row.get("symbol")
    if isinstance(sym, str):
        return [sym]
    return [s for s in sym if isinstance(s, str)] if isinstance(sym, list) else []


def numeric_value(row: dict[str, Any]) -> Any:
    """Comparable form of the value of a row: a float, an exact p/q string, or a (min, max) pair."""
    if "range" in row and isinstance(row["range"], dict):
        return ("range", float(row["range"].get("min", math.nan)), float(row["range"].get("max", math.nan)))
    value = row.get("value")
    if isinstance(value, bool) or not isinstance(value, int | float):
        return ("text", value)
    return ("number", float(value))


# ------------------------------------------------------------------ bibliography


class _Parser:
    def __init__(self, text: str) -> None:
        self.s = text
        self.i = 0
        self.errors: list[str] = []

    def line(self, pos: int | None = None) -> int:
        return self.s.count("\n", 0, self.i if pos is None else pos) + 1

    def skip(self) -> None:
        while self.i < len(self.s) and self.s[self.i] in " \t\r\n":
            self.i += 1

    def braced(self) -> str | None:
        depth, start = 0, self.i
        while self.i < len(self.s):
            ch = self.s[self.i]
            depth += (ch == "{") - (ch == "}")
            self.i += 1
            if depth == 0:
                return self.s[start + 1 : self.i - 1]
        return None


def parse_bib(text: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Parse the BibTeX subset of DC-000-03; returns the entries (key -> fields, with `entry_type`) and error lines."""
    p = _Parser(text)
    entries: dict[str, dict[str, str]] = {}
    while True:
        at = p.s.find("@", p.i)
        if at < 0:
            return entries, p.errors
        p.i = at + 1
        m = re.match(r"([A-Za-z]+)\s*\{\s*([^,\s{}]+)\s*,", p.s[p.i :])
        if not m:
            p.errors.append(f"references.bib: line {p.line()}: not a well-formed entry header")
            continue
        entry_type, key = m.group(1).lower(), m.group(2)
        p.i += m.end()
        entry: dict[str, str] = {"entry_type": entry_type}
        closed = False
        while p.i < len(p.s):
            p.skip()
            if p.i < len(p.s) and p.s[p.i] == ",":
                p.i += 1
                continue
            if p.i < len(p.s) and p.s[p.i] == "}":
                p.i += 1
                closed = True
                break
            name = re.match(r"([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*", p.s[p.i :])
            if not name:
                break
            p.i += name.end()
            field_name = name.group(1).lower()
            value = _field_value(p)
            if value is None:
                break
            if field_name in entry:
                p.errors.append(f"references.bib: entry {key}: field {field_name}: repeated")
            entry.setdefault(field_name, re.sub(r"\s+", " ", value).strip())
        if not closed:
            p.errors.append(f"references.bib: entry {key}: line {p.line()}: unbalanced braces or quotes")
            return entries, p.errors
        if key in entries:
            p.errors.append(f"references.bib: entry {key}: duplicate key")
        entries.setdefault(key, entry)


def _field_value(p: _Parser) -> str | None:
    if p.i >= len(p.s):
        return None
    if p.s[p.i] == "{":
        return p.braced()
    if p.s[p.i] == '"':
        end = p.s.find('"', p.i + 1)
        if end < 0:
            return None
        value = p.s[p.i + 1 : end]
        p.i = end + 1
        return value
    m = re.match(r"[^,\s}]+", p.s[p.i :])
    if not m:
        return None
    p.i += m.end()
    return m.group(0)


def validate_entry(key: str, entry: dict[str, str]) -> list[str]:
    """DC-000-03 entry rules; each line names the entry key and the field."""
    out: list[str] = []

    def bad(name: str, why: str) -> None:
        out.append(f"references.bib: entry {key}: field {name}: {why}")

    if not (BIB_KEY.match(key) and len(key) <= 64):
        bad("key", "must match ^[a-z][a-z0-9_:-]*$")
    if entry.get("entry_type") not in ENTRY_TYPES:
        bad("entry_type", f"must be one of {', '.join(ENTRY_TYPES)}")
    for name in entry:
        if name != "entry_type" and name not in BIB_FIELDS:
            bad(name, "unknown BibTeX field")
    if not ("author" in entry or "organization" in entry):
        bad("author", "an author or an organization is required")
    if not entry.get("title"):
        bad("title", "missing")
    year = entry.get("year", "")
    if not (year.isdigit() and 1800 <= int(year) <= 2100):
        bad("year", "must be an integer from 1800 to 2100")
    if "doi" not in entry and "url" not in entry:
        bad("doi", "a doi or a url is required")
    if "doi" in entry and not (DOI.match(entry["doi"]) and len(entry["doi"]) <= 256):
        bad("doi", "must look like 10.NNNN/suffix (no resolver prefix)")
    if "url" in entry and not (URL.match(entry["url"]) and len(entry["url"]) <= 2048):
        bad("url", "must be an http(s) URL without user information")
    if entry.get("access") not in ACCESS:
        bad("access", f"must be one of {', '.join(ACCESS)}")
    if "licence" in entry and entry["licence"] not in SOURCE_LICENCES:
        bad("licence", "must be an SPDX id from the allowed list")
    for name, limit in BIB_LIMITS.items():
        if name in entry and not 1 <= len(entry[name]) <= limit:
            bad(name, f"must have 1 to {limit} characters")
    return out


def read_bibliography(root: Path) -> tuple[dict[str, dict[str, str]], list[str]]:
    """The parsed bibliography of `root` and its parse and validation errors."""
    path = root / KNOWLEDGE / "references.bib"
    try:
        text = path.read_bytes().decode("utf-8")
    except FileNotFoundError:
        return {}, ["references.bib: missing"]
    except (OSError, UnicodeDecodeError) as err:
        return {}, [f"references.bib: unreadable: {err}"]
    entries, errors = parse_bib(text)
    for key, entry in entries.items():
        errors += validate_entry(key, entry)
    return entries, errors


def plain(text: str) -> str:
    """BibTeX text without its case-protecting braces."""
    return text.replace("{", "").replace("}", "")


# ------------------------------------------------------------------ source tree


def exported_names(root: Path, module: str) -> set[str] | None:
    """Names in the static `__all__` of `src/minephys/<module>` (package or module), None when it does not exist."""
    base = root / "src" / "minephys"
    for candidate in (base / module / "__init__.py", base / f"{module}.py"):
        if candidate.is_file():
            try:
                tree = ast.parse(candidate.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError, OSError):
                return set()
            names: set[str] = set()
            for node in ast.walk(tree):
                target = None
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
                    target = node.value
                elif isinstance(node, ast.AnnAssign | ast.AugAssign) and (
                    isinstance(node.target, ast.Name) and node.target.id == "__all__"
                ):
                    target = node.value
                if isinstance(target, ast.List | ast.Tuple):
                    names |= {e.value for e in target.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
            return names
    return None


SECTION_RULE = re.compile(r"^\s*-{3,}\s*$")


def doc_sections(doc: str) -> dict[str, list[str]]:
    """numpydoc split: a title line followed by a dashes line starts a section."""
    lines = doc.splitlines()
    sections: dict[str, list[str]] = {}
    current: str | None = None
    i = 0
    while i < len(lines):
        if i + 1 < len(lines) and lines[i].strip() and SECTION_RULE.match(lines[i + 1]):
            current = lines[i].strip()
            sections[current] = []
            i += 2
            continue
        if current is not None:
            sections[current].append(lines[i])
        i += 1
    return sections


def knowledge_rows_of_functions(root: Path) -> list[tuple[str, str, list[str]]]:
    """(file, function name, words of its `Knowledge rows` section) for every function under src/minephys."""
    found: list[tuple[str, str, list[str]]] = []
    base = root / "src" / "minephys"
    if not base.is_dir():
        return found
    for path in sorted(base.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                doc = ast.get_docstring(node)
                if doc and "Knowledge rows" in doc_sections(doc):
                    body = " ".join(doc_sections(doc)["Knowledge rows"]).replace("`", " ")
                    found.append((path.relative_to(base).as_posix(), node.name, re.findall(r"[a-z][a-z0-9_]*", body)))
    return found


def pinned_rows(root: Path) -> set[str]:
    """Row ids named by `@pytest.mark.knowledge("<row id>")` decorators anywhere under tests/ (AST)."""
    pinned: set[str] = set()
    tests = root / "tests"
    if not tests.is_dir():
        return pinned
    for path in tests.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "knowledge"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                pinned.add(node.args[0].value)
    return pinned

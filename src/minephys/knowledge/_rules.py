"""Pure-Python validation of the knowledge documents (spec 008 FR-008-02, FR-008-04, FR-008-05).

These are the rules of the JSON Schemas under `contracts/` (DC-000-02, DC-008-01, DC-008-02), written as code so that
the runtime
needs no schema engine (the tests prove the agreement with the reference validator, P-008-01), plus the rules a
schema cannot
express: finite numbers, `min <= max`, the file stem, the licence of the folder and the cross-file integrity of ids and
citations. Every function returns the list of (index, field, message) it finds; index is the 1-based row or entry,
None for
the document itself.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable
from typing import Any

__all__ = [
    "DOMAINS",
    "ROLES",
    "check_cross_file",
    "check_equations",
    "check_glossary",
    "check_table",
]

Issue = tuple["int | None", "str | None", str]

ROLES = ("model_constant", "parameter", "limit", "conversion")
DOMAINS = ("haulage", "blasting", "geotech", "bulk", "comminution", "environment", "planning")
TABLE_LICENCES = ("CC-BY-4.0", "CC-BY-SA-4.0", "CC-BY-SA-3.0")
VERIFICATION = ("verified", "UNVERIFIED")
_BANNED_UNITS = ("-", "none", "None", "dimensionless", "unitless", "n/a", "N/A")

_IDENT = re.compile(r"^[a-z][a-z0-9_]*$")
_BIB_KEY = re.compile(r"^[a-z][a-z0-9_:-]*$")
_LINE = re.compile(r"^[^ \t\r\n]([^\r\n]*[^ \t\r\n])?$")
_RATIONAL = re.compile(r"^-?[0-9]+/[0-9]*[1-9][0-9]*$")
_DATE = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")
_DOTTED = re.compile(r"^minephys\.[a-z][a-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*$")


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _text(value: Any, cap: int, pattern: re.Pattern[str] | None = _LINE) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= cap and (pattern is None or pattern.search(value) is not None)


def _identifier(value: Any) -> bool:
    return isinstance(value, str) and len(value) <= 64 and _IDENT.search(value) is not None


def _bib_key(value: Any) -> bool:
    return isinstance(value, str) and len(value) <= 64 and _BIB_KEY.search(value) is not None


def _units(value: Any) -> bool:
    return _text(value, 64) and value not in _BANNED_UNITS


def _dotted(value: Any) -> bool:
    return isinstance(value, str) and len(value) <= 128 and _DOTTED.search(value) is not None


def _date(value: Any) -> bool:
    return isinstance(value, str) and len(value) <= 10 and _DATE.search(value) is not None


def _unique_ids(values: Any, cap: int, valid: Callable[[Any], bool]) -> bool:
    return (
        isinstance(values, list)
        and 1 <= len(values) <= cap
        and all(valid(v) for v in values)
        and len(set(values)) == len(values)
    )


def _unknown(doc: dict[Any, Any], allowed: Iterable[str], index: int | None) -> list[Issue]:
    names = set(allowed)
    return [(index, str(k), f"unknown field {k!r}") for k in doc if k not in names]


def _missing(doc: dict[Any, Any], required: Iterable[str], index: int | None) -> list[Issue]:
    return [(index, name, f"missing required field {name!r}") for name in required if name not in doc]


def _verification(doc: dict[str, Any], index: int | None) -> list[Issue]:
    out: list[Issue] = []
    if "verification" in doc and doc["verification"] not in VERIFICATION:
        out.append((index, "verification", "must be 'verified' or 'UNVERIFIED'"))
    if "verification" in doc and doc["verification"] == "verified":
        if "verified_on" not in doc:
            out.append((index, "verified_on", "a verified entry needs verified_on (YYYY-MM-DD)"))
    elif "verified_on" in doc:
        out.append((index, "verified_on", "verified_on is allowed only on a verified entry"))
    if "verified_on" in doc and not _date(doc["verified_on"]):
        out.append((index, "verified_on", "must be a date written YYYY-MM-DD"))
    return out


def _number_issue(value: Any, index: int | None, field: str) -> str | None:
    if not _is_number(value):
        return "must be a number"
    if isinstance(value, float) and not math.isfinite(value):
        return "must be finite"
    return None


def _row(raw: Any, index: int) -> list[Issue]:
    if not isinstance(raw, dict):
        return [(index, None, "a row must be a mapping")]
    out: list[Issue] = []
    required = ("id", "quantity", "units", "role", "citation", "page", "verification", "symbol")
    out += _missing(raw, required, index)
    out += _unknown(raw, (*required, "value", "range", "verified_on", "notes"), index)
    if "id" in raw and not _identifier(raw["id"]):
        out.append((index, "id", "must match [a-z][a-z0-9_]* (at most 64 characters)"))
    if "quantity" in raw and not _text(raw["quantity"], 200):
        out.append((index, "quantity", "must be one non-blank line of at most 200 characters"))
    has_value, has_range = "value" in raw, "range" in raw
    if has_value == has_range:
        out.append((index, "value", "exactly one of value and range is required"))
    if has_value:
        value = raw["value"]
        if isinstance(value, str):
            if len(value) > 32 or not _RATIONAL.search(value):
                out.append((index, "value", "a text value must be an exact rational p/q with q > 0"))
        else:
            why = _number_issue(value, index, "value")
            if why:
                out.append((index, "value", f"must be a finite number or a rational string: {why}"))
    if has_range:
        span = raw["range"]
        if not isinstance(span, dict):
            out.append((index, "range", "must be a mapping with min and max"))
        else:
            out.extend((index, "range", f"range.{name} is missing") for name in ("min", "max") if name not in span)
            out.extend((index, "range", f"unknown key range.{name}") for name in span if name not in ("min", "max"))
            ends: list[Any] = [span.get(name) for name in ("min", "max") if name in span]
            problems = [_number_issue(v, index, "range") for v in ends]
            if any(problems):
                out.append((index, "range", f"min and max must be finite numbers: {next(p for p in problems if p)}"))
            elif len(ends) == 2 and ends[0] > ends[1]:
                out.append((index, "range", "min must not exceed max"))
    if "units" in raw and not _units(raw["units"]):
        out.append(
            (index, "units", "must be one non-blank line of at most 64 characters, not a placeholder such as 'none'")
        )
    if "role" in raw and raw["role"] not in ROLES:
        out.append((index, "role", f"must be one of {', '.join(ROLES)}"))
    if "citation" in raw and not _bib_key(raw["citation"]):
        out.append((index, "citation", "must be a bibliography key [a-z][a-z0-9_:-]*"))
    if "page" in raw and not _text(raw["page"], 200):
        out.append((index, "page", "must be one non-blank line of at most 200 characters"))
    out += _verification(raw, index)
    if "symbol" in raw:
        symbol = raw["symbol"]
        if not (_dotted(symbol) or _unique_ids(symbol, 32, _dotted)):
            out.append((index, "symbol", "must be minephys.<module>.<name> or a list of unique ones"))
    if "notes" in raw and not _text(raw["notes"], 1000, None):
        out.append((index, "notes", "must be a non-empty text of at most 1000 characters"))
    return out


def _document_head(doc: Any, required: Iterable[str], allowed: Iterable[str]) -> tuple[list[Issue], bool]:
    if not isinstance(doc, dict):
        return [(None, None, "the top level must be a mapping")], False
    out = _missing(doc, required, None) + _unknown(doc, allowed, None)
    if "schema_version" in doc and (not _is_number(doc["schema_version"]) or doc["schema_version"] != 1):
        out.append((None, "schema_version", "must be 1"))
    if "title" in doc and not _text(doc["title"], 200):
        out.append((None, "title", "must be one non-blank line of at most 200 characters"))
    return out, True


def check_table(doc: Any, stem: str, share_alike: bool) -> list[Issue]:
    """DC-000-02 rules for one table document read from `<stem>.yaml` (in `share-alike/` when `share_alike`)."""
    keys = ("schema_version", "table", "title", "licence", "rows")
    out, ok = _document_head(doc, keys, keys)
    if not ok:
        return out
    if "table" in doc:
        if not _identifier(doc["table"]):
            out.append((None, "table", "must match [a-z][a-z0-9_]* (at most 64 characters)"))
        elif doc["table"] != stem:
            out.append((None, "table", f"the table name {doc['table']!r} differs from the file stem {stem!r}"))
    if not _identifier(stem):
        out.append((None, "table", f"the file stem {stem!r} is not a valid table name"))
    if "licence" in doc:
        if doc["licence"] not in TABLE_LICENCES:
            out.append((None, "licence", f"must be one of {', '.join(TABLE_LICENCES)}"))
        elif share_alike and not str(doc["licence"]).startswith("CC-BY-SA-"):
            out.append((None, "licence", "a table in share-alike/ must carry a CC-BY-SA licence"))
        elif not share_alike and doc["licence"] != "CC-BY-4.0":
            out.append((None, "licence", "a table outside share-alike/ must carry CC-BY-4.0"))
    if "rows" in doc:
        rows = doc["rows"]
        if not isinstance(rows, list):
            out.append((None, "rows", "must be a list of rows"))
        elif not 1 <= len(rows) <= 1000:
            out.append((None, "rows", "needs 1 to 1000 rows (a table is shipped only with at least one row)"))
        else:
            for i, raw in enumerate(rows, start=1):
                out += _row(raw, i)
    return out


def _symbols(raw: Any) -> list[str]:
    if not isinstance(raw, list) or not 1 <= len(raw) <= 64:
        return ["needs 1 to 64 symbols"]
    out: list[str] = []
    for n, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            out.append(f"symbol {n} must be a mapping")
            continue
        out.extend(f"symbol {n}: {name} is missing" for name in ("symbol", "meaning", "units") if name not in entry)
        out.extend(f"symbol {n}: unknown key {name}" for name in entry if name not in ("symbol", "meaning", "units"))
        if "symbol" in entry and not _text(entry["symbol"], 64):
            out.append(f"symbol {n}: symbol must be one non-blank token of at most 64 characters")
        if "meaning" in entry and not _text(entry["meaning"], 200):
            out.append(f"symbol {n}: meaning must be one non-blank line of at most 200 characters")
        if "units" in entry and not _units(entry["units"]):
            out.append(f"symbol {n}: units must be a unit string (1 for dimensionless)")
    return out


def _equation(raw: Any, index: int) -> list[Issue]:
    if not isinstance(raw, dict):
        return [(index, None, "an equation entry must be a mapping")]
    required = ("id", "title", "domain", "latex", "symbols", "function", "citation", "page", "verification")
    out = _missing(raw, required, index) + _unknown(raw, (*required, "verified_on", "rows", "notes"), index)
    if "id" in raw and not _identifier(raw["id"]):
        out.append((index, "id", "must match [a-z][a-z0-9_]* (at most 64 characters)"))
    if "title" in raw and not _text(raw["title"], 200):
        out.append((index, "title", "must be one non-blank line of at most 200 characters"))
    if "domain" in raw and raw["domain"] not in DOMAINS:
        out.append((index, "domain", f"must be one of {', '.join(DOMAINS)}"))
    if "latex" in raw and not _text(raw["latex"], 2000, None):
        out.append((index, "latex", "must be a non-empty text of at most 2000 characters"))
    if "symbols" in raw:
        out += [(index, "symbols", why) for why in _symbols(raw["symbols"])]
    if "function" in raw and not _dotted(raw["function"]):
        out.append((index, "function", "must be minephys.<module>.<name>"))
    if "citation" in raw and not _bib_key(raw["citation"]):
        out.append((index, "citation", "must be a bibliography key [a-z][a-z0-9_:-]*"))
    if "page" in raw and not _text(raw["page"], 200):
        out.append((index, "page", "must be one non-blank line of at most 200 characters"))
    out += _verification(raw, index)
    if "rows" in raw and not _unique_ids(raw["rows"], 64, _identifier):
        out.append((index, "rows", "must be a non-empty list of unique row ids"))
    if "notes" in raw and not _text(raw["notes"], 1000, None):
        out.append((index, "notes", "must be a non-empty text of at most 1000 characters"))
    return out


def check_equations(doc: Any) -> list[Issue]:
    """DC-008-01 rules for `catalogue/equations.yaml`."""
    keys = ("schema_version", "title", "licence", "equations")
    out, ok = _document_head(doc, keys, keys)
    if not ok:
        return out
    if "licence" in doc and doc["licence"] != "CC-BY-4.0":
        out.append((None, "licence", "must be CC-BY-4.0"))
    if "equations" in doc:
        entries = doc["equations"]
        if not isinstance(entries, list):
            out.append((None, "equations", "must be a list of equations"))
        elif not 1 <= len(entries) <= 500:
            out.append((None, "equations", "needs 1 to 500 entries (a catalogue is shipped only with at least one)"))
        else:
            for i, raw in enumerate(entries, start=1):
                out += _equation(raw, i)
    return out


def _term(raw: Any, index: int) -> list[Issue]:
    if not isinstance(raw, dict):
        return [(index, None, "a glossary term must be a mapping")]
    required = ("id", "domain", "term_en", "term_es", "definition_en", "definition_es")
    out = _missing(raw, required, index) + _unknown(raw, (*required, "citation", "see_also"), index)
    if "id" in raw and not _identifier(raw["id"]):
        out.append((index, "id", "must match [a-z][a-z0-9_]* (at most 64 characters)"))
    if "domain" in raw and raw["domain"] not in (*DOMAINS, "general"):
        out.append((index, "domain", f"must be one of {', '.join((*DOMAINS, 'general'))}"))
    for name in ("term_en", "term_es"):
        if name in raw and not _text(raw[name], 1000):
            out.append((index, name, "must be one non-blank line of at most 1000 characters"))
    for name in ("definition_en", "definition_es"):
        if name in raw and not _text(raw[name], 1000, None):
            out.append((index, name, "must be a non-empty text of at most 1000 characters"))
    if "citation" in raw and not _bib_key(raw["citation"]):
        out.append((index, "citation", "must be a bibliography key [a-z][a-z0-9_:-]*"))
    if "see_also" in raw and not _unique_ids(raw["see_also"], 16, _identifier):
        out.append((index, "see_also", "must be a list of 1 to 16 unique term ids"))
    return out


def check_glossary(doc: Any) -> list[Issue]:
    """DC-008-02 rules for `catalogue/glossary.yaml`."""
    keys = ("schema_version", "title", "licence", "terms")
    out, ok = _document_head(doc, keys, keys)
    if not ok:
        return out
    if "licence" in doc and doc["licence"] != "CC-BY-4.0":
        out.append((None, "licence", "must be CC-BY-4.0"))
    if "terms" in doc:
        entries = doc["terms"]
        if not isinstance(entries, list):
            out.append((None, "terms", "must be a list of terms"))
        elif not 1 <= len(entries) <= 1000:
            out.append((None, "terms", "needs 1 to 1000 terms (a catalogue is shipped only with at least one)"))
        else:
            for i, raw in enumerate(entries, start=1):
                out += _term(raw, i)
    return out


def check_cross_file(
    tables: dict[str, Any],
    bib_keys: Any,
    equations: Any,
    glossary: Any,
) -> dict[str, list[Issue]]:
    """FR-008-05: unique row ids across all tables, citations in the bibliography, resolvable equation rows and
    see_also ids.

    `tables` maps a document label to its (already schema-valid or not) document; only well-formed entries are
    inspected.
    Returns the issues per document label ('equations' and 'glossary' for the catalogues).
    """
    out: dict[str, list[Issue]] = {}
    seen: dict[str, str] = {}
    for label, doc in tables.items():
        found: list[Issue] = []
        rows = doc.get("rows") if isinstance(doc, dict) else None
        for i, raw in enumerate(rows if isinstance(rows, list) else [], start=1):
            if not isinstance(raw, dict):
                continue
            row_id = raw.get("id")
            if isinstance(row_id, str):
                if row_id in seen:
                    found.append((i, "id", f"duplicate row id {row_id!r} (first in {seen[row_id]})"))
                else:
                    seen[row_id] = label
            citation = raw.get("citation")
            if isinstance(citation, str) and citation not in bib_keys:
                found.append((i, "citation", f"citation {citation!r} is not in references.bib"))
        if found:
            out[label] = found
    found = []
    ids: set[str] = set()
    entries = equations.get("equations") if isinstance(equations, dict) else None
    for i, raw in enumerate(entries if isinstance(entries, list) else [], start=1):
        if not isinstance(raw, dict):
            continue
        eid = raw.get("id")
        if isinstance(eid, str):
            if eid in ids:
                found.append((i, "id", f"duplicate equation id {eid!r}"))
            ids.add(eid)
        citation = raw.get("citation")
        if isinstance(citation, str) and citation not in bib_keys:
            found.append((i, "citation", f"citation {citation!r} is not in references.bib"))
        rows = raw.get("rows")
        for row_id in rows if isinstance(rows, list) else []:
            if isinstance(row_id, str) and row_id not in seen:
                found.append((i, "rows", f"row {row_id!r} is not in any table"))
    if found:
        out["equations"] = found
    found = []
    ids = set()
    terms = glossary.get("terms") if isinstance(glossary, dict) else None
    term_list = terms if isinstance(terms, list) else []
    all_ids = {t.get("id") for t in term_list if isinstance(t, dict)}
    for i, raw in enumerate(term_list, start=1):
        if not isinstance(raw, dict):
            continue
        tid = raw.get("id")
        if isinstance(tid, str):
            if tid in ids:
                found.append((i, "id", f"duplicate term id {tid!r}"))
            ids.add(tid)
        citation = raw.get("citation")
        if isinstance(citation, str) and citation not in bib_keys:
            found.append((i, "citation", f"citation {citation!r} is not in references.bib"))
        see = raw.get("see_also")
        for ref in see if isinstance(see, list) else []:
            if isinstance(ref, str) and ref not in all_ids:
                found.append((i, "see_also", f"term {ref!r} is not in the glossary"))
    if found:
        out["glossary"] = found
    return out

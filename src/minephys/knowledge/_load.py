"""Reading and validating a knowledge folder (spec 008 FR-008-01 to FR-008-07, FR-008-19, FR-008-22).

A knowledge folder has the layout of the package data: `<table>.yaml`, `share-alike/<table>.yaml`, `references.bib` and
`catalogue/{equations,glossary}.yaml`. The folder is any object with the `importlib.resources.abc.Traversable`
interface (the
package resources or a `pathlib.Path`), so the packaged knowledge and a user folder go through the same code. Errors are
collected per file in a fixed order (tables by name, the bibliography, the equations, the glossary); nothing is
raised here.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from . import _bibtex, _rules
from ._model import Equation, Reference, Row, Table, Term, ValidationError
from ._yamlio import MAX_BYTES, YamlRejected, load_document

__all__ = ["Knowledge", "Loaded", "read_folder", "read_tables"]


@dataclass(frozen=True)
class Knowledge:
    """Everything a validated folder holds, as immutable objects, plus the documents as written (for the export)."""

    tables: Mapping[str, Table]
    rows: Mapping[str, Row]
    raw_tables: Mapping[str, Any]
    references: tuple[Reference, ...]
    equations: tuple[Equation, ...]
    glossary: tuple[Term, ...]
    raw_equations: tuple[Any, ...]
    raw_terms: tuple[Any, ...]


@dataclass
class Loaded:
    """Result of reading a folder: the errors in order, the counts, and the knowledge when there is no error."""

    errors: list[ValidationError] = field(default_factory=list)
    rows: int = 0
    unverified: int = 0
    equations: int = 0
    terms: int = 0
    references: int = 0
    tables: int = 0
    knowledge: Knowledge | None = None


def _error(label: str, issue: _rules.Issue) -> ValidationError:
    index, name, message = issue
    return ValidationError(file=label, index=index, field=name, message=message)


def _table_entries(root: Any) -> list[tuple[str, Any, bool]]:
    found: list[tuple[str, Any, bool]] = []
    if root.is_dir():
        found += [
            (p.name[: -len(".yaml")], p, False) for p in root.iterdir() if p.is_file() and p.name.endswith(".yaml")
        ]
        shared = root.joinpath("share-alike")
        if shared.is_dir():
            found += [
                (p.name[: -len(".yaml")], p, True) for p in shared.iterdir() if p.is_file() and p.name.endswith(".yaml")
            ]
    return sorted(found, key=lambda item: (item[0], item[2]))


def _read_yaml(path: Any, label: str, errors: list[ValidationError]) -> tuple[bool, Any]:
    try:
        return True, load_document(path.read_bytes())
    except YamlRejected as err:
        errors.append(ValidationError(file=label, index=None, field=None, message=str(err)))
        return False, None


def _row_object(raw: Mapping[str, Any], table: str) -> Row:
    symbol = raw["symbol"]
    span = raw.get("range")
    return Row(
        id=raw["id"],
        quantity=raw["quantity"],
        value=raw.get("value"),
        range=None if span is None else (float(span["min"]), float(span["max"])),
        units=raw["units"],
        role=raw["role"],
        citation=raw["citation"],
        page=raw["page"],
        verification=raw["verification"],
        verified_on=raw.get("verified_on"),
        symbol=(symbol,) if isinstance(symbol, str) else tuple(symbol),
        notes=raw.get("notes"),
        table=table,
    )


def _equation_object(raw: Mapping[str, Any]) -> Equation:
    rows = raw.get("rows")
    return Equation(
        id=raw["id"],
        title=raw["title"],
        domain=raw["domain"],
        latex=raw["latex"],
        symbols=tuple(MappingProxyType(dict(s)) for s in raw["symbols"]),
        function=raw["function"],
        citation=raw["citation"],
        page=raw["page"],
        verification=raw["verification"],
        verified_on=raw.get("verified_on"),
        rows=None if rows is None else tuple(rows),
        notes=raw.get("notes"),
    )


def _term_object(raw: Mapping[str, Any]) -> Term:
    see = raw.get("see_also")
    return Term(
        id=raw["id"],
        domain=raw["domain"],
        term_en=raw["term_en"],
        term_es=raw["term_es"],
        definition_en=raw["definition_en"],
        definition_es=raw["definition_es"],
        citation=raw.get("citation"),
        see_also=None if see is None else tuple(see),
    )


def _read_bibliography(
    path: Any, label: str, errors: list[ValidationError]
) -> tuple[list[_bibtex.BibEntry] | None, bool]:
    """Parse and check references.bib; returns the entries (None when the syntax is broken) and whether it was
    readable."""
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        errors.append(ValidationError(label, None, None, f"the file is larger than {MAX_BYTES} bytes"))
        return None, False
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as err:
        errors.append(ValidationError(label, None, None, f"the file is not valid UTF-8: {err.reason}"))
        return None, False
    try:
        entries = _bibtex.parse(text)
    except _bibtex.BibSyntaxError as err:
        errors.append(ValidationError(label, err.line, "syntax", f"line {err.line}: {err}"))
        return None, False
    for entry in entries:
        for name, message in _bibtex.check_entry(entry):
            errors.append(ValidationError(label, entry.line, name, message))
    return entries, True


def _read_tables(
    root: Any, label_of: Callable[[str], str], out: Loaded
) -> tuple[list[tuple[str, list[ValidationError]]], dict[str, Any], dict[str, str], bool]:
    """Read and check every table file; returns (errors per file, documents by stem, labels by stem, any file
    unparsed)."""
    per_file: list[tuple[str, list[ValidationError]]] = []
    table_docs: dict[str, Any] = {}
    labels: dict[str, str] = {}
    unparsed = False
    seen_stems: dict[str, str] = {}
    for stem, path, shared in _table_entries(root):
        rel = f"share-alike/{stem}.yaml" if shared else f"{stem}.yaml"
        label = label_of(rel)
        errors: list[ValidationError] = []
        per_file.append((label, errors))
        if stem in seen_stems:
            errors.append(
                ValidationError(label, None, "table", f"table {stem!r} is also defined in {seen_stems[stem]}")
            )
            continue
        seen_stems[stem] = label
        ok, doc = _read_yaml(path, label, errors)
        if not ok:
            unparsed = True
            continue
        if doc is None:
            errors.append(
                ValidationError(label, None, None, "the file is empty: no table is shipped without a row (FR-008-22)")
            )
        else:
            errors += [_error(label, issue) for issue in _rules.check_table(doc, stem, shared)]
        table_docs[stem] = doc
        labels[stem] = label
        out.tables += 1
        rows = doc.get("rows") if isinstance(doc, dict) else None
        for raw in rows if isinstance(rows, list) else []:
            if isinstance(raw, dict):
                out.rows += 1
                out.unverified += raw.get("verification") == "UNVERIFIED"
    return per_file, table_docs, labels, unparsed


def read_tables(root: Any, label_of: Callable[[str], str]) -> tuple[dict[str, Any], list[ValidationError]]:
    """Only the table files of a folder: the documents by stem and the errors of those files."""
    per_file, docs, _, _ = _read_tables(root, label_of, Loaded())
    return docs, [e for _, errs in per_file for e in errs]


def read_folder(root: Any, label_of: Callable[[str], str]) -> Loaded:
    """Read and validate the knowledge folder `root`; `label_of(relative_path)` names a file in the errors."""
    out = Loaded()
    per_file, table_docs, labels, unparsed_tables = _read_tables(root, label_of, out)

    bib_label = label_of("references.bib")
    bib_errors: list[ValidationError] = []
    per_file.append((bib_label, bib_errors))
    entries: list[_bibtex.BibEntry] | None = []
    bib_path = root.joinpath("references.bib")
    bib_known = True
    if bib_path.is_file():
        entries, bib_known = _read_bibliography(bib_path, bib_label, bib_errors)
    bib_keys = {e.key for e in entries} if entries is not None else set()
    out.references = len(entries) if entries is not None else 0

    catalogue = root.joinpath("catalogue")
    docs: dict[str, Any] = {}
    errors: list[ValidationError]
    for name, checker in (("equations", _rules.check_equations), ("glossary", _rules.check_glossary)):
        label = label_of(f"catalogue/{name}.yaml")
        errors = []
        per_file.append((label, errors))
        path = catalogue.joinpath(f"{name}.yaml") if catalogue.is_dir() else None
        if path is None or not path.is_file():
            continue
        ok, doc = _read_yaml(path, label, errors)
        if not ok:
            continue
        if doc is None:
            errors.append(
                ValidationError(
                    label, None, None, "the file is empty: no catalogue is shipped without an entry (FR-008-22)"
                )
            )
            continue
        errors += [_error(label, issue) for issue in checker(doc)]
        docs[name] = doc
        entries_list = doc.get("equations" if name == "equations" else "terms") if isinstance(doc, dict) else None
        count = len(entries_list) if isinstance(entries_list, list) else 0
        if name == "equations":
            out.equations = count
        else:
            out.terms = count

    cross = _rules.check_cross_file(
        {labels[stem]: doc for stem, doc in table_docs.items()},
        bib_keys if bib_known else _EVERYTHING,
        docs.get("equations"),
        docs.get("glossary"),
    )
    by_label = dict(per_file)
    for key, issues in cross.items():
        label = label_of(f"catalogue/{key}.yaml") if key in ("equations", "glossary") else key
        if key == "equations" and unparsed_tables:
            issues = [i for i in issues if i[1] != "rows"]
        by_label[label] += [_error(label, issue) for issue in issues]

    for _, errs in per_file:
        out.errors += errs
    if not out.errors:
        out.knowledge = _build(table_docs, entries or [], docs)
    return out


class _Everything:
    """A set that contains every key (used when the bibliography could not be read, to avoid cascading citation
    errors)."""

    def __contains__(self, item: object) -> bool:
        return True


_EVERYTHING = _Everything()


def _build(table_docs: dict[str, Any], entries: list[_bibtex.BibEntry], docs: dict[str, Any]) -> Knowledge:
    tables: dict[str, Table] = {}
    rows: dict[str, Row] = {}
    for stem in sorted(table_docs):
        doc = table_docs[stem]
        objects = tuple(_row_object(raw, stem) for raw in doc["rows"])
        tables[stem] = Table(table=stem, title=doc["title"], licence=doc["licence"], rows=objects)
        for row in objects:
            rows[row.id] = row
    eq_doc = docs.get("equations")
    gl_doc = docs.get("glossary")
    raw_equations = tuple(eq_doc["equations"]) if eq_doc else ()
    raw_terms = tuple(gl_doc["terms"]) if gl_doc else ()
    return Knowledge(
        tables=MappingProxyType(tables),
        rows=MappingProxyType(rows),
        raw_tables=MappingProxyType({stem: table_docs[stem] for stem in sorted(table_docs)}),
        references=tuple(sorted((_bibtex.to_reference(e) for e in entries), key=lambda r: r.key)),
        equations=tuple(_equation_object(raw) for raw in raw_equations),
        glossary=tuple(_term_object(raw) for raw in raw_terms),
        raw_equations=raw_equations,
        raw_terms=raw_terms,
    )

"""Loader, validator, lookup, catalogues, export and page renderer of the knowledge base (spec 008).

The package data are the parameter tables (`<table>.yaml`, `share-alike/<table>.yaml`), the bibliography
`references.bib` and the
catalogues `catalogue/equations.yaml` and `catalogue/glossary.yaml`. Importing the package reads no file; the first
call that
needs knowledge reads, validates and caches every file once (through `importlib.resources`), and the objects returned
are
immutable. A file that breaks a rule makes every call raise `KnowledgeSchemaError` (no partially validated data is
served).
Reading an UNVERIFIED `model_constant` or `parameter` row through `get_value` warns with
`UnverifiedParameterWarning`, so
that nothing unverified is used silently. PyYAML is imported only when a file is read.
"""

from __future__ import annotations

import importlib.resources
import json
import os
import warnings
from pathlib import Path
from typing import Any

from .._errors import InputError, InputTypeError
from ._load import Knowledge, Loaded, read_folder, read_tables
from ._model import (
    Equation,
    KnowledgeSchemaError,
    Reference,
    Row,
    Table,
    Term,
    UnverifiedParameterWarning,
    ValidationError,
    ValidationReport,
)

__all__ = [
    "Equation",
    "KnowledgeSchemaError",
    "Reference",
    "Row",
    "Table",
    "Term",
    "UnverifiedParameterWarning",
    "ValidationError",
    "ValidationReport",
    "bibliography",
    "equations",
    "export",
    "export_json",
    "get_parameter",
    "get_value",
    "glossary",
    "knowledge_changes",
    "list_parameters",
    "list_tables",
    "load_table",
    "render_pages",
    "validate_tables",
]

_WARNING_ROLES = ("model_constant", "parameter")
_loaded: Loaded | None = None
_export_cache: dict[str, Any] | None = None


def _packaged_root() -> Any:
    return importlib.resources.files("minephys.knowledge")


def _packaged_label(relative: str) -> str:
    return f"knowledge/{relative}"


def _packaged() -> Loaded:
    """The packaged knowledge read and validated once; the result (errors included) is cached."""
    global _loaded
    if _loaded is None:
        _loaded = read_folder(_packaged_root(), _packaged_label)
    return _loaded


def _knowledge() -> Knowledge:
    """The validated packaged knowledge; if it is invalid every call raises the first error (no partial data is
    served)."""
    loaded = _packaged()
    if loaded.knowledge is None:
        first = loaded.errors[0]
        raise KnowledgeSchemaError(str(first), file=first.file, index=first.index, field=first.field)
    return loaded.knowledge


def _name(value: Any, argument: str) -> str:
    if not isinstance(value, str):
        raise InputTypeError(f"argument '{argument}' must be a string, got {type(value).__name__}", argument=argument)
    return value


def list_tables() -> tuple[str, ...]:
    """Names of the packaged tables (file stems of `knowledge/*.yaml` and `knowledge/share-alike/*.yaml`), sorted."""
    return tuple(_knowledge().tables)


def load_table(table: str) -> Table:
    """The table named `table`; a name that is not in `list_tables()` raises `minephys.InputError` without opening a
    file."""
    name = _name(table, "table")
    tables = _knowledge().tables
    if name not in tables:
        raise InputError(f"argument 'table' must be one of {sorted(tables)}, got {name[:60]!r}", argument="table")
    return tables[name]


def get_parameter(id: str) -> Row:
    """The row with this id; an unknown id raises `minephys.InputError`, a non-string `minephys.InputTypeError`."""
    row_id = _name(id, "id")
    rows = _knowledge().rows
    if row_id not in rows:
        raise InputError(f"argument 'id': unknown knowledge row {row_id[:60]!r}", argument="id")
    return rows[row_id]


def list_parameters(
    table: str | None = None, role: str | None = None, verification: str | None = None
) -> tuple[Row, ...]:
    """Every row (UNVERIFIED ones included), optionally filtered by table, role and verification status."""
    return tuple(
        r
        for r in _knowledge().rows.values()
        if (table is None or r.table == table)
        and (role is None or r.role == role)
        and (verification is None or r.verification == verification)
    )


def get_value(id: str) -> float | tuple[float, float]:
    """The value of a row as a float (a `"p/q"` string evaluated as p / q in float64) or the `(min, max)` of a range
    row.

    An UNVERIFIED row of role `model_constant` or `parameter` emits `UnverifiedParameterWarning` naming the row id
    and its
    citation key; `limit` and `conversion` rows never warn.
    """
    row = get_parameter(id)
    if row.verification != "verified" and row.role in _WARNING_ROLES:
        warnings.warn(
            f"knowledge row {row.id!r} ({row.role}) is UNVERIFIED; source {row.citation}, {row.page}",
            UnverifiedParameterWarning,
            stacklevel=2,
        )
    if row.range is not None:
        return row.range
    return _numeric(row.value)


def _numeric(value: Any) -> float:
    if isinstance(value, str):
        numerator, denominator = value.split("/")
        return int(numerator) / int(denominator)
    return float(value)


def bibliography() -> tuple[Reference, ...]:
    """Every parsed bibliography entry, sorted by key."""
    return _knowledge().references


def equations(domain: str | None = None) -> tuple[Equation, ...]:
    """The equations catalogue (empty when none is shipped), optionally for one domain."""
    items = _knowledge().equations
    return items if domain is None else tuple(e for e in items if e.domain == domain)


def glossary(domain: str | None = None) -> tuple[Term, ...]:
    """The bilingual glossary (empty when none is shipped), optionally for one domain."""
    items = _knowledge().glossary
    return items if domain is None else tuple(t for t in items if t.domain == domain)


def _directory(value: Any, argument: str) -> Path:
    if not isinstance(value, str | os.PathLike) or isinstance(value, bytes):
        raise InputTypeError(
            f"argument '{argument}' must be a folder path, got {type(value).__name__}", argument=argument
        )
    path = Path(value)
    if not path.is_dir():
        raise InputError(
            f"argument '{argument}' must be an existing directory, got {str(path)[:80]!r}", argument=argument
        )
    return path


def validate_tables(path: str | os.PathLike[str] | None = None) -> ValidationReport:
    """Validate the packaged knowledge, or a folder with the same layout, and report every error with the counts."""
    if path is None:
        loaded = _packaged()
    else:
        folder = _directory(path, "path")
        loaded = read_folder(folder, lambda rel: str(folder / rel))
    return ValidationReport(
        errors=tuple(loaded.errors),
        rows=loaded.rows,
        unverified=loaded.unverified,
        equations=loaded.equations,
        terms=loaded.terms,
        references=loaded.references,
        tables=loaded.tables,
    )


def _version() -> str:
    from .. import __version__

    return __version__


def export() -> dict[str, Any]:
    """Every table, equation, term and reference with a summary of counts (FR-008-15); a new mapping on each call."""
    import copy

    global _export_cache
    if _export_cache is None:
        from ._render import build_export

        _export_cache = build_export(_knowledge(), _version())
    return copy.deepcopy(_export_cache)


def export_json() -> str:
    """`export()` as deterministic JSON: sorted keys, two-space indent, UTF-8 characters, LF line ends, trailing
    newline."""
    return json.dumps(export(), sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def render_pages(out_dir: str | os.PathLike[str], source: str | os.PathLike[str] | None = None) -> None:
    """Write one Markdown page per table plus `equations.md`, `bibliography.md` and `glossary.md` into an existing
    folder; `source` renders a knowledge folder with the layout of the package instead of the packaged knowledge (an
    invalid folder raises `KnowledgeSchemaError`)."""
    from ._render import build_pages

    folder = _directory(out_dir, "out_dir")
    if source is None:
        knowledge = _knowledge()
    else:
        root = _directory(source, "source")
        loaded = read_folder(root, lambda rel: str(root / rel))
        if loaded.knowledge is None:
            first = loaded.errors[0]
            raise KnowledgeSchemaError(str(first), file=first.file, index=first.index, field=first.field)
        knowledge = loaded.knowledge
    pages = build_pages(knowledge)
    for name, text in pages.items():
        (folder / name).write_bytes(text.encode("utf-8"))


def _signatures(path: Path) -> dict[str, tuple[str, Any, str]]:
    documents, errors = read_tables(path, lambda rel: str(path / rel))
    if errors:
        first = errors[0]
        raise KnowledgeSchemaError(str(first), file=first.file, index=first.index, field=first.field)
    out: dict[str, tuple[str, Any, str]] = {}
    for doc in documents.values():
        for raw in doc["rows"]:
            kind: str
            number: Any
            if "range" in raw:
                kind, number = "range", (float(raw["range"]["min"]), float(raw["range"]["max"]))
            else:
                kind, number = "value", _numeric(raw["value"])
            out[raw["id"]] = (kind, number, raw["verification"])
    return out


def knowledge_changes(old_dir: str | os.PathLike[str], new_dir: str | os.PathLike[str]) -> tuple[str, ...]:
    """Sorted ids of the rows whose value, range or verification differ between two knowledge folders (added and
    removed too)."""
    old = _signatures(_directory(old_dir, "old_dir"))
    new = _signatures(_directory(new_dir, "new_dir"))
    return tuple(sorted(i for i in old.keys() | new.keys() if old.get(i) != new.get(i)))

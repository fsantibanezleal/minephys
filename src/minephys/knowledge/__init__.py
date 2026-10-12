"""Reader of the packaged knowledge tables (DC-000-02), loaded lazily on first use (spec 000 FR-000-06, FR-000-20).

The tables are YAML files next to this module (`<table>.yaml`, `share-alike/<table>.yaml`). Importing the package
reads no file; the first call that needs a row loads and validates every table once and caches the result. The rows
are immutable. Reading an UNVERIFIED `model_constant` or `parameter` row through `get_value` emits
`UnverifiedParameterWarning` (spec 008 FR-008-12), so that no unverified constant is used silently.
"""

from __future__ import annotations

import functools
import importlib.resources
import re
import warnings
from dataclasses import dataclass
from typing import Any

__all__ = [
    "KnowledgeSchemaError",
    "Row",
    "Table",
    "UnverifiedParameterWarning",
    "get_parameter",
    "get_value",
    "list_parameters",
    "list_tables",
    "load_table",
]

_RATIONAL = re.compile(r"^-?[0-9]+/[0-9]+$")
_ROLES = ("model_constant", "parameter", "limit", "conversion")
_WARNING_ROLES = ("model_constant", "parameter")


class UnverifiedParameterWarning(UserWarning):
    """A model read an UNVERIFIED knowledge row of role `model_constant` or `parameter`."""


class KnowledgeSchemaError(ValueError):
    """A packaged knowledge table violates DC-000-02."""

    def __init__(self, message: str, *, file: str, index: int | None = None, field: str | None = None) -> None:
        super().__init__(message)
        self.file = file
        self.index = index
        self.field = field


@dataclass(frozen=True)
class Row:
    """One knowledge row (data model section 1); `value` is a float, `range` a (min, max) pair, one of them None."""

    id: str
    table: str
    quantity: str
    value: float | None
    range: tuple[float, float] | None
    units: str
    role: str
    citation: str
    page: str
    verification: str
    verified_on: str | None
    symbol: tuple[str, ...]
    notes: str | None


@dataclass(frozen=True)
class Table:
    """One knowledge table: header and rows in file order."""

    name: str
    title: str
    licence: str
    rows: tuple[Row, ...]


def _read_yaml(text: str, file: str) -> Any:
    import yaml  # PyYAML is a runtime dependency; imported on first use to keep `import minephys` cheap

    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    try:
        return yaml.load(text, Loader=loader)
    except yaml.YAMLError as err:
        raise KnowledgeSchemaError(f"{file}: not valid YAML: {err}", file=file) from None


def _number(value: Any, file: str, index: int, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise KnowledgeSchemaError(
            f"{file}: row {index}: {field} must be a number", file=file, index=index, field=field
        )
    return float(value)


def _row(raw: Any, name: str, file: str, index: int) -> Row:
    if not isinstance(raw, dict):
        raise KnowledgeSchemaError(f"{file}: row {index} is not a mapping", file=file, index=index)
    for key in ("id", "quantity", "units", "role", "citation", "page", "verification", "symbol"):
        if key not in raw:
            raise KnowledgeSchemaError(f"{file}: row {index}: field {key} missing", file=file, index=index, field=key)
    if raw["role"] not in _ROLES:
        raise KnowledgeSchemaError(
            f"{file}: row {index}: field role: unknown role", file=file, index=index, field="role"
        )
    value: float | None = None
    span: tuple[float, float] | None = None
    if "value" in raw:
        raw_value = raw["value"]
        if isinstance(raw_value, str):
            if not _RATIONAL.match(raw_value):
                raise KnowledgeSchemaError(
                    f"{file}: row {index}: field value: not a number or p/q", file=file, index=index, field="value"
                )
            numerator, denominator = raw_value.split("/")
            value = int(numerator) / int(denominator)
        else:
            value = _number(raw_value, file, index, "value")
    elif "range" in raw:
        bounds = raw["range"]
        span = (_number(bounds["min"], file, index, "range"), _number(bounds["max"], file, index, "range"))
    else:
        raise KnowledgeSchemaError(
            f"{file}: row {index}: value or range missing", file=file, index=index, field="value"
        )
    symbol = raw["symbol"]
    return Row(
        id=raw["id"],
        table=name,
        quantity=raw["quantity"],
        value=value,
        range=span,
        units=raw["units"],
        role=raw["role"],
        citation=raw["citation"],
        page=raw["page"],
        verification=raw["verification"],
        verified_on=raw.get("verified_on"),
        symbol=(symbol,) if isinstance(symbol, str) else tuple(symbol),
        notes=raw.get("notes"),
    )


def _build(text: str, name: str, file: str) -> Table:
    doc = _read_yaml(text, file)
    if not isinstance(doc, dict) or doc.get("table") != name or not isinstance(doc.get("rows"), list):
        raise KnowledgeSchemaError(f"{file}: not a knowledge table named {name!r}", file=file)
    rows = tuple(_row(raw, name, file, i) for i, raw in enumerate(doc["rows"], start=1))
    return Table(name=name, title=str(doc.get("title", "")), licence=str(doc.get("licence", "")), rows=rows)


@functools.cache
def _tables() -> dict[str, Table]:
    root = importlib.resources.files(__name__)
    sources = [(p.name[: -len(".yaml")], p) for p in root.iterdir() if p.name.endswith(".yaml")]
    shared = root.joinpath("share-alike")
    if shared.is_dir():
        sources += [(p.name[: -len(".yaml")], p) for p in shared.iterdir() if p.name.endswith(".yaml")]
    tables: dict[str, Table] = {}
    for name, path in sorted(sources, key=lambda item: item[0]):
        tables[name] = _build(path.read_text(encoding="utf-8"), name, f"knowledge/{name}.yaml")
    return tables


@functools.cache
def _rows() -> dict[str, Row]:
    index: dict[str, Row] = {}
    for table in _tables().values():
        for row in table.rows:
            if row.id in index:
                raise KnowledgeSchemaError(
                    f"knowledge/{table.name}.yaml: duplicate row id {row.id}", file=f"knowledge/{table.name}.yaml"
                )
            index[row.id] = row
    return index


def list_tables() -> tuple[str, ...]:
    """Names of the packaged tables, sorted."""
    return tuple(sorted(_tables()))


def load_table(table: str) -> Table:
    """The table named `table`; an unknown name raises `minephys.InputError`."""
    from .._errors import InputError, InputTypeError

    if not isinstance(table, str):
        raise InputTypeError(f"argument 'table' must be a string, got {type(table).__name__}", argument="table")
    tables = _tables()
    if table not in tables:
        raise InputError(f"argument 'table' must be one of {sorted(tables)}, got {table!r}", argument="table")
    return tables[table]


def get_parameter(id: str) -> Row:
    """The row with this id; an unknown id raises `minephys.InputError`."""
    from .._errors import InputError, InputTypeError

    if not isinstance(id, str):
        raise InputTypeError(f"argument 'id' must be a string, got {type(id).__name__}", argument="id")
    rows = _rows()
    if id not in rows:
        raise InputError(f"argument 'id': unknown knowledge row {id!r}", argument="id")
    return rows[id]


def list_parameters(
    table: str | None = None, role: str | None = None, verification: str | None = None
) -> tuple[Row, ...]:
    """Every row, optionally filtered by table, role and verification status (UNVERIFIED rows are never hidden)."""
    rows = _rows().values()
    return tuple(
        r
        for r in rows
        if (table is None or r.table == table)
        and (role is None or r.role == role)
        and (verification is None or r.verification == verification)
    )


def get_value(id: str) -> float | tuple[float, float]:
    """The value of a row as a float (a `p/q` string evaluated in float64) or the `(min, max)` of a range row.

    An UNVERIFIED row of role `model_constant` or `parameter` emits `UnverifiedParameterWarning` naming the row id and
    its citation key; `limit` and `conversion` rows never warn.
    """
    row = get_parameter(id)
    if row.verification != "verified" and row.role in _WARNING_ROLES:
        warnings.warn(
            f"knowledge row {row.id!r} ({row.role}) is UNVERIFIED; source {row.citation}, {row.page}",
            UnverifiedParameterWarning,
            stacklevel=2,
        )
    if row.value is not None:
        return row.value
    assert row.range is not None
    return row.range

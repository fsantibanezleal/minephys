"""Immutable data classes, errors and the warning of `minephys.knowledge` (spec 008 FR-008-06, FR-008-09, FR-008-12,
FR-008-19)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

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
]


class UnverifiedParameterWarning(UserWarning):
    """A model read an UNVERIFIED knowledge row of role `model_constant` or `parameter`."""


class KnowledgeSchemaError(ValueError):
    """A knowledge file violates the rules of its data contract; `file`, `index` (1-based) and `field` locate the
    error."""

    def __init__(self, message: str, *, file: str, index: int | None = None, field: str | None = None) -> None:
        super().__init__(message)
        self.file = file
        self.index = index
        self.field = field


@dataclass(frozen=True)
class ValidationError:
    """One rule violation found by `validate_tables`: the file, the 1-based row or entry index and the field."""

    file: str
    index: int | None
    field: str | None
    message: str

    def __str__(self) -> str:
        where = self.file
        if self.index:
            where += f", entry {self.index}"
        if self.field:
            where += f", field {self.field}"
        return f"{where}: {self.message}"


@dataclass(frozen=True)
class ValidationReport:
    """Result of `validate_tables`: every error (not only the first) and the counts of what was read."""

    errors: tuple[ValidationError, ...]
    rows: int
    unverified: int
    equations: int
    terms: int
    references: int
    tables: int

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class Row:
    """One knowledge row (DC-000-02). `value` is the number or the `"p/q"` string as written; `range` is `(min,
    max)`."""

    id: str
    quantity: str
    value: float | int | str | None
    range: tuple[float, float] | None
    units: str
    role: str
    citation: str
    page: str
    verification: str
    verified_on: str | None
    symbol: tuple[str, ...]
    notes: str | None
    table: str = ""


@dataclass(frozen=True)
class Table:
    """One knowledge table: header and rows in file order."""

    table: str
    title: str
    licence: str
    rows: tuple[Row, ...]

    @property
    def name(self) -> str:
        return self.table


@dataclass(frozen=True)
class Equation:
    """One entry of the equations catalogue (DC-008-01); `symbols` is a tuple of read-only mappings."""

    id: str
    title: str
    domain: str
    latex: str
    symbols: tuple[Mapping[str, str], ...]
    function: str
    citation: str
    page: str
    verification: str
    verified_on: str | None
    rows: tuple[str, ...] | None
    notes: str | None


@dataclass(frozen=True)
class Term:
    """One term of the bilingual glossary (DC-008-02)."""

    id: str
    domain: str
    term_en: str
    term_es: str
    definition_en: str
    definition_es: str
    citation: str | None
    see_also: tuple[str, ...] | None


@dataclass(frozen=True)
class Reference:
    """One parsed bibliography entry (DC-000-03); a field the entry does not have is None."""

    key: str
    entry_type: str
    author: str | None
    organization: str | None
    title: str
    year: int
    doi: str | None
    url: str | None
    access: str
    licence: str | None
    journal: str | None
    booktitle: str | None
    volume: str | None
    number: str | None
    pages: str | None
    publisher: str | None
    edition: str | None
    note: str | None

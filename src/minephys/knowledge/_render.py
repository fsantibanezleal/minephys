"""Deterministic Markdown pages and the JSON export of the knowledge (spec 008 FR-008-15, FR-008-16, FR-008-21).

Pages and export list their items in a canonical order (rows, equations and terms by id, references by key), so that
the same
knowledge gives the same bytes whatever the order of the source files. Every UNVERIFIED item carries the word
UNVERIFIED once,
in its verification line, and no verified item carries it.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from ._load import Knowledge
from ._model import Equation, Reference, Row, Table, Term
from ._rules import ROLES

__all__ = ["build_export", "build_pages"]


def _esc(text: Any) -> str:
    return str(text).replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")


def _scalar(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    return repr(float(value))


def _status(verification: str, verified_on: str | None) -> str:
    return "UNVERIFIED" if verification == "UNVERIFIED" else f"verified ({verified_on})"


def _locator(ref: Reference | None) -> str:
    if ref is None:
        return ""
    parts = []
    if ref.doi:
        parts.append(f"DOI {ref.doi}")
    if ref.url:
        parts.append(ref.url)
    return ", ".join(parts)


def _head(title: str, line: str, items: int, unverified: int) -> list[str]:
    return [f"# {_esc(title)}", "", line, "", f"Items: {items}", f"UNVERIFIED: {unverified}", ""]


def _row_block(row: Row, refs: Mapping[str, Reference]) -> list[str]:
    value = (
        f"Range: {_scalar(row.range[0])} to {_scalar(row.range[1])}" if row.range else f"Value: {_scalar(row.value)}"
    )
    cited = f"`{row.citation}`"
    where = _locator(refs.get(row.citation))
    lines = [
        f"### `{row.id}`",
        "",
        f"- Quantity: {_esc(row.quantity)}",
        f"- {value}",
        f"- Units: {_esc(row.units)}",
        f"- Role: {row.role}",
        f"- Citation: {cited}" + (f", {_esc(where)}" if where else ""),
        f"- Page: {_esc(row.page)}",
        f"- Verification: {_status(row.verification, row.verified_on)}",
        "- Symbol: " + ", ".join(f"`{s}`" for s in row.symbol),
    ]
    if row.notes:
        lines.append(f"- Notes: {_esc(row.notes)}")
    return [*lines, ""]


def _table_page(table: Table, refs: Mapping[str, Reference]) -> str:
    rows = sorted(table.rows, key=lambda r: r.id)
    unverified = sum(r.verification == "UNVERIFIED" for r in rows)
    out = _head(table.title, f"Table `{table.table}`, licence {table.licence}.", len(rows), unverified)
    for row in rows:
        out += _row_block(row, refs)
    return "\n".join(out)


def _equation_block(eq: Equation, refs: Mapping[str, Reference]) -> list[str]:
    where = _locator(refs.get(eq.citation))
    lines = [
        f"### `{eq.id}`",
        "",
        f"- Title: {_esc(eq.title)}",
        f"- Domain: {eq.domain}",
        f"- Function: `{eq.function}`",
        "- Equation:",
        "",
        "$$",
        eq.latex,
        "$$",
        "",
        "- Symbols:",
    ]
    lines += [f"  - `{s['symbol']}`: {_esc(s['meaning'])} [{_esc(s['units'])}]" for s in eq.symbols]
    lines += [
        f"- Citation: `{eq.citation}`" + (f", {_esc(where)}" if where else ""),
        f"- Page: {_esc(eq.page)}",
        f"- Verification: {_status(eq.verification, eq.verified_on)}",
    ]
    if eq.rows:
        lines.append("- Rows: " + ", ".join(f"`{r}`" for r in eq.rows))
    if eq.notes:
        lines.append(f"- Notes: {_esc(eq.notes)}")
    return [*lines, ""]


def _equations_page(equations: tuple[Equation, ...], refs: Mapping[str, Reference]) -> str:
    items = sorted(equations, key=lambda e: e.id)
    unverified = sum(e.verification == "UNVERIFIED" for e in items)
    out = _head("Equations catalogue", "Licence CC-BY-4.0.", len(items), unverified)
    if not items:
        out += ["No equation is catalogued yet.", ""]
    for eq in items:
        out += _equation_block(eq, refs)
    return "\n".join(out)


def _bibliography_page(references: tuple[Reference, ...]) -> str:
    out = _head("Bibliography", "Sources cited by the knowledge tables and catalogues.", len(references), 0)
    for ref in references:
        author = ref.author or ref.organization
        lines = [
            f"### `{ref.key}`",
            "",
            f"- Title: {_esc(ref.title)}",
            f"- Author: {_esc(author)}",
            f"- Year: {ref.year}",
            f"- Type: {ref.entry_type}",
            f"- Access: {ref.access}",
        ]
        if ref.doi:
            lines.append(f"- DOI: {ref.doi}")
        if ref.url:
            lines.append(f"- URL: {ref.url}")
        for name in ("journal", "booktitle", "volume", "number", "pages", "publisher", "edition", "licence", "note"):
            value = getattr(ref, name)
            if value:
                lines.append(f"- {name.capitalize()}: {_esc(value)}")
        out += [*lines, ""]
    if not references:
        out += ["No reference is listed.", ""]
    return "\n".join(out)


def _cell(text: Any) -> str:
    return _esc(text).replace("|", "\\|")


def _glossary_page(terms: tuple[Term, ...]) -> str:
    items = sorted(terms, key=lambda t: t.id)
    out = _head("Glossary", "English and Spanish terms and definitions. Licence CC-BY-4.0.", len(items), 0)
    if not items:
        return "\n".join([*out, "No term is defined yet.", ""])
    out += [
        "| Id | Domain | Term (EN) | Término (ES) | Definition (EN) | Definición (ES) | See also |",
        "|---|---|---|---|---|---|---|",
    ]
    for t in items:
        see = ", ".join(f"`{s}`" for s in t.see_also or ())
        out.append(
            f"| `{t.id}` | {t.domain} | {_cell(t.term_en)} | {_cell(t.term_es)} | {_cell(t.definition_en)} | "
            f"{_cell(t.definition_es)} | {see} |"
        )
    return "\n".join([*out, ""])


def build_pages(k: Knowledge) -> dict[str, str]:
    """The page name and text of every page: one per table, then equations, bibliography and glossary."""
    refs = {r.key: r for r in k.references}
    pages = {f"{name}.md": _table_page(table, refs) for name, table in sorted(k.tables.items())}
    pages["equations.md"] = _equations_page(k.equations, refs)
    pages["bibliography.md"] = _bibliography_page(k.references)
    pages["glossary.md"] = _glossary_page(k.glossary)
    return pages


def _count(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {"total": len(rows), "unverified": sum(r["verification"] == "UNVERIFIED" for r in rows)}


def build_export(k: Knowledge, version: str) -> dict[str, Any]:
    """The mapping of FR-008-15: tables, equations, glossary, bibliography sorted canonically, and the summary
    counts."""
    tables = []
    all_rows: list[Mapping[str, Any]] = []
    for name in sorted(k.raw_tables):
        doc = copy.deepcopy(dict(k.raw_tables[name]))
        doc["rows"] = sorted(doc["rows"], key=lambda r: r["id"])
        tables.append(doc)
        all_rows += doc["rows"]
    equations = sorted((copy.deepcopy(dict(e)) for e in k.raw_equations), key=lambda e: e["id"])
    terms = sorted((copy.deepcopy(dict(t)) for t in k.raw_terms), key=lambda t: t["id"])
    references = []
    for ref in k.references:
        entry = {name: getattr(ref, name) for name in ref.__dataclass_fields__ if getattr(ref, name) is not None}
        references.append(entry)
    summary = {
        "rows": _count(all_rows),
        "equations": _count(equations),
        "terms": len(terms),
        "references": len(references),
        "per_table": {doc["table"]: _count(doc["rows"]) for doc in tables},
        "per_role": {role: _count([r for r in all_rows if r["role"] == role]) for role in ROLES},
    }
    return {
        "version": version,
        "tables": tables,
        "equations": equations,
        "glossary": terms,
        "bibliography": references,
        "summary": summary,
    }

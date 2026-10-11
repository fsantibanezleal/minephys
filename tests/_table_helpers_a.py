"""Test-support helpers for the knowledge-table contract tests of specs 001 to 004 (haulage, blasting, geotech, bulk).

Reads `src/minephys/knowledge/<table>.yaml` and `references.bib` of the repository and checks them against the
JSON Schemas of DC-000-02 and DC-000-03 (reference implementation: `jsonschema`, imported inside the functions so that a
missing first-party artefact is the failure reason). Nothing here is an oracle for a value; the expected values live in
the test files that call these helpers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "src" / "minephys" / "knowledge"
CONTRACTS = ROOT / "contracts"


def load_table(name: str) -> dict[str, Any]:
    path = KNOWLEDGE / f"{name}.yaml"
    assert path.is_file(), f"missing knowledge table src/minephys/knowledge/{name}.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(doc, dict), f"{name}.yaml is not a mapping"
    return doc


def rows_by_id(name: str) -> dict[str, dict[str, Any]]:
    return {r["id"]: r for r in load_table(name)["rows"]}


def all_row_ids(exclude: str) -> set[str]:
    ids: set[str] = set()
    for f in KNOWLEDGE.glob("*.yaml"):
        if f.stem != exclude:
            ids |= {r["id"] for r in yaml.safe_load(f.read_text(encoding="utf-8"))["rows"]}
    return ids


def parse_bib(text: str) -> dict[str, dict[str, str]]:
    """Minimal BibTeX parser: `@type{key, field = {value} | "value" | number, ...}` with nested braces."""
    entries: dict[str, dict[str, str]] = {}
    pos = 0
    head = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")
    while True:
        m = head.search(text, pos)
        if not m:
            return entries
        entry: dict[str, str] = {"entry_type": m.group(1).lower()}
        i = m.end()
        depth = 1
        start = i
        while i < len(text) and depth > 0:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        body = text[start : i - 1]
        for fm in re.finditer(r"(\w+)\s*=\s*", body):
            j = fm.end()
            if j >= len(body):
                continue
            if body[j] == "{":
                d = 1
                k = j + 1
                while k < len(body) and d > 0:
                    d += {"{": 1, "}": -1}.get(body[k], 0)
                    k += 1
                value = body[j + 1 : k - 1]
            elif body[j] == '"':
                k = body.index('"', j + 1)
                value = body[j + 1 : k]
            else:
                value = re.match(r"[^,\s}]+", body[j:]).group(0)  # type: ignore[union-attr]
            entry.setdefault(fm.group(1).lower(), re.sub(r"\s+", " ", value).strip())
        entries[m.group(2)] = entry
        pos = i


def load_bib() -> dict[str, dict[str, str]]:
    path = KNOWLEDGE / "references.bib"
    assert path.is_file(), "missing src/minephys/knowledge/references.bib"
    return parse_bib(path.read_text(encoding="utf-8"))


def bib_entry_as_object(key: str, raw: dict[str, str]) -> dict[str, Any]:
    """The DC-000-03 object of a parsed entry (key and entry_type added, year as integer)."""
    obj: dict[str, Any] = dict(raw)
    obj["key"] = key
    if "year" in obj and obj["year"].isdigit():
        obj["year"] = int(obj["year"])
    return obj


def schema_errors(schema_file: str, instance: Any) -> list[str]:
    from jsonschema import Draft202012Validator

    path = CONTRACTS / schema_file
    assert path.is_file(), f"missing contracts/{schema_file}"
    validator = Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))
    return [f"/{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in validator.iter_errors(instance)]

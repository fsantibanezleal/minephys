"""CI check: knowledge honesty (spec 000 FR-000-20, FR-000-21, FR-000-22, FR-000-31, SC-000-03).

Usage:  python tools/check_knowledge.py [--root PATH]
Checks, over `<root>/src/minephys/knowledge/*.yaml`, `knowledge/share-alike/*.yaml` and `references.bib`:
  1. every table and bibliography entry satisfies the data model (DC-000-02, DC-000-03) and row ids are unique;
  2. every `citation` resolves in the bibliography; a CC-BY-4.0 table cites no share-alike source;
  3. every `symbol` minephys.<module>.<name> resolves in the static `__all__` of its module (a module that does not
     exist yet is "planned" and not reported);
  4. every `verified` row is pinned by an `@pytest.mark.knowledge("<row id>")` test;
  5. no function lists an UNVERIFIED `parameter` row under `Knowledge rows` in its docstring;
  6. `REUSE.toml` annotates the knowledge folder (CC-BY-4.0) and the share-alike folder (CC-BY-SA).
Exit 0 and `OK` when clean, 1 with one line per violation naming file, row (or function) and field.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import Any

import _knowledge_io as kio

HERE = Path(__file__).resolve().parents[1]


def reuse_problems(root: Path) -> list[str]:
    path = root / "REUSE.toml"
    if not path.is_file():
        return ["REUSE.toml: missing"]
    try:
        doc = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as err:
        return [f"REUSE.toml: not valid TOML: {err}"]
    annotations = doc.get("annotations", [])
    out: list[str] = []
    for label, needle, licences in (
        ("src/minephys/knowledge/*.yaml", "knowledge/*.yaml", ("CC-BY-4.0",)),
        ("src/minephys/knowledge/references.bib", "references.bib", ("CC-BY-4.0",)),
        ("src/minephys/knowledge/share-alike/*.yaml", "share-alike/*.yaml", kio.SHARE_ALIKE_LICENCES),
    ):
        covered = any(
            isinstance(a, dict)
            and needle in " ".join(a["path"] if isinstance(a.get("path"), list) else [str(a.get("path", ""))])
            and a.get("SPDX-License-Identifier") in licences
            for a in annotations
        )
        if not covered:
            out.append(f"REUSE.toml: no annotation gives {label} the licence {' or '.join(licences)} (FR-000-31)")
    return out


def check(root: Path) -> list[str]:
    problems: list[str] = []
    files = [kio.read_table(tf) for tf in kio.table_files(root)]
    bib, bib_errors = kio.read_bibliography(root)
    problems += bib_errors
    seen: dict[str, str] = {}
    rows: list[tuple[kio.TableFile, dict[str, Any]]] = []
    for tf in files:
        problems += tf.errors + kio.validate_table(tf)
        for row in kio.rows_of(tf):
            if row["id"] in seen:
                problems.append(f"{tf.label}: row {row['id']}: field id: duplicate of a row in {seen[row['id']]}")
            seen.setdefault(row["id"], tf.label)
            rows.append((tf, row))
    all_rows = {row["id"]: row for _, row in rows}
    pinned = kio.pinned_rows(root)
    for tf, row in rows:
        cite = row.get("citation")
        if isinstance(cite, str) and kio.BIB_KEY.match(cite):
            if cite not in bib:
                problems.append(f"{tf.label}: row {row['id']}: field citation: key {cite} is not in references.bib")
            elif not tf.share_alike and str(bib[cite].get("licence", "")).startswith("CC-BY-SA"):
                problems.append(
                    f"{tf.label}: row {row['id']}: field citation: {cite} is share-alike but the table is CC-BY-4.0"
                )
        for symbol in kio.symbols_of(row):
            if not kio.SYMBOL.match(symbol):
                continue
            _, module, name = symbol.split(".")
            exported = kio.exported_names(root, module)
            if exported is not None and name not in exported:
                problems.append(
                    f"{tf.label}: row {row['id']}: field symbol: {symbol} is not exported by minephys.{module}"
                )
        if row.get("verification") == "verified" and row["id"] not in pinned:
            problems.append(
                f"{tf.label}: row {row['id']}: verified but no @pytest.mark.knowledge({row['id']!r}) test pins it"
            )
    for file, function, words in kio.knowledge_rows_of_functions(root):
        for word in dict.fromkeys(words):
            row = all_rows.get(word)
            if row and row.get("role") == "parameter" and row.get("verification") == "UNVERIFIED":
                problems.append(
                    f"{file}: function {function}: row {word}: lists an UNVERIFIED parameter row under Knowledge rows"
                )
    problems += reuse_problems(root)
    return problems


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=HERE)
    args = ap.parse_args(argv[1:])
    problems = check(args.root.resolve())
    if problems:
        print(f"KNOWLEDGE CHECK FAIL ({len(problems)}):")
        for line in problems:
            print(line)
        return 1
    print("KNOWLEDGE CHECK OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

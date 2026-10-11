"""T-008-011 (P-008-05): bibliography round trip with nested braces and accents.

Public API under test (`minephys.knowledge`): `bibliography()` (see tests/unit/test_t_008_011_bibtex.py) reading a generated
`references.bib` served through a fixture package tree.

P-008-05: rendering parsed entries back to BibTeX and parsing again gives the same entries. The renderer is written in this file (the
library's own renderer is private): generated entries -> text (this file) -> parse (library) = P1 -> text (this file) -> parse
(library) = P2, and P1 = P2 exactly. Independently of the brace policy, P1 equals the generated entries with all braces removed from
the text fields (content is preserved: nested braces, BibTeX accents such as {\\'e}, UTF-8 letters, digits, punctuation).
Generated entries: 1 to 4 entries with distinct keys, a random allowed type, `author` or `organization`, `title`, an integer `year`,
a DOI or a URL, an access class, optional journal / publisher / note; text values contain balanced nested braces and accents.
25 examples (each example starts an interpreter that serves the fixture tree through `importlib.resources`).
Oracle: the generators themselves.
"""

from __future__ import annotations

import dataclasses  # noqa: F401  (used in the interpreter script strings)
import string
import tempfile
from pathlib import Path
from typing import Any

import _knowledge_fixtures as fx
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

PLAIN = st.text(
    alphabet=string.ascii_letters + string.digits + " .,;:-_/()+=!?'áéíóúñüµÅ", min_size=1, max_size=20
).filter(lambda s: s.strip() == s and s)
ACCENT = st.sampled_from(["{\\'e}", "{\\~n}", '{\\"u}', "{\\'\\i}", "{\\c c}", "\\&", "\\%"])


@st.composite
def braced(draw: Any, depth: int = 0) -> str:
    """Text with balanced nested braces, accents and plain runs."""
    parts = []
    for _ in range(draw(st.integers(1, 4))):
        kind = draw(st.sampled_from(["plain", "plain", "accent", "group" if depth < 2 else "plain"]))
        if kind == "plain":
            parts.append(draw(PLAIN))
        elif kind == "accent":
            parts.append(draw(ACCENT))
        else:
            parts.append("{" + draw(braced(depth + 1)) + "}")
    return " ".join(parts).replace("  ", " ")


@st.composite
def entries(draw: Any) -> list[dict[str, Any]]:
    keys = draw(st.lists(st.from_regex(r"[a-z][a-z0-9_:-]{0,14}", fullmatch=True), min_size=1, max_size=4, unique=True))
    out = []
    for key in keys:
        e: dict[str, Any] = {
            "key": key,
            "entry_type": draw(
                st.sampled_from(["article", "book", "inbook", "inproceedings", "techreport", "manual", "misc"])
            ),
            "title": draw(braced()),
            "year": draw(st.integers(1800, 2100)),
            "access": draw(st.sampled_from(["open", "paywalled", "regulation", "bibliographic-only"])),
        }
        e["author" if draw(st.booleans()) else "organization"] = draw(braced())
        if draw(st.booleans()):
            e["doi"] = (
                "10."
                + str(draw(st.integers(1000, 99999)))
                + "/"
                + draw(st.from_regex(r"[A-Za-z0-9.()_-]{1,10}", fullmatch=True))
            )
        else:
            e["url"] = "https://example.org/" + draw(st.from_regex(r"[a-z0-9]{1,8}", fullmatch=True))
        for opt in ("journal", "publisher", "note"):
            if draw(st.booleans()):
                e[opt] = draw(braced())
        out.append(e)
    return out


def render(es: list[dict[str, Any]], style: str = "braces") -> str:
    chunks = []
    for e in es:
        lines = [f"@{e['entry_type']}{{{e['key']},"]
        fields = []
        for k, v in e.items():
            if k in {"key", "entry_type"}:
                continue
            fields.append(f"  {k} = {v}" if k == "year" and style == "digits" else f"  {k} = {{{v}}}")
        chunks.append("\n".join(lines) + "\n" + ",\n".join(fields) + "\n}\n")
    return "\n% a comment\n".join(chunks)


def parse(bib: str) -> dict[str, dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="mpk-") as tmp:
        table = fx.good_tables()["haulage"]
        # every citation must exist in the generated bibliography: point the table at the first key
        first = next(iter(_keys(bib)))
        for row in table["rows"]:
            row["citation"] = first
        base = fx.write_package_tree(
            Path(tmp) / "pkg", bib=bib, tables={"haulage": table}, equations=None, glossary=None
        )
        return fx.run_api(
            base,
            """
import dataclasses
print(json.dumps({r.key: {k: v for k, v in dataclasses.asdict(r).items() if v is not None} for r in K.bibliography()}))
""",
        )


def _keys(bib: str) -> list[str]:
    import re

    return re.findall(r"(?m)^@\w+\{([^,\s]+),", bib)


def strip_braces(value: Any) -> Any:
    return value.replace("{", "").replace("}", "") if isinstance(value, str) else value


@pytest.mark.req("P-008-05")
@pytest.mark.oracle(
    "analytical", "the generated entries: parse(render(parse(render(x)))) = parse(render(x)); content preserved"
)
@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(es=entries(), style=st.sampled_from(["braces", "digits"]))
def test_p_008_05_round_trip(es: list[dict[str, Any]], style: str) -> None:
    p1 = parse(render(es, style))
    assert set(p1) == {e["key"] for e in es}
    for e in es:
        got = p1[e["key"]]
        assert got["entry_type"] == e["entry_type"] and got["year"] == e["year"] and got["access"] == e["access"]
        for k, v in e.items():
            if k in {"key", "entry_type", "year", "access"}:
                continue
            assert strip_braces(got[k]) == strip_braces(v), (k, v, got[k])
        assert set(got) == set(e), "no field is added or lost"
    # render the PARSED entries again (with this file's renderer) and parse once more
    p2 = parse(render([p1[k] for k in sorted(p1)], style))
    assert p2 == p1


@pytest.mark.req("P-008-05")
@pytest.mark.oracle("hand-calculation", "nested braces three levels deep and BibTeX accent macros survive a round trip")
def test_p_008_05_deeply_nested_braces_and_accents() -> None:
    e = {
        "key": "nest1",
        "entry_type": "article",
        "title": "A {B {C {D}} e} {\\'e}tude de {\\~n}andú µm",
        "author": "M{\\\"u}ller, {J}. and Garc{\\'\\i}a",
        "year": 2022,
        "doi": "10.1000/nest.1",
        "access": "open",
    }
    p1 = parse(render([e]))
    assert strip_braces(p1["nest1"]["title"]) == strip_braces(e["title"])
    assert strip_braces(p1["nest1"]["author"]) == strip_braces(e["author"])
    assert parse(render([p1["nest1"]])) == p1

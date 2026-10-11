"""T-008-040 (FR-008-16): Markdown pages with counts, UNVERIFIED labels, roles, licences and the EN/ES glossary.

Expected behaviour (`minephys.knowledge.render_pages(out_dir)`): writes, deterministically and as UTF-8 text with LF line ends, one Markdown
page per table (`<table>.md`, share-alike tables included with their licence) plus `equations.md`, `bibliography.md` and `glossary.md`;
each page starts with the counts of its items and of its UNVERIFIED items (within the first lines of the page), labels every UNVERIFIED
item with the word "UNVERIFIED" (and no verified item), shows for every row its value or range, units, citation with the DOI or URL of the
cited source, page, role, verification and symbol, and shows the glossary in English and Spanish columns (the English and the Spanish
term and definition of a term on one table row).
The layout is not specified beyond that, so the tests are layout-neutral: an item's block is the text from the first occurrence of its id
(or key) to the first occurrence of the next item's id; counts are looked for as standalone integers in the first 8 lines.

Oracle: the hand-counted fixture knowledge (tests/_knowledge_fixtures.py): haulage 3 rows / 2 UNVERIFIED, blasting 2 / 1, geotech_sa 1 / 1,
2 equations / 1 UNVERIFIED, 4 references, 3 glossary terms.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import _knowledge_fixtures as fx
import pytest

HEAD_LINES = 8
CITE = {
    "doe2020": ("10.1000/xyz123",),
    "agency2025": ("https://example.org/factors.pdf",),
    "epa2025ghghub": ("https://www.epa.gov/climateleadership/ghg-emission-factors-hub",),
    "sharealike2019": ("https://example.org/handbook",),
}


def _render(tmp_path: Path, **kw: Any) -> dict[str, str]:
    base = fx.write_package_tree(tmp_path / "pkg", share_alike=fx.good_share_alike(), **kw)
    pages = tmp_path / "pages"
    pages.mkdir()
    fx.run_api(base, "K.render_pages(%r); print(json.dumps(True))" % str(pages))
    out = {}
    for p in sorted(pages.iterdir()):
        raw = p.read_bytes()
        assert b"\r" not in raw, f"{p.name}: LF line ends are expected"
        out[p.name] = raw.decode("utf-8")  # strict UTF-8
    return out


def _head(page: str) -> str:
    return "\n".join(page.splitlines()[:HEAD_LINES])


def _has_int(text: str, n: int) -> bool:
    return re.search(rf"(?<![\w.]){n}(?![\w.])", text) is not None


def _blocks(page: str, ids: list[str]) -> dict[str, str]:
    pos = sorted((page.index(i), i) for i in ids)
    out = {}
    for k, (start, item) in enumerate(pos):
        end = pos[k + 1][0] if k + 1 < len(pos) else len(page)
        out[item] = page[start:end]
    return out


@pytest.mark.req("FR-008-16")
@pytest.mark.oracle("hand-calculation", "one page per table plus equations, bibliography and glossary")
def test_fr_008_16_the_set_of_pages(tmp_path: Path) -> None:
    pages = _render(tmp_path)
    assert set(pages) == {
        "haulage.md",
        "blasting.md",
        "geotech_sa.md",
        "equations.md",
        "bibliography.md",
        "glossary.md",
    }
    assert all(text.strip() for text in pages.values())


@pytest.mark.req("FR-008-16")
@pytest.mark.oracle("hand-calculation", "each page starts with the item count and the UNVERIFIED count")
@pytest.mark.parametrize(
    ("page", "items", "unverified"),
    [
        ("haulage.md", 3, 2),
        ("blasting.md", 2, 1),
        ("geotech_sa.md", 1, 1),
        ("equations.md", 2, 1),
        ("bibliography.md", 4, 0),
        ("glossary.md", 3, 0),
    ],
)
def test_fr_008_16_pages_start_with_the_counts(tmp_path: Path, page: str, items: int, unverified: int) -> None:
    head = _head(_render(tmp_path)[page])
    assert _has_int(head, items), f"the item count {items} is not in the head of {page}:\n{head}"
    assert _has_int(head, unverified), f"the UNVERIFIED count {unverified} is not in the head of {page}:\n{head}"
    assert re.search(r"unverified", head, re.I), "the head must say which count is the UNVERIFIED one"


@pytest.mark.req("FR-008-16")
@pytest.mark.oracle(
    "hand-calculation",
    "every row is shown with value or range, units, citation with DOI or URL, page, role, verification and symbol",
)
def test_fr_008_16_rows_show_every_required_field_and_label_unverified_ones(tmp_path: Path) -> None:
    pages = _render(tmp_path)
    docs = {**fx.good_tables(), **fx.good_share_alike()}
    for name, doc in docs.items():
        page = pages[f"{name}.md"]
        assert doc["licence"] in page, f"{name}: the licence is shown"
        assert doc["title"] in page
        blocks = _blocks(page, [r["id"] for r in doc["rows"]])
        for r in doc["rows"]:
            block = blocks[r["id"]]
            if r["verification"] == "UNVERIFIED":
                assert "UNVERIFIED" in block, f"{r['id']} is not labelled UNVERIFIED"
            else:
                assert "UNVERIFIED" not in block and "verified" in block, (
                    f"{r['id']}: verified rows are not labelled UNVERIFIED"
                )
            if "value" in r:
                assert str(r["value"]) in block, (r["id"], r["value"])
            else:
                assert "0.15" in block and re.search(r"(?<![\d.])0(\.0)?(?![\d])", block), (r["id"], "range ends")
            for key in ("units", "role", "citation", "page"):
                assert r[key] in block, (r["id"], key, r[key])
            assert any(c in block for c in CITE[r["citation"]]), (r["id"], "DOI or URL of", r["citation"])
            symbols = r["symbol"] if isinstance(r["symbol"], list) else [r["symbol"]]
            assert all(s in block for s in symbols), (r["id"], symbols)


@pytest.mark.req("FR-008-16")
@pytest.mark.oracle("hand-calculation", "the share-alike page carries its licence, the others the main one")
def test_fr_008_16_licences_are_shown_per_page(tmp_path: Path) -> None:
    pages = _render(tmp_path)
    assert "CC-BY-SA-4.0" in pages["geotech_sa.md"]
    for name in ("haulage.md", "blasting.md"):
        assert "CC-BY-4.0" in pages[name] and "CC-BY-SA" not in pages[name]


@pytest.mark.req("FR-008-16")
@pytest.mark.oracle(
    "hand-calculation", "equations page: id, LaTeX, function, citation with page, units of symbols, UNVERIFIED label"
)
def test_fr_008_16_equations_page(tmp_path: Path) -> None:
    page = _render(tmp_path)["equations.md"]
    eqs = fx.good_equations()["equations"]
    blocks = _blocks(page, [e["id"] for e in eqs])
    for e in eqs:
        block = blocks[e["id"]]
        assert e["latex"] in block and e["function"] in block and e["citation"] in block and e["page"] in block
        for s in e["symbols"]:
            assert s["units"] in block and s["meaning"] in block
        assert ("UNVERIFIED" in block) == (e["verification"] == "UNVERIFIED"), e["id"]
        for row_id in e.get("rows", []):
            assert row_id in block


@pytest.mark.req("FR-008-16")
@pytest.mark.oracle("hand-calculation", "bibliography page: key, title, year, DOI or URL of every entry")
def test_fr_008_16_bibliography_page(tmp_path: Path) -> None:
    page = _render(tmp_path)["bibliography.md"]
    entries = {
        "doe2020": ("A Sourced Model of Comminution Energy", "2020", "10.1000/xyz123"),
        "agency2025": ("Emission factors", "2025", "https://example.org/factors.pdf"),
        "epa2025ghghub": (
            "GHG Emission Factors Hub",
            "2025",
            "https://www.epa.gov/climateleadership/ghg-emission-factors-hub",
        ),
        "sharealike2019": ("A share-alike handbook", "2019", "https://example.org/handbook"),
    }
    blocks = _blocks(page, list(entries))
    for key, (title, year, locator) in entries.items():
        assert title in blocks[key] and year in blocks[key] and locator in blocks[key], key


@pytest.mark.req("FR-008-16")
@pytest.mark.oracle(
    "hand-calculation", "glossary page: English and Spanish columns on the same table row, accents preserved"
)
def test_fr_008_16_glossary_page_has_english_and_spanish_columns(tmp_path: Path) -> None:
    page = _render(tmp_path)["glossary.md"]
    lines = page.splitlines()
    for t in fx.good_glossary()["terms"]:
        row = [ln for ln in lines if t["term_en"] in ln]
        assert row, f"term {t['term_en']!r} is not on the page"
        joined = " ".join(row)
        for field in ("term_es", "definition_en", "definition_es"):
            assert t[field] in joined or t[field] in page, (t["id"], field)
        assert t["term_es"] in joined, f"{t['id']}: the Spanish term is not on the same row as the English one"
    assert "ángulo" in page and "aceleración" in page and "tamaño" in page and "camión de extracción" in page
    assert page.count("|") >= 6, "a Markdown table is expected for the two-column glossary"


@pytest.mark.req("FR-008-16")
def test_fr_008_16_pages_are_valid_utf_8_with_no_trailing_garbage(tmp_path: Path) -> None:
    for name, text in _render(tmp_path).items():
        assert text.endswith("\n"), name
        assert "�" not in text and "\x00" not in text, name
        assert json.dumps(text)  # round-trips as text

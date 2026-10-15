"""T-000-015 (FR-000-23): the knowledge documentation generator, `tools/gen_knowledge_docs.py`.

Expected CLI:

    python tools/gen_knowledge_docs.py [--root PATH] [--check]

Without `--check` it writes one page per table (files of `src/minephys/knowledge/*.yaml` and of
`src/minephys/knowledge/share-alike/*.yaml`) to `<root>/docs/reference/knowledge/<table>.md`, deterministic (no time
stamp, same bytes on every run). A page lists every row, in table order, with: id, value or range (a `"p/q"` value as
written), units, citation key with its DOI or URL from `references.bib`, page locator, verification status and
symbol(s); every UNVERIFIED row is marked with the word `UNVERIFIED` and no verified row carries that word.
With `--check` nothing is written and the exit status is 1 when any committed page is missing or differs from the
generated one (stdout names the page), else 0. A malformed table makes the tool exit non-zero naming the file
without a traceback.

Oracle: hand-written fixture tables and the expectations written in this file (hand calculation).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from _mini_repo import GOOD_BIB, REPO_ROOT, row, run_tool, table, write_repo

REQ_PAGE = "docs/reference/knowledge"


def fixture_tables() -> dict[str, dict]:
    rows = [
        row("alpha_verified", value=10.21, units="kg CO2 / US gal", verification="verified", symbol="minephys.demo.f"),
        row(
            "beta_range",
            citation="agency2025",
            units="1",
            symbol=["minephys.demo.f", "minephys.demo.g"],
            page="Table 5, p. 3",
        ),
        row("gamma_rational", value="19/30", citation="agency2025", role="limit", page="eq. 1"),
        row("delta_negative", value=-0.8, verification="verified", symbol="minephys.demo.g"),
    ]
    del rows[1]["value"]
    rows[1]["range"] = {"min": 0.55, "max": 0.65}
    rows[1]["role"] = "parameter"
    return {"demo": table("demo", rows)}


def build(tmp: Path) -> Path:
    return write_repo(tmp, tables=fixture_tables(), bib=GOOD_BIB)


def generate(root: Path):
    return run_tool("gen_knowledge_docs.py", "--root", str(root))


def page_of(root: Path, name: str = "demo") -> str:
    path = root / REQ_PAGE / f"{name}.md"
    assert path.is_file(), f"missing page {path}"
    return path.read_text(encoding="utf-8")


def segment(text: str, row_id: str, order: list[str]) -> str:
    """Text from the row's first mention up to the next row's first mention."""
    start = text.index(row_id)
    later = [text.index(o) for o in order if o != row_id and o in text and text.index(o) > start]
    return text[start : min(later) if later else len(text)]


ORDER = ["alpha_verified", "beta_range", "gamma_rational", "delta_negative"]


@pytest.mark.req("FR-000-23")
@pytest.mark.oracle("hand-calculation", "one page per table with every row's fields")
def test_page_lists_every_row_with_all_fields(tmp_path: Path) -> None:
    root = build(tmp_path)
    proc = generate(root)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = page_of(root)
    by_id = sorted(ORDER)
    assert by_id != ORDER, "the fixture lists its rows out of id order, so the sort is really tested"
    assert [text.index(i) for i in by_id] == sorted(text.index(i) for i in ORDER), "rows are sorted by id (FR-008-15)"
    a = segment(text, "alpha_verified", ORDER)
    for token in ("10.21", "kg CO2 / US gal", "doe2020", "10.1000/xyz123", "p. 1", "minephys.demo.f", "verified"):
        assert token in a, (token, a)
    b = segment(text, "beta_range", ORDER)
    for token in ("0.55", "0.65", "agency2025", "https://example.org/factors.pdf", "Table 5, p. 3", "minephys.demo.g"):
        assert token in b, (token, b)
    g = segment(text, "gamma_rational", ORDER)
    assert "19/30" in g
    assert "eq. 1" in g
    d = segment(text, "delta_negative", ORDER)
    assert "-0.8" in d or chr(0x2212) + "0.8" in d


@pytest.mark.req("FR-000-23")
@pytest.mark.oracle("hand-calculation", "FR-000-23: every UNVERIFIED row is marked, no verified row is")
def test_unverified_rows_are_marked_and_verified_rows_are_not(tmp_path: Path) -> None:
    root = build(tmp_path)
    assert generate(root).returncode == 0
    text = page_of(root)
    assert "UNVERIFIED" in segment(text, "beta_range", ORDER)
    assert "UNVERIFIED" in segment(text, "gamma_rational", ORDER)
    assert "UNVERIFIED" not in segment(text, "alpha_verified", ORDER)
    assert "UNVERIFIED" not in segment(text, "delta_negative", ORDER)
    assert text.count("UNVERIFIED") >= 2


@pytest.mark.req("FR-000-23")
@pytest.mark.oracle("hand-calculation", "one page per table, share-alike tables included, named after the table")
def test_one_page_per_table_including_share_alike(tmp_path: Path) -> None:
    sa = {"sa": table("sa", [row("sa_row", citation="sharealike2019")], licence="CC-BY-SA-4.0")}
    root = write_repo(tmp_path, tables=fixture_tables(), share_alike_tables=sa, bib=GOOD_BIB)
    assert generate(root).returncode == 0
    pages = sorted(p.name for p in (root / REQ_PAGE).glob("*.md"))
    assert "demo.md" in pages
    assert "sa.md" in pages
    assert "sa_row" in page_of(root, "sa")
    assert "CC-BY-SA-4.0" in page_of(root, "sa"), "the page states the table licence"


@pytest.mark.req("FR-000-23")
@pytest.mark.oracle("hand-calculation", "determinism: two runs give identical bytes, and no time stamp appears")
def test_generation_is_deterministic(tmp_path: Path) -> None:
    root = build(tmp_path)
    assert generate(root).returncode == 0
    first = (root / REQ_PAGE / "demo.md").read_bytes()
    assert generate(root).returncode == 0
    assert (root / REQ_PAGE / "demo.md").read_bytes() == first
    import datetime as dt

    body = first.decode("utf-8").replace("2026-10-06", "")  # the fixture's verified_on date is legitimate content
    assert dt.date.today().isoformat() not in body, "a generation date would make the pages non-reproducible"


@pytest.mark.req("FR-000-23")
@pytest.mark.oracle("hand-calculation", "--check: clean pages pass; a missing page, a hand edit or a stale value fail")
def test_check_mode(tmp_path: Path) -> None:
    root = build(tmp_path)
    assert run_tool("gen_knowledge_docs.py", "--root", str(root), "--check").returncode == 1, "no page yet: differs"
    assert generate(root).returncode == 0
    clean = run_tool("gen_knowledge_docs.py", "--root", str(root), "--check")
    assert clean.returncode == 0, clean.stdout + clean.stderr

    page = root / REQ_PAGE / "demo.md"
    original = page.read_bytes()
    page.write_bytes(original + b"\nhand edit\n")
    edited = run_tool("gen_knowledge_docs.py", "--root", str(root), "--check")
    assert edited.returncode == 1
    assert "demo.md" in edited.stdout
    page.write_bytes(original)

    # stale page: the table changed (10.21 -> 10.22) but the page was not regenerated
    yaml_file = root / "src" / "minephys" / "knowledge" / "demo.yaml"
    yaml_file.write_text(yaml_file.read_text(encoding="utf-8").replace("10.21", "10.22"), encoding="utf-8")
    stale = run_tool("gen_knowledge_docs.py", "--root", str(root), "--check")
    assert stale.returncode == 1
    assert "demo.md" in stale.stdout

    page.unlink()
    missing = run_tool("gen_knowledge_docs.py", "--root", str(root), "--check")
    assert missing.returncode == 1
    assert "demo.md" in missing.stdout


@pytest.mark.req("FR-000-23")
@pytest.mark.oracle("hand-calculation", "--check writes nothing")
def test_check_mode_does_not_write(tmp_path: Path) -> None:
    root = build(tmp_path)
    proc = run_tool("gen_knowledge_docs.py", "--root", str(root), "--check")
    assert proc.returncode == 1, "no page exists yet, so the check reports a difference"
    assert not (root / REQ_PAGE).exists() or not list((root / REQ_PAGE).glob("*.md"))


@pytest.mark.req("FR-000-23")
@pytest.mark.oracle(
    "hand-calculation", "hostile text in a row (table pipes, markdown, unicode) keeps every row present"
)
def test_hostile_text_does_not_break_the_page(tmp_path: Path) -> None:
    rows = [
        row("pipe_row", units="m | s", page="p. 1 | p. 2"),
        row("md_row", page="*bold* `code` <b>x</b> [l](u)"),
        row("uni_row", units="kg CO₂ / m³", page="§2 — μσ"),
        row("last_row"),
    ]
    rows[0]["quantity"] = "a | b * c <d> `e`"
    root = write_repo(tmp_path, tables={"demo": table("demo", rows)}, bib=GOOD_BIB)
    proc = generate(root)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = page_of(root)
    order = ["pipe_row", "md_row", "uni_row", "last_row"]
    by_id = sorted(order)
    assert by_id != order, "the fixture lists its rows out of id order, so the sort is really tested"
    assert [text.index(o) for o in by_id] == sorted(text.index(o) for o in order), "rows are sorted by id (FR-008-15)"
    for token in ("CO₂", "μσ"):
        assert token in text
    assert (root / REQ_PAGE / "demo.md").read_bytes().decode("utf-8")  # valid UTF-8


@pytest.mark.req("FR-000-23")
@pytest.mark.oracle("hand-calculation", "hostile: a malformed table is reported by file name, without a traceback")
def test_malformed_table_is_reported(tmp_path: Path) -> None:
    root = build(tmp_path)
    (root / "src" / "minephys" / "knowledge" / "broken.yaml").write_text("rows: [unclosed\n", encoding="utf-8")
    proc = generate(root)
    assert proc.returncode != 0
    assert "broken.yaml" in proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr


@pytest.mark.req("FR-000-23")
@pytest.mark.oracle("hand-calculation", "the committed pages of this repository are up to date")
def test_repository_pages_are_current() -> None:
    proc = run_tool("gen_knowledge_docs.py", "--check")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (REPO_ROOT / REQ_PAGE / "units.md").is_file(), "the units table has a page"

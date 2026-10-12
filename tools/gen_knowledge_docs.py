"""Generate the knowledge reference pages (spec 000 FR-000-23, spec 008 FR-008-21) through `render_pages`.

Usage:  python tools/gen_knowledge_docs.py [--root PATH] [--check]
Writes `<root>/docs/reference/knowledge/*.md`: one page per knowledge table plus `equations.md`, `bibliography.md` and
`glossary.md`, exactly as `minephys.knowledge.render_pages` renders them (this tool has no renderer of its own: one code
path serves the pages, the export and the API). The pages are deterministic (no time stamp). With `--check` nothing is
written and the exit status is 1 when a page is missing, differs or is no longer generated (stdout names the page).
Knowledge that does not validate exits 2 naming each error, and writes nothing.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
PAGES = Path("docs") / "reference" / "knowledge"


def _knowledge(root: Path):  # type: ignore[no-untyped-def]
    try:
        import minephys.knowledge as knowledge
    except ImportError:
        sys.path.insert(0, str(root / "src"))
        import minephys.knowledge as knowledge
    return knowledge


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=HERE)
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if a page is missing or differs")
    args = ap.parse_args(argv[1:])
    root = args.root.resolve()
    knowledge = _knowledge(root)
    # the knowledge of the repository the tool sits in when it has one (`<root>/src/minephys/knowledge`), else the
    # packaged knowledge
    source = root / "src" / "minephys" / "knowledge"
    folder = source if source.is_dir() else None
    report = knowledge.validate_tables(folder)
    if report.errors:
        print("the knowledge does not validate, no page generated:")
        for error in report.errors:
            print(f"  {error}")
        return 2
    with tempfile.TemporaryDirectory(prefix="minephys-pages-") as tmp:
        out = Path(tmp)
        knowledge.render_pages(out, folder)
        generated = {p.name: p.read_bytes() for p in sorted(out.glob("*.md"))}
    target = root / PAGES
    if args.check:
        differing = 0
        for name, data in generated.items():
            page = target / name
            current = page.read_bytes().replace(b"\r\n", b"\n") if page.is_file() else None
            if current != data:
                differing += 1
                state = "missing" if current is None else "differs from the generated page"
                print(f"{(PAGES / name).as_posix()}: {state}")
        for page in sorted(target.glob("*.md")) if target.is_dir() else []:
            if page.name not in generated:
                differing += 1
                print(f"{(PAGES / page.name).as_posix()}: no longer generated")
        print("KNOWLEDGE PAGES OK" if not differing else f"KNOWLEDGE PAGES STALE ({differing})")
        return 1 if differing else 0
    target.mkdir(parents=True, exist_ok=True)
    for name, data in generated.items():
        (target / name).write_bytes(data)
    print(f"wrote {len(generated)} page(s) under {PAGES.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

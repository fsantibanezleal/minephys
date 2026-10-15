"""Cut a release: next X.YY.ZZZ version from Conventional Commits, update version files, CHANGELOG, CITATION, tag.

Usage:  python tools/release.py            # dry run: print the computed version and notes
        python tools/release.py --apply    # write files, commit "chore(release): vX.YY.ZZZ", create the tag
        python tools/release.py --apply --version 1.02.000   # force a version
Then: git push --follow-tags  and  gh release create vX.YY.ZZZ --notes-file release-notes.md
Display version = zero-padded X.YY.ZZZ (tags vX.YY.ZZZ, CHANGELOG, CITATION, VERSION). Package managers get the
normalised form (pyproject 0.1.0, package.json 0.1.0) because PEP 440 and SemVer forbid leading zeros.
        python tools/release.py --check-knowledge --previous DIR --current DIR --changelog FILE
            # FR-000-30: a knowledge row whose value, range or verification changed since the previous release must be
            # named in the "## [Unreleased]" section of the changelog (exit 1 lists the rows, 2 for unreadable input)
Bump rules since the last v* tag: "BREAKING CHANGE" or "type!:" -> X; "feat" -> YY; anything else -> ZZZ.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _knowledge_io as kio  # noqa: E402

PADDED = re.compile(r"^(\d+)\.(\d{2})\.(\d{3})$")


def git(*a: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, encoding="utf-8").stdout.strip()


def norm(v: str) -> str:
    x, y, z = PADDED.match(v).groups()
    return f"{int(x)}.{int(y)}.{int(z)}"


def current() -> str:
    f = ROOT / "VERSION"
    return f.read_text(encoding="utf-8").strip() if f.is_file() else "0.00.000"


def bump(v: str, commits: list[str]) -> str:
    x, y, z = (int(p) for p in PADDED.match(v).groups())
    if any("BREAKING CHANGE" in c or re.match(r"^\w+(\(.+\))?!:", c) for c in commits):
        return f"{x + 1}.00.000"
    if any(re.match(r"^feat(\(.+\))?:", c) for c in commits):
        return f"{x}.{y + 1:02d}.000"
    return f"{x}.{y:02d}.{z + 1:03d}"


def _rows_by_id(folder: Path) -> dict[str, tuple[object, object]]:
    """(comparable value, verification) of every row of the tables under `folder` (and its share-alike folder)."""
    rows: dict[str, tuple[object, object]] = {}
    for shared, base in ((False, folder), (True, folder / "share-alike")):
        for path in sorted(base.glob("*.yaml")) if base.is_dir() else []:
            tf = kio.read_table(kio.TableFile(path, path.name, path.stem, shared))
            if tf.errors:
                raise ValueError("; ".join(tf.errors))
            for r in kio.rows_of(tf):
                rows[r["id"]] = (kio.numeric_value(r), r.get("verification"))
    return rows


def check_knowledge(previous: Path, current: Path, changelog: Path) -> int:
    """Rows changed since the previous release must be named in the Unreleased section of the changelog."""
    for label, path in (("previous", previous), ("current", current)):
        if not path.is_dir():
            print(f"--{label}: {path} is not a directory", file=sys.stderr)
            return 2
    if not changelog.is_file():
        print(f"--changelog: {changelog} is not a file", file=sys.stderr)
        return 2
    try:
        before, after = _rows_by_id(previous), _rows_by_id(current)
        text = changelog.read_text(encoding="utf-8")
    except (ValueError, OSError, UnicodeDecodeError) as err:
        print(f"unreadable input: {err}", file=sys.stderr)
        return 2
    section = re.search(r"(?ms)^## \[Unreleased\][^\n]*\n(.*?)(?=^## |\Z)", text)
    unreleased = section.group(1) if section else ""
    unnamed = [
        row_id
        for row_id in sorted(before.keys() & after.keys())
        if before[row_id] != after[row_id]
        and not re.search(rf"(?<![A-Za-z0-9_]){re.escape(row_id)}(?![A-Za-z0-9_])", unreleased)
    ]
    for row_id in unnamed:
        print(
            f"{row_id}: value, range or verification changed since the previous release; "
            f"name it under [Unreleased] in {changelog.name}"
        )
    if unnamed:
        return 1
    print("OK")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--version")
    ap.add_argument("--check-knowledge", action="store_true", help="FR-000-30 value-change check (see the module doc)")
    ap.add_argument("--previous", type=Path, help="knowledge folder of the previous release")
    ap.add_argument("--current", type=Path, help="knowledge folder of the working tree")
    ap.add_argument("--changelog", type=Path, help="CHANGELOG.md")
    a = ap.parse_args(argv[1:])
    if a.check_knowledge:
        if not (a.previous and a.current and a.changelog):
            ap.error("--check-knowledge needs --previous, --current and --changelog")
        return check_knowledge(a.previous, a.current, a.changelog)
    last = git("describe", "--tags", "--abbrev=0", "--match", "v*")
    rng = f"{last}..HEAD" if last else "HEAD"
    commits = [c for c in git("log", "--format=%s%n%b%x1e", rng).split("\x1e") if c.strip()]
    if not commits:
        print("nothing to release")
        return 1
    gate = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "trace.py"), "--check", "--release"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if gate.returncode != 0:  # G6: no release while a spec is below Converged or a requirement has no test
        print(gate.stdout[-4000:])
        print("release refused: tools/trace.py --check --release failed")
        return 3
    new = a.version or bump(current(), [c.strip() for c in commits])
    if not PADDED.match(new):
        print(f"invalid version {new!r}: use X.YY.ZZZ")
        return 2
    today = dt.date.today().isoformat()
    groups = {
        "Added": "feat",
        "Fixed": "fix",
        "Changed": "refactor|perf|style",
        "Documentation": "docs",
        "Tests": "test",
        "Maintenance": "chore|build|ci",
    }
    notes = [f"## [{new}] - {today}"]
    subjects = [c.strip().splitlines()[0] for c in commits]
    for title, types in groups.items():
        items = [s for s in subjects if re.match(rf"^({types})(\(.+\))?!?:", s) and not s.startswith("chore(release)")]
        if items:
            notes += ["", f"### {title}"] + [f"- {s}" for s in items]
    text = "\n".join(notes) + "\n"
    print(f"release {current()} -> {new} ({norm(new)} for package managers)\n\n{text}")
    if not a.apply:
        return 0
    (ROOT / "VERSION").write_text(new + "\n", encoding="utf-8", newline="\n")
    pp = ROOT / "pyproject.toml"
    if pp.is_file():
        s = pp.read_text(encoding="utf-8")
        pp.write_text(
            re.sub(r'(?m)^version\s*=\s*"[^"]*"', f'version = "{norm(new)}"', s, count=1),
            encoding="utf-8",
            newline="\n",
        )
    pj = ROOT / "web" / "package.json"
    if pj.is_file():
        d = json.loads(pj.read_text(encoding="utf-8"))
        d["version"] = norm(new)
        pj.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8", newline="\n")
    cff = ROOT / "CITATION.cff"
    if cff.is_file():
        s = cff.read_text(encoding="utf-8")
        s = re.sub(r"(?m)^version:.*$", f'version: "{new}"', s)
        s = re.sub(r"(?m)^date-released:.*$", f'date-released: "{today}"', s)
        cff.write_text(s, encoding="utf-8", newline="\n")
    ch = ROOT / "CHANGELOG.md"
    s = ch.read_text(encoding="utf-8")
    s = s.replace("## [Unreleased]", "## [Unreleased]\n\n" + text.rstrip(), 1)
    ch.write_text(s, encoding="utf-8", newline="\n")
    (ROOT / "release-notes.md").write_text(text, encoding="utf-8", newline="\n")
    git("add", "VERSION", "pyproject.toml", "web/package.json", "CITATION.cff", "CHANGELOG.md")
    git("commit", "-m", f"chore(release): v{new}")
    git("tag", "-a", f"v{new}", "-m", f"Release {new}")
    print(f"tagged v{new}. Next: git push --follow-tags && gh release create v{new} --notes-file release-notes.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

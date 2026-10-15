"""T-008-063 (NFR-008-04): the built wheel contains the catalogue files in addition to the tables and the bibliography.

Expected: a `py3-none-any` wheel of the package (the one in `dist/` when it exists, as in the CI wheel job, `uv build --no-sources`;
otherwise one built here from a copy of `pyproject.toml` and `src/` so that the repository stays clean) installs, with
`uv pip install --no-deps --target <folder> <wheel>`, a tree that contains
- `minephys/knowledge/catalogue/equations.yaml` and `minephys/knowledge/catalogue/glossary.yaml` (NFR-008-04: both present),
- `minephys/knowledge/references.bib` and every table file of the source tree (`minephys/knowledge/*.yaml` and
  `minephys/knowledge/share-alike/*.yaml`, FR-000-24), byte for byte equal to the source files,
- no empty knowledge file (FR-008-22: no table or catalogue is shipped without an entry), and
- `minephys/py.typed`; the wheel's file name carries the `py3-none-any` tag (FR-000-24), and the installed `RECORD` lists the knowledge files.
The knowledge files read through `importlib.resources` therefore exist in the installed package.

The wheel is inspected through its installed tree and `RECORD` rather than by opening the archive: the installer is the consumer the
requirement is about, and on some Windows set-ups the archive written by the build tool is not readable by the test process.

Oracle: the installed tree compared with the source tree (`pathlib`): a structural comparison, no computed value.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "minephys" / "knowledge"
PREFIX = "minephys/knowledge/"


def _run(cmd: list[str], what: str) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    assert proc.returncode == 0, f"{what} failed:\n{proc.stderr[-1500:]}"


def _wheel(work: Path, uv: str) -> Path:
    built = sorted((ROOT / "dist").glob("minephys-*.whl")) if (ROOT / "dist").is_dir() else []
    if built:
        return built[-1]
    build = work / "build"
    build.mkdir()
    shutil.copyfile(ROOT / "pyproject.toml", build / "pyproject.toml")
    for extra in ("README.md", "LICENSE", "LICENSE.md", "LICENSE.txt", "NOTICE"):
        if (ROOT / extra).is_file():
            shutil.copyfile(ROOT / extra, build / extra)
    shutil.copytree(ROOT / "src", build / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"))
    out = work / "out"
    out.mkdir()
    _run([uv, "build", "--wheel", "--no-sources", "--out-dir", str(out), str(build)], "building the wheel")
    wheels = sorted(out.glob("minephys-*.whl"))
    assert wheels, "no wheel was built"
    return wheels[-1]


@pytest.fixture(scope="module")
def installed() -> Iterator[tuple[str, Path]]:
    uv = shutil.which("uv")
    assert uv, "no `uv` on the PATH: it builds the wheel and installs it"
    # a plain folder with default permissions: the build tool writes the wheel as another process
    work = Path(tempfile.gettempdir()) / f"mpk-wheel-{uuid.uuid4().hex}"
    work.mkdir()
    try:
        wheel = _wheel(work, uv)
        target = work / "site"
        _run([uv, "pip", "install", "--no-deps", "--target", str(target), str(wheel)], "installing the wheel")
        yield wheel.name, target
    finally:
        shutil.rmtree(work, ignore_errors=True)


@pytest.mark.req("NFR-008-04")
@pytest.mark.oracle("hand-calculation", "both catalogue files are in the wheel and are not empty")
def test_nfr_008_04_the_wheel_contains_both_catalogue_files(installed: tuple[str, Path]) -> None:
    _, site = installed
    for name in ("equations.yaml", "glossary.yaml"):
        path = site / PREFIX / "catalogue" / name
        assert path.is_file(), f"{PREFIX}catalogue/{name} is not in the wheel"
        assert path.read_bytes().strip(), f"{path.name} is empty (FR-008-22: no empty file is shipped)"


@pytest.mark.req("NFR-008-04")
@pytest.mark.oracle("hand-calculation", "the bibliography and every source table are in the wheel, byte for byte")
def test_nfr_008_04_the_wheel_contains_the_tables_and_the_bibliography(installed: tuple[str, Path]) -> None:
    _, site = installed
    assert (site / PREFIX / "references.bib").is_file()
    source_files = [p for p in SRC.rglob("*") if p.is_file() and p.suffix in {".yaml", ".bib"}]
    assert source_files, "no knowledge file under src/minephys/knowledge/"
    tables = [p for p in source_files if p.parent in (SRC, SRC / "share-alike") and p.suffix == ".yaml"]
    assert tables, "the source tree has no knowledge table (the units table of the foundation is expected at least)"
    for path in source_files:
        rel = path.relative_to(SRC).as_posix()
        shipped = site / PREFIX / rel
        assert shipped.is_file(), f"{PREFIX}{rel} is missing from the wheel"
        assert shipped.read_bytes().replace(b"\r\n", b"\n") == path.read_bytes().replace(b"\r\n", b"\n"), (
            f"{rel} differs from the source file"
        )


@pytest.mark.req("NFR-008-04")
@pytest.mark.oracle("hand-calculation", "no empty knowledge file is shipped (FR-008-22)")
def test_nfr_008_04_no_empty_knowledge_file_is_shipped(installed: tuple[str, Path]) -> None:
    _, site = installed
    shipped = [p for p in (site / "minephys" / "knowledge").rglob("*") if p.is_file() and p.suffix in {".yaml", ".bib"}]
    assert shipped, "no knowledge file in the wheel"
    empty = [p.relative_to(site).as_posix() for p in shipped if not p.read_bytes().strip()]
    assert empty == [], f"empty knowledge files in the wheel: {empty}"


@pytest.mark.req("NFR-008-04")
@pytest.mark.oracle(
    "hand-calculation", "FR-000-24: a pure-Python py3-none-any wheel with py.typed; RECORD lists the knowledge files"
)
def test_nfr_008_04_the_wheel_is_pure_python_and_typed(installed: tuple[str, Path]) -> None:
    name, site = installed
    assert name.endswith("-py3-none-any.whl"), name
    assert (site / "minephys" / "py.typed").is_file()
    records = list(site.glob("minephys-*.dist-info/RECORD"))
    assert len(records) == 1, records
    listed = records[0].read_text(encoding="utf-8")
    for member in ("catalogue/equations.yaml", "catalogue/glossary.yaml", "references.bib"):
        assert PREFIX + member in listed, f"{PREFIX}{member} is not listed in RECORD"

"""T-000-020 (FR-000-24, NFR-000-04, NFR-000-05): wheel contents, tag, size and metadata.

The test builds the wheel of this repository with `uv build --wheel` into a temporary folder (a build tool, not a
Python package; the CI wheel job uses the same command) and inspects it with `zipfile` and the metadata parser.
Expected result:

* the file name ends with `-py3-none-any.whl` and `WHEEL` says `Tag: py3-none-any` and `Root-Is-Purelib: true`;
* the wheel contains `minephys/py.typed`, EVERY table of `src/minephys/knowledge/*.yaml` and of
  `src/minephys/knowledge/share-alike/*.yaml`, and `minephys/knowledge/references.bib` (package data), and no
  `tests/`, `specs/`, `tools/` or `docs/` content;
* size <= 1 MiB (1,048,576 bytes; target <= 512 KiB is reported, not enforced);
* `Requires-Dist` is exactly `numpy>=2.0` and `pyyaml>=6.0` (no extras, no environment markers, no
  `Provides-Extra`), `Requires-Python` is `>=3.12`, and the metadata version is the normalised `VERSION`;
* installed into a clean virtual environment together with its two dependencies only, `import minephys` works and the
  package's own knowledge table is readable through `importlib.resources`.

Oracle: analytical (zip listing and metadata fields stated by FR-000-24, NFR-000-04, NFR-000-05).
"""

from __future__ import annotations

import email
import re
import shutil
import subprocess
import sys
import zipfile
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "src" / "minephys" / "knowledge"


@pytest.fixture(scope="module")
def workdir() -> Iterator[Path]:
    """A scratch folder under the git-ignored `build/` (default folder ACLs; pytest's 0o700 temp folders are not
    readable by the processes that `uv` spawns on Windows with Python >= 3.13)."""
    d = ROOT / "build" / "t_000_020"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="module")
def wheel(workdir: Path) -> Path:
    uv = shutil.which("uv")
    assert uv, "the `uv` build tool is required (the CI wheel job uses `uv build`)"
    out = workdir / "dist"
    out.mkdir()
    proc = subprocess.run(
        [uv, "build", "--wheel", "--no-sources", "--out-dir", str(out), str(ROOT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=600,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    wheels = sorted(out.glob("*.whl"))
    assert len(wheels) == 1, wheels
    return wheels[0]


def names(whl: Path) -> list[str]:
    with zipfile.ZipFile(whl) as z:
        return z.namelist()


def read(whl: Path, suffix: str) -> str:
    with zipfile.ZipFile(whl) as z:
        (member,) = [n for n in z.namelist() if n.endswith(suffix)]
        return z.read(member).decode("utf-8")


@pytest.mark.req("FR-000-24")
@pytest.mark.oracle("analytical", "wheel tag py3-none-any (pure Python)")
def test_wheel_is_pure_python_py3_none_any(wheel: Path) -> None:
    assert wheel.name.endswith("-py3-none-any.whl"), wheel.name
    meta = email.message_from_string(read(wheel, ".dist-info/WHEEL"))
    assert meta["Root-Is-Purelib"] == "true"
    assert meta.get_all("Tag") == ["py3-none-any"]
    assert not [n for n in names(wheel) if n.endswith((".so", ".pyd", ".dll", ".dylib"))]


@pytest.mark.req("FR-000-24")
@pytest.mark.oracle("analytical", "package data of the wheel equals the knowledge folder of the source tree")
def test_wheel_ships_py_typed_every_table_and_the_bibliography(wheel: Path) -> None:
    listed = set(names(wheel))
    assert "minephys/py.typed" in listed
    sources = sorted(p for p in KNOWLEDGE.rglob("*.yaml")) if KNOWLEDGE.is_dir() else []
    assert sources, "src/minephys/knowledge/ has no table (units.yaml is the first one)"
    for p in sources:
        rel = "minephys/knowledge/" + p.relative_to(KNOWLEDGE).as_posix()
        assert rel in listed, f"{rel} is missing from the wheel"
    assert (KNOWLEDGE / "references.bib").is_file(), "missing src/minephys/knowledge/references.bib"
    assert "minephys/knowledge/references.bib" in listed


@pytest.mark.req("FR-000-24")
@pytest.mark.oracle("analytical", "only the package and its metadata belong in the wheel")
def test_wheel_holds_nothing_but_the_package(wheel: Path) -> None:
    for n in names(wheel):
        assert n.startswith(("minephys/", "minephys-")), n
        assert not re.search(r"(^|/)(tests?|specs|tools|docs|scripts|\.github|\.claude)(/|$)", n), n
        assert not n.endswith((".env", ".pem", ".key")), n


@pytest.mark.req("NFR-000-04")
@pytest.mark.oracle("analytical", "NFR-000-04: <= 1 MiB = 1,048,576 bytes")
def test_wheel_size_budget(wheel: Path) -> None:
    size = wheel.stat().st_size
    assert size <= 1_048_576, f"{size} bytes"
    assert (ROOT / "src" / "minephys" / "knowledge" / "units.yaml").is_file(), "an empty package would pass trivially"


@pytest.mark.req("NFR-000-05")
@pytest.mark.oracle("analytical", "NFR-000-05: Requires-Dist is exactly numpy>=2.0 and pyyaml>=6.0")
def test_runtime_dependencies_are_exactly_numpy_and_pyyaml(wheel: Path) -> None:
    meta = email.message_from_string(read(wheel, ".dist-info/METADATA"))
    requires = sorted(re.sub(r"\s+", "", r).lower() for r in (meta.get_all("Requires-Dist") or []))
    assert requires == ["numpy>=2.0", "pyyaml>=6.0"]
    assert not meta.get_all("Provides-Extra")
    assert meta["Requires-Python"].replace(" ", "") == ">=3.12"
    assert meta["Name"].lower() == "minephys"


@pytest.mark.req("FR-000-24")
@pytest.mark.req("FR-000-27")
@pytest.mark.oracle("analytical", "the wheel version is the normalised VERSION file")
def test_wheel_version_matches_the_version_file(wheel: Path) -> None:
    x, y, z = (int(p) for p in (ROOT / "VERSION").read_text(encoding="utf-8").strip().split("."))
    meta = email.message_from_string(read(wheel, ".dist-info/METADATA"))
    assert meta["Version"] == f"{x}.{y}.{z}"
    assert f"-{x}.{y}.{z}-" in wheel.name
    assert (KNOWLEDGE / "units.yaml").is_file(), "the wheel must carry the units table"


@pytest.mark.slow
@pytest.mark.req("FR-000-24")
@pytest.mark.oracle(
    "analytical", "a clean environment with only the wheel and its dependencies imports and reads a table"
)
def test_wheel_installs_in_a_clean_environment(wheel: Path, workdir: Path) -> None:
    uv = shutil.which("uv")
    assert uv
    venv = workdir / "venv"
    subprocess.run([uv, "venv", "--python", sys.executable, str(venv)], check=True, capture_output=True, timeout=300)
    py = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run(
        [uv, "pip", "install", "--python", str(py), str(wheel)], check=True, capture_output=True, timeout=600
    )
    code = (
        "import importlib.resources as r, minephys\n"
        "t = r.files('minephys').joinpath('knowledge', 'units.yaml').read_text(encoding='utf-8')\n"
        "assert 'standard_gravity' in t\n"
        "print(minephys.__version__)\n"
    )
    proc = subprocess.run([str(py), "-c", code], capture_output=True, text=True, timeout=120, check=False)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == (ROOT / "VERSION").read_text(encoding="utf-8").strip()

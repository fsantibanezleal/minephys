"""T-000-011 (FR-000-06, NFR-000-03): import purity under an audit hook, and import time.

Expected behaviour: in a fresh interpreter, `import minephys`, `import minephys.units` and the import of every public
subpackage of `src/minephys/` (directories with an `__init__.py` whose name does not start with an underscore, found
on disk so that each module spec's subpackage is covered as it lands) raise NO audit event for
    * `open` of a `.yaml`, `.bib` or `.json` file,
    * `socket.*`, `subprocess.Popen`, `os.system`, `os.posix_spawn`, `_thread.start_new_thread`,
and the knowledge tables are loaded lazily: the first call of a function that needs a table (here
`minephys.units.us_gal_to_m3`, which reads the `inch` and `us_gallon_cubic_inches` rows) opens `units.yaml`.
NFR-000-03: the summed self time of the `minephys.*` modules in `python -X importtime` (NumPy and PyYAML excluded)
is <= 100 ms as the median of 5 fresh interpreters.

Oracle: the CPython audit-event log of a fresh interpreter (analytical: the expected event list is empty); a control
script that DOES open a `.yaml` file proves that the harness sees such events.
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "src" / "minephys"

FORBIDDEN_PREFIXES = ("socket.",)
FORBIDDEN_EVENTS = {"subprocess.Popen", "os.system", "os.posix_spawn", "_thread.start_new_thread"}
DATA_SUFFIXES = (".yaml", ".yml", ".bib", ".json")

HARNESS = """
import json, sys
events = []
def hook(event, args):
    if event == "open":
        p = str(args[0]) if args else ""
        if p.lower().endswith({suffixes!r}):
            events.append(["open", p])
    elif event.startswith({prefixes!r}) or event in {forbidden!r}:
        events.append([event, ""])
sys.addaudithook(hook)
{body}
sys.stdout.write("\\n@@EVENTS@@" + json.dumps(events))
"""


def _run(body: str) -> list[list[str]]:
    code = HARNESS.format(suffixes=DATA_SUFFIXES, prefixes=FORBIDDEN_PREFIXES, forbidden=FORBIDDEN_EVENTS, body=body)
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", timeout=120, check=False
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(proc.stdout.split("@@EVENTS@@")[1])


def _public_modules() -> list[str]:
    subs = sorted(
        p.name for p in PKG.iterdir() if p.is_dir() and (p / "__init__.py").is_file() and not p.name.startswith("_")
    )
    return ["minephys", "minephys.units", *(f"minephys.{s}" for s in subs)]


MODULES = _public_modules()


@pytest.mark.req("FR-000-06")
@pytest.mark.oracle("analytical", "an empty audit-event log for the listed events in a fresh interpreter")
@pytest.mark.parametrize("module", MODULES)
def test_import_raises_no_forbidden_audit_event(module: str) -> None:
    events = _run(f"import {module}")
    assert events == [], f"importing {module} caused {events}"


@pytest.mark.req("FR-000-06")
@pytest.mark.oracle("analytical", "the harness itself sees a .yaml open, a thread start and a socket (control)")
def test_harness_control_detects_forbidden_events(tmp_path: Path) -> None:
    target = tmp_path / "control.yaml"
    target.write_text("a: 1\n", encoding="utf-8")
    body = (
        f"open({str(target)!r}).read()\n"
        "import _thread, socket\n"
        "_thread.start_new_thread(lambda: None, ())\n"
        "socket.socket().close()\n"
    )
    events = _run(body)
    names = {e[0] for e in events}
    assert "open" in names
    assert "_thread.start_new_thread" in names
    assert any(n.startswith("socket.") for n in names)


@pytest.mark.req("FR-000-06")
@pytest.mark.oracle("analytical", "tables are read lazily: the first use opens units.yaml, the import did not")
def test_knowledge_table_is_read_lazily_on_first_use() -> None:
    body = (
        "import minephys.units as u\n"
        "n_after_import = len(events)\n"
        "u.us_gal_to_m3(1.0)\n"
        "events.append(['marker', str(n_after_import)])\n"
    )
    events = _run(body)
    marker = next(e for e in events if e[0] == "marker")
    assert marker[1] == "0", "the import already read a data file"
    opened = [e[1] for e in events if e[0] == "open"]
    assert any(p.replace("\\", "/").endswith("knowledge/units.yaml") for p in opened), opened


@pytest.mark.req("FR-000-06")
@pytest.mark.oracle("analytical", "importing every public subpackage together stays silent as well")
def test_importing_everything_in_one_interpreter_raises_no_forbidden_event() -> None:
    events = _run("\n".join(f"import {m}" for m in MODULES))
    assert events == []


def _self_time_us(module_list: list[str]) -> int:
    proc = subprocess.run(
        [sys.executable, "-X", "importtime", "-c", "\n".join(f"import {m}" for m in module_list)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    total = 0
    seen = 0
    for line in proc.stderr.splitlines():
        if not line.startswith("import time:"):
            continue
        parts = [p.strip() for p in line[len("import time:") :].split("|")]
        if len(parts) == 3 and parts[2].startswith("minephys"):
            total += int(parts[0])
            seen += 1
    assert seen >= 2, f"expected minephys modules in the import-time log, saw {seen}"
    return total


@pytest.mark.slow
@pytest.mark.req("NFR-000-03")
@pytest.mark.oracle("analytical", "NFR-000-03 budget: 100 ms of self time, median of 5 fresh interpreters")
def test_import_time_of_all_public_subpackages_is_within_budget() -> None:
    samples = [_self_time_us(MODULES) for _ in range(5)]
    assert statistics.median(samples) <= 100_000, samples

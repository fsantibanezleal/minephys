"""T-008-060 (NFR-008-01, NFR-008-02): importing `minephys.knowledge` reads no knowledge file; the first use loads, later uses hit the cache.

Method: a fresh interpreter installs `sys.addaudithook` before the import and records every `open` event whose path ends in `.yaml`, `.yml`,
`.bib` or `.json` (the import system's own reads of `.py`/`.pyc` files are not counted).
1. NFR-008-01: `import minephys.knowledge` (and `import minephys`) on the packaged knowledge records 0 such events.
2. Laziness and caching, on the fixture package tree (tests/_knowledge_fixtures.py, `importlib.resources` redirected as in FR-008-01): the
   import records 0 events; the first call `get_value("diesel_co2_factor")` records at least one `.yaml` open and the `references.bib`
   open (loading validates the whole knowledge); later calls (`get_value`, `list_parameters`, `get_parameter`, `load_table`, `export`,
   `export_json`, `equations`, `glossary`) record 0 further events (the warm path serves the cache, NFR-008-02); the returned objects
   are the cached ones (identity, as in T-008-010).

Oracle: the audit-event counts of NFR-008-01 (0 events at import) and the fixture knowledge of tests/_knowledge_fixtures.py.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import _knowledge_fixtures as fx
import pytest

SUFFIXES = (".yaml", ".yml", ".bib", ".json")

HOOK = """
import sys
EVENTS = []
def _hook(event, args):
    if event == "open":
        p = args[0]
        if isinstance(p, bytes):
            p = p.decode("utf-8", "replace")
        if isinstance(p, str) and p.lower().endswith(%r):
            EVENTS.append(p)
sys.addaudithook(_hook)
""" % (SUFFIXES,)


def _real_import() -> dict[str, object]:
    script = (
        HOOK
        + """
import json
import minephys
import minephys.knowledge
print(json.dumps({"events": EVENTS}))
"""
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=fx.ROOT,
        timeout=120,
    )
    assert proc.returncode == 0, f"importing minephys.knowledge failed:\n{proc.stderr[-1500:]}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


@pytest.mark.req("NFR-008-01")
@pytest.mark.oracle("hand-calculation", "0 open events for .yaml/.yml/.bib/.json at import of the packaged package")
def test_nfr_008_01_importing_reads_no_knowledge_file() -> None:
    assert _real_import()["events"] == []


@pytest.mark.req("NFR-008-01")
@pytest.mark.req("NFR-008-02")
@pytest.mark.oracle(
    "hand-calculation", "fixture knowledge: 0 events at import, files read on first use, none afterwards"
)
def test_nfr_008_01_loading_is_lazy_and_cached(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", share_alike=fx.good_share_alike())
    prelude = fx.PRELUDE.replace("import minephys.knowledge as K", "")
    script = (
        HOOK
        + prelude
        + """
import minephys.knowledge as K
steps = {"import": len(EVENTS)}
a = K.get_value("diesel_co2_factor")
steps["first_call_events"] = list(EVENTS)
mark = len(EVENTS)
b = K.get_value("diesel_co2_factor")
K.list_parameters()
K.get_parameter("diesel_co2_factor")
K.load_table("haulage")
K.export()
K.export_json()
K.equations(); K.glossary()
steps["later_events"] = EVENTS[mark:]
steps["same_rows"] = K.load_table("haulage") is K.load_table("haulage")
steps["same_parameters"] = K.get_parameter("inch") is K.get_parameter("inch")
steps["values_equal"] = a == b == 10.21
print(json.dumps(steps))
"""
    )
    # `fx.run_script` would import the module before the audit hook exists, so the child is started here with the same environment
    env = dict(
        os.environ,
        MINEPHYS_FIXTURE_BASE=str(base),
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONUTF8="1",
        PYTHONIOENCODING="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=fx.ROOT,
        env=env,
        timeout=180,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    got = json.loads(proc.stdout.strip().splitlines()[-1])
    assert got["import"] == 0, "importing the module must not read a knowledge file"
    first = [Path(p).name for p in got["first_call_events"]]
    assert "haulage.yaml" in first and "blasting.yaml" in first and "references.bib" in first, first
    assert got["later_events"] == [], f"the warm path re-read files: {got['later_events']}"
    assert got["same_rows"] is True and got["same_parameters"] is True, (
        "cached objects must be returned as they are (immutable)"
    )
    assert got["values_equal"] is True

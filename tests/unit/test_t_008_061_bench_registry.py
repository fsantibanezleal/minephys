"""T-008-061 (NFR-008-02): the knowledge cold and warm load are registered in `tools/bench.py`.

Expected: `tools/bench.py` (foundation T-000-023) registers a reference entry for the knowledge load with the two thresholds of NFR-008-02:
the cold load-and-validate of all packaged knowledge (<= 0.5 s) and the warm call served from the cache (<= 1 ms, median of 5), so that
`python tools/bench.py` can report them. The registry format is owned by T-000-023; this test reads the tool's source text, which is stable
under any registry representation (the open point is recorded in the red-phase report).

The behavioural half of the requirement runs here directly on the packaged knowledge: in a fresh interpreter the first `validate_tables()`,
`list_parameters()` and `get_parameter` (cold, after the import) take at most 0.5 s of wall time, and the median of 5 warm
`get_parameter` calls takes at most 1 ms. Both measures are repeated in 3 fresh interpreters and the best of each is taken, so that a
loaded machine does not fail a correct implementation.

Oracle: hand-written thresholds of NFR-008-02.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "tools" / "bench.py"

TIMING = """
import json, statistics, time
import minephys.knowledge as K
t0 = time.perf_counter()
report = K.validate_tables()
first = K.list_parameters()[0].id
K.get_parameter(first)
cold = time.perf_counter() - t0
warm = []
for _ in range(5):
    t = time.perf_counter()
    K.get_parameter(first)
    warm.append(time.perf_counter() - t)
print(json.dumps({"cold": cold, "warm": statistics.median(warm), "errors": len(list(report.errors)), "rows": report.rows}))
"""


def _text() -> str:
    assert BENCH.is_file(), "missing tools/bench.py (foundation task T-000-023)"
    return BENCH.read_text(encoding="utf-8")


@pytest.mark.req("NFR-008-02")
@pytest.mark.oracle("hand-calculation", "NFR-008-02: cold and warm knowledge load registered")
def test_nfr_008_02_cold_and_warm_entries_are_registered() -> None:
    text = _text()
    assert re.search(r"knowledge", text), "no knowledge entry in tools/bench.py"
    assert re.search(r"cold", text, re.I) and re.search(r"warm", text, re.I), (
        "the cold and the warm load must both be registered"
    )


@pytest.mark.req("NFR-008-02")
@pytest.mark.oracle("hand-calculation", "NFR-008-02 thresholds: 0.5 s cold, 1 ms warm")
def test_nfr_008_02_thresholds_are_stated() -> None:
    text = _text()
    assert re.search(r"(?<![\d.])0?\.5(?!\d)|500\s*ms|500\.0", text), "the 0.5 s cold threshold is not stated"
    assert re.search(r"1e-3|0\.001|(?<![\d.])1(\.0)?\s*ms|1000(\.0)?\s*(us|µs)", text), (
        "the 1 ms warm threshold is not stated"
    )


@pytest.mark.req("NFR-008-02")
@pytest.mark.oracle("hand-calculation", "measured: cold <= 0.5 s, warm median of 5 <= 1 ms")
def test_nfr_008_02_cold_and_warm_load_meet_the_thresholds() -> None:
    best_cold = None
    warm = None
    for _ in range(3):
        proc = subprocess.run(
            [sys.executable, "-c", TIMING],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=ROOT,
            timeout=120,
        )
        assert proc.returncode == 0, proc.stderr[-1500:]
        got = json.loads(proc.stdout.strip().splitlines()[-1])
        assert got["errors"] == 0 and got["rows"] >= 1
        best_cold = got["cold"] if best_cold is None else min(best_cold, got["cold"])
        warm = got["warm"] if warm is None else min(warm, got["warm"])
    assert best_cold is not None and warm is not None
    assert best_cold <= 0.5, f"cold load and validation took {best_cold:.3f} s (limit 0.5 s)"
    assert warm <= 1e-3, f"warm call took {warm * 1e3:.3f} ms (limit 1 ms)"

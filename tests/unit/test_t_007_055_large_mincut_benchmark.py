"""T-007-055 (NFR-007-05): the 10,164-block min-cut benchmark (`slow`).

Expected: `ultimate_pit_mincut` on a 22 x 22 x 21 grid (10,164 blocks, "1-5" arcs from `regular_grid_precedence`, seeded integer
values in [-50, 50]) has a median wall-clock time of 3 runs <= 10 s on the CI runner's CPython. The runs happen in a fresh
interpreter (so that import and warm-up costs are those of a user's first call, and nothing else competes for the process); the
result of the last run is checked for closure feasibility and for the value identity value = sum of the selected values.

Oracle: the wall clock (a measurement) and the structural properties of the result (closure feasibility, value identity).
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LIMIT_S = 10.0

SCRIPT = """
import json, time
import numpy as np
from minephys.planning import regular_grid_precedence, ultimate_pit_mincut
shape = (22, 22, 21)
arcs = regular_grid_precedence(shape, "1-5")
n = shape[0] * shape[1] * shape[2]
values = np.random.default_rng(2026).integers(-50, 51, n).astype(np.float64)
times = []
for _ in range(3):
    t0 = time.perf_counter()
    res = ultimate_pit_mincut(values, arcs)
    times.append(time.perf_counter() - t0)
mask = np.asarray(res.mask)
feasible = bool(np.all(~mask[arcs[:, 0]] | mask[arcs[:, 1]]))
print(json.dumps({"n": n, "arcs": int(arcs.shape[0]), "times": times, "feasible": feasible,
                  "value_ok": bool(float(values[mask].sum()) == float(res.value)), "pit_size": int(mask.sum())}))
"""


@pytest.mark.slow
@pytest.mark.req("NFR-007-05")
@pytest.mark.oracle("hand-calculation", "NFR-007-05: median of 3 runs <= 10 s on 10,164 blocks")
def test_nfr_007_05_teaching_size_min_cut_is_fast_enough() -> None:
    proc = subprocess.run([sys.executable, "-c", SCRIPT], capture_output=True, text=True, cwd=ROOT, timeout=900)
    assert proc.returncode == 0, f"benchmark interpreter failed:\n{proc.stderr[-1500:]}"
    data = json.loads(proc.stdout.strip().splitlines()[-1])
    assert data["n"] == 10_164
    assert data["arcs"] == 20 * (22 * 22 + 2 * 21 * 22 + 2 * 22 * 21)  # (nz - 1) [nx ny + 2 (nx - 1) ny + 2 nx (ny - 1)]
    assert data["feasible"] and data["value_ok"] and 0 < data["pit_size"] < data["n"]
    assert statistics.median(data["times"]) <= LIMIT_S, f"median {statistics.median(data['times']):.2f} s > {LIMIT_S} s"

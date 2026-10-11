"""T-007-056 (NFR-007-06, P-007-10): the minimal maximum closure at the 10^5-block cap, and the penalised-problem relation.

Public API under test (`minephys.planning`): `ultimate_pit_mincut(values, arcs) -> UltimatePit(mask, value)` and
`regular_grid_precedence(shape, pattern="1-5")` (see tests/unit/test_t_007_021_mincut.py and test_t_007_020_precedence.py).

P-007-10 (CI size, Hypothesis): for integer values v and n = (number of blocks) + 1, `ultimate_pit_mincut(v)` equals
`ultimate_pit_mincut(n v - 1)` (every value scaled by n and lowered by 1), whose maximum closure is unique and is the minimal maximum
closure of v; its value equals n V - |pit|, V the value of the pit of v. Grids up to 12 x 12 x 8 (1,152 blocks) with "1-5" arcs
written in this file, integer values in [-50, 50]; exact (TC-0).

NFR-007-06 (`slow`): on a 50 x 50 x 40 grid (100,000 blocks, "1-5" arcs, 479,700 arcs) with seeded integer values in [-50, 50]
- the module returns the minimal maximum closure within 60 s (median of 3 runs) and 2 GB of peak resident memory, measured in a fresh
  interpreter (the process peak working set on Windows, `resource` elsewhere);
- the mask equals the `networkx` source side of the minimum cut of the penalised instance n v - 1 (whose optimum is unique, so
  networkx's `minimum_cut` partition is that closure; on the unpenalised instance networkx returns the MAXIMAL source side, which
  differs when zero-value ties exist) and the value satisfies value = n V - |pit| there. The networkx run happens in the test
  process after the timing interpreter has exited.
Oracle: the invariant itself (P-007-10), the networkx minimum cut (a reference implementation) and the wall clock / memory
measurement.
"""

from __future__ import annotations

import base64
import importlib
import itertools
import json
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[2]
SEEDS = st.integers(0, 2**32 - 1)


def _p():
    return importlib.import_module("minephys.planning")


def grid_arcs(nx: int, ny: int, nz: int) -> np.ndarray:
    arcs = []
    for x, y, z in itertools.product(range(nx), range(ny), range(1, nz)):
        i = (x * ny + y) * nz + z
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + dx < nx and 0 <= y + dy < ny:
                arcs.append((i, ((x + dx) * ny + (y + dy)) * nz + (z - 1)))
    return np.array(arcs, dtype=np.int64).reshape(-1, 2)


@pytest.mark.req("P-007-10")
@pytest.mark.oracle("analytical", "the penalised problem n v - 1 has a unique optimum: the minimal maximum closure of v")
@settings(max_examples=200, deadline=None)
@given(nx=st.integers(1, 12), ny=st.integers(1, 12), nz=st.integers(1, 8), seed=SEEDS)
def test_p_007_10_penalised_problem_returns_the_minimal_closure(nx: int, ny: int, nz: int, seed: int) -> None:
    f = _p().ultimate_pit_mincut
    n = nx * ny * nz
    values = np.random.default_rng(seed).integers(-50, 51, n).astype(np.float64)
    arcs = grid_arcs(nx, ny, nz)
    plain = f(values, arcs)
    penalised = f((n + 1) * values - 1.0, arcs)
    assert np.array_equal(np.asarray(plain.mask), np.asarray(penalised.mask))
    assert float(penalised.value) == (n + 1) * float(plain.value) - float(np.asarray(plain.mask).sum())


@pytest.mark.req("P-007-10")
@pytest.mark.oracle("analytical", "the relation on a tie-heavy instance: zeros and plateaus of equal values")
def test_p_007_10_tie_heavy_instances() -> None:
    f = _p().ultimate_pit_mincut
    for seed in range(40):
        rng = np.random.default_rng(seed)
        nx, ny, nz = int(rng.integers(1, 7)), int(rng.integers(1, 7)), int(rng.integers(2, 6))
        n = nx * ny * nz
        values = rng.choice([-2.0, -1.0, 0.0, 0.0, 1.0, 2.0], n)  # many zeros and ties
        arcs = grid_arcs(nx, ny, nz)
        plain, pen = f(values, arcs), f((n + 1) * values - 1.0, arcs)
        assert np.array_equal(np.asarray(plain.mask), np.asarray(pen.mask)), f"seed {seed}"
        assert float(pen.value) == (n + 1) * float(plain.value) - float(np.asarray(plain.mask).sum())


SCRIPT = """
import json, sys, time
import numpy as np
from minephys.planning import regular_grid_precedence, ultimate_pit_mincut

def peak_bytes():
    try:
        import resource
        kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return kb * 1024 if sys.platform != "darwin" else kb
    except ImportError:
        import ctypes
        from ctypes import wintypes
        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = PMC()
        counters.cb = ctypes.sizeof(PMC)
        if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise OSError("GetProcessMemoryInfo failed")
        return int(counters.PeakWorkingSetSize)

shape = (50, 50, 40)
arcs = regular_grid_precedence(shape, "1-5")
n = shape[0] * shape[1] * shape[2]
values = np.random.default_rng(2026).integers(-50, 51, n).astype(np.float64)
times, res = [], None
for _ in range(3):
    t0 = time.perf_counter()
    res = ultimate_pit_mincut(values, arcs)
    times.append(time.perf_counter() - t0)
mask = np.asarray(res.mask)
import base64
print(json.dumps({"mask": base64.b64encode(np.packbits(mask).tobytes()).decode(), "n": n, "arcs": int(arcs.shape[0]), "times": times, "peak": peak_bytes(),
                  "feasible": bool(np.all(~mask[arcs[:, 0]] | mask[arcs[:, 1]])), "value": float(res.value),
                  "value_ok": bool(float(values[mask].sum()) == float(res.value)), "pit_size": int(mask.sum())}))
"""


@pytest.mark.slow
@pytest.mark.req("NFR-007-06")
@pytest.mark.oracle("reference-implementation", "networkx minimum cut of the penalised instance; wall clock and peak memory")
def test_nfr_007_06_minimal_closure_at_the_block_cap() -> None:
    proc = subprocess.run([sys.executable, "-c", SCRIPT], capture_output=True, text=True, cwd=ROOT, timeout=3600)
    assert proc.returncode == 0, f"timing interpreter failed:\n{proc.stderr[-1500:]}"
    data = json.loads(proc.stdout.strip().splitlines()[-1])
    assert data["n"] == 100_000 and data["arcs"] == 479_700
    assert data["feasible"] and data["value_ok"]
    assert statistics.median(data["times"]) <= 60.0, f"median {statistics.median(data['times']):.1f} s > 60 s"
    assert data["peak"] <= 2 * 1024**3, f"peak memory {data['peak'] / 1024**3:.2f} GiB > 2 GiB"

    import networkx as nx  # reference implementation, imported after the module under test has been exercised

    shape = (50, 50, 40)
    n = 100_000
    values = np.random.default_rng(2026).integers(-50, 51, n).astype(np.float64)
    arcs = _p().regular_grid_precedence(shape, "1-5")
    penal = (n + 1) * values - 1.0
    g = nx.DiGraph()
    g.add_nodes_from(range(n))
    for i, v in enumerate(penal):
        if v > 0:
            g.add_edge("s", i, capacity=float(v))
        else:
            g.add_edge(i, "t", capacity=float(-v))  # no penalised value is zero: every value is a multiple of n plus -1
    for i, j in arcs:
        g.add_edge(int(i), int(j))
    cut_value, (source_side, _) = nx.minimum_cut(g, "s", "t")
    expected = np.zeros(n, dtype=bool)
    expected[[i for i in source_side if i != "s"]] = True
    mask = np.unpackbits(np.frombuffer(base64.b64decode(data["mask"]), dtype=np.uint8))[:n].astype(bool)
    assert np.array_equal(mask, expected)  # the unique optimum of the penalised problem = the minimal closure of v
    pit_value = float(values[mask].sum())
    assert float(penal[penal > 0].sum()) - cut_value == pytest.approx((n + 1) * pit_value - float(mask.sum()), abs=1e-6)
    assert pit_value == pytest.approx(data["value"], abs=0.0)

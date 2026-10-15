"""T-007-021 (FR-007-04, FR-007-05, P-007-02, SC-007-01): the min-cut pit against exhaustive enumeration and `networkx`.

Public API under test (`minephys.planning`): `ultimate_pit_mincut(values, arcs) -> UltimatePit(mask, value)` (see
tests/unit/test_t_007_021_mincut.py).

Independent oracles, all written in this file
- exhaustive enumeration of every subset of up to 16 blocks: the closed subsets are those with pit[i] => pit[j] for every arc,
  the maximum value is taken over them, and the SMALLEST optimal closure is the intersection of all optimal closures (closed
  and optimal because optimal closures form a lattice);
- `networkx` (a reference implementation, imported inside the tests after the module under test): the closure network s -> i
  (capacity v_i), i -> t (capacity -v_i), i -> j (infinite), `networkx.maximum_flow`, and the set reachable from s in the residual
  network, computed here by a breadth-first search (networkx's own `minimum_cut` partition is the MAXIMAL source side and differs
  from the smallest closure when zero-value blocks tie, which is reported in the red-phase report);
- value identity: the pit value is the sum of the positive values minus the maximum flow.
Instances: random acyclic precedence on up to 14 blocks (i requires j < i), small regular grids, and seeded grids up to
12 x 12 x 8 with integer values in [-50, 50]; real-valued instances are compared by value (atol 1e-9 x sum |v|).
"""

from __future__ import annotations

import importlib
import itertools

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

SEEDS = st.integers(0, 2**32 - 1)


def _f():
    return importlib.import_module("minephys.planning").ultimate_pit_mincut


def grid_arcs(nx: int, ny: int, nz: int) -> np.ndarray:
    """'1-5' arcs of a C-ordered grid, level 0 on top, written independently of the module under test."""
    arcs = []
    for x, y, z in itertools.product(range(nx), range(ny), range(1, nz)):
        i = (x * ny + y) * nz + z
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + dx < nx and 0 <= y + dy < ny:
                arcs.append((i, ((x + dx) * ny + (y + dy)) * nz + (z - 1)))
    return np.array(arcs, dtype=np.int64).reshape(-1, 2)


def random_dag(n: int, seed: int, density: float) -> np.ndarray:
    rng = np.random.default_rng(seed)
    arcs = [(i, j) for i in range(n) for j in range(i) if rng.random() < density]
    return np.array(arcs, dtype=np.int64).reshape(-1, 2)


def exhaustive(values: np.ndarray, arcs: np.ndarray) -> tuple[np.ndarray, float]:
    n = len(values)
    masks = ((np.arange(1 << n)[:, None] >> np.arange(n)) & 1).astype(bool)
    closed = np.ones(1 << n, dtype=bool)
    for i, j in arcs:
        closed &= ~masks[:, i] | masks[:, j]
    totals = masks.astype(np.float64) @ values.astype(np.float64)
    totals[~closed] = -np.inf
    best = totals.max()
    optimal = masks[totals == best]
    return optimal.all(axis=0), float(best)  # the intersection of all optimal closures


def networkx_pit(values: np.ndarray, arcs: np.ndarray) -> tuple[np.ndarray, float]:
    import networkx as nx

    n = len(values)
    g = nx.DiGraph()
    g.add_nodes_from(range(n))
    g.add_nodes_from(["s", "t"])
    for i, v in enumerate(values):
        if v > 0:
            g.add_edge("s", i, capacity=float(v))
        elif v < 0:
            g.add_edge(i, "t", capacity=float(-v))
    for i, j in arcs:
        g.add_edge(int(i), int(j))  # no capacity attribute: infinite
    flow_value, flow = nx.maximum_flow(g, "s", "t")
    seen = {"s"}
    stack = ["s"]
    while stack:
        u = stack.pop()
        for v, d in g[u].items():
            if v not in seen and d.get("capacity", float("inf")) - flow[u][v] > 0:
                seen.add(v)
                stack.append(v)
        for w in g.pred[u]:
            if w not in seen and flow[w][u] > 0:
                seen.add(w)
                stack.append(w)
    mask = np.array([i in seen for i in range(n)])
    assert float(values[mask].sum()) == pytest.approx(float(values[values > 0].sum()) - flow_value, abs=1e-9)
    return mask, float(values[mask].sum())


@pytest.mark.req("FR-007-04")
@pytest.mark.req("FR-007-05")
@pytest.mark.req("P-007-02")
@pytest.mark.oracle("reference-implementation", "exhaustive enumeration of the closed subsets: smallest optimal closure")
@settings(max_examples=200, deadline=None)
@given(n=st.integers(1, 14), seed=SEEDS, density=st.floats(0.0, 0.6))
def test_p_007_02_pit_equals_the_smallest_optimal_closure(n: int, seed: int, density: float) -> None:
    values = np.random.default_rng(seed + 1).integers(-50, 51, n).astype(np.float64)
    arcs = random_dag(n, seed, density)
    res = _f()(values, arcs)
    mask, best = exhaustive(values, arcs)
    assert np.array_equal(np.asarray(res.mask), mask)  # TC-0
    assert float(res.value) == best
    for i, j in arcs:  # closure feasibility (P-007-02)
        assert (not res.mask[i]) or res.mask[j]


@pytest.mark.req("FR-007-05")
@pytest.mark.req("P-007-02")
@pytest.mark.oracle("reference-implementation", "exhaustive enumeration on small regular grids (at most 16 blocks)")
@settings(max_examples=100, deadline=None)
@given(shape=st.sampled_from([(2, 2, 3), (2, 2, 4), (3, 2, 2), (1, 4, 4), (4, 1, 3), (2, 3, 2), (3, 3, 1), (1, 1, 9)]), seed=SEEDS)
def test_p_007_02_small_regular_grids(shape: tuple[int, int, int], seed: int) -> None:
    n = shape[0] * shape[1] * shape[2]
    values = np.random.default_rng(seed).integers(-50, 51, n).astype(np.float64)
    arcs = grid_arcs(*shape)
    res = _f()(values, arcs)
    mask, best = exhaustive(values, arcs)
    assert np.array_equal(np.asarray(res.mask), mask) and float(res.value) == best


@pytest.mark.req("P-007-02")
@pytest.mark.oracle("reference-implementation", "no closed set found by enumeration beats the pit and the pit is inside every optimal one")
@settings(max_examples=100, deadline=None)
@given(n=st.integers(1, 12), seed=SEEDS, density=st.floats(0.05, 0.5))
def test_p_007_02_optimality_and_containment(n: int, seed: int, density: float) -> None:
    values = np.random.default_rng(seed + 7).integers(-50, 51, n).astype(np.float64)
    arcs = random_dag(n, seed, density)
    res = _f()(values, arcs)
    masks = ((np.arange(1 << n)[:, None] >> np.arange(n)) & 1).astype(bool)
    closed = np.ones(1 << n, dtype=bool)
    for i, j in arcs:
        closed &= ~masks[:, i] | masks[:, j]
    totals = masks.astype(np.float64) @ values
    assert totals[closed].max() <= float(res.value)  # optimality
    optimal = masks[closed & (totals == totals[closed].max())]
    assert np.all(optimal[:, np.asarray(res.mask)])  # the pit is contained in every optimal closed set


@pytest.mark.req("FR-007-05")
@pytest.mark.oracle("reference-implementation", "networkx maximum flow and the residual reachable set, regular grids up to 12 x 12 x 8")
@settings(max_examples=100, deadline=None)
@given(nx=st.integers(1, 12), ny=st.integers(1, 12), nz=st.integers(1, 8), seed=SEEDS)
def test_fr_007_05_pit_equals_the_networkx_residual_source_side(nx: int, ny: int, nz: int, seed: int) -> None:
    f = _f()
    values = np.random.default_rng(seed).integers(-50, 51, nx * ny * nz).astype(np.float64)
    arcs = grid_arcs(nx, ny, nz)
    res = f(values, arcs)
    mask, value = networkx_pit(values, arcs)
    assert np.array_equal(np.asarray(res.mask), mask)
    assert float(res.value) == value


@pytest.mark.req("SC-007-01")
@pytest.mark.req("FR-007-05")
@pytest.mark.oracle("reference-implementation", "500 seeded integer instances against networkx")
def test_sc_007_01_five_hundred_seeded_instances_agree_with_networkx() -> None:
    f = _f()
    for seed in range(500):
        rng = np.random.default_rng(10_000 + seed)
        nx, ny, nz = (int(rng.integers(1, 9)), int(rng.integers(1, 9)), int(rng.integers(1, 7)))
        values = rng.integers(-50, 51, nx * ny * nz).astype(np.float64)
        arcs = grid_arcs(nx, ny, nz)
        res = f(values, arcs)
        mask, value = networkx_pit(values, arcs)
        assert np.array_equal(np.asarray(res.mask), mask), f"seed {seed}: mask differs"
        assert float(res.value) == value, f"seed {seed}: value differs"


@pytest.mark.req("SC-007-01")
@pytest.mark.oracle("reference-implementation", "every instance of at most 16 blocks against the exhaustive smallest closure")
def test_sc_007_01_small_instances_agree_with_enumeration() -> None:
    f = _f()
    for seed in range(120):
        rng = np.random.default_rng(seed)
        n = int(rng.integers(1, 15))
        values = rng.integers(-50, 51, n).astype(np.float64)
        arcs = random_dag(n, seed, float(rng.uniform(0.0, 0.5)))
        res = f(values, arcs)
        mask, best = exhaustive(values, arcs)
        assert np.array_equal(np.asarray(res.mask), mask) and float(res.value) == best, f"seed {seed}"


@pytest.mark.req("FR-007-05")
@pytest.mark.oracle("reference-implementation", "real values: the value agrees with enumeration within atol 1e-9 x sum |v|")
@settings(max_examples=100, deadline=None)
@given(n=st.integers(1, 12), seed=SEEDS, density=st.floats(0.0, 0.6))
def test_fr_007_05_real_values_agree_in_value(n: int, seed: int, density: float) -> None:
    rng = np.random.default_rng(seed)
    values = rng.normal(0.0, 25.0, n)
    arcs = random_dag(n, seed + 3, density)
    res = _f()(values, arcs)
    _, best = exhaustive(values, arcs)
    assert abs(float(res.value) - best) <= 1e-9 * float(np.abs(values).sum()) + 1e-12
    for i, j in arcs:
        assert (not res.mask[i]) or res.mask[j]
    assert float(values[np.asarray(res.mask)].sum()) == pytest.approx(float(res.value), abs=1e-9 * float(np.abs(values).sum()) + 1e-12)

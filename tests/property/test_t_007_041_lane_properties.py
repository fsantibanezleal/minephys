"""T-007-041 (P-007-08, P-007-09): properties of the Lane cut-offs.

Public API under test (`minephys.planning`): `lane_cutoff_grades(...)` returning `LaneCutoffs` with `g_m`, `g_c`, `g_r`, `optimum`,
`value`, `binding` (see tests/unit/test_t_007_040_lane_cutoffs.py and test_t_007_041_lane_optimum.py).
Generators (spec 007 section 4): histograms with 1 to 50 bins on [0, 0.05] (positive tonnage in every bin), capacities log-uniform
over three decades, prices 5e3 to 2e4 with the selling cost 5-30 % of the price, recovery 0.5 to 1, costs in plausible ranges;
200 examples.

Relations
- P-007-08 optimality: V(g*) is not below the objective at any grade of a 1e5-point grid over the range (the 1e6-point grid of the
  spec is used in tests/unit/test_t_007_041_lane_optimum.py; the optimum can never be below a finer grid's maximum, so the coarser
  grid is a weaker but faster check here), within 1e-9 |V|; with C and R multiplied to 1e12 M the optimum tends to g_m clipped to the
  range; g_m <= g_c and g_m <= g_r (None counts as +infinity); raising f or F never lowers g_c or g_r;
- P-007-09 unit invariance: dividing the capacities and the fixed and opportunity costs by k (a new time unit), or rescaling
  tonnage, capacities and per-mass prices and costs by k (a new mass unit), leaves g* and the binding capacities unchanged (rtol 1e-10).
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
SEEDS = st.integers(0, 2**32 - 1)
BINS = st.integers(1, 50)


def _f():
    return importlib.import_module("minephys.planning").lane_cutoff_grades


def xq(g, edges, tonnage, y):
    total = tonnage.sum()
    x = np.zeros_like(g)
    q = np.zeros_like(g)
    for a, b, t in zip(edges[:-1], edges[1:], tonnage, strict=True):
        lo = np.clip(g, a, b)
        x += t * (b - lo) / (b - a)
        q += t * (b * b - lo * lo) / (2.0 * (b - a))
    return x / total, y * q / total


def objective(g, p):
    x, q = xq(np.asarray(g, dtype=float), p["grade_edges"], p["tonnage"], p["recovery"])
    time = np.maximum.reduce(
        [np.full_like(x, 1.0 / p["mine_capacity"]), x / p["plant_capacity"], q / p["market_capacity"]]
    )
    return (p["price"] - p["selling_cost"]) * q - p["processing_cost"] * x - p["mining_cost"] - (p["fixed_cost"] + p["opportunity_cost"]) * time


def instance(n: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    edges = np.r_[0.0, np.cumsum(rng.uniform(1e-4, 1e-3, n))]
    edges = edges * (0.05 / edges[-1]) if edges[-1] > 0.05 else edges
    s = rng.uniform(5e3, 2e4)
    mine = float(np.exp(rng.uniform(math.log(10.0), math.log(1e4))))
    return dict(
        grade_edges=edges,
        tonnage=np.exp(rng.uniform(math.log(1e3), math.log(1e7), n)),
        price=s,
        selling_cost=s * rng.uniform(0.05, 0.3),
        recovery=float(rng.uniform(0.5, 1.0)),
        processing_cost=float(rng.uniform(0.5, 20.0)),
        mining_cost=float(rng.uniform(0.1, 5.0)),
        fixed_cost=float(rng.uniform(0.0, 1000.0)),
        mine_capacity=mine,
        plant_capacity=mine * float(10.0 ** rng.uniform(-1.3, 0.3)),
        market_capacity=mine * float(10.0 ** rng.uniform(-5.0, -1.5)),
        opportunity_cost=float(rng.uniform(0.0, 500.0)),
    )


def run(p: dict):
    return _f()(**p)


@pytest.mark.req("P-007-08")
@pytest.mark.oracle("reference-implementation", "brute-force maximum of Lane's objective on a 1e5-point grid")
@CI
@given(n=BINS, seed=SEEDS)
def test_p_007_08_optimum_is_not_beaten_by_a_dense_grid(n: int, seed: int) -> None:
    p = instance(n, seed)
    res = run(p)
    grid = np.linspace(p["grade_edges"][0], p["grade_edges"][-1], 100_001)
    best = float(objective(grid, p).max())
    assert float(res.value) >= best - 1e-9 * abs(best)
    assert p["grade_edges"][0] <= float(res.optimum) <= p["grade_edges"][-1]
    np.testing.assert_allclose(res.value, float(objective(float(res.optimum), p)), rtol=1e-10, atol=1e-9)


@pytest.mark.req("P-007-08")
@pytest.mark.oracle("analytical", "without capacity limits V has its maximum at g_m (clipped to the range)")
@CI
@given(n=BINS, seed=SEEDS)
def test_p_007_08_unlimited_capacities_give_the_mine_cutoff(n: int, seed: int) -> None:
    p = instance(n, seed)
    p["plant_capacity"] = p["mine_capacity"] * 1e12
    p["market_capacity"] = p["mine_capacity"] * 1e12
    res = run(p)
    g_m = p["processing_cost"] / ((p["price"] - p["selling_cost"]) * p["recovery"])
    expected = min(max(g_m, p["grade_edges"][0]), p["grade_edges"][-1])
    np.testing.assert_allclose(res.optimum, expected, rtol=1e-6, atol=1e-12)


@pytest.mark.req("P-007-08")
@pytest.mark.oracle("analytical", "g_m <= g_c and g_m <= g_r; f and F raise g_c and g_r")
@CI
@given(n=BINS, seed=SEEDS, df=st.floats(0.0, 500.0), dF=st.floats(0.0, 500.0))
def test_p_007_08_ordering_and_monotonicity_of_the_limiting_cutoffs(n: int, seed: int, df: float, dF: float) -> None:
    p = instance(n, seed)
    base = run(p)
    inf = float("inf")
    g_r = inf if base.g_r is None else float(base.g_r)
    assert float(base.g_m) <= float(base.g_c) * (1.0 + 1e-12)
    assert float(base.g_m) <= g_r * (1.0 + 1e-12)
    q = dict(p, fixed_cost=p["fixed_cost"] + df, opportunity_cost=p["opportunity_cost"] + dF)
    more = run(q)
    assert float(more.g_c) >= float(base.g_c) * (1.0 - 1e-12)
    more_r = inf if more.g_r is None else float(more.g_r)
    assert more_r >= g_r * (1.0 - 1e-12)


@pytest.mark.req("P-007-09")
@pytest.mark.oracle("analytical", "the optimum depends on the units only through the products capacity x time and tonnage x price")
@CI
@given(n=BINS, seed=SEEDS, k=st.floats(math.log(1e-3), math.log(1e8)).map(math.exp))
def test_p_007_09_time_unit_invariance(n: int, seed: int, k: float) -> None:
    p = instance(n, seed)
    q = dict(
        p,
        mine_capacity=p["mine_capacity"] / k,
        plant_capacity=p["plant_capacity"] / k,
        market_capacity=p["market_capacity"] / k,
        fixed_cost=p["fixed_cost"] / k,
        opportunity_cost=p["opportunity_cost"] / k,
    )
    a, b = run(p), run(q)
    np.testing.assert_allclose(b.optimum, a.optimum, rtol=1e-10, atol=1e-14)
    assert set(a.binding) == set(b.binding)


@pytest.mark.req("P-007-09")
@CI
@given(n=BINS, seed=SEEDS, k=st.floats(math.log(1e-3), math.log(1e8)).map(math.exp))
def test_p_007_09_mass_unit_invariance(n: int, seed: int, k: float) -> None:
    p = instance(n, seed)
    # a new mass unit: masses become k times as many units, so per-mass prices and costs are divided by k
    q = dict(
        p,
        tonnage=p["tonnage"] * k,
        mine_capacity=p["mine_capacity"] * k,
        plant_capacity=p["plant_capacity"] * k,
        market_capacity=p["market_capacity"] * k,
        price=p["price"] / k,
        selling_cost=p["selling_cost"] / k,
        processing_cost=p["processing_cost"] / k,
        mining_cost=p["mining_cost"] / k,
    )
    a, b = run(p), run(q)
    np.testing.assert_allclose(b.optimum, a.optimum, rtol=1e-10, atol=1e-14)
    assert set(a.binding) == set(b.binding)

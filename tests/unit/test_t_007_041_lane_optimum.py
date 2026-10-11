"""T-007-041 (FR-007-16): the Lane optimum cut-off against a brute-force grid, with the binding capacity.

Expected public API (`minephys.planning`): `lane_cutoff_grades(...)` returning `LaneCutoffs` with the attributes `optimum` (g*),
`value` (V(g*)) and `binding` (a tuple of the names "mine", "plant", "market" of the capacities that bind at g*), besides the
limiting and balancing cut-offs of tests/unit/test_t_007_040_lane_cutoffs.py. The optimum maximises Lane's objective
    V(g) = (s - r) q(g) - h x(g) - m - (f + F) max(1/M, x(g)/C, q(g)/R)
over the grade range, and is the best of the in-range limiting and balancing cut-offs and the range ends (the smallest such grade on
ties within 1e-12 relative).

Oracles (plan 007, brute force over 2e6 grades on the single-bin histogram of test_t_007_040, written in this file):
- C = 50, R = 1 -> g* = g_c = 1.111111e-3, V = 27.944444, the plant binds;
- C = 95, R = 1 -> g* = g_mc = 5e-4, V = 30.51, the mine and the plant bind;
- C = 95, R = 0.2 -> g* = g_r = 3.418803e-4, V = 26.784188, the market binds;
- C = 1,000, R = 10 -> g* = g_m = 2.777778e-4, V = 30.527778, the mine binds.
A seeded 12-bin histogram is checked against the same brute force (V(g*) not below any grid value).
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest

S, RS, Y, H, MC, FF = 10_000.0, 2_000.0, 0.9, 2.0, 0.5, 300.0
EDGES, TON = np.array([0.0, 0.01]), np.array([1.0e6])


def _f():
    return importlib.import_module("minephys.planning").lane_cutoff_grades


def xq(g: np.ndarray, edges: np.ndarray, tonnage: np.ndarray, y: float) -> tuple[np.ndarray, np.ndarray]:
    """Ore fraction x(g) and recovered metal per unit of material q(g) for tonnage uniform in grade inside each bin."""
    total = tonnage.sum()
    x = np.zeros_like(g)
    q = np.zeros_like(g)
    for a, b, t in zip(edges[:-1], edges[1:], tonnage, strict=True):
        lo = np.clip(g, a, b)
        x += t * (b - lo) / (b - a)
        q += t * (b * b - lo * lo) / (2.0 * (b - a))
    return x / total, y * q / total


def objective(g, edges, tonnage, s, r, y, h, m, f, F, M, C, R):
    x, q = xq(np.asarray(g, dtype=float), edges, tonnage, y)
    return (s - r) * q - h * x - m - (f + F) * np.maximum.reduce([np.full_like(x, 1.0 / M), x / C, q / R])


def lane(mine, plant, market, edges=EDGES, tonnage=TON, opportunity=0.0, **over):
    kw = dict(
        grade_edges=edges,
        tonnage=tonnage,
        price=S,
        selling_cost=RS,
        recovery=Y,
        processing_cost=H,
        mining_cost=MC,
        fixed_cost=FF,
        mine_capacity=mine,
        plant_capacity=plant,
        market_capacity=market,
        opportunity_cost=opportunity,
    )
    kw.update(over)
    return _f()(**kw)


SCENARIOS = [
    (100.0, 50.0, 1.0, "g_c", 1.111111e-3, 27.944444, {"plant"}),
    (100.0, 95.0, 1.0, "g_mc", 5e-4, 30.51, {"mine", "plant"}),
    (100.0, 95.0, 0.2, "g_r", 3.418803e-4, 26.784188, {"market"}),
    (100.0, 1000.0, 10.0, "g_m", 2.777778e-4, 30.527778, {"mine"}),
]


@pytest.mark.req("FR-007-16")
@pytest.mark.oracle("analytical", "plan 007 hand-computed optima, confirmed by brute force over 2e6 grades")
@pytest.mark.parametrize(("mine", "plant", "market", "name", "g_star", "v_star", "binding"), SCENARIOS)
def test_fr_007_16_plan_scenarios(mine, plant, market, name, g_star, v_star, binding) -> None:
    res = lane(mine, plant, market)
    np.testing.assert_allclose(res.optimum, g_star, rtol=0, atol=6e-10 if g_star > 1e-3 else 6e-11)
    np.testing.assert_allclose(res.optimum, getattr(res, name), rtol=1e-12, atol=0)  # the optimum is that candidate
    np.testing.assert_allclose(res.value, v_star, rtol=0, atol=6e-7)
    assert set(res.binding) == binding
    # brute force
    grid = np.linspace(0.0, 0.01, 2_000_001)
    v = objective(grid, EDGES, TON, S, RS, Y, H, MC, FF, 0.0, mine, plant, market)
    best = float(v.max())
    assert float(res.value) >= best - 1e-9 * abs(best)
    np.testing.assert_allclose(res.value, objective(res.optimum, EDGES, TON, S, RS, Y, H, MC, FF, 0.0, mine, plant, market), rtol=1e-12)
    assert abs(float(res.optimum) - float(grid[int(v.argmax())])) <= 2.0 * 0.01 / 2_000_000  # within one grid step of the best grid grade


@pytest.mark.req("FR-007-16")
@pytest.mark.oracle("reference-implementation", "brute-force maximum of Lane's objective on a seeded 12-bin histogram")
@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5, 6])
def test_fr_007_16_multi_bin_histogram_against_a_dense_grid(seed: int) -> None:
    rng = np.random.default_rng(seed)
    edges = np.r_[0.0, np.cumsum(rng.uniform(0.001, 0.005, 12))]
    tonnage = np.exp(rng.uniform(np.log(1e4), np.log(1e7), 12))
    mine = float(np.exp(rng.uniform(np.log(50.0), np.log(500.0))))
    plant = mine * float(rng.uniform(0.1, 1.2))
    market = mine * float(np.exp(rng.uniform(np.log(1e-4), np.log(3e-2))))
    opportunity = float(rng.uniform(0.0, 200.0))
    res = lane(mine, plant, market, edges=edges, tonnage=tonnage, opportunity=opportunity)
    grid = np.linspace(edges[0], edges[-1], 1_000_001)
    v = objective(grid, edges, tonnage, S, RS, Y, H, MC, FF, opportunity, mine, plant, market)
    best = float(v.max())
    assert float(res.value) >= best - 1e-9 * abs(best)
    np.testing.assert_allclose(
        res.value, objective(res.optimum, edges, tonnage, S, RS, Y, H, MC, FF, opportunity, mine, plant, market), rtol=1e-12
    )
    assert edges[0] <= float(res.optimum) <= edges[-1]
    assert set(res.binding) <= {"mine", "plant", "market"} and len(res.binding) >= 1

@pytest.mark.req("FR-007-16")
@pytest.mark.oracle("analytical", "with unlimited capacities Lane's optimum is the mine limiting cut-off g_m")
def test_fr_007_16_unlimited_plant_and_market_give_the_mine_cutoff() -> None:
    res = lane(100.0, 100.0 * 1e12, 1e12)
    np.testing.assert_allclose(res.optimum, H / ((S - RS) * Y), rtol=1e-6)
    assert set(res.binding) == {"mine"}


@pytest.mark.req("FR-007-16")
def test_fr_007_16_range_ends_are_candidates() -> None:
    # g_m = 2.78e-4 lies below the first edge 0.002: V decreases over the whole range, so the optimum is the lower end
    res = lane(1000.0, 1e12, 1e12, edges=np.array([0.002, 0.012]), tonnage=np.array([1.0e6]))
    np.testing.assert_allclose(res.optimum, 0.002, rtol=1e-12)
    # g_m above the last edge: the optimum is the upper end
    res = lane(1000.0, 1e12, 1e12, edges=np.array([0.0, 0.0001]), tonnage=np.array([1.0e6]))
    np.testing.assert_allclose(res.optimum, 0.0001, rtol=1e-12)


@pytest.mark.req("FR-007-16")
def test_fr_007_16_the_value_is_reported_for_the_returned_optimum() -> None:
    res = lane(100.0, 70.0, 0.5, opportunity=40.0)
    expected = objective(res.optimum, EDGES, TON, S, RS, Y, H, MC, FF, 40.0, 100.0, 70.0, 0.5)
    np.testing.assert_allclose(res.value, expected, rtol=1e-12)
    assert isinstance(res.value, np.float64) and isinstance(res.optimum, np.float64)

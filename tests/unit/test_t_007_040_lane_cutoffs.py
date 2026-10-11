"""T-007-040 (FR-007-15): Lane's limiting and balancing cut-off grades on analytical histograms.

Expected public API (`minephys.planning`):
    lane_cutoff_grades(grade_edges, tonnage, price, selling_cost, recovery, processing_cost, mining_cost, fixed_cost,
                       mine_capacity, plant_capacity, market_capacity, opportunity_cost=0) -> LaneCutoffs
Notation (Lane): s price and r selling cost per kg of metal, y recovery, h processing cost per kg of ore, m mining cost per kg of
material, f fixed cost and F opportunity cost per unit time, M, C, R the mine, plant and market capacities per unit time (M and C in
kg of material and of ore, R in kg of metal). `grade_edges` are the n + 1 strictly increasing bin edges (mass fractions), `tonnage`
the n bin masses; inside each bin the tonnage is uniform in grade. x(g) is the ore fraction (the fraction of the total tonnage with
grade >= g) and q(g) the recovered metal per unit of material, y x integral of g over the material above g.
`LaneCutoffs` exposes the attributes (the plan names the class, not its fields: the names below are the symbols of FR-007-15, with
the optimum and its value as `optimum` and `value` and the binding capacities as `binding`, a tuple of "mine", "plant", "market")
    g_m  = h / ((s - r) y)                         limiting cut-off of the mine
    g_c  = (h + (f + F) / C) / ((s - r) y)         limiting cut-off of the plant
    g_r  = h / ((s - r - (f + F) / R) y)           limiting cut-off of the market (None when the denominator is <= 0)
    g_mc: x(g) = C / M,  g_mr: q(g) = R / M,  g_cr: q(g) / x(g) = R / C   balancing cut-offs (None when no root lies in the grade range)

Oracles (analytical, plan 007): a single bin with uniform grade on [0, 0.01] has x(g) = 1 - 100 g and
q(g) = y (1e-4 - g^2) / (2e-2); with s = 10,000, r = 2,000, y = 0.9, h = 2, m = 0.5, f = 300, F = 0, M = 100
- g_m = 2.777778e-4; C = 50 -> g_c = 1.111111e-3 and g_mc = 5e-3 (x = 0.5);
- C = 95, R = 0.2 -> g_r = 3.418803e-4 and g_mr = 7.453560e-3 (q = R / M = 0.002), g_cr has no root in range (None);
- R small enough that s - r - (f + F)/R <= 0 -> g_r is None;
and a two-bin histogram whose balancing cut-off g_mc = 3/800 = 3.75e-3 is solved by hand.
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest

S, R_SELL, Y, H, M_COST, F_FIX = 10_000.0, 2_000.0, 0.9, 2.0, 0.5, 300.0
ONE_BIN = dict(
    grade_edges=np.array([0.0, 0.01]),
    tonnage=np.array([1.0e6]),
    price=S,
    selling_cost=R_SELL,
    recovery=Y,
    processing_cost=H,
    mining_cost=M_COST,
    fixed_cost=F_FIX,
)


def _f():
    return importlib.import_module("minephys.planning").lane_cutoff_grades


def lane(mine=100.0, plant=50.0, market=1e9, opportunity=0.0, **over):
    kw = dict(ONE_BIN, mine_capacity=mine, plant_capacity=plant, market_capacity=market, opportunity_cost=opportunity)
    kw.update(over)
    return _f()(**kw)


@pytest.mark.req("FR-007-15")
@pytest.mark.oracle("analytical", "plan 007: g_m = 2.777778e-4, g_c = 1.111111e-3, g_mc = 5e-3 for C = 50")
def test_fr_007_15_plant_limited_case() -> None:
    res = lane(plant=50.0, market=1e9)
    np.testing.assert_allclose(res.g_m, H / ((S - R_SELL) * Y), rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.g_m, 2.777778e-4, rtol=0, atol=6e-11)
    np.testing.assert_allclose(res.g_c, (H + F_FIX / 50.0) / ((S - R_SELL) * Y), rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.g_c, 1.111111e-3, rtol=0, atol=6e-10)
    np.testing.assert_allclose(res.g_mc, (1.0 - 50.0 / 100.0) / 100.0, rtol=1e-12, atol=0)  # x(g) = 1 - 100 g = C / M
    np.testing.assert_allclose(res.g_mc, 5e-3, rtol=1e-12)
    # a market that can absorb 1e9 per unit time does not limit: g_r is practically g_m, and no root exists for the market balances
    np.testing.assert_allclose(res.g_r, res.g_m, rtol=1e-9)
    assert res.g_mr is None and res.g_cr is None


@pytest.mark.req("FR-007-15")
@pytest.mark.oracle("analytical", "plan 007: C = 95, R = 0.2 -> g_r = 3.418803e-4, g_mr = 7.453560e-3")
def test_fr_007_15_market_limited_case() -> None:
    res = lane(plant=95.0, market=0.2)
    np.testing.assert_allclose(res.g_r, H / ((S - R_SELL - F_FIX / 0.2) * Y), rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.g_r, 3.418803e-4, rtol=0, atol=6e-11)
    # q(g) = R / M = 0.002 with q(g) = y (1e-4 - g^2) / 2e-2  ->  g = sqrt(1e-4 - 0.002 x 2e-2 / y)
    np.testing.assert_allclose(res.g_mr, np.sqrt(1e-4 - 0.002 * 2e-2 / Y), rtol=1e-9, atol=0)
    np.testing.assert_allclose(res.g_mr, 7.453560e-3, rtol=0, atol=6e-10)
    np.testing.assert_allclose(res.g_c, (H + F_FIX / 95.0) / ((S - R_SELL) * Y), rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.g_mc, (1.0 - 0.95) / 100.0, rtol=1e-9)  # x(g) = 0.95
    assert res.g_cr is None  # q/x = y (0.01 + g) / 2 = R/C = 0.0021 has its root at a negative grade


@pytest.mark.req("FR-007-15")
@pytest.mark.oracle("analytical", "g_r has no finite value when s - r - (f + F)/R <= 0")
@pytest.mark.parametrize("market", [0.0374, 0.03, 0.001])
def test_fr_007_15_no_finite_market_cutoff(market: float) -> None:
    res = lane(plant=95.0, market=market)  # (f + F)/R exceeds s - r = 8,000 for every R below 0.0375: the denominator is negative
    assert res.g_r is None


@pytest.mark.req("FR-007-15")
@pytest.mark.oracle("analytical", "the opportunity cost F enters like the fixed cost: g_c and g_r use f + F")
def test_fr_007_15_opportunity_cost() -> None:
    res = lane(plant=50.0, market=0.2, opportunity=100.0)
    np.testing.assert_allclose(res.g_c, (H + (F_FIX + 100.0) / 50.0) / ((S - R_SELL) * Y), rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.g_r, H / ((S - R_SELL - (F_FIX + 100.0) / 0.2) * Y), rtol=1e-12, atol=0)
    base = lane(plant=50.0, market=0.2)
    assert res.g_c > base.g_c and res.g_r > base.g_r and res.g_m == base.g_m  # g_m does not depend on f or F


@pytest.mark.req("FR-007-15")
@pytest.mark.oracle("hand-calculation", "two bins [0, 0.005] (2e6) and [0.005, 0.02] (1e6): x(g) = 0.5 gives g = 3/800")
def test_fr_007_15_balancing_cutoff_on_a_two_bin_histogram() -> None:
    # for g <= 0.005 the whole second bin lies above g: x(g) = [2 (1 - 200 g) + 1] / 3 = 1 - 400 g / 3; x = 0.5 -> g = 0.00375 = 3/800
    res = lane(
        plant=50.0,
        market=1e9,
        grade_edges=np.array([0.0, 0.005, 0.02]),
        tonnage=np.array([2.0e6, 1.0e6]),
    )
    np.testing.assert_allclose(res.g_mc, 3.0 / 800.0, rtol=1e-9, atol=0)
    # at that grade the ore fraction is exactly C / M
    g = res.g_mc
    x = (2.0 * (0.005 - g) / 0.005 + 1.0) / 3.0
    np.testing.assert_allclose(x, 0.5, rtol=1e-9)
    # a second balancing root inside the upper bin: x(g) = (0.02 - g) / 0.015 / 3 = 0.2 -> g = 0.011 (C / M = 0.2)
    upper = lane(mine=100.0, plant=20.0, market=1e9, grade_edges=np.array([0.0, 0.005, 0.02]), tonnage=np.array([2.0e6, 1.0e6]))
    np.testing.assert_allclose(upper.g_mc, 0.02 - 0.2 * 3.0 * 0.015, rtol=1e-9)


@pytest.mark.req("FR-007-15")
def test_fr_007_15_balancing_roots_are_returned_only_inside_the_grade_range() -> None:
    # R / M = 0.2 / 100 -> q(g) = 0.002 is reached inside [0, 0.01]; with R = 0.5 it would need q = 0.005 > q(0) = 0.0045: no root
    assert lane(plant=95.0, market=0.2).g_mr is not None
    assert lane(plant=95.0, market=0.5).g_mr is None
    # C / M = 1.5 > 1: x(g) <= 1 never reaches it
    assert lane(mine=100.0, plant=150.0, market=1e9).g_mc is None
    # edges not starting at zero: the ore fraction at the first edge is 1 and the root must lie above it
    res = lane(plant=50.0, grade_edges=np.array([0.002, 0.012]), tonnage=np.array([1.0e6]))
    np.testing.assert_allclose(res.g_mc, 0.002 + (1.0 - 0.5) * 0.01, rtol=1e-12)  # x(g) = 1 - (g - 0.002) / 0.01 = 0.5


@pytest.mark.req("FR-007-15")
def test_fr_007_15_inputs_are_not_modified_and_the_result_is_deterministic() -> None:
    f = _f()
    edges, ton = np.array([0.0, 0.01]), np.array([1.0e6])
    kw = dict(ONE_BIN, grade_edges=edges, tonnage=ton, mine_capacity=100.0, plant_capacity=50.0, market_capacity=0.2)
    a, b = f(**kw), f(**kw)
    assert a.g_c == b.g_c and a.optimum == b.optimum and a.value == b.value
    assert np.array_equal(edges, [0.0, 0.01]) and np.array_equal(ton, [1.0e6])

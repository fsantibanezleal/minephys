"""T-007-010 (FR-007-01, FR-007-02): block economic value, destination and break-even cut-off grade.

Expected public API (`minephys.planning`; mass in kg, grade as a mass fraction, prices and costs per kg, every formula homogeneous):
    block_economic_value(tonnage, grade, price, selling_cost, recovery, processing_cost, mining_cost) -> BlockValue(value, processed)
        v = max(T [g y (p - s_r) - c_p], 0) - T c_m ; processed is True exactly where T [g y (p - s_r) - c_p] > 0
    breakeven_cutoff_grade(processing_cost, price, selling_cost, recovery) -> g_be = c_p / (y (p - s_r))
Arrays broadcast; scalars give `numpy.float64` (value, g_be) and `numpy.bool_` (processed). `BlockValue` exposes `.value`
and `.processed` (plan 007 design table).

Oracles (hand calculation, plan 007)
- T = 1e6 kg, g = 0.01, y = 0.85, p - s_r = 8 per kg (price 10, selling cost 2), c_p = 0.01 per kg, c_m = 0.002 per kg: ore,
  processed, v = 1e6 (0.01 x 0.85 x 8 - 0.01) - 2,000 = 56,000; g = 0.001: waste, v = -T c_m = -2,000;
- g_be = 0.01 / (0.85 x 8) = 1.470588e-3 (0.147 %, the PitStudio planning example).
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest


def _p():
    return importlib.import_module("minephys.planning")


@pytest.mark.req("FR-007-01")
@pytest.mark.oracle("hand-calculation", "plan 007: ore block 56,000, waste block -2,000")
def test_fr_007_01_ore_and_waste_hand_values() -> None:
    p = _p()
    ore = p.block_economic_value(1e6, 0.01, 10.0, 2.0, 0.85, 0.01, 0.002)
    np.testing.assert_allclose(ore.value, 1e6 * (0.01 * 0.85 * 8.0 - 0.01) - 1e6 * 0.002, rtol=1e-12, atol=0)
    np.testing.assert_allclose(ore.value, 56_000.0, rtol=1e-9)
    assert bool(ore.processed) is True
    waste = p.block_economic_value(1e6, 0.001, 10.0, 2.0, 0.85, 0.01, 0.002)
    np.testing.assert_allclose(waste.value, -2_000.0, rtol=1e-12, atol=0)
    assert bool(waste.processed) is False
    assert isinstance(ore.value, np.float64)


@pytest.mark.req("FR-007-01")
@pytest.mark.oracle("hand-calculation", "v = max(T [g y (p - s_r) - c_p], 0) - T c_m on a vector of grades")
def test_fr_007_01_vectorised_values_and_destinations() -> None:
    p = _p()
    grades = np.array([0.0, 0.0005, 0.001, 0.0014, 0.002, 0.01, 0.05])
    tonnage = np.full(7, 5.0e5)
    out = p.block_economic_value(tonnage, grades, 10.0, 2.0, 0.85, 0.01, 0.002)
    margin = 5.0e5 * (grades * 0.85 * 8.0 - 0.01)
    expected = np.maximum(margin, 0.0) - 5.0e5 * 0.002
    np.testing.assert_allclose(out.value, expected, rtol=1e-12, atol=1e-9)
    assert np.array_equal(np.asarray(out.processed), margin > 0)
    assert np.asarray(out.value).dtype == np.float64 and np.asarray(out.processed).dtype == np.bool_


@pytest.mark.req("FR-007-01")
def test_fr_007_01_a_block_exactly_at_the_break_even_grade_is_waste() -> None:
    p = _p()
    g_be = 0.01 / (0.85 * 8.0)
    below = p.block_economic_value(1e6, g_be * (1 - 1e-9), 10.0, 2.0, 0.85, 0.01, 0.002)
    above = p.block_economic_value(1e6, g_be * (1 + 1e-9), 10.0, 2.0, 0.85, 0.01, 0.002)
    assert bool(below.processed) is False and bool(above.processed) is True
    np.testing.assert_allclose(below.value, -2_000.0, rtol=1e-12)  # waste: only the mining cost
    assert above.value > -2_000.0


@pytest.mark.req("FR-007-01")
def test_fr_007_01_zero_tonnage_has_zero_value() -> None:
    p = _p()
    out = p.block_economic_value(0.0, 0.05, 10.0, 2.0, 0.85, 0.01, 0.002)
    assert out.value == 0.0 and bool(out.processed) is False


@pytest.mark.req("FR-007-01")
def test_fr_007_01_broadcasting_over_every_argument() -> None:
    p = _p()
    out = p.block_economic_value(
        np.array([[1e5], [2e5]]), np.array([0.005, 0.01, 0.02]), 10.0, 2.0, np.array([[0.8], [0.9]]), 0.01, 0.002
    )
    assert np.asarray(out.value).shape == (2, 3) and np.asarray(out.processed).shape == (2, 3)
    t = np.array([[1e5], [2e5]])
    g = np.array([0.005, 0.01, 0.02])
    y = np.array([[0.8], [0.9]])
    margin = t * (g * y * 8.0 - 0.01)
    np.testing.assert_allclose(out.value, np.maximum(margin, 0.0) - t * 0.002, rtol=1e-12, atol=1e-9)


@pytest.mark.req("FR-007-02")
@pytest.mark.oracle("hand-calculation", "g_be = 0.01 / (0.85 x 8) = 1.470588e-3")
def test_fr_007_02_breakeven_cutoff_grade() -> None:
    p = _p()
    got = p.breakeven_cutoff_grade(0.01, 10.0, 2.0, 0.85)
    np.testing.assert_allclose(got, 0.01 / (0.85 * 8.0), rtol=1e-12, atol=0)
    np.testing.assert_allclose(got, 1.470588e-3, rtol=0, atol=6e-10)
    assert isinstance(got, np.float64)
    assert p.breakeven_cutoff_grade(0.0, 10.0, 2.0, 0.85) == 0.0  # no processing cost: every positive grade pays
    arr = p.breakeven_cutoff_grade(np.array([0.005, 0.01]), np.array([[10.0], [12.0]]), 2.0, 0.85)
    assert arr.shape == (2, 2)
    np.testing.assert_allclose(arr, [[0.005 / 6.8, 0.01 / 6.8], [0.005 / 8.5, 0.01 / 8.5]], rtol=1e-12)


@pytest.mark.req("FR-007-02")
@pytest.mark.req("FR-007-01")
@pytest.mark.oracle("analytical", "the break-even grade is where the processing margin vanishes")
def test_fr_007_02_the_margin_vanishes_at_the_break_even_grade() -> None:
    p = _p()
    for cp, price, sr, y in ((0.01, 10.0, 2.0, 0.85), (3.5, 900.0, 80.0, 0.6), (1e-4, 1.0, 0.1, 1.0)):
        g = p.breakeven_cutoff_grade(cp, price, sr, y)
        assert g * y * (price - sr) == pytest.approx(cp, rel=1e-12)

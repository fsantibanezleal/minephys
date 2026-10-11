"""T-005-040 (FR-005-24, FR-005-25): passing size, class masses and cumulative passing.

Expected public API (`minephys.comminution`; sizes in m, passing as fractions):
    passing_size(sizes, passing, fraction=0.8) -> size at which the cumulative passing curve equals `fraction`, interpolating
        linearly in (log x, log P) between the two bracketing points; a grid size exactly when `fraction` equals its passing value.
        `sizes` strictly monotone (either order), `passing` non-decreasing with size.
    class_masses(sizes, passing)               -> m_i = P(s_i) - P(s_{i+1}) for i < n, m_n = P(s_n)   (sizes s_1 > ... > s_n, upper class sizes)
    cumulative_passing(masses)                 -> P_i = sum_{k >= i} m_k, the exact inverse of class_masses

Oracles
- analytical: the Swebrec distribution (`ouchterlony2005swebrec`) F(x) = 1 / (1 + [ln(xmax/x) / ln(xmax/x50)]^b) has the closed-form
  80 % passing size x80 = xmax (x50/xmax)^(0.25^(1/b)); plan 005 prints 0.70711 m for x50 = 0.25 m, xmax = 2 m, b = 2
  (0.25^(1/2) = 0.5, x80 = 2 x 0.125^0.5). On a 400-point log-spaced grid from 10 um to xmax the log-log interpolation error
  is at most 4.3e-4 (plan 005, hand-checked), so the test tolerance is rtol 2e-3;
- hand calculation: a three-point curve interpolated with the formula written out in the test;
- exactness: returned grid sizes, round trip `cumulative_passing(class_masses(.)) = passing`.
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest


def _c():
    return importlib.import_module("minephys.comminution")


def swebrec_passing(x: np.ndarray, x50: float, xmax: float, b: float) -> np.ndarray:
    """Swebrec cumulative passing (Ouchterlony 2005): 1 / (1 + (ln(xmax/x) / ln(xmax/x50))^b), 1 at x = xmax."""
    return 1.0 / (1.0 + (np.log(xmax / x) / math.log(xmax / x50)) ** b)


def swebrec_x80(x50: float, xmax: float, b: float) -> float:
    return xmax * (x50 / xmax) ** (0.25 ** (1.0 / b))


@pytest.mark.req("FR-005-24")
@pytest.mark.oracle("analytical", "Swebrec closed form x80 = xmax (x50/xmax)^(0.25^(1/b)) = 0.70711 m (x50 = 0.25, xmax = 2, b = 2)")
@pytest.mark.parametrize("ascending", [False, True])
def test_fr_005_24_swebrec_x80_on_a_400_point_grid(ascending: bool) -> None:
    c = _c()
    x50, xmax, b = 0.25, 2.0, 2.0
    sizes = np.geomspace(xmax, 10e-6, 400)  # coarse to fine
    passing = swebrec_passing(sizes, x50, xmax, b)
    if ascending:
        sizes, passing = sizes[::-1].copy(), passing[::-1].copy()
    x80 = c.passing_size(sizes, passing)  # fraction defaults to 0.8
    assert swebrec_x80(x50, xmax, b) == pytest.approx(0.70711, abs=6e-6)
    np.testing.assert_allclose(x80, swebrec_x80(x50, xmax, b), rtol=2e-3, atol=0)
    assert isinstance(x80, np.float64)
    np.testing.assert_allclose(c.passing_size(sizes, passing, fraction=0.8), x80, rtol=0, atol=0)


@pytest.mark.req("FR-005-24")
@pytest.mark.oracle("analytical", "Swebrec closed form for other fractions: x_p = xmax (x50/xmax)^(((1-p)/p)^(1/b))")
@pytest.mark.parametrize("fraction", [0.1, 0.3, 0.5, 0.9, 0.95])
def test_fr_005_24_other_fractions(fraction: float) -> None:
    c = _c()
    x50, xmax, b = 0.25, 2.0, 2.0
    sizes = np.geomspace(xmax, 10e-6, 400)
    passing = swebrec_passing(sizes, x50, xmax, b)
    expected = xmax * (x50 / xmax) ** (((1.0 - fraction) / fraction) ** (1.0 / b))
    np.testing.assert_allclose(c.passing_size(sizes, passing, fraction), expected, rtol=2e-3, atol=0)


@pytest.mark.req("FR-005-24")
@pytest.mark.oracle("hand-calculation", "log-log interpolation between (0.02 m, 0.5) and (0.05 m, 0.9) at P = 0.8")
def test_fr_005_24_log_log_interpolation_by_hand() -> None:
    c = _c()
    sizes = np.array([0.1, 0.05, 0.02, 0.01])
    passing = np.array([1.0, 0.9, 0.5, 0.2])
    lx0, lx1 = math.log(0.05), math.log(0.02)
    lp0, lp1 = math.log(0.9), math.log(0.5)
    expected = math.exp(lx0 + (math.log(0.8) - lp0) * (lx1 - lx0) / (lp1 - lp0))
    np.testing.assert_allclose(c.passing_size(sizes, passing, 0.8), expected, rtol=1e-12, atol=0)
    # the same curve in ascending order gives the same size
    np.testing.assert_allclose(c.passing_size(sizes[::-1], passing[::-1], 0.8), expected, rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-24")
@pytest.mark.oracle("analytical", "a fraction equal to a grid passing value returns that grid size exactly")
def test_fr_005_24_exact_grid_points() -> None:
    c = _c()
    sizes = np.array([0.1, 0.05, 0.02, 0.01])
    passing = np.array([1.0, 0.9, 0.5, 0.2])
    for x, p in zip(sizes, passing, strict=True):
        assert c.passing_size(sizes, passing, p) == pytest.approx(x, rel=1e-13, abs=0)
    # the curve ends are inside the allowed range of `fraction`
    assert c.passing_size(sizes, passing, 1.0) == pytest.approx(0.1, rel=1e-13)
    assert c.passing_size(sizes, passing, 0.2) == pytest.approx(0.01, rel=1e-13)


@pytest.mark.req("FR-005-25")
@pytest.mark.oracle("hand-calculation", "m_i = P(s_i) - P(s_{i+1}), m_n = P(s_n)")
def test_fr_005_25_class_masses_hand_calculation() -> None:
    c = _c()
    sizes = np.array([0.4, 0.2, 0.1, 0.05])
    passing = np.array([1.0, 0.75, 0.4, 0.15])
    m = c.class_masses(sizes, passing)
    assert m.shape == (4,) and m.dtype == np.float64
    np.testing.assert_allclose(m, [0.25, 0.35, 0.25, 0.15], rtol=1e-12, atol=1e-15)
    np.testing.assert_allclose(m.sum(), passing[0], rtol=0, atol=1e-15)  # the masses add up to P(s_1)


@pytest.mark.req("FR-005-25")
@pytest.mark.oracle("analytical", "cumulative_passing inverts class_masses: P_i = sum of the masses of classes i..n")
def test_fr_005_25_cumulative_passing_and_exact_round_trip() -> None:
    c = _c()
    masses = np.array([0.25, 0.35, 0.25, 0.15])
    p = c.cumulative_passing(masses)
    np.testing.assert_allclose(p, [1.0, 0.75, 0.4, 0.15], rtol=1e-12, atol=1e-15)
    sizes = np.geomspace(1.0, 1e-4, 50)
    passing = swebrec_passing(sizes, 0.2, 1.0, 1.5)
    back = c.cumulative_passing(c.class_masses(sizes, passing))
    np.testing.assert_allclose(back, passing, rtol=1e-12, atol=1e-15)
    again = c.class_masses(sizes, back)
    np.testing.assert_allclose(again, c.class_masses(sizes, passing), rtol=1e-11, atol=1e-15)


@pytest.mark.req("FR-005-25")
def test_fr_005_25_inputs_are_not_modified() -> None:
    c = _c()
    sizes = np.array([0.4, 0.2, 0.1])
    passing = np.array([1.0, 0.6, 0.2])
    s0, p0 = sizes.copy(), passing.copy()
    c.class_masses(sizes, passing)
    c.passing_size(sizes, passing, 0.5)
    c.cumulative_passing(passing)
    assert np.array_equal(sizes, s0) and np.array_equal(passing, p0)

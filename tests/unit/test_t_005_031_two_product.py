"""T-005-031 (FR-005-22, P-005-12): the two-product formula.

Expected public API (`minephys.comminution`):
    two_product_recovery(feed_grade, concentrate_grade, tail_grade) -> (mass_yield, recovery)
the pair is unpacked as `mass_yield, recovery = two_product_recovery(f, c, t)` (a tuple or a named tuple whose first
two items are the yield C/F = (f - t) / (c - t) and the recovery R = c (f - t) / (f (c - t)), both dimensionless).
Grades share any one unit (fraction or percent); 0 <= t < f < c.

Oracles
- hand calculation (plan 005): f = 1 %, c = 25 %, t = 0.1 % -> yield 0.9 / 24.9 = 0.0361446, recovery 25 x 0.9 / 24.9 =
  0.903614 (rtol 1e-12 against the fractions written out below);
- invariance: multiplying the three grades by lambda (percent vs fraction) leaves both results unchanged;
- identity R = (C/F) c / f (P-005-12).
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


def _c():
    return importlib.import_module("minephys.comminution")


@pytest.mark.req("FR-005-22")
@pytest.mark.oracle("hand-calculation", "f = 1 %, c = 25 %, t = 0.1 %: yield 0.0361446, recovery 0.903614")
def test_fr_005_22_hand_calculation_in_percent_and_fraction() -> None:
    c = _c()
    for scale in (1.0, 0.01):
        y, r = c.two_product_recovery(1.0 * scale, 25.0 * scale, 0.1 * scale)
        np.testing.assert_allclose(y, 0.9 / 24.9, rtol=1e-12, atol=0)
        np.testing.assert_allclose(r, 25.0 * 0.9 / (1.0 * 24.9), rtol=1e-12, atol=0)
        np.testing.assert_allclose(y, 0.0361446, rtol=0, atol=6e-8)
        np.testing.assert_allclose(r, 0.903614, rtol=0, atol=6e-7)
        assert isinstance(y, np.float64) and isinstance(r, np.float64)


@pytest.mark.req("FR-005-22")
@pytest.mark.oracle("hand-calculation", "t = 0: perfect tails; c -> f: all feed reports to the concentrate")
def test_fr_005_22_limits() -> None:
    c = _c()
    y, r = c.two_product_recovery(0.05, 0.5, 0.0)
    np.testing.assert_allclose(y, 0.1, rtol=1e-12)  # f / c
    np.testing.assert_allclose(r, 1.0, rtol=1e-12)  # no metal lost to the tails
    y, r = c.two_product_recovery(0.05, 0.0500001, 0.01)
    assert y > 0.99 and r > 0.99  # concentrate almost the feed: nearly everything recovered


@pytest.mark.req("FR-005-22")
def test_fr_005_22_arrays_broadcast() -> None:
    c = _c()
    f = np.array([0.01, 0.02, 0.03])
    y, r = c.two_product_recovery(f, 0.3, 0.002)
    assert y.shape == (3,) and r.shape == (3,) and y.dtype == np.float64
    np.testing.assert_allclose(y, (f - 0.002) / (0.3 - 0.002), rtol=1e-12, atol=0)
    np.testing.assert_allclose(r, 0.3 * (f - 0.002) / (f * (0.3 - 0.002)), rtol=1e-12, atol=0)


GRADES = st.tuples(st.floats(0.0, 0.5), st.floats(1e-4, 0.5), st.floats(1e-4, 0.5)).map(
    lambda x: (x[0], x[0] + x[1], x[0] + x[1] + x[2])
)  # tail < feed < concentrate, spacing at least 1e-4


@pytest.mark.req("P-005-12")
@pytest.mark.oracle("analytical", "R = (C/F) c / f and unit invariance of the grades")
@settings(max_examples=200, deadline=None)
@given(grades=GRADES, lam=st.floats(1e-2, 1e2))
def test_p_005_12_unit_invariance_and_consistency(grades: tuple[float, float, float], lam: float) -> None:
    c = _c()
    t, f, conc = grades
    y, r = c.two_product_recovery(f, conc, t)
    ys, rs = c.two_product_recovery(lam * f, lam * conc, lam * t)
    np.testing.assert_allclose(ys, y, rtol=1e-12, atol=0)
    np.testing.assert_allclose(rs, r, rtol=1e-12, atol=0)
    np.testing.assert_allclose(r, y * conc / f, rtol=1e-12, atol=0)
    assert 0.0 < y < 1.0
    assert 0.0 < r <= 1.0 + 1e-12  # recovery is a fraction of the feed metal

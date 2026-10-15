"""T-002-021 (P-002-06): the KCO link matches the Swebrec and Rosin-Rammler curves at x50.

P-002-06: with b from `kco_undulation`, the Swebrec and Rosin-Rammler curves have the same value (0.5) and the
same slope dP / d ln x at x50. The slopes are derived analytically here, independently of the published
relation:

    Rosin-Rammler  P = 1 - exp(-ln 2 (x / x50)^n):   dP/dln x at x50 = n ln 2 exp(-ln 2) = n ln 2 / 2
    Swebrec        P = 1 / (1 + u^b), u = ln(xmax/x) / ln(xmax/x50):   dP/dln x at x50 = b / (4 ln(xmax / x50))
    equal when b = 2 ln 2 ln(xmax / x50) n, the KCO relation.

Numerically the slope is the central difference in ln x with step h = 1e-6 (rtol 1e-6; truncation ~h^2 =
1e-12, rounding ~1e-10). Generators: x50 / xmax in [0.01, 0.8], n in [0.5, 2], xmax in [0.1, 10].
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from minephys import blasting as B

CFG = settings(deadline=None)
H_STEP = 1e-6
ratio = st.floats(0.01, 0.8)
expo = st.floats(0.5, 2.0)
xmax_s = st.floats(0.1, 10.0)


def slope(curve, x0: float) -> float:
    up = float(curve(x0 * math.exp(H_STEP)))
    down = float(curve(x0 * math.exp(-H_STEP)))
    return (up - down) / (2.0 * H_STEP)


@pytest.mark.req("P-002-06")
@pytest.mark.oracle("analytical", "both curves pass through 1/2 at x50 when b is the KCO value")
@CFG
@given(r=ratio, n=expo, xmax=xmax_s)
def test_same_median(r: float, n: float, xmax: float) -> None:
    x50 = r * xmax
    b = float(B.kco_undulation(n, x50, xmax))
    assert float(B.swebrec_passing(x50, x50, xmax, b)) == pytest.approx(0.5, rel=1e-12)
    assert float(B.rosin_rammler_passing(x50, x50, n)) == pytest.approx(0.5, rel=1e-12)
    assert float(B.kco_distribution(x50, x50, xmax, n)) == pytest.approx(0.5, rel=1e-12)


@pytest.mark.req("P-002-06")
@pytest.mark.oracle(
    "analytical", "slope of Rosin-Rammler at x50 = n ln 2 / 2; slope of Swebrec at x50 = b / (4 ln(xmax / x50))"
)
@CFG
@given(r=ratio, n=expo, xmax=xmax_s)
def test_slopes_against_the_analytical_derivatives(r: float, n: float, xmax: float) -> None:
    x50 = r * xmax
    b = float(B.kco_undulation(n, x50, xmax))
    rr_slope = slope(lambda x: B.rosin_rammler_passing(x, x50, n), x50)
    swe_slope = slope(lambda x: B.swebrec_passing(x, x50, xmax, b), x50)
    assert rr_slope == pytest.approx(n * math.log(2.0) / 2.0, rel=1e-6)
    assert swe_slope == pytest.approx(b / (4.0 * math.log(xmax / x50)), rel=1e-6)


@pytest.mark.req("P-002-06")
@pytest.mark.oracle("analytical", "KCO: the two curves share value and slope at x50 (central differences agree)")
@CFG
@given(r=ratio, n=expo, xmax=xmax_s)
def test_slopes_agree_at_x50(r: float, n: float, xmax: float) -> None:
    x50 = r * xmax
    rr_slope = slope(lambda x: B.rosin_rammler_passing(x, x50, n), x50)
    kco_slope = slope(lambda x: B.kco_distribution(x, x50, xmax, n), x50)
    assert kco_slope == pytest.approx(rr_slope, rel=1e-6)


@pytest.mark.req("P-002-06")
@pytest.mark.oracle("analytical", "a different b breaks the slope match: the KCO value is the only one that matches")
@CFG
@given(r=ratio, n=expo, xmax=xmax_s, factor=st.floats(1.05, 3.0))
def test_other_undulation_values_do_not_match(r: float, n: float, xmax: float, factor: float) -> None:
    x50 = r * xmax
    b = float(B.kco_undulation(n, x50, xmax))
    rr_slope = slope(lambda x: B.rosin_rammler_passing(x, x50, n), x50)
    off = slope(lambda x: B.swebrec_passing(x, x50, xmax, factor * b), x50)
    assert off == pytest.approx(factor * rr_slope, rel=1e-6)
    assert abs(off - rr_slope) > 1e-3 * rr_slope

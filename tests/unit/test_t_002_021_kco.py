"""T-002-021 (FR-002-07, FR-002-15): the KCO link between the uniformity index and the Swebrec undulation parameter.

Expected API:
    `B.kco_undulation(n, x50, xmax)` -> b = 2 ln 2 * ln(xmax / x50) * n
    (dimensionless) `B.kco_distribution(size, x50, xmax, n)` -> `swebrec_passing(size, x50, xmax,
    kco_undulation(n, x50, xmax))`
`x50 >= xmax` raises `InputError` naming `x50` or `xmax` (FR-002-15).

Oracles: spec 002 section 7.4 (b = 2.4940490 for n = 1.1164546, x50 = 0.29940630 m, xmax = 1.5 m; TC-2),
evaluated with the example's UNROUNDED inputs recomputed in this file from the published equations (the
rounded inputs shift the 7th decimal), and the closed-form relation itself (hand transcription, TC-1).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

import minephys
from minephys import blasting as B

Q = 850.0 * math.pi / 4.0 * 0.25**2 * 7.2
K = Q / (6.0 * 7.0 * 12.0)
X50 = 7.0 * K**-0.8 * Q ** (1.0 / 6.0) * (115.0 / 100.0) ** (19.0 / 30.0) / 100.0
N = (2.2 - 14.0 * 6.0 / 250.0) * math.sqrt((1.0 + 7.0 / 6.0) / 2.0) * (1.0 - 0.3 / 6.0) * 1.1**0.1 * 7.2 / 12.0
XMAX = 1.5


@pytest.mark.req("FR-002-07")
@pytest.mark.oracle(
    "hand-calculation", "spec 002 7.4: kco_undulation(n = 1.1164546, x50 = 0.2994063, xmax = 1.5) = 2.4940490"
)
def test_printed_value() -> None:
    got = B.kco_undulation(N, X50, XMAX)
    assert type(got) is np.float64
    assert got == pytest.approx(2.4940490, abs=5e-8)  # TC-2: 7 decimals
    assert got == pytest.approx(2.0 * math.log(2.0) * math.log(XMAX / X50) * N, rel=1e-12)


@pytest.mark.req("FR-002-07")
@pytest.mark.oracle(
    "analytical", "x50 = 0.1, xmax = 1, n = 1: b = 2 ln 2 ln 10; n = 2 doubles it; x50 -> xmax sends b to 0"
)
def test_closed_form_cases() -> None:
    b1 = 2.0 * math.log(2.0) * math.log(10.0)
    assert B.kco_undulation(1.0, 0.1, 1.0) == pytest.approx(b1, rel=1e-12)
    assert B.kco_undulation(2.0, 0.1, 1.0) == pytest.approx(2.0 * b1, rel=1e-12)
    assert B.kco_undulation(1.0, 0.999, 1.0) == pytest.approx(2.0 * math.log(2.0) * math.log(1.0 / 0.999), rel=1e-12)
    assert 0.0 < B.kco_undulation(1.0, 0.999999, 1.0) < 1e-5


@pytest.mark.req("FR-002-07")
@pytest.mark.oracle("analytical", "the KCO distribution is the Swebrec curve with the KCO undulation parameter")
@pytest.mark.parametrize("x", [0.02, 0.1, 0.2994, 0.8, 1.4, 1.5, 3.0])
def test_kco_distribution_is_swebrec_with_the_kco_parameter(x: float) -> None:
    b = B.kco_undulation(N, X50, XMAX)
    assert B.kco_distribution(x, X50, XMAX, N) == pytest.approx(float(B.swebrec_passing(x, X50, XMAX, b)), rel=1e-13)


@pytest.mark.req("FR-002-07")
@pytest.mark.oracle(
    "hand-calculation", "spec 002 7.4: the KCO curve of the example has x80 = 0.59521759 m (found by bisection on P)"
)
def test_kco_curve_reproduces_the_printed_x80() -> None:
    lo, hi = 0.3, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if B.kco_distribution(mid, X50, XMAX, N) < 0.8:
            lo = mid
        else:
            hi = mid
    assert 0.5 * (lo + hi) == pytest.approx(0.59521759, abs=5e-9)
    assert float(B.kco_distribution(X50, X50, XMAX, N)) == pytest.approx(0.5, rel=1e-14)
    assert float(B.kco_distribution(XMAX, X50, XMAX, N)) == 1.0


@pytest.mark.req("FR-002-07")
@pytest.mark.oracle("analytical", "arrays broadcast; empty arrays give empty float64 arrays")
def test_arrays() -> None:
    n = np.array([0.8, 1.0, 1.2])
    out = B.kco_undulation(n, X50, XMAX)
    np.testing.assert_allclose(out, 2.0 * math.log(2.0) * math.log(XMAX / X50) * n, rtol=1e-14)
    grid = B.kco_distribution(np.array([[0.1], [0.5]]), X50, XMAX, n)
    assert grid.shape == (2, 3)
    assert B.kco_distribution(np.empty(0), X50, XMAX, N).shape == (0,)
    assert B.kco_undulation(np.empty(0), X50, XMAX).dtype == np.float64


@pytest.mark.req("FR-002-15")
@pytest.mark.oracle("analytical", "x50 >= xmax is outside the KCO relation (ln(xmax / x50) <= 0)")
@pytest.mark.parametrize(("x50", "xmax"), [(1.5, 1.5), (2.0, 1.5), (10.0, 0.5)])
def test_x50_must_be_below_xmax(x50: float, xmax: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        B.kco_undulation(1.0, x50, xmax)
    assert ei.value.argument in {"x50", "xmax"}
    with pytest.raises(minephys.InputError) as ei2:
        B.kco_distribution(0.5, x50, xmax, 1.0)
    assert ei2.value.argument in {"x50", "xmax"}

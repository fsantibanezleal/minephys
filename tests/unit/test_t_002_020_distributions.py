"""T-002-020 (FR-002-05, FR-002-06, FR-002-15): Rosin-Rammler and Swebrec passing curves and their percentiles.

Expected API (sizes in m, n and b dimensionless):
    `B.rosin_rammler_passing(size, x50, n)`  -> P = 1 - exp(-ln 2 * (x / x50)^n) `B.rosin_rammler_size(passing,
    x50, n)`  -> x50 * (ln(1 / (1 - P)) / ln 2)^(1 / n) `B.swebrec_passing(size, x50, xmax, b)`  -> P = 1 / (1 +
    [ln(xmax / x) / ln(xmax / x50)]^b) for 0 < x < xmax, 1 for x >= xmax `B.swebrec_size(passing, x50, xmax, b)`
    -> xmax * (x50 / xmax)^(((1 - P) / P)^(1 / b)) for 0 < P < 1
FR-002-15: `x50 >= xmax` in a Swebrec function, or `passing` outside (0, 1) in an inverse function, raises
`InputError` naming the argument (`x50` or `xmax`; `passing`).

Oracles: spec 002 section 7.4 worked example 1 (x80 = 0.59521759 m Swebrec and 0.63672061 m Rosin-Rammler;
oversize above 1 m 3.1027 % and 6.9660 %; fines below 0.05 m 13.434 % and 8.9695 %; TC-2) with the example's
UNROUNDED x50, n and b recomputed in this file from the published equations, and analytical identities (P(x50)
= 1/2, P(xmax) = 1, round trip).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

import minephys
from minephys import blasting as B

# worked example 1 (spec 002 section 7.4), unrounded, from the equations of Cunningham 2005 (hand transcription)
Q = 850.0 * math.pi / 4.0 * 0.25**2 * 7.2
K = Q / (6.0 * 7.0 * 12.0)
X50 = 7.0 * K**-0.8 * Q ** (1.0 / 6.0) * (115.0 / 100.0) ** (19.0 / 30.0) / 100.0  # 0.299406298 m
N = (
    (2.2 - 14.0 * 6.0 / 250.0) * math.sqrt((1.0 + 7.0 / 6.0) / 2.0) * (1.0 - 0.3 / 6.0) * 1.1**0.1 * 7.2 / 12.0
)  # 1.1164546
XMAX = 1.5
BUND = 2.0 * math.log(2.0) * math.log(XMAX / X50) * N  # 2.4940490


@pytest.mark.req("FR-002-06")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: Swebrec x80 = 0.59521759 m")
def test_swebrec_x80() -> None:
    got = B.swebrec_size(0.8, X50, XMAX, BUND)
    assert type(got) is np.float64
    assert got == pytest.approx(0.59521759, abs=5e-9)  # TC-2: 8 decimals


@pytest.mark.req("FR-002-05")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: Rosin-Rammler x80 = 0.63672061 m")
def test_rosin_rammler_x80() -> None:
    got = B.rosin_rammler_size(0.8, X50, N)
    assert type(got) is np.float64
    assert got == pytest.approx(0.63672061, abs=5e-9)  # TC-2: 8 decimals


@pytest.mark.req("FR-002-06")
@pytest.mark.req("FR-002-05")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 002 7.4: oversize above 1 m (3.1027 % / 6.9660 %) and fines below 0.05 m (13.434 % / 8.9695 %)",
)
def test_oversize_and_fines_percentages() -> None:
    assert 100.0 * (1.0 - B.swebrec_passing(1.0, X50, XMAX, BUND)) == pytest.approx(3.1027, abs=5e-5)
    assert 100.0 * (1.0 - B.rosin_rammler_passing(1.0, X50, N)) == pytest.approx(6.9660, abs=5e-5)
    assert 100.0 * B.swebrec_passing(0.05, X50, XMAX, BUND) == pytest.approx(13.434, abs=5e-4)
    assert 100.0 * B.rosin_rammler_passing(0.05, X50, N) == pytest.approx(8.9695, abs=5e-5)


@pytest.mark.req("FR-002-05")
@pytest.mark.req("FR-002-06")
@pytest.mark.oracle(
    "analytical", "the median is x50: P(x50) = 1/2 for both curves, and the inverse returns x50 at P = 1/2"
)
@pytest.mark.parametrize(
    ("x50", "xmax", "n"), [(0.2994, 1.5, 1.1165), (0.05, 2.0, 0.7), (0.5, 0.9, 3.5), (1e-3, 1e-1, 2.0)]
)
def test_median_identity(x50: float, xmax: float, n: float) -> None:
    b = 2.0 * math.log(2.0) * math.log(xmax / x50) * n
    assert B.rosin_rammler_passing(x50, x50, n) == pytest.approx(0.5, rel=1e-14)
    assert B.swebrec_passing(x50, x50, xmax, b) == pytest.approx(0.5, rel=1e-14)
    assert B.rosin_rammler_size(0.5, x50, n) == pytest.approx(x50, rel=1e-14)
    assert B.swebrec_size(0.5, x50, xmax, b) == pytest.approx(x50, rel=1e-14)


@pytest.mark.req("FR-002-06")
@pytest.mark.oracle("analytical", "Swebrec: P = 1 at xmax and beyond (exactly), tends to 0 for tiny sizes")
def test_swebrec_end_points() -> None:
    assert B.swebrec_passing(XMAX, X50, XMAX, BUND) == 1.0
    assert B.swebrec_passing(XMAX * 1.0000001, X50, XMAX, BUND) == 1.0
    assert B.swebrec_passing(100.0 * XMAX, X50, XMAX, BUND) == 1.0
    assert 0.0 < B.swebrec_passing(1e-300, X50, XMAX, BUND) < 1e-5
    just_below = B.swebrec_passing(XMAX * (1.0 - 1e-9), X50, XMAX, BUND)
    assert 0.999999 < just_below <= 1.0


@pytest.mark.req("FR-002-05")
@pytest.mark.oracle(
    "analytical", "Rosin-Rammler: P -> 1 for sizes far above x50, P -> 0 for tiny sizes, never negative or above 1"
)
def test_rosin_rammler_tails() -> None:
    assert B.rosin_rammler_passing(1e-12, X50, N) == pytest.approx(0.0, abs=1e-9)
    assert B.rosin_rammler_passing(1e3, X50, N) == 1.0
    p = B.rosin_rammler_passing(np.logspace(-6, 3, 50), X50, N)
    assert np.all((p >= 0.0) & (p <= 1.0))
    assert np.all(np.diff(p) >= 0.0)


@pytest.mark.req("FR-002-05")
@pytest.mark.req("FR-002-06")
@pytest.mark.oracle("analytical", "inverse functions round-trip: size(passing(x)) = x")
@pytest.mark.parametrize("x", [0.02, 0.05, 0.1, 0.2994, 0.5, 0.8, 1.2, 1.49])
def test_round_trips(x: float) -> None:
    assert B.swebrec_size(B.swebrec_passing(x, X50, XMAX, BUND), X50, XMAX, BUND) == pytest.approx(x, rel=1e-10)
    assert B.rosin_rammler_size(B.rosin_rammler_passing(x, X50, N), X50, N) == pytest.approx(x, rel=1e-10)


@pytest.mark.req("FR-002-05")
@pytest.mark.req("FR-002-06")
@pytest.mark.oracle("analytical", "closed forms evaluated independently on a grid")
@pytest.mark.parametrize("x", [0.01, 0.1, 0.3, 0.7, 1.4])
def test_curves_against_the_written_formulas(x: float) -> None:
    rr = 1.0 - math.exp(-math.log(2.0) * (x / X50) ** N)
    swe = 1.0 / (1.0 + (math.log(XMAX / x) / math.log(XMAX / X50)) ** BUND)
    assert B.rosin_rammler_passing(x, X50, N) == pytest.approx(rr, rel=1e-12)
    assert B.swebrec_passing(x, X50, XMAX, BUND) == pytest.approx(swe, rel=1e-12)


@pytest.mark.req("FR-002-05")
@pytest.mark.req("FR-002-06")
@pytest.mark.oracle("analytical", "arrays broadcast; empty arrays give empty float64 arrays")
def test_arrays() -> None:
    sizes = np.array([0.05, 0.3, 1.0])
    out = B.swebrec_passing(sizes, X50, XMAX, BUND)
    assert out.shape == (3,)
    assert out.dtype == np.float64
    assert np.all(np.diff(out) > 0)
    grid = B.rosin_rammler_passing(sizes[:, None], np.array([0.2, 0.4]), 1.5)
    assert grid.shape == (3, 2)
    assert B.swebrec_passing(np.empty(0), X50, XMAX, BUND).shape == (0,)
    assert B.rosin_rammler_size(np.empty(0), X50, N).shape == (0,)


# ---------------------------------------------------------------- FR-002-15


@pytest.mark.req("FR-002-15")
@pytest.mark.oracle("analytical", "x50 >= xmax leaves the domain of the Swebrec form (ln(xmax / x50) <= 0)")
@pytest.mark.parametrize(("x50", "xmax"), [(1.5, 1.5), (2.0, 1.5), (1.5000001, 1.5), (10.0, 0.1)])
def test_swebrec_requires_x50_below_xmax(x50: float, xmax: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        B.swebrec_passing(0.5, x50, xmax, 2.0)
    assert ei.value.argument in {"x50", "xmax"}
    with pytest.raises(minephys.InputError) as ei2:
        B.swebrec_size(0.5, x50, xmax, 2.0)
    assert ei2.value.argument in {"x50", "xmax"}


@pytest.mark.req("FR-002-15")
@pytest.mark.oracle("analytical", "the inverse functions need 0 < P < 1")
@pytest.mark.parametrize("bad", [0.0, 1.0, -0.1, 1.2, math.nan, math.inf, -math.inf])
def test_passing_outside_the_open_unit_interval(bad: float) -> None:
    for fn, args in ((B.rosin_rammler_size, (X50, N)), (B.swebrec_size, (X50, XMAX, BUND))):
        with pytest.raises(minephys.InputError) as ei:
            fn(bad, *args)
        assert ei.value.argument == "passing"


@pytest.mark.req("FR-002-15")
@pytest.mark.oracle("analytical", "passing values next to the open ends are accepted and finite")
@pytest.mark.parametrize("p", [1e-12, 1e-6, 0.999999, 1.0 - 1e-12])
def test_passing_close_to_the_ends(p: float) -> None:
    assert math.isfinite(B.rosin_rammler_size(p, X50, N))
    # Swebrec: for P = 1e-12 the size (x50/xmax)^(1e12^(1/b)) * xmax underflows to 0.0 (the correct float64 value)
    size = B.swebrec_size(p, X50, XMAX, BUND)
    assert 0.0 <= size < XMAX * (1.0 + 1e-9)
    if p >= 1e-6:
        assert size > 0.0

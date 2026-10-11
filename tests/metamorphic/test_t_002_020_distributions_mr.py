"""T-002-020 (P-002-04, P-002-05): metamorphic properties of the size distributions.

P-002-04: every passing function is non-decreasing in size, equals 0.5 at x50, equals 1 at and beyond xmax
(Swebrec), and its inverse round-trips (`size(passing(x)) = x`). P-002-05: scaling size, x50 and xmax by the
same lambda leaves every passing value unchanged (m <-> cm <-> mm). Generators (spec 002): x in (0, xmax), n
and b in [0.5, 4], x50 / xmax in [0.01, 0.8], lambda in [1e-3, 1e3]; the round trip uses x = f * xmax with f
in [0.02, 0.98] and rtol 1e-9 (the inverse is ill-conditioned only in the far tails, excluded by f).

Oracle: analytical (properties of the two closed-form CDFs).
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import blasting as B

CFG = settings(deadline=None)
xmax_s = st.floats(0.1, 10.0)
ratio_s = st.floats(0.01, 0.8)
expo = st.floats(0.5, 4.0)


@pytest.mark.req("P-002-04")
@pytest.mark.oracle("analytical", "non-decreasing in size, values in [0, 1]")
@CFG
@given(xmax=xmax_s, r=ratio_s, e=expo, seed=st.integers(0, 2**32 - 1))
def test_monotone_in_size_and_bounded(xmax: float, r: float, e: float, seed: int) -> None:
    x50 = r * xmax
    sizes = np.sort(np.random.default_rng(seed).uniform(1e-4, 1.2, 40) * xmax)
    swe = B.swebrec_passing(sizes, x50, xmax, e)
    rr = B.rosin_rammler_passing(sizes, x50, e)
    for p in (swe, rr):
        assert np.all(np.diff(p) >= 0.0)
        assert np.all((p >= 0.0) & (p <= 1.0))
    kco = B.kco_distribution(sizes, x50, xmax, e)
    assert np.all(np.diff(kco) >= 0.0)


@pytest.mark.req("P-002-04")
@pytest.mark.oracle("analytical", "P(x50) = 1/2 for every curve; Swebrec reaches 1 at xmax and stays there")
@CFG
@given(xmax=xmax_s, r=ratio_s, e=expo, over=st.floats(1.0, 50.0))
def test_median_and_upper_bound(xmax: float, r: float, e: float, over: float) -> None:
    x50 = r * xmax
    assert float(B.swebrec_passing(x50, x50, xmax, e)) == pytest.approx(0.5, rel=1e-12)
    assert float(B.rosin_rammler_passing(x50, x50, e)) == pytest.approx(0.5, rel=1e-12)
    assert float(B.swebrec_passing(xmax, x50, xmax, e)) == 1.0
    assert float(B.swebrec_passing(over * xmax, x50, xmax, e)) == 1.0


@pytest.mark.req("P-002-04")
@pytest.mark.oracle("analytical", "the inverses undo the passing curves")
@CFG
@given(xmax=xmax_s, r=ratio_s, e=expo, f=st.floats(0.02, 0.98))
def test_round_trip(xmax: float, r: float, e: float, f: float) -> None:
    x50, x = r * xmax, f * xmax
    assert float(B.swebrec_size(B.swebrec_passing(x, x50, xmax, e), x50, xmax, e)) == pytest.approx(x, rel=1e-9)
    p = float(B.rosin_rammler_passing(x, x50, e))
    assume(1e-6 < p < 1.0 - 1e-6)  # the inverse amplifies the rounding of p by 1 / (n (1 - p) ln(1 / (1 - p)))
    assert float(B.rosin_rammler_size(p, x50, e)) == pytest.approx(x, rel=1e-9)


@pytest.mark.req("P-002-05")
@pytest.mark.oracle("analytical", "unit-change invariance: scaling size, x50 and xmax by lambda leaves P unchanged")
@CFG
@given(xmax=xmax_s, r=ratio_s, e=expo, f=st.floats(0.02, 1.5), lam=st.floats(1e-3, 1e3))
def test_unit_change_invariance(xmax: float, r: float, e: float, f: float, lam: float) -> None:
    x50, x = r * xmax, f * xmax
    assert float(B.swebrec_passing(lam * x, lam * x50, lam * xmax, e)) == pytest.approx(
        float(B.swebrec_passing(x, x50, xmax, e)), rel=1e-11, abs=1e-14
    )
    assert float(B.rosin_rammler_passing(lam * x, lam * x50, e)) == pytest.approx(
        float(B.rosin_rammler_passing(x, x50, e)), rel=1e-11, abs=1e-14
    )
    assert float(B.kco_distribution(lam * x, lam * x50, lam * xmax, e)) == pytest.approx(
        float(B.kco_distribution(x, x50, xmax, e)), rel=1e-11, abs=1e-14
    )


@pytest.mark.req("P-002-05")
@pytest.mark.oracle("analytical", "the inverses scale with the length unit: size(P) scales with x50 and xmax")
@CFG
@given(xmax=xmax_s, r=ratio_s, e=expo, p=st.floats(0.05, 0.95), lam=st.floats(1e-3, 1e3))
def test_inverse_scales_with_the_length_unit(xmax: float, r: float, e: float, p: float, lam: float) -> None:
    x50 = r * xmax
    assert float(B.swebrec_size(p, lam * x50, lam * xmax, e)) == pytest.approx(
        lam * float(B.swebrec_size(p, x50, xmax, e)), rel=1e-11
    )
    assert float(B.rosin_rammler_size(p, lam * x50, e)) == pytest.approx(
        lam * float(B.rosin_rammler_size(p, x50, e)), rel=1e-11
    )

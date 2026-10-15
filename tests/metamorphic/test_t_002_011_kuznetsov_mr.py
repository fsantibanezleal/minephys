"""T-002-011 (P-002-01, P-002-02): metamorphic properties of `kuznetsov_x50`.

P-002-01: x50 is strictly decreasing in the powder factor and in RWS, linear in the rock factor, and
multiplies by 2 when the charge multiplies by 64 (monotonicity, scaling; TC-1, strict orderings on pairs with
a relative gap >= 1e-3). P-002-02: the two variants agree exactly at RWS = 115 and their ratio is (115 /
RWS)^(19/20 - 19/30) for every other RWS. Generators (spec 002): A in [0.8, 22], K in [0.1, 3] kg/m^3, Q in
[1, 3000] kg, RWS in [50, 200].

Oracle: analytical (derivatives of A K^-0.8 Q^(1/6) (115/RWS)^e; the exponent difference 19/20 - 19/30 = 19/60).
"""

from __future__ import annotations

import warnings

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import blasting as B

CFG = settings(deadline=None)
rock = st.floats(0.8, 22.0)
pf = st.floats(0.1, 3.0)
charge = st.floats(1.0, 3000.0)
rws = st.floats(50.0, 200.0)


def x50(a, k, q, r, variant="cunningham2005"):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return float(B.kuznetsov_x50(a, k, q, r, variant=variant))


@pytest.mark.req("P-002-01")
@pytest.mark.oracle("analytical", "strictly decreasing in the powder factor")
@CFG
@given(a=rock, k1=pf, k2=pf, q=charge, r=rws)
def test_decreasing_in_powder_factor(a: float, k1: float, k2: float, q: float, r: float) -> None:
    assume(abs(k1 - k2) > 1e-3 * max(k1, k2))
    lo, hi = sorted((k1, k2))
    assert x50(a, hi, q, r) < x50(a, lo, q, r)
    assert x50(a, hi, q, r, "cunningham1983") < x50(a, lo, q, r, "cunningham1983")


@pytest.mark.req("P-002-01")
@pytest.mark.oracle("analytical", "strictly decreasing in RWS (a stronger explosive gives finer fragments)")
@CFG
@given(a=rock, k=pf, q=charge, r1=rws, r2=rws)
def test_decreasing_in_rws(a: float, k: float, q: float, r1: float, r2: float) -> None:
    assume(abs(r1 - r2) > 1e-3 * max(r1, r2))
    lo, hi = sorted((r1, r2))
    assert x50(a, k, q, hi) < x50(a, k, q, lo)
    assert x50(a, k, q, hi, "cunningham1983") < x50(a, k, q, lo, "cunningham1983")


@pytest.mark.req("P-002-01")
@pytest.mark.oracle("analytical", "strictly increasing in the charge, linear in the rock factor")
@CFG
@given(a=rock, k=pf, q1=charge, q2=charge, r=rws, c=st.floats(0.1, 10.0))
def test_increasing_in_charge_and_linear_in_rock_factor(
    a: float, k: float, q1: float, q2: float, r: float, c: float
) -> None:
    assume(abs(q1 - q2) > 1e-3 * max(q1, q2))
    lo, hi = sorted((q1, q2))
    assert x50(a, k, hi, r) > x50(a, k, lo, r)
    assert x50(c * a, k, q1, r) == pytest.approx(c * x50(a, k, q1, r), rel=1e-12)


@pytest.mark.req("P-002-01")
@pytest.mark.oracle("analytical", "the charge enters as Q^(1/6): a factor 64 on Q doubles x50, 729 triples it")
@CFG
@given(a=rock, k=pf, q=st.floats(1.0, 40.0), r=rws)
def test_charge_sixth_root_law(a: float, k: float, q: float, r: float) -> None:
    assert x50(a, k, 64.0 * q, r) == pytest.approx(2.0 * x50(a, k, q, r), rel=1e-12)
    assert x50(a, k, 729.0 * q, r) == pytest.approx(3.0 * x50(a, k, q, r), rel=1e-12)


@pytest.mark.req("P-002-02")
@pytest.mark.oracle("analytical", "the variants differ only by the factor (115 / RWS)^(19/60)")
@CFG
@given(a=rock, k=pf, q=charge, r=rws)
def test_variant_ratio(a: float, k: float, q: float, r: float) -> None:
    ratio = x50(a, k, q, r, "cunningham2005") / x50(a, k, q, r, "cunningham1983")
    assert ratio == pytest.approx((115.0 / r) ** (19.0 / 20.0 - 19.0 / 30.0), rel=1e-12)
    assert x50(a, k, q, 115.0, "cunningham2005") == x50(a, k, q, 115.0, "cunningham1983")

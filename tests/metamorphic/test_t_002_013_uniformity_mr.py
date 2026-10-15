"""T-002-013 (P-002-03): metamorphic properties of `uniformity_index`.

P-002-03: the index is unchanged when every length (B, S, d, W, L, BCL, CCL, H) is scaled by the same factor,
strictly decreasing in the drilling deviation and in B/d, and linear in L/H with all ratios fixed (TC-1;
strict orderings on pairs with a relative gap >= 1e-3). Generators (spec 002): B in [1, 12] m, S/B in [1,
1.5], W/B in [0, 0.2], L/H in [0.3, 1], d in [0.05, 0.4] m; the diameter range is narrowed to d >= 8.4 B /
1000 (d in m, B in m) so that 14 B / d_mm <= 1.67 stays inside the domain of the first factor (with d = 0.05 m
and B = 12 m the formula itself leaves its domain, FR-002-14).

Oracle: analytical (every term of the formula is a ratio of lengths except the explicit millimetre conversion
of d, which scales with the other lengths).
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import blasting as B

CFG = settings(deadline=None)


@st.composite
def designs(draw):
    burden = draw(st.floats(1.0, 12.0))
    d_min = max(0.05, 8.4 * burden / 1000.0)
    diameter = draw(st.floats(d_min, 0.4))
    spacing = burden * draw(st.floats(1.0, 1.5))
    deviation = burden * draw(st.floats(0.0, 0.2))
    height = draw(st.floats(5.0, 30.0))
    length = height * draw(st.floats(0.3, 1.0))
    return {
        "burden": burden,
        "spacing": spacing,
        "hole_diameter": diameter,
        "drilling_deviation": deviation,
        "charge_length": length,
        "bench_height": height,
    }


def n_of(**kw):
    return float(B.uniformity_index(**kw))


@pytest.mark.req("P-002-03")
@pytest.mark.oracle("analytical", "unit-change invariance: metres, centimetres or feet give the same index")
@CFG
@given(kw=designs(), k=st.floats(1e-2, 1e3), split=st.floats(0.0, 1.0))
def test_common_length_scaling_is_neutral(kw: dict, k: float, split: float) -> None:
    base = n_of(**kw)
    scaled = {name: k * value for name, value in kw.items()}
    assert n_of(**scaled) == pytest.approx(base, rel=1e-11)
    # with explicit column lengths as well
    usable = kw["charge_length"] * (1.0 - 1e-9)  # keep BCL + CCL < L despite rounding
    bcl, ccl = split * usable, (1.0 - split) * usable
    explicit = n_of(**kw, bottom_charge_length=bcl, column_charge_length=ccl)
    explicit_scaled = n_of(**scaled, bottom_charge_length=k * bcl, column_charge_length=k * ccl)
    assert explicit_scaled == pytest.approx(explicit, rel=1e-11)


@pytest.mark.req("P-002-03")
@pytest.mark.oracle("analytical", "strictly decreasing in the drilling deviation")
@CFG
@given(kw=designs(), f1=st.floats(0.0, 0.2), f2=st.floats(0.0, 0.2))
def test_decreasing_in_drilling_deviation(kw: dict, f1: float, f2: float) -> None:
    assume(abs(f1 - f2) > 1e-3 * max(f1, f2, 1e-3))
    lo, hi = sorted((f1, f2))
    b = kw["burden"]
    assert n_of(**{**kw, "drilling_deviation": hi * b}) < n_of(**{**kw, "drilling_deviation": lo * b})


@pytest.mark.req("P-002-03")
@pytest.mark.oracle("analytical", "strictly decreasing in B/d: a larger diameter at fixed burden raises the index")
@CFG
@given(kw=designs(), d2=st.floats(0.05, 0.4))
def test_decreasing_in_burden_to_diameter_ratio(kw: dict, d2: float) -> None:
    d1 = kw["hole_diameter"]
    assume(abs(d1 - d2) > 1e-3 * max(d1, d2))
    assume(d2 >= 8.4 * kw["burden"] / 1000.0)
    small, large = sorted((d1, d2))
    assert n_of(**{**kw, "hole_diameter": large}) > n_of(**{**kw, "hole_diameter": small})


@pytest.mark.req("P-002-03")
@pytest.mark.oracle("analytical", "linear in L/H with every other ratio fixed")
@CFG
@given(kw=designs(), k=st.floats(0.5, 2.0))
def test_linear_in_charge_to_bench_ratio(kw: dict, k: float) -> None:
    base = n_of(**kw)
    taller = {**kw, "bench_height": kw["bench_height"] / k}  # L/H grows by k, nothing else changes
    assert n_of(**taller) == pytest.approx(k * base, rel=1e-11)


@pytest.mark.req("P-002-03")
@pytest.mark.oracle(
    "analytical", "more of the charged length in a single explosive raises the last factor: |BCL - CCL| / L grows"
)
@CFG
@given(kw=designs(), s1=st.floats(0.0, 0.5), s2=st.floats(0.0, 0.5))
def test_balanced_decks_lower_the_index(kw: dict, s1: float, s2: float) -> None:
    assume(abs(s1 - s2) > 1e-3)
    length = kw["charge_length"] * (1.0 - 1e-9)  # keep BCL + CCL < L despite rounding
    lo, hi = sorted((s1, s2))  # the share of the shorter deck: 0.5 is a perfectly even split (|BCL - CCL| = 0)

    def with_share(share: float) -> float:
        return n_of(**kw, bottom_charge_length=(1.0 - share) * length, column_charge_length=share * length)

    assert with_share(hi) <= with_share(lo)

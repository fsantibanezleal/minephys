"""T-001-010 (P-001-01): metamorphic properties of `grade_resistance` and `total_resistance`.

Relations (spec 001 P-001-01): oddness GR(-x) = -GR(x) (exact), strict monotonicity, the bound |GR_exact(x)| <= |x| with
equality only at 0, plus two relations of the sum form (total resistance is affine in the rolling resistance with unit
slope, and equals RR + GR). Generators: grade in [-1, 1]. Tolerance: exact for the symmetry, TC-1 otherwise; the strict
orderings use pairs whose relative gap is at least 1e-9, far above float64 rounding of x / sqrt(1 + x^2).

Oracle: analytical (the relations above are consequences of sin(arctan x)).
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

grades = st.floats(-1.0, 1.0, allow_nan=False, allow_infinity=False)


@pytest.mark.req("P-001-01")
@pytest.mark.oracle("analytical", "odd function: GR(-x) = -GR(x) bitwise")
@settings(deadline=None)
@given(x=grades)
def test_odd_symmetry_is_exact(x: float) -> None:
    assert H.grade_resistance(-x) == -H.grade_resistance(x)
    assert H.grade_resistance(-x, small_angle=True) == -H.grade_resistance(x, small_angle=True)


@pytest.mark.req("P-001-01")
@pytest.mark.oracle("analytical", "strictly increasing in the grade")
@settings(deadline=None)
@given(x=grades, y=grades)
def test_strictly_increasing(x: float, y: float) -> None:
    assume(abs(x - y) > 1e-9 * max(abs(x), abs(y), 1e-3))
    lo, hi = sorted((x, y))
    assert H.grade_resistance(lo) < H.grade_resistance(hi)


@pytest.mark.req("P-001-01")
@pytest.mark.oracle("analytical", "|GR_exact(x)| <= |x| with equality only at x = 0")
@settings(deadline=None)
@given(x=grades)
def test_exact_resistance_is_bounded_by_the_small_angle_value(x: float) -> None:
    gr = float(H.grade_resistance(x))
    assert abs(gr) <= abs(x) * (1.0 + 1e-12)  # TC-1 slack; the true gap is x^2 / 2 in relative terms
    if x == 0.0:
        assert gr == 0.0
    elif abs(x) > 1e-3:
        assert abs(gr) < abs(x), "strict inequality away from zero"


@pytest.mark.req("P-001-01")
@pytest.mark.oracle("analytical", "the exact resistance stays inside (-1, 1) however steep the grade")
@settings(deadline=None)
@given(x=st.floats(-1e6, 1e6, allow_nan=False, allow_infinity=False))
def test_exact_resistance_is_a_sine(x: float) -> None:
    assert -1.0 <= float(H.grade_resistance(x)) <= 1.0


@pytest.mark.req("P-001-01")
@pytest.mark.req("FR-001-02")
@pytest.mark.oracle("analytical", "TR(RR + d, g) = TR(RR, g) + d and TR(RR, g) - RR = GR(g)")
@settings(deadline=None)
@given(rr=st.floats(0.0, 0.4), d=st.floats(0.0, 0.4), g=st.floats(-0.3, 0.3))
def test_total_resistance_is_affine_in_the_rolling_resistance(rr: float, d: float, g: float) -> None:
    base = float(H.total_resistance(rr, g))
    shifted = float(H.total_resistance(rr + d, g))
    assert shifted - base == pytest.approx(d, rel=1e-9, abs=1e-14)
    assert base - rr == pytest.approx(float(H.grade_resistance(g)), rel=1e-9, abs=1e-14)
    assert math.isfinite(base)


@pytest.mark.req("P-001-01")
@pytest.mark.req("FR-001-02")
@pytest.mark.oracle("analytical", "vectorised evaluation equals scalar evaluation")
@settings(deadline=None)
@given(xs=st.lists(st.floats(-0.3, 0.3), min_size=1, max_size=30), rr=st.floats(0.0, 0.3))
def test_total_resistance_vectorised_matches_scalar(xs: list[float], rr: float) -> None:
    arr = np.array(xs)
    out = H.total_resistance(rr, arr)
    for i, x in enumerate(xs):
        assert out[i] == pytest.approx(float(H.total_resistance(rr, x)), rel=1e-14, abs=1e-14)

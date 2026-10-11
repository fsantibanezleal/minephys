"""T-002-040 (P-002-09): metamorphic properties of the drag-free flyrock range.

P-002-09: `flyrock_range_no_drag` is symmetric about 45 degrees (R(theta) = R(pi/2 - theta)), scales as v0^2
and as 1/g (TC-1). Generators (spec 002): v0 in [1, 300] m/s, theta in (0, pi/2); the symmetry test keeps
theta in [0.02, pi/2 - 0.02] so that the sines are not rounding-dominated. Extra relations (analytical): the
maximum at 45 degrees equals v0^2 / g, and complementary launch angles give equal ranges.

Oracle: analytical (R = v0^2 sin(2 theta) / g; sin(2 theta) = sin(pi - 2 theta)).
"""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import blasting as B

CFG = settings(deadline=None)
speed = st.floats(1.0, 300.0)
angle = st.floats(0.02, math.pi / 2.0 - 0.02)
grav = st.floats(1.0, 25.0)


def r(v, th, g=9.80665):
    return float(B.flyrock_range_no_drag(v, th, g=g))


@pytest.mark.req("P-002-09")
@pytest.mark.oracle("analytical", "symmetry about 45 degrees: complementary angles give the same range")
@CFG
@given(v=speed, th=angle)
def test_symmetry_about_45_degrees(v: float, th: float) -> None:
    assert r(v, th) == pytest.approx(r(v, math.pi / 2.0 - th), rel=1e-12)


@pytest.mark.req("P-002-09")
@pytest.mark.oracle("analytical", "R scales as v0^2")
@CFG
@given(v=speed, th=angle, k=st.floats(1e-2, 1e2))
def test_quadratic_in_speed(v: float, th: float, k: float) -> None:
    assert r(k * v, th) == pytest.approx(k * k * r(v, th), rel=1e-12)


@pytest.mark.req("P-002-09")
@pytest.mark.oracle("analytical", "R scales as 1 / g")
@CFG
@given(v=speed, th=angle, g=grav, k=st.floats(1e-2, 1e2))
def test_inverse_in_gravity(v: float, th: float, g: float, k: float) -> None:
    assert r(v, th, k * g) == pytest.approx(r(v, th, g) / k, rel=1e-12)


@pytest.mark.req("P-002-09")
@pytest.mark.oracle("analytical", "45 degrees gives the maximum v0^2 / g")
@CFG
@given(v=speed, th=angle, g=grav)
def test_maximum_at_45_degrees(v: float, th: float, g: float) -> None:
    best = r(v, math.pi / 4.0, g)
    assert best == pytest.approx(v * v / g, rel=1e-12)
    assert r(v, th, g) <= best * (1.0 + 1e-12)


@pytest.mark.req("P-002-09")
@pytest.mark.oracle("analytical", "R is strictly increasing in the angle below 45 degrees and decreasing above")
@CFG
@given(v=speed, t1=st.floats(0.02, math.pi / 4.0), t2=st.floats(0.02, math.pi / 4.0))
def test_unimodal_in_the_angle(v: float, t1: float, t2: float) -> None:
    assume(abs(t1 - t2) >= 1e-3)
    lo, hi = sorted((t1, t2))
    assert r(v, lo) < r(v, hi)  # increasing below 45 degrees
    assert r(v, math.pi / 2.0 - lo) < r(v, math.pi / 2.0 - hi)  # decreasing above 45 degrees

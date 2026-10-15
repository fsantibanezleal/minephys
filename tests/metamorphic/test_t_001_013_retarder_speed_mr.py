"""T-001-013 (P-001-04): metamorphic properties of `retarder_limited_speed`.

P-001-04: the uncapped speed times the mass is constant in the mass (TC-1), the speed is linear in the retarder power,
and the speed is non-increasing in the downgrade steepness (exact ordering). Generators (spec 001): grade in
[-0.3, -0.03], rolling resistance in [0, 0.03], mass in [2e4, 7e5] kg; cases whose net braking fraction
f = -GR - RR is below 1e-3 (ill-conditioned: the speed is ~1/f) are discarded.

Oracle: analytical (v = P / (m g f): v*m = P/(g f) does not depend on the mass; f grows with steepness).
"""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

G0 = 9.80665
power = st.floats(5e5, 5e6)
mass = st.floats(2e4, 7e5)
grade = st.floats(-0.3, -0.03)
rr = st.floats(0.0, 0.03)
CFG = settings(deadline=None)


def f_net(g: float, r: float) -> float:
    return -g / math.sqrt(1.0 + g * g) - r


def speed(p, m, r, g, **kw):
    return float(H.retarder_limited_speed(p, m, r, g, **kw))


@pytest.mark.req("P-001-04")
@pytest.mark.oracle("analytical", "speed * mass is constant in the mass")
@CFG
@given(p=power, m1=mass, m2=mass, r=rr, g=grade)
def test_speed_times_mass_is_constant(p: float, m1: float, m2: float, r: float, g: float) -> None:
    assume(f_net(g, r) > 1e-3)
    assert speed(p, m1, r, g) * m1 == pytest.approx(speed(p, m2, r, g) * m2, rel=1e-12)
    assert speed(p, m1, r, g) * m1 == pytest.approx(p / (G0 * f_net(g, r)), rel=1e-12)


@pytest.mark.req("P-001-04")
@pytest.mark.oracle("analytical", "the speed is linear in the retarder power and inversely proportional to the mass")
@CFG
@given(p=power, m=mass, r=rr, g=grade, k=st.floats(0.1, 10.0))
def test_linear_in_power_and_inverse_in_mass(p: float, m: float, r: float, g: float, k: float) -> None:
    assume(f_net(g, r) > 1e-3)
    base = speed(p, m, r, g)
    assert speed(k * p, m, r, g) == pytest.approx(k * base, rel=1e-12)
    assert speed(p, k * m, r, g) == pytest.approx(base / k, rel=1e-12)
    assert speed(k * p, k * m, r, g) == pytest.approx(base, rel=1e-12)


@pytest.mark.req("P-001-04")
@pytest.mark.oracle("analytical", "a steeper downgrade (more negative grade) never raises the speed")
@CFG
@given(p=power, m=mass, r=rr, g1=grade, g2=grade)
def test_non_increasing_in_downgrade_steepness(p: float, m: float, r: float, g1: float, g2: float) -> None:
    assume(abs(g1 - g2) > 1e-3 * max(abs(g1), abs(g2)))
    steep, gentle = sorted((g1, g2))  # steep is the more negative grade
    assume(f_net(gentle, r) > 1e-3)
    assert speed(p, m, r, steep) <= speed(p, m, r, gentle)


@pytest.mark.req("P-001-04")
@pytest.mark.oracle("analytical", "more rolling resistance helps the brakes: the speed is non-decreasing in RR")
@CFG
@given(p=power, m=mass, g=grade, r1=rr, r2=rr)
def test_non_decreasing_in_rolling_resistance(p: float, m: float, g: float, r1: float, r2: float) -> None:
    assume(abs(r1 - r2) > 1e-3 * max(r1, r2, 1e-3))
    lo, hi = sorted((r1, r2))
    assume(f_net(g, hi) > 1e-3)
    assert speed(p, m, hi, g) >= speed(p, m, lo, g)


@pytest.mark.req("P-001-04")
@pytest.mark.oracle("analytical", "the speed limit only ever lowers the uncapped speed: min law")
@CFG
@given(p=power, m=mass, r=rr, g=grade, cap=st.floats(0.5, 60.0))
def test_speed_limit_is_a_min(p: float, m: float, r: float, g: float, cap: float) -> None:
    assume(f_net(g, r) > 1e-3)
    free = speed(p, m, r, g)
    assert speed(p, m, r, g, speed_limit=cap) == pytest.approx(min(free, cap), rel=1e-12)

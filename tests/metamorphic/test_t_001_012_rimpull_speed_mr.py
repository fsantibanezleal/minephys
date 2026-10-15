"""T-001-012 (P-001-02, P-001-03): metamorphic properties of `rimpull_limited_speed`.

P-001-02 (scaling, TC-1, rtol 1e-12): without drag and traction limit the speed is linear in `power * efficiency` and
inversely proportional to `mass` and to `total_resistance` (below `speed_limit`).
P-001-03 (monotonicity, exact ordering): non-increasing in mass, total resistance, drag area and air density;
non-decreasing in power, efficiency, traction limit and speed limit; adding drag never increases the speed.
Generators (spec 001): power in [1e5, 5e6] W, mass in [2e4, 7e5] kg, TR in [0.01, 0.3], k in [0.1, 10], drag area in
[0, 100] m^2. Ordered pairs differ by a relative gap of at least 1e-3 so that the 1e-12 tolerance of an iterative root
cannot reorder them.

Oracle: analytical (v = eta * P / (m g TR) and the signs of its partial derivatives; the drag equation
0.5 rho CdA v^3 + m g TR v = eta P is increasing in v, so more drag or more load lowers its root).
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

G0 = 9.80665
power = st.floats(1e5, 5e6)
mass = st.floats(2e4, 7e5)
tr = st.floats(0.01, 0.3)
scale = st.floats(0.1, 10.0)
CFG = settings(deadline=None)


def v(p, m, r, **kw):
    return float(H.rimpull_limited_speed(p, m, r, **kw))


def gapped(a: float, b: float) -> bool:
    return abs(a - b) > 1e-3 * max(abs(a), abs(b))


# ---------------------------------------------------------------- P-001-02


@pytest.mark.req("P-001-02")
@pytest.mark.oracle("analytical", "v is linear in the power")
@CFG
@given(p=power, m=mass, r=tr, k=scale)
def test_linear_in_power(p: float, m: float, r: float, k: float) -> None:
    assert v(k * p, m, r) == pytest.approx(k * v(p, m, r), rel=1e-12)


@pytest.mark.req("P-001-02")
@pytest.mark.oracle("analytical", "v is linear in the efficiency")
@CFG
@given(p=power, m=mass, r=tr, k=st.floats(0.2, 2.0))
def test_linear_in_efficiency(p: float, m: float, r: float, k: float) -> None:
    base = v(p, m, r, efficiency=0.5)
    assert v(p, m, r, efficiency=0.5 * k) == pytest.approx(k * base, rel=1e-12)
    assert v(k * p, m, r, efficiency=0.5) == pytest.approx(v(p, m, r, efficiency=0.5 * k), rel=1e-12)


@pytest.mark.req("P-001-02")
@pytest.mark.oracle("analytical", "v is inversely proportional to the mass and to the total resistance")
@CFG
@given(p=power, m=mass, r=tr, k=scale)
def test_inverse_in_mass_and_resistance(p: float, m: float, r: float, k: float) -> None:
    base = v(p, m, r)
    assert v(p, k * m, r) == pytest.approx(base / k, rel=1e-12)
    assert v(p, m, k * r) == pytest.approx(base / k, rel=1e-12)


@pytest.mark.req("P-001-02")
@pytest.mark.oracle(
    "analytical", "only the ratio power / (mass * TR) matters: scaling power and mass together is neutral"
)
@CFG
@given(p=power, m=mass, r=tr, k=scale)
def test_scaling_power_and_mass_together_is_neutral(p: float, m: float, r: float, k: float) -> None:
    assert v(k * p, k * m, r) == pytest.approx(v(p, m, r), rel=1e-12)
    assert v(k * p, m, k * r) == pytest.approx(v(p, m, r), rel=1e-12)


@pytest.mark.req("P-001-02")
@pytest.mark.oracle("analytical", "linear scaling holds below the speed limit and the limit then caps it")
@CFG
@given(p=power, m=mass, r=tr, cap=st.floats(0.5, 30.0))
def test_speed_limit_caps_the_linear_law(p: float, m: float, r: float, cap: float) -> None:
    free = p / (m * G0 * r)
    assert v(p, m, r, speed_limit=cap) == pytest.approx(min(free, cap), rel=1e-12)


# ---------------------------------------------------------------- P-001-03


@pytest.mark.req("P-001-03")
@pytest.mark.oracle("analytical", "non-increasing in mass, total resistance and (with drag) drag area and air density")
@CFG
@given(
    p=power,
    m1=mass,
    m2=mass,
    r1=tr,
    r2=tr,
    c1=st.floats(0.5, 100.0),
    c2=st.floats(0.5, 100.0),
    d1=st.floats(0.3, 2.0),
    d2=st.floats(0.3, 2.0),
)
def test_non_increasing_in_load_and_drag(p, m1, m2, r1, r2, c1, c2, d1, d2) -> None:
    for a, b, name in ((m1, m2, "m"), (r1, r2, "r"), (c1, c2, "c"), (d1, d2, "d")):
        assume(gapped(a, b))
        lo, hi = sorted((a, b))
        args = {"m": 2e5, "r": 0.1, "c": 40.0, "d": 1.2}
        low, high = dict(args, **{name: lo}), dict(args, **{name: hi})
        v_low = v(p, low["m"], low["r"], drag_area=low["c"], air_density=low["d"])
        v_high = v(p, high["m"], high["r"], drag_area=high["c"], air_density=high["d"])
        assert v_high <= v_low, name


@pytest.mark.req("P-001-03")
@pytest.mark.oracle("analytical", "non-decreasing in power and efficiency")
@CFG
@given(p1=power, p2=power, e1=st.floats(0.05, 1.0), e2=st.floats(0.05, 1.0), cda=st.floats(0.0, 100.0))
def test_non_decreasing_in_power_and_efficiency(p1, p2, e1, e2, cda) -> None:
    kw = {"drag_area": cda, "air_density": 1.2} if cda > 0 else {}
    assume(gapped(p1, p2))
    lo, hi = sorted((p1, p2))
    assert v(hi, 2e5, 0.08, **kw) >= v(lo, 2e5, 0.08, **kw)
    assume(gapped(e1, e2))
    lo, hi = sorted((e1, e2))
    assert v(1e6, 2e5, 0.08, efficiency=hi, **kw) >= v(1e6, 2e5, 0.08, efficiency=lo, **kw)


@pytest.mark.req("P-001-03")
@pytest.mark.oracle("analytical", "non-decreasing in the traction limit (zero below m g TR) and in the speed limit")
@CFG
@given(u1=st.floats(0.5, 3.0), u2=st.floats(0.5, 3.0), s1=st.floats(0.5, 20.0), s2=st.floats(0.5, 20.0))
def test_non_decreasing_in_traction_and_speed_limits(u1, u2, s1, s2) -> None:
    m, r = 2e5, 0.08
    f0 = m * G0 * r
    kw = {"drag_area": 40.0, "air_density": 1.2}
    assume(gapped(u1, u2))
    lo, hi = sorted((u1, u2))
    assert v(1.2e6, m, r, traction_limit=hi * f0, **kw) >= v(1.2e6, m, r, traction_limit=lo * f0, **kw)
    assume(gapped(s1, s2))
    lo, hi = sorted((s1, s2))
    assert v(1.2e6, m, r, speed_limit=hi, **kw) >= v(1.2e6, m, r, speed_limit=lo, **kw)


@pytest.mark.req("P-001-03")
@pytest.mark.oracle("analytical", "adding drag never increases the speed")
@CFG
@given(p=power, m=mass, r=tr, cda=st.floats(0.5, 100.0), rho=st.floats(0.3, 2.0))
def test_drag_never_increases_the_speed(p: float, m: float, r: float, cda: float, rho: float) -> None:
    assert v(p, m, r, drag_area=cda, air_density=rho) <= v(p, m, r)


@pytest.mark.req("P-001-03")
@pytest.mark.req("FR-001-05")
@pytest.mark.oracle("analytical", "a traction limit below m g TR stalls the truck, whatever the power")
@CFG
@given(p=power, m=mass, r=tr, u=st.floats(0.05, 0.99))
def test_traction_limit_below_the_resistance_force_always_stalls(p: float, m: float, r: float, u: float) -> None:
    assert v(p, m, r, traction_limit=u * m * G0 * r) == 0.0
    assert np.isfinite(v(p, m, r))

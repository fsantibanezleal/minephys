"""T-002-041 (FR-002-12, FR-002-13, P-002-10): the drag-inclusive flyrock trajectory (fixed-step RK4).

Expected API: `B.flyrock_trajectory(launch_speed, launch_angle, diameter, rock_density, drag_coefficient,
air_density, launch_height=0, time_step=1e-3, max_time=600, g=9.80665)` with scalar inputs, integrating m
dv/dt = -m g z^ - 1/2 rho_a C_D A |v| v for a sphere (m = rho_r pi D^3 / 6, A = pi D^2 / 4) by fixed-step RK4
from `launch_height` until z = 0, landing found by cubic Hermite interpolation on the last step. It returns a
named result with the 1-D float64 arrays `t`, `x`, `z`, `vx`, `vz` (index 0 is the launch; the last sample is
the landing point, z = 0) and the floats `range`, `flight_time` (= t[-1]) and `apex_height` (the maximum
height, refined between samples). FR-002-13: if the rock has not landed by `max_time`, or `max_time /
time_step` exceeds 1e6 steps, `InputError` naming `max_time` (or `time_step`); `time_step` above 0.1 s is a
domain error naming `time_step`.

Oracles (all independent of the code): the vacuum parabola (range v^2 sin 2 theta / g, flight time 2 v sin
theta / g, apex (v sin theta)^2 / 2 g, and with a launch height the quadratic root t_f = (v_z + sqrt(v_z^2 + 2
g h0)) / g; TC-1), the closed form of the vertical launch with quadratic drag (apex (v_t^2 / 2g) ln(1 + v0^2 /
v_t^2) at t = (v_t / g) atan(v0 / v_t), fall back by t = (v_t / g) acosh(exp(g H / v_t^2)); TC-5 and the
printed 72.500448 m, 3.7715338 s of spec 002 section 7.4; TC-2) and energy and monotonicity invariants. SciPy
(DOP853) parity is in `tests/parity/test_t_002_041_flyrock_scipy.py`.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

import minephys
from minephys import blasting as B

G0 = 9.80665


def traj(v=40.0, th=math.pi / 4.0, d=0.1, rho_r=2650.0, cd=0.47, rho_a=1.2, **kw):
    return B.flyrock_trajectory(v, th, d, rho_r, cd, rho_a, **kw)


def terminal_speed_squared(d: float, rho_r: float, cd: float, rho_a: float, g: float = G0) -> float:
    m = rho_r * math.pi * d**3 / 6.0
    area = math.pi * d * d / 4.0
    return 2.0 * m * g / (rho_a * cd * area)


@pytest.mark.req("FR-002-12")
@pytest.mark.req("P-002-10")
@pytest.mark.oracle(
    "analytical", "no drag: the vacuum parabola, range 163.15459 m for 40 m/s at 45 degrees, for any fragment size"
)
@pytest.mark.parametrize("d", [0.02, 0.1, 0.5, 1.0])
def test_drag_free_trajectory_is_the_vacuum_parabola(d: float) -> None:
    r = traj(d=d, cd=0.0)
    vz = 40.0 * math.sin(math.pi / 4.0)
    assert r.range == pytest.approx(1600.0 / G0, rel=1e-12)
    assert r.range == pytest.approx(163.15459, abs=5e-6)  # spec 002 7.4, TC-2
    assert r.flight_time == pytest.approx(2.0 * vz / G0, rel=1e-12)
    assert r.apex_height == pytest.approx(vz * vz / (2.0 * G0), rel=1e-12)


@pytest.mark.req("FR-002-12")
@pytest.mark.oracle(
    "analytical", "the arrays: launch state, equal lengths, landing sample at z = 0, uniform step except the last"
)
def test_result_arrays() -> None:
    r = traj(cd=0.0)
    for name in ("t", "x", "z", "vx", "vz"):
        a = getattr(r, name)
        assert isinstance(a, np.ndarray)
        assert a.dtype == np.float64
        assert a.ndim == 1
        assert a.shape == r.t.shape
    vx0, vz0 = 40.0 * math.cos(math.pi / 4.0), 40.0 * math.sin(math.pi / 4.0)
    assert (r.t[0], r.x[0], r.z[0]) == (0.0, 0.0, 0.0)
    assert r.vx[0] == pytest.approx(vx0, rel=1e-14)
    assert r.vz[0] == pytest.approx(vz0, rel=1e-14)
    assert abs(r.z[-1]) < 1e-9
    assert r.range == r.x[-1]
    assert r.flight_time == r.t[-1]
    steps = np.diff(r.t)
    np.testing.assert_allclose(steps[:-1], 1e-3, rtol=1e-12)
    assert 0.0 < steps[-1] <= 1e-3 * (1.0 + 1e-12)
    assert np.all(r.z[1:-1] > 0.0)
    assert r.z.max() <= r.apex_height + 1e-12
    assert (
        r.apex_height - r.z.max() <= G0 * 1e-6 / 8.0 * 1.01 + 1e-12
    )  # the sampled maximum is within g dt^2 / 8 of the apex
    # drag-free horizontal velocity is constant, vertical velocity decreases by g dt per step
    np.testing.assert_allclose(r.vx, vx0, rtol=1e-12)
    np.testing.assert_allclose(r.vz[:-1], vz0 - G0 * r.t[:-1], rtol=1e-9, atol=1e-9)


@pytest.mark.req("FR-002-12")
@pytest.mark.oracle(
    "analytical", "launch height 5 m at 45 degrees, no drag: t_f = (vz + sqrt(vz^2 + 2 g h0)) / g, range = vx t_f"
)
def test_launch_height_without_drag() -> None:
    vz = 40.0 * math.sin(math.pi / 4.0)
    t_f = (vz + math.sqrt(vz * vz + 2.0 * G0 * 5.0)) / G0
    r = traj(cd=0.0, launch_height=5.0)
    assert r.z[0] == 5.0
    assert r.flight_time == pytest.approx(t_f, rel=1e-12)
    assert r.range == pytest.approx(40.0 * math.cos(math.pi / 4.0) * t_f, rel=1e-12)
    assert r.apex_height == pytest.approx(5.0 + vz * vz / (2.0 * G0), rel=1e-12)


@pytest.mark.req("FR-002-12")
@pytest.mark.oracle(
    "analytical",
    "downward launch (theta = -45 degrees) from 20 m without drag: t_f = (vz + sqrt(vz^2 + 2 g h0)) / g with vz < 0",
)
def test_downward_launch_from_height() -> None:
    vz = -40.0 * math.sin(math.pi / 4.0)
    t_f = (vz + math.sqrt(vz * vz + 2.0 * G0 * 20.0)) / G0
    r = traj(th=-math.pi / 4.0, cd=0.0, launch_height=20.0)
    assert r.flight_time == pytest.approx(t_f, rel=1e-12)
    assert r.range == pytest.approx(40.0 * math.cos(math.pi / 4.0) * t_f, rel=1e-12)
    assert r.apex_height == pytest.approx(20.0, rel=1e-12)  # the launch point is the highest one


@pytest.mark.req("FR-002-12")
@pytest.mark.oracle("analytical", "gravity override: on a body with g = 1.62 the vacuum range is v^2 / g")
def test_gravity_override() -> None:
    assert traj(cd=0.0, g=1.62, max_time=600.0).range == pytest.approx(1600.0 / 1.62, rel=1e-12)


@pytest.mark.req("FR-002-12")
@pytest.mark.req("P-002-10")
@pytest.mark.oracle(
    "hand-calculation", "spec 002 7.4: vertical launch with drag, apex 72.500448 m at 3.7715338 s (closed form)"
)
def test_vertical_launch_with_drag_closed_form() -> None:
    d, rho_r, cd, rho_a, v0 = 0.1, 2650.0, 0.47, 1.2, 40.0
    vt2 = terminal_speed_squared(d, rho_r, cd, rho_a)
    vt = math.sqrt(vt2)
    apex = vt2 / (2.0 * G0) * math.log(1.0 + v0 * v0 / vt2)
    t_apex = vt / G0 * math.atan(v0 / vt)
    t_down = vt / G0 * math.acosh(math.exp(G0 * apex / vt2))
    r = traj(th=math.pi / 2.0)
    assert apex == pytest.approx(72.500448, abs=5e-7)  # the closed form reproduces the printed value (TC-2)
    assert t_apex == pytest.approx(3.7715338, abs=5e-8)
    assert r.apex_height == pytest.approx(apex, rel=1e-6)  # TC-5
    assert r.flight_time == pytest.approx(t_apex + t_down, rel=1e-6)
    assert abs(r.t[int(np.argmax(r.z))] - t_apex) <= 1.5e-3  # the sampled apex is within one step
    assert abs(r.range) < 1e-9
    assert np.max(np.abs(r.vx)) < 1e-12
    assert r.apex_height < 40.0**2 / (2.0 * G0), "less than the vacuum apex 81.577297 m"
    assert r.apex_height == pytest.approx(72.500448, abs=1e-3)


@pytest.mark.req("FR-002-12")
@pytest.mark.req("P-002-10")
@pytest.mark.oracle(
    "analytical", "drag decelerates: vx never increases, mechanical energy never increases, the range is below vacuum"
)
def test_drag_invariants() -> None:
    r = traj()
    m = 2650.0 * math.pi * 0.1**3 / 6.0
    assert np.all(np.diff(r.vx) <= 1e-12)
    assert np.all(r.vx > 0.0)
    energy = 0.5 * m * (r.vx**2 + r.vz**2) + m * G0 * r.z
    assert np.all(np.diff(energy) <= 1e-9 * energy[0])
    assert 0.0 < r.range < 1600.0 / G0
    assert r.flight_time < 2.0 * 40.0 * math.sin(math.pi / 4.0) / G0
    assert r.apex_height < (40.0 * math.sin(math.pi / 4.0)) ** 2 / (2.0 * G0)


@pytest.mark.req("P-002-10")
@pytest.mark.oracle("analytical", "with drag the range increases strictly with the fragment diameter at fixed density")
@pytest.mark.parametrize(("v0", "theta"), [(30.0, 0.5), (30.0, 1.2), (150.0, 0.5), (150.0, 1.2)])
def test_range_increases_with_diameter(v0: float, theta: float) -> None:
    ranges = [traj(v=v0, th=theta, d=d, time_step=5e-3).range for d in (0.05, 0.2, 1.0)]
    vacuum = v0 * v0 * math.sin(2.0 * theta) / G0
    assert ranges[0] < ranges[1] < ranges[2] < vacuum


@pytest.mark.req("FR-002-12")
@pytest.mark.oracle(
    "analytical",
    "a heavier drag coefficient or a lighter rock shortens the throw (ballistic coefficient rho_r D / C_D)",
)
def test_ballistic_coefficient_ordering() -> None:
    base = traj(time_step=5e-3).range
    assert traj(cd=1.0, time_step=5e-3).range < base
    assert traj(rho_r=1500.0, time_step=5e-3).range < base
    assert traj(rho_a=0.6, time_step=5e-3).range > base


@pytest.mark.req("FR-002-12")
@pytest.mark.oracle(
    "analytical", "a coarser step still lands and agrees with the fine step to about 1e-5 relative (RK4)"
)
def test_step_size_convergence() -> None:
    fine = traj(time_step=1e-3)
    coarse = traj(time_step=1e-2)
    assert coarse.range == pytest.approx(fine.range, rel=1e-5)
    assert coarse.flight_time == pytest.approx(fine.flight_time, rel=1e-5)
    assert len(coarse.t) < len(fine.t)


# ---------------------------------------------------------------- FR-002-13


@pytest.mark.req("FR-002-13")
@pytest.mark.oracle(
    "analytical",
    "a vertical launch at 100 m/s stays up for more than 15 s, so max_time = 1 s is an error naming max_time",
)
def test_not_landed_by_max_time() -> None:
    with pytest.raises(minephys.InputError) as ei:
        traj(v=100.0, th=math.pi / 2.0, max_time=1.0)
    assert ei.value.argument == "max_time"
    ok = traj(v=100.0, th=math.pi / 2.0, max_time=60.0)
    assert ok.flight_time < 60.0


@pytest.mark.req("FR-002-13")
@pytest.mark.oracle("analytical", "max_time / time_step above 1e6 steps is refused, whatever the flight time")
@pytest.mark.parametrize(("dt", "t_max"), [(1e-4, 600.0), (1e-3, 1001.0), (1e-6, 10.0), (1e-3, 1e9)])
def test_step_cap(dt: float, t_max: float) -> None:
    assert t_max / dt > 1e6
    with pytest.raises(minephys.InputError) as ei:
        traj(time_step=dt, max_time=t_max)
    assert ei.value.argument in {"max_time", "time_step"}


@pytest.mark.req("FR-002-13")
@pytest.mark.oracle("analytical", "900,000 steps are allowed (the flight itself takes about 5 s)")
def test_cap_is_not_exceeded_below_one_million_steps() -> None:
    r = traj(time_step=1e-3, max_time=900.0)
    assert r.flight_time < 10.0


@pytest.mark.req("FR-002-13")
@pytest.mark.req("FR-002-16")
@pytest.mark.oracle("analytical", "spec 002 7.2: time_step <= 0.1 s; 0.1 s itself is accepted")
@pytest.mark.parametrize("dt", [0.1000001, 0.2, 1.0, 10.0])
def test_time_step_above_a_tenth_of_a_second(dt: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        traj(time_step=dt)
    assert ei.value.argument == "time_step"


@pytest.mark.req("FR-002-12")
@pytest.mark.oracle("analytical", "the largest allowed step still produces a landing sample")
def test_largest_allowed_step() -> None:
    r = traj(time_step=0.1, cd=0.0)
    assert abs(r.z[-1]) < 1e-9
    assert r.range == pytest.approx(1600.0 / G0, rel=1e-9)

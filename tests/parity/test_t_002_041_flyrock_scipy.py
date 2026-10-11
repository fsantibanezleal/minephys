"""T-002-041 (FR-002-12): parity of `flyrock_trajectory` with SciPy's DOP853 integrator for oblique drag cases.

Reference implementation (dev-only dependency, T-002-002): `scipy.integrate.solve_ivp(method="DOP853",
rtol=1e-11, atol=1e-12)` of the same ODE, state (x, z, vx, vz), m dv/dt = -m g z^ - 1/2 rho_a C_D A |v| v with
m = rho_r pi D^3 / 6 and A = pi D^2 / 4, with terminal event z = 0 (landing, downward crossing) and an event
vz = 0 for the apex. Tolerance TC-5 (rtol 1e-6) on range, flight time and apex height. SciPy is imported
inside the test, after the first-party function has been called, so that the failure reason is the missing
implementation.
"""

from __future__ import annotations

import math

import pytest

from minephys import blasting as B

G0 = 9.80665

CASES = [
    # v0, theta, D, rho_r, C_D, rho_a, h0
    (40.0, math.pi / 4.0, 0.1, 2650.0, 0.47, 1.2, 0.0),
    (100.0, 0.6, 0.3, 2650.0, 0.8, 1.2, 10.0),
    (250.0, 1.2, 0.05, 2500.0, 1.0, 1.1, 0.0),
    (60.0, 0.9, 1.0, 2800.0, 1.8, 1.24, 25.0),
    (15.0, -0.4, 0.02, 2650.0, 0.47, 1.2, 30.0),
    (180.0, 0.35, 0.2, 2700.0, 0.6, 0.9, 5.0),
]


def scipy_reference(
    v0: float, th: float, d: float, rho_r: float, cd: float, rho_a: float, h0: float
) -> tuple[float, float, float]:
    import numpy as np
    from scipy.integrate import solve_ivp

    m = rho_r * math.pi * d**3 / 6.0
    k = 0.5 * rho_a * cd * (math.pi * d * d / 4.0) / m

    def rhs(_t: float, y: np.ndarray) -> list[float]:
        _, _, vx, vz = y
        sp = math.hypot(vx, vz)
        return [vx, vz, -k * sp * vx, -G0 - k * sp * vz]

    def landing(_t: float, y: np.ndarray) -> float:
        return y[1]

    landing.terminal = True  # type: ignore[attr-defined]
    landing.direction = -1  # type: ignore[attr-defined]

    def apex(_t: float, y: np.ndarray) -> float:
        return y[3]

    apex.direction = -1  # type: ignore[attr-defined]

    sol = solve_ivp(
        rhs,
        (0.0, 600.0),
        [0.0, h0, v0 * math.cos(th), v0 * math.sin(th)],
        method="DOP853",
        rtol=1e-11,
        atol=1e-12,
        events=[landing, apex],
    )
    assert sol.t_events[0].size == 1, "the reference trajectory must land"
    apex_h = float(sol.y_events[1][0][1]) if sol.t_events[1].size else h0
    return float(sol.y_events[0][0][0]), float(sol.t_events[0][0]), max(apex_h, h0)


@pytest.mark.req("FR-002-12")
@pytest.mark.req("P-002-10")
@pytest.mark.oracle(
    "reference-implementation", "scipy.integrate.solve_ivp, DOP853, rtol 1e-11, atol 1e-12 (TC-5: rtol 1e-6)"
)
@pytest.mark.parametrize(("v0", "th", "d", "rho_r", "cd", "rho_a", "h0"), CASES, ids=lambda v: f"{v}")
def test_oblique_drag_trajectories_match_dop853(
    v0: float, th: float, d: float, rho_r: float, cd: float, rho_a: float, h0: float
) -> None:
    ours = B.flyrock_trajectory(v0, th, d, rho_r, cd, rho_a, launch_height=h0)
    rng, t_flight, apex_h = scipy_reference(v0, th, d, rho_r, cd, rho_a, h0)
    assert ours.range == pytest.approx(rng, rel=1e-6)
    assert ours.flight_time == pytest.approx(t_flight, rel=1e-6)
    assert ours.apex_height == pytest.approx(apex_h, rel=1e-6)


@pytest.mark.req("FR-002-12")
@pytest.mark.oracle(
    "reference-implementation", "the sampled path agrees with the reference at a mid-flight time (TC-5)"
)
def test_mid_flight_state_matches_dop853() -> None:
    import numpy as np
    from scipy.integrate import solve_ivp

    v0, th, d, rho_r, cd, rho_a = 100.0, 0.6, 0.3, 2650.0, 0.8, 1.2
    ours = B.flyrock_trajectory(v0, th, d, rho_r, cd, rho_a, launch_height=10.0)
    m = rho_r * math.pi * d**3 / 6.0
    k = 0.5 * rho_a * cd * (math.pi * d * d / 4.0) / m

    def rhs(_t: float, y: np.ndarray) -> list[float]:
        sp = math.hypot(y[2], y[3])
        return [y[2], y[3], -k * sp * y[2], -G0 - k * sp * y[3]]

    t_mid = 0.5 * ours.flight_time
    i = int(np.argmin(np.abs(ours.t - t_mid)))
    sol_i = solve_ivp(
        rhs,
        (0.0, float(ours.t[i])),
        [0.0, 10.0, v0 * math.cos(th), v0 * math.sin(th)],
        method="DOP853",
        rtol=1e-11,
        atol=1e-12,
    )
    x_ref, z_ref, vx_ref, vz_ref = (float(c[-1]) for c in sol_i.y)
    assert ours.x[i] == pytest.approx(x_ref, rel=1e-6)
    assert ours.z[i] == pytest.approx(z_ref, rel=1e-6)
    assert ours.vx[i] == pytest.approx(vx_ref, rel=1e-6)
    assert ours.vz[i] == pytest.approx(vz_ref, rel=1e-6, abs=1e-9)

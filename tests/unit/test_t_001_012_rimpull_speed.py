"""T-001-012 (FR-001-04, FR-001-05): rimpull- and traction-limited steady speed.

Expected API: `H.rimpull_limited_speed(power, mass, total_resistance, efficiency=1, traction_limit=inf,
speed_limit=inf, drag_area=0, air_density=None, g=9.80665)` -> m/s (float64 / ndarray); optional parameters by keyword.

    v = min(v_ss, speed_limit), v_ss the largest v >= 0 with min(traction_limit, efficiency * power / v)
        >= mass * g * total_resistance + 0.5 * air_density * drag_area * v**2
    without drag and traction limit: v_ss = efficiency * power / (mass * g * total_resistance)
    mass * g * total_resistance > traction_limit  ->  0.0 (FR-001-05)

Oracles: the printed values of spec 001 section 7.4 (TC-2, half a unit in the last printed digit), the closed form
written out below, `numpy.roots` of the cubic 0.5*rho*CdA*v^3 + F0*v - eta*P = 0 as the reference implementation for
the drag case (TC-3, rtol 1e-9), and the traction branch v = sqrt((T - F0) / (0.5*rho*CdA)) (hand calculation).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

G0 = 9.80665
INF = math.inf


def reference(p, m, tr, eta=1.0, t=INF, vmax=INF, cda=0.0, rho=None, g=G0):
    """Independent oracle: closed form without drag, numpy.roots of the cubic with drag, traction branch."""
    f0 = m * g * tr
    if cda == 0.0:
        if f0 > t:
            return 0.0
        return min(eta * p / f0, vmax) if f0 > 0 else vmax
    k = 0.5 * rho * cda
    roots = np.roots([k, 0.0, f0, -eta * p])
    v = max(r.real for r in roots if abs(r.imag) <= 1e-9 * max(1.0, abs(r.real)) and r.real > 0)
    if f0 + k * v * v > t:  # the traction limit binds: drag + rolling = T
        v = math.sqrt((t - f0) / k) if t > f0 else 0.0
    return min(v, vmax)


@pytest.mark.req("FR-001-04")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: 1.8e6 / (400000 * 9.80665 * 0.12) = 3.8239358 m/s")
def test_printed_value() -> None:
    got = H.rimpull_limited_speed(1.8e6, 400000, 0.12)
    assert type(got) is np.float64
    assert got == pytest.approx(3.8239358, abs=5e-8)  # TC-2: 8 significant figures
    assert got == pytest.approx(1.8e6 / (400000 * G0 * 0.12), rel=1e-12)


@pytest.mark.req("FR-001-04")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4 and 8: g = 9.81 gives 3.8226300 m/s, the docs' 3.82 m/s")
def test_docs_worked_example_with_g_9_81() -> None:
    got = H.rimpull_limited_speed(1.8e6, 400000, 0.12, g=9.81)
    assert got == pytest.approx(3.8226300, abs=5e-8)
    assert got == pytest.approx(3.82, abs=5e-3)  # TC-2 on the docs' printed value


@pytest.mark.req("FR-001-04")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: speeds at TR = 0.04, 0.08, 0.16 (inversely proportional to TR)")
@pytest.mark.parametrize(
    ("tr", "printed"),
    [(0.04, 11.471807), (0.08, 5.7359037), (0.16, 2.8679518)],
)
def test_speeds_at_other_resistances(tr: float, printed: float) -> None:
    got = H.rimpull_limited_speed(1.8e6, 400000, tr)
    unit = 10.0 ** -(len(str(printed).split(".")[1]))
    assert got == pytest.approx(printed, abs=0.5 * unit)
    assert got == pytest.approx(1.8e6 / (400000 * G0 * tr), rel=1e-12)


@pytest.mark.req("FR-001-04")
@pytest.mark.oracle("hand-calculation", "efficiency 0.9 scales the power: 0.9 * 3.8239358 = 3.44154222 m/s")
def test_efficiency_scales_the_power() -> None:
    assert H.rimpull_limited_speed(1.8e6, 400000, 0.12, efficiency=0.9) == pytest.approx(0.9 * 3.8239358, abs=1e-7)


@pytest.mark.req("FR-001-04")
@pytest.mark.oracle("hand-calculation", "min(v_ss, speed_limit): the limit binds below v_ss and is ignored above it")
def test_speed_limit() -> None:
    assert H.rimpull_limited_speed(1.8e6, 400000, 0.12, speed_limit=3.0) == 3.0
    assert H.rimpull_limited_speed(1.8e6, 400000, 0.12, speed_limit=10.0) == pytest.approx(3.8239358, abs=5e-8)
    assert H.rimpull_limited_speed(1.8e6, 400000, 0.12, speed_limit=INF) == pytest.approx(3.8239358, abs=5e-8)


@pytest.mark.req("FR-001-04")
@pytest.mark.oracle(
    "hand-calculation", "spec 001 7.4: with drag_area 45 and air density 1.2 (cubic root) 3.8207366 m/s"
)
def test_drag_cubic_printed_value() -> None:
    got = H.rimpull_limited_speed(1.8e6, 400000, 0.12, drag_area=45.0, air_density=1.2)
    assert got == pytest.approx(3.8207366, abs=5e-8)
    assert got == pytest.approx(reference(1.8e6, 400000, 0.12, cda=45.0, rho=1.2), rel=1e-9)
    assert got < H.rimpull_limited_speed(1.8e6, 400000, 0.12), "drag never increases the speed"


@pytest.mark.req("FR-001-04")
@pytest.mark.oracle("reference-implementation", "numpy.roots of 0.5*rho*CdA*v^3 + F0*v - eta*P = 0 (TC-3)")
@pytest.mark.parametrize(
    ("p", "m", "tr", "eta", "cda", "rho"),
    [
        (1.8e6, 400000.0, 0.12, 1.0, 45.0, 1.2),
        (2.5e6, 180000.0, 0.03, 0.85, 60.0, 1.1),
        (5e5, 50000.0, 0.02, 0.9, 10.0, 1.25),
        (1.8e6, 400000.0, 0.0, 1.0, 45.0, 1.2),  # level road without rolling resistance: pure drag
        (1.8e6, 400000.0, -0.05, 1.0, 45.0, 1.2),  # downhill: still a unique positive root
        (1e5, 20000.0, 0.3, 0.5, 100.0, 2.0),
        (1e6, 1e5, 0.01, 1.0, 1e-3, 0.1),  # almost no drag: tends to the closed form
    ],
)
def test_drag_root_against_numpy_roots(p: float, m: float, tr: float, eta: float, cda: float, rho: float) -> None:
    got = H.rimpull_limited_speed(p, m, tr, efficiency=eta, drag_area=cda, air_density=rho)
    assert got == pytest.approx(reference(p, m, tr, eta=eta, cda=cda, rho=rho), rel=1e-9)
    # the defining balance: available force = required force at the returned speed
    assert eta * p / got == pytest.approx(m * G0 * tr + 0.5 * rho * cda * got * got, rel=1e-9)


@pytest.mark.req("FR-001-05")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: traction_limit = 400 kN < m g TR = 470,719.2 N gives 0.0")
def test_stall_on_the_grade() -> None:
    got = H.rimpull_limited_speed(1.8e6, 400000, 0.12, traction_limit=400e3)
    assert got == 0.0
    assert type(got) is np.float64
    assert H.rimpull_limited_speed(1.8e6, 400000, 0.12, traction_limit=400e3, speed_limit=5.0) == 0.0


@pytest.mark.req("FR-001-05")
@pytest.mark.oracle(
    "hand-calculation", "g = 10, mass 1000, TR 0.5: F0 = 5000 N exactly; equality is not exceedance: v = 1e5/5000 = 20"
)
def test_traction_limit_equal_to_the_resistance_force_does_not_stall() -> None:
    assert H.rimpull_limited_speed(1e5, 1000.0, 0.5, traction_limit=5000.0, g=10.0) == pytest.approx(20.0, rel=1e-12)
    assert H.rimpull_limited_speed(1e5, 1000.0, 0.5, traction_limit=4999.999, g=10.0) == 0.0


@pytest.mark.req("FR-001-04")
@pytest.mark.oracle("hand-calculation", "without drag a traction limit above m g TR does not change the speed")
def test_ample_traction_limit_is_inactive_without_drag() -> None:
    assert H.rimpull_limited_speed(1.8e6, 400000, 0.12, traction_limit=500e3) == pytest.approx(3.8239358, abs=5e-8)
    assert H.rimpull_limited_speed(1.8e6, 400000, 0.12, traction_limit=INF) == pytest.approx(3.8239358, abs=5e-8)


@pytest.mark.req("FR-001-04")
@pytest.mark.oracle(
    "hand-calculation", "(470,800 - 470,719.2) / 27 = 2.99259; sqrt = 1.72991 m/s (traction branch with drag)"
)
def test_traction_branch_with_drag() -> None:
    # F0 = 470,719.2 N; 0.5 * 1.2 * 45 = 27; the power-limited speed 3.82 m/s would need 471,113 N > 470,800 N
    got = H.rimpull_limited_speed(1.8e6, 400000, 0.12, drag_area=45.0, air_density=1.2, traction_limit=470800.0)
    assert got == pytest.approx(math.sqrt((470800.0 - 470719.2) / 27.0), rel=1e-9)
    assert got == pytest.approx(1.7299, abs=5e-5)  # TC-2: five significant figures
    ample = H.rimpull_limited_speed(1.8e6, 400000, 0.12, drag_area=45.0, air_density=1.2, traction_limit=472000.0)
    assert ample == pytest.approx(3.8207366, abs=5e-8)
    stalled = H.rimpull_limited_speed(1.8e6, 400000, 0.12, drag_area=45.0, air_density=1.2, traction_limit=470000.0)
    assert stalled == 0.0


@pytest.mark.req("FR-001-04")
@pytest.mark.oracle("hand-calculation", "arrays broadcast elementwise; inputs of every real dtype work")
def test_array_inputs() -> None:
    power = np.array([[1.0e6], [2.0e6]], dtype=np.float32)
    tr = np.array([0.04, 0.08, 0.16], dtype=np.float64)
    out = H.rimpull_limited_speed(power, 400000, tr)
    assert out.shape == (2, 3)
    assert out.dtype == np.float64
    for i in range(2):
        for j in range(3):
            assert out[i, j] == pytest.approx(float(power[i, 0]) / (400000 * G0 * tr[j]), rel=1e-12)
    assert H.rimpull_limited_speed(np.empty(0), 400000, 0.12).shape == (0,)
    assert H.rimpull_limited_speed(np.int64(1_800_000), np.int32(400000), 0.12) == pytest.approx(3.8239358, abs=5e-8)

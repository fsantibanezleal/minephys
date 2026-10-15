"""T-001-013 (FR-001-06): retarder-limited downhill speed.

Expected API: `H.retarder_limited_speed(retarder_power, mass, rolling_resistance, grade, speed_limit=inf,
small_angle=False, g=9.80665)` -> m/s. With the net braking fraction f = -grade_resistance(grade) - rolling_resistance
(exact grade resistance unless `small_angle=True`):

    v = min(retarder_power / (mass * g * f), speed_limit)   for f > 0
    v = speed_limit                                         for f <= 0 (the retarder is not needed)

(`f <= 0` with `speed_limit = inf` is an error, T-001-014.) Oracles: the printed values of spec 001 section 7.4
(TC-2) and the closed form written out in `reference`.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

G0 = 9.80665


def reference(p, m, rr, grade, vmax=math.inf, small=False, g=G0):
    gr = grade if small else grade / math.sqrt(1.0 + grade * grade)
    f = -gr - rr
    return vmax if f <= 0 else min(p / (m * g * f), vmax)


@pytest.mark.req("FR-001-06")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: 2.5e6 / (400000 * 9.80665 * 0.08) = 7.9665329 m/s (small angle)")
def test_printed_value_small_angle() -> None:
    got = H.retarder_limited_speed(2.5e6, 400000, 0.02, -0.10, small_angle=True)
    assert type(got) is np.float64
    assert got == pytest.approx(7.9665329, abs=5e-8)  # TC-2: 8 significant figures
    assert got == pytest.approx(2.5e6 / (400000 * G0 * 0.08), rel=1e-12)


@pytest.mark.req("FR-001-06")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: the empty 180 t truck is 400/180 times faster: 17.703406 m/s")
def test_printed_value_empty_truck() -> None:
    got = H.retarder_limited_speed(2.5e6, 180000, 0.02, -0.10, small_angle=True)
    assert got == pytest.approx(17.703406, abs=5e-7)
    assert got == pytest.approx(7.9665329 * 400000 / 180000, abs=1e-6)


@pytest.mark.req("FR-001-06")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: exact grade resistance 0.099503719 gives 8.0162619 m/s")
def test_printed_value_exact_grade_resistance() -> None:
    got = H.retarder_limited_speed(2.5e6, 400000, 0.02, -0.10)
    assert got == pytest.approx(8.0162619, abs=5e-8)
    assert got == pytest.approx(reference(2.5e6, 400000, 0.02, -0.10), rel=1e-12)
    assert got > H.retarder_limited_speed(2.5e6, 400000, 0.02, -0.10, small_angle=True)


@pytest.mark.req("FR-001-06")
@pytest.mark.oracle("hand-calculation", "min(retarder speed, speed_limit): the limit binds below 7.97 m/s only")
def test_speed_limit_caps_the_result() -> None:
    assert H.retarder_limited_speed(2.5e6, 400000, 0.02, -0.10, speed_limit=5.0, small_angle=True) == 5.0
    assert H.retarder_limited_speed(2.5e6, 400000, 0.02, -0.10, speed_limit=12.0, small_angle=True) == pytest.approx(
        7.9665329, abs=5e-8
    )


@pytest.mark.req("FR-001-06")
@pytest.mark.oracle("hand-calculation", "f <= 0 returns the speed limit: grade -1 %, RR 2 % gives f = -0.01")
@pytest.mark.parametrize(
    ("rr", "grade"),
    [(0.02, -0.01), (0.02, -0.02), (0.0, 0.05), (0.03, 0.0), (0.02, 0.2)],
)
def test_no_braking_needed_returns_the_speed_limit(rr: float, grade: float) -> None:
    # (0.02, -0.02) with small_angle is exactly f = 0.02 - 0.02 = 0 -> not strictly positive -> the limit
    got = H.retarder_limited_speed(2.5e6, 400000, rr, grade, speed_limit=12.0, small_angle=True)
    assert got == 12.0
    assert type(got) is np.float64


@pytest.mark.req("FR-001-06")
@pytest.mark.oracle("hand-calculation", "the exact grade resistance of -0.02 is below 0.02: f = 0.0199... - 0.02 < 0")
def test_exact_grade_makes_the_threshold_slightly_steeper() -> None:
    # GR(-0.02) = -0.0199960..., so f = 0.019996 - 0.02 < 0: still no braking; GR(-0.0201) = -0.0200959 -> f > 0
    assert H.retarder_limited_speed(2.5e6, 400000, 0.02, -0.02, speed_limit=12.0) == 12.0
    assert H.retarder_limited_speed(2.5e6, 400000, 0.02, -0.0201, speed_limit=1e9) < 1e9


@pytest.mark.req("FR-001-06")
@pytest.mark.oracle("analytical", "elementwise over arrays: powers (column) by grades (row)")
def test_array_inputs() -> None:
    p = np.array([[1.0e6], [2.5e6]])
    grade = np.array([-0.05, -0.10, -0.15])
    out = H.retarder_limited_speed(p, 400000, 0.02, grade, speed_limit=40.0)
    assert out.shape == (2, 3)
    for i in range(2):
        for j in range(3):
            assert out[i, j] == pytest.approx(reference(float(p[i, 0]), 400000, 0.02, float(grade[j]), 40.0), rel=1e-12)


@pytest.mark.req("FR-001-06")
@pytest.mark.oracle("analytical", "g override: with g = 9.81 the small-angle value is 2.5e6 / (400000 * 9.81 * 0.08)")
def test_gravity_override() -> None:
    got = H.retarder_limited_speed(2.5e6, 400000, 0.02, -0.10, small_angle=True, g=9.81)
    assert got == pytest.approx(2.5e6 / (400000 * 9.81 * 0.08), rel=1e-12)

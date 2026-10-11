"""T-001-014 (FR-001-07): an unbounded steady speed needs a finite speed limit.

Behaviour (spec 001 FR-001-07): if the steady speed is unbounded and `speed_limit` is +inf, the function raises
`minephys.InputError` whose `argument` is `speed_limit`.

* `rimpull_limited_speed`: unbounded when `total_resistance <= 0` and `drag_area = 0` (drag bounds the speed, so a
  positive drag area never raises);
* `retarder_limited_speed`: unbounded when the net braking fraction `f = -grade_resistance(grade) - rolling_resistance`
  is <= 0.

With a finite `speed_limit` the same inputs return that limit. Oracle: analytical (the steady-state force balance has no
finite solution), the closed-form drag root via `numpy.roots` for the drag case.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

import minephys
from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


@pytest.mark.req("FR-001-07")
@pytest.mark.oracle("analytical", "TR <= 0 without drag: no resisting force, so no finite steady speed")
@pytest.mark.parametrize("tr", [0.0, -0.01, -0.3])
def test_rimpull_with_non_positive_resistance_needs_a_speed_limit(tr: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        H.rimpull_limited_speed(1.8e6, 400000, tr)
    assert ei.value.argument == "speed_limit"
    with pytest.raises(minephys.InputError) as ei2:
        H.rimpull_limited_speed(1.8e6, 400000, tr, speed_limit=math.inf)
    assert ei2.value.argument == "speed_limit"
    assert H.rimpull_limited_speed(1.8e6, 400000, tr, speed_limit=25.0) == 25.0


@pytest.mark.req("FR-001-07")
@pytest.mark.oracle(
    "analytical", "a drag area bounds the speed even on a level, frictionless road: v = (eta P / k)^(1/3)"
)
def test_rimpull_with_drag_is_bounded_without_a_limit() -> None:
    k = 0.5 * 1.2 * 45.0
    expected = (1.8e6 / k) ** (1.0 / 3.0)
    assert H.rimpull_limited_speed(1.8e6, 400000, 0.0, drag_area=45.0, air_density=1.2) == pytest.approx(
        expected, rel=1e-9
    )
    downhill = H.rimpull_limited_speed(1.8e6, 400000, -0.05, drag_area=45.0, air_density=1.2)
    f0 = 400000 * 9.80665 * -0.05
    root = max(r.real for r in np.roots([k, 0.0, f0, -1.8e6]) if abs(r.imag) < 1e-9 and r.real > 0)
    assert downhill == pytest.approx(root, rel=1e-9)
    assert math.isfinite(downhill)


@pytest.mark.req("FR-001-07")
@pytest.mark.oracle("analytical", "no braking needed (f <= 0) and no limit: unbounded")
@pytest.mark.parametrize(("rr", "grade"), [(0.02, -0.01), (0.02, -0.02), (0.0, 0.05), (0.03, 0.0)])
def test_retarder_with_no_braking_need_requires_a_speed_limit(rr: float, grade: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        H.retarder_limited_speed(2.5e6, 400000, rr, grade, small_angle=True)
    assert ei.value.argument == "speed_limit"
    with pytest.raises(minephys.InputError) as ei2:
        H.retarder_limited_speed(2.5e6, 400000, rr, grade, speed_limit=math.inf, small_angle=True)
    assert ei2.value.argument == "speed_limit"
    assert H.retarder_limited_speed(2.5e6, 400000, rr, grade, speed_limit=30.0, small_angle=True) == 30.0


@pytest.mark.req("FR-001-07")
@pytest.mark.oracle("analytical", "a bounded case with the default (infinite) limit does not raise")
def test_bounded_cases_do_not_raise_with_the_default_limit() -> None:
    assert math.isfinite(H.rimpull_limited_speed(1.8e6, 400000, 0.12))
    assert math.isfinite(H.retarder_limited_speed(2.5e6, 400000, 0.02, -0.10, small_angle=True))


@pytest.mark.req("FR-001-07")
@pytest.mark.oracle("analytical", "arrays: one unbounded element is enough to raise when no finite limit is given")
def test_one_unbounded_element_in_an_array_raises() -> None:
    tr = np.array([0.12, 0.08, 0.0])
    with pytest.raises(minephys.InputError) as ei:
        H.rimpull_limited_speed(1.8e6, 400000, tr)
    assert ei.value.argument == "speed_limit"
    out = H.rimpull_limited_speed(1.8e6, 400000, tr, speed_limit=20.0)
    assert out[2] == 20.0
    assert out[0] == pytest.approx(3.8239358, abs=5e-8)
    grade = np.array([-0.10, -0.01])
    with pytest.raises(minephys.InputError) as ei2:
        H.retarder_limited_speed(2.5e6, 400000, 0.02, grade, small_angle=True)
    assert ei2.value.argument == "speed_limit"

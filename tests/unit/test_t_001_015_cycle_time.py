"""T-001-015 (FR-001-10): segment travel time and cycle time.

Expected API: `H.segment_travel_time(length, speed)` -> `length / speed` in s;
`H.cycle_time(spot_load, load, haul_travel, spot_dump, dump, return_travel, queue_load=0, queue_dump=0)` -> the sum of
its eight components in s (the first six required, the two queue components optional; all names are tested as keywords).

Oracles: hand calculation (integer-valued second counts add exactly), the identity time * speed = length, scaling.
Tolerance TC-1 (the sums of integer-valued floats are exact: TC-0).
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

COMPONENTS = ("spot_load", "load", "haul_travel", "spot_dump", "dump", "return_travel", "queue_load", "queue_dump")


@pytest.mark.req("FR-001-10")
@pytest.mark.oracle("hand-calculation", "3000 m at 4 m/s = 750 s; 1000 m at 10 m/s = 100 s")
@pytest.mark.parametrize(
    ("length", "speed", "expected"), [(3000.0, 4.0, 750.0), (1000.0, 10.0, 100.0), (0.0, 5.0, 0.0)]
)
def test_segment_travel_time(length: float, speed: float, expected: float) -> None:
    got = H.segment_travel_time(length, speed)
    assert type(got) is np.float64
    assert got == pytest.approx(expected, rel=1e-12)


@pytest.mark.req("FR-001-10")
@pytest.mark.oracle("hand-calculation", "arrays: lengths (row) over speeds (column)")
def test_segment_travel_time_broadcasts() -> None:
    length = np.array([1000.0, 2000.0, 3000.0])
    speed = np.array([[2.0], [4.0]])
    out = H.segment_travel_time(length, speed)
    assert out.shape == (2, 3)
    np.testing.assert_allclose(out, length / speed, rtol=1e-14, atol=0.0)


@pytest.mark.req("FR-001-10")
@pytest.mark.oracle("hand-calculation", "60 + 240 + 900 + 90 + 45 + 600 + 30 + 15 = 1980 s (all eight components)")
def test_cycle_time_sums_the_eight_components() -> None:
    got = H.cycle_time(
        spot_load=60.0,
        load=240.0,
        haul_travel=900.0,
        spot_dump=90.0,
        dump=45.0,
        return_travel=600.0,
        queue_load=30.0,
        queue_dump=15.0,
    )
    assert type(got) is np.float64
    assert got == 1980.0


@pytest.mark.req("FR-001-10")
@pytest.mark.oracle("hand-calculation", "the queue components default to 0: 60 + 240 + 900 + 90 + 45 + 600 = 1935 s")
def test_queue_components_default_to_zero() -> None:
    assert H.cycle_time(60.0, 240.0, 900.0, 90.0, 45.0, 600.0) == 1935.0
    assert H.cycle_time(60.0, 240.0, 900.0, 90.0, 45.0, 600.0, queue_load=0.0, queue_dump=0.0) == 1935.0


@pytest.mark.req("FR-001-10")
@pytest.mark.oracle(
    "hand-calculation", "each component enters with unit weight: raising one by 1 s raises the sum by 1 s"
)
@pytest.mark.parametrize("name", COMPONENTS)
def test_every_component_counts_exactly_once(name: str) -> None:
    base = dict.fromkeys(COMPONENTS, 0.0)
    assert H.cycle_time(**base) == 0.0
    bumped = dict(base, **{name: 1.0})
    assert H.cycle_time(**bumped) == 1.0


@pytest.mark.req("FR-001-10")
@pytest.mark.oracle(
    "hand-calculation", "a cycle from per-segment travel times: 750 + 100 + 120 s of travel plus 60 + 240 + 45 s"
)
def test_cycle_time_from_segment_times() -> None:
    haul = H.segment_travel_time(3000.0, 4.0) + H.segment_travel_time(1000.0, 10.0)
    ret = H.segment_travel_time(2400.0, 20.0)
    assert H.cycle_time(60.0, 240.0, haul, 0.0, 45.0, ret) == pytest.approx(60 + 240 + 850 + 45 + 120, rel=1e-12)


@pytest.mark.req("FR-001-10")
@pytest.mark.oracle("hand-calculation", "arrays broadcast elementwise")
def test_cycle_time_arrays() -> None:
    haul = np.array([100.0, 200.0, 300.0])
    out = H.cycle_time(10.0, 20.0, haul, 5.0, 6.0, 7.0)
    np.testing.assert_allclose(out, 48.0 + haul, rtol=0.0, atol=0.0)
    assert H.cycle_time(np.empty(0), 1.0, 1.0, 1.0, 1.0, 1.0).shape == (0,)


@pytest.mark.req("FR-001-10")
@pytest.mark.oracle("analytical", "time * speed = length and linear scaling of every component")
@settings(deadline=None)
@given(
    length=st.floats(0.0, 1e5),
    speed=st.floats(0.1, 40.0),
    parts=st.lists(st.floats(0.0, 3600.0), min_size=8, max_size=8),
    k=st.floats(1e-3, 1e3),
)
def test_properties(length: float, speed: float, parts: list[float], k: float) -> None:
    assert H.segment_travel_time(length, speed) * speed == pytest.approx(length, rel=1e-12, abs=1e-12)
    kw = dict(zip(COMPONENTS, parts, strict=True))
    total = H.cycle_time(**kw)
    assert total == pytest.approx(sum(parts), rel=1e-12, abs=1e-12)
    scaled = H.cycle_time(**{n: k * p for n, p in kw.items()})
    assert scaled == pytest.approx(k * total, rel=1e-12, abs=1e-12)
    assert H.segment_travel_time(k * length, speed) == pytest.approx(
        k * H.segment_travel_time(length, speed), rel=1e-12, abs=1e-12
    )

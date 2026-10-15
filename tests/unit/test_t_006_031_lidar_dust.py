"""T-006-031 (FR-006-17): the lidar return state at the published thresholds and the leading edge of a profile.

Expected public API (`minephys.environment`):
    lidar_dust_return(distance, extinction, positions=None, target="retroreflective", onset_transmittance=None, min_transmittance=None)
returns a named tuple or dataclass whose fields, in this order, are
    transmittance (one-way T of the sensor-to-target path), two_way_transmittance (T^2), optical_depth (-ln T), state, and, when
    `positions` is given, leading_edge (distance of the first position with beta > 0, or None when there is none);
the tests read them by position (a tuple) or by declaration order (a dataclass), so the field names are not fixed here.
- uniform `extinction` [1/m] over `distance` [m] (`positions=None`), or, with `positions` running from 0 to `distance`, the
  profile integrated with the trapezoid rule (FR-006-16);
- state "unaffected" where T >= the onset threshold (default 0.74, the upper end of the published 71-74 % band of row
  `lidar_dust_onset_transmittance`), "degraded" where the target minimum <= T < onset (defaults 0.02 for target
  "retroreflective" and 0.06 for "low_reflectivity", rows `lidar_dust_min_transmittance_*`), "lost" where T is below the
  target minimum. The thresholds apply to the one-way transmittance (an interpretation marked UNVERIFIED in spec 006).

Oracles (`phillips2017dust` abstract, as transcribed in spec 006 section 7): optical depths -ln T at the published thresholds,
0.301105 (74 %), 0.342490 (71 %), 2.813411 (6 %), 3.912023 (2 %); uniform beta = 0.01 1/m gives T = 0.8187 at 20 m (unaffected),
0.6703 at 40 m (degraded), 0.0498 at 300 m (degraded for the retroreflective target, lost for the low-reflectivity target) and
0.0183 at 400 m (lost); a profile that is zero before 15 m has its leading edge at 15 m.
"""

from __future__ import annotations

import dataclasses
import importlib
import math
from typing import Any

import numpy as np
import pytest


def _e():
    return importlib.import_module("minephys.environment")


def fields(result: Any) -> list[Any]:
    if isinstance(result, tuple):
        return list(result)
    assert dataclasses.is_dataclass(result), "lidar_dust_return must return a named tuple or a dataclass"
    return [getattr(result, f.name) for f in dataclasses.fields(result)]


def call(distance: float, extinction: Any, **kw: Any) -> list[Any]:
    return fields(_e().lidar_dust_return(distance, extinction, **kw))


@pytest.mark.req("FR-006-17")
@pytest.mark.oracle("hand-calculation", "optical depths at the published thresholds: 0.301105, 0.342490, 2.813411, 3.912023")
@pytest.mark.knowledge("lidar_dust_onset_transmittance")
@pytest.mark.knowledge("lidar_dust_min_transmittance_retroreflective")
@pytest.mark.knowledge("lidar_dust_min_transmittance_low_reflectivity")
def test_fr_006_17_optical_depth_of_the_published_thresholds() -> None:
    for threshold, depth in ((0.74, 0.301105), (0.71, 0.342490), (0.06, 2.813411), (0.02, 3.912023)):
        np.testing.assert_allclose(-math.log(threshold), depth, rtol=0, atol=6e-7)
        res = call(100.0, -math.log(threshold) / 100.0)
        np.testing.assert_allclose(res[0], threshold, rtol=1e-12)  # transmittance
        np.testing.assert_allclose(res[1], threshold**2, rtol=1e-12)  # two-way
        np.testing.assert_allclose(res[2], depth, rtol=0, atol=6e-7)  # optical depth


@pytest.mark.req("FR-006-17")
@pytest.mark.oracle("hand-calculation", "uniform beta = 0.01 1/m: T = exp(-0.01 L) at 20, 40, 300, 400 m")
@pytest.mark.parametrize(
    ("distance", "t_expected", "retro", "low"),
    [
        (20.0, 0.8187, "unaffected", "unaffected"),
        (40.0, 0.6703, "degraded", "degraded"),
        (300.0, 0.0498, "degraded", "lost"),
        (400.0, 0.0183, "lost", "lost"),
    ],
)
def test_fr_006_17_states_for_uniform_extinction(distance: float, t_expected: float, retro: str, low: str) -> None:
    res = call(distance, 0.01)
    t = math.exp(-0.01 * distance)
    np.testing.assert_allclose(res[0], t, rtol=1e-12, atol=0)
    assert abs(res[0] - t_expected) <= 5e-5  # printed to 4 decimals
    np.testing.assert_allclose(res[1], t * t, rtol=1e-12, atol=0)
    np.testing.assert_allclose(res[2], 0.01 * distance, rtol=1e-12, atol=0)
    assert res[3] == retro  # default target is retroreflective
    assert call(distance, 0.01, target="retroreflective")[3] == retro
    assert call(distance, 0.01, target="low_reflectivity")[3] == low
    assert isinstance(res[0], np.float64) and isinstance(res[2], np.float64)


@pytest.mark.req("FR-006-17")
@pytest.mark.oracle("analytical", "the state changes exactly where T crosses a threshold (nudged by 1e-9 in optical depth)")
def test_fr_006_17_state_boundaries() -> None:
    d = 100.0
    onset, retro_min, low_min = 0.74, 0.02, 0.06
    eps = 1e-9
    below = lambda t: (-math.log(t) - eps) / d  # noqa: E731  optical depth just under the threshold's
    above = lambda t: (-math.log(t) + eps) / d  # noqa: E731
    assert call(d, below(onset))[3] == "unaffected" and call(d, above(onset))[3] == "degraded"
    assert call(d, below(retro_min))[3] == "degraded" and call(d, above(retro_min))[3] == "lost"
    assert call(d, below(low_min), target="low_reflectivity")[3] == "degraded"
    assert call(d, above(low_min), target="low_reflectivity")[3] == "lost"
    # no dust at all: unaffected, T = 1, optical depth 0
    res = call(d, 0.0)
    assert res[0] == 1.0 and res[1] == 1.0 and res[2] == 0.0 and res[3] == "unaffected"


@pytest.mark.req("FR-006-17")
def test_fr_006_17_threshold_overrides() -> None:
    d = 100.0
    # T = 0.72 lies inside the published 71-74 % band: degraded with the default onset 0.74, unaffected with 0.71
    assert call(d, (-math.log(0.72)) / d)[3] == "degraded"
    # a caller-supplied onset and minimum replace the defaults
    assert call(d, (-math.log(0.72)) / d, onset_transmittance=0.71)[3] == "unaffected"
    assert call(d, (-math.log(0.70)) / d, onset_transmittance=0.71)[3] == "degraded"
    assert call(d, (-math.log(0.30)) / d, onset_transmittance=0.9, min_transmittance=0.4)[3] == "lost"
    assert call(d, (-math.log(0.50)) / d, onset_transmittance=0.9, min_transmittance=0.4)[3] == "degraded"


@pytest.mark.req("FR-006-17")
@pytest.mark.oracle("hand-calculation", "a profile that is zero before 15 m has its leading edge at 15 m; trapezoid integral by hand")
def test_fr_006_17_profile_and_leading_edge() -> None:
    positions = np.arange(0.0, 101.0, 5.0)
    beta = np.where(positions >= 15.0, 0.01, 0.0)
    res = call(100.0, beta, positions=positions)
    area = 0.5 * (0.0 + 0.01) * 5.0 + 0.01 * 85.0  # ramp between 10 and 15 m, then constant out to 100 m
    t = math.exp(-area)
    np.testing.assert_allclose(res[0], t, rtol=1e-12, atol=0)
    np.testing.assert_allclose(res[1], t * t, rtol=1e-12, atol=0)
    np.testing.assert_allclose(res[2], area, rtol=1e-12, atol=0)
    assert res[3] == "degraded"  # T = 0.417: below the 0.74 onset, above the 0.02 minimum
    assert len(res) == 5 and res[4] == 15.0


@pytest.mark.req("FR-006-17")
def test_fr_006_17_profile_without_dust_has_no_leading_edge() -> None:
    positions = np.linspace(0.0, 50.0, 11)
    res = call(50.0, np.zeros(11), positions=positions)
    assert res[0] == 1.0 and res[3] == "unaffected"
    assert res[4] is None
    # a profile that starts dusty has its leading edge at the sensor
    assert call(50.0, np.full(11, 0.001), positions=positions)[4] == 0.0


@pytest.mark.req("FR-006-17")
@pytest.mark.oracle("analytical", "a constant profile gives the same result as the uniform extinction")
def test_fr_006_17_constant_profile_equals_uniform_extinction() -> None:
    positions = np.array([0.0, 7.0, 30.0, 120.0])
    uniform = call(120.0, 0.008)
    profile = call(120.0, np.full(4, 0.008), positions=positions)
    for a, b in zip(uniform[:4], profile[:4], strict=True):
        if isinstance(a, str):
            assert a == b
        else:
            np.testing.assert_allclose(a, b, rtol=1e-12, atol=0)


@pytest.mark.req("FR-006-17")
def test_fr_006_17_the_two_way_transmittance_is_the_square_and_the_depth_is_minus_ln_t() -> None:
    for beta, d in ((0.0005, 80.0), (0.002, 250.0), (0.05, 5.0)):
        res = call(d, beta)
        np.testing.assert_allclose(res[1], res[0] ** 2, rtol=1e-12, atol=0)
        np.testing.assert_allclose(res[2], -math.log(res[0]), rtol=1e-10, atol=1e-15)

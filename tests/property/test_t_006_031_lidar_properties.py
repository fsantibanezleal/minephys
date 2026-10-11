"""T-006-031 (P-006-12): the lidar state never moves towards "unaffected" as dust or distance increase.

Public API under test (`minephys.environment`): `lidar_dust_return(distance, extinction, positions=None, target=...)`
(see tests/unit/test_t_006_031_lidar_dust.py; fields read by position: transmittance, two-way transmittance, optical depth,
state). Generators: concentrations log-uniform in [1e-10, 1e-2] kg/m^3 converted with k_m = 113.2 m^2/kg (10 um quartz-density
dust), distances in [1, 1000] m, 200 examples.

Relations (TC-0 on the ordered states unaffected < degraded < lost)
- a larger concentration (extinction) never gives a better state; a larger distance never gives a better state;
- the transmittance never increases and the optical depth never decreases along either axis; both targets obey the same order,
  and the low-reflectivity target is never better than the retroreflective one at the same T.
"""

from __future__ import annotations

import dataclasses
import importlib
import math
from typing import Any

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
ORDER = {"unaffected": 0, "degraded": 1, "lost": 2}
KM = 113.207547  # m^2/kg
CONC = st.floats(math.log(1e-10), math.log(1e-2)).map(math.exp)
DIST = st.floats(1.0, 1000.0)
TARGET = st.sampled_from(["retroreflective", "low_reflectivity"])


def _e():
    return importlib.import_module("minephys.environment")


def _fields(result: Any) -> list[Any]:
    if isinstance(result, tuple):
        return list(result)
    return [getattr(result, f.name) for f in dataclasses.fields(result)]


def _ret(d: float, beta: float, target: str) -> list[Any]:
    return _fields(_e().lidar_dust_return(d, beta, target=target))


@pytest.mark.req("P-006-12")
@pytest.mark.oracle("analytical", "T = exp(-beta L) is decreasing in beta and L; thresholds are fixed")
@CI
@given(c1=CONC, c2=CONC, d=DIST, target=TARGET)
def test_p_006_12_more_dust_never_improves_the_state(c1: float, c2: float, d: float, target: str) -> None:
    lo, hi = sorted((c1, c2))
    a, b = _ret(d, KM * lo, target), _ret(d, KM * hi, target)
    assert ORDER[b[3]] >= ORDER[a[3]]
    assert b[0] <= a[0] * (1.0 + 1e-15) and b[2] >= a[2] * (1.0 - 1e-15)


@pytest.mark.req("P-006-12")
@CI
@given(c=CONC, d1=DIST, d2=DIST, target=TARGET)
def test_p_006_12_a_longer_path_never_improves_the_state(c: float, d1: float, d2: float, target: str) -> None:
    lo, hi = sorted((d1, d2))
    a, b = _ret(lo, KM * c, target), _ret(hi, KM * c, target)
    assert ORDER[b[3]] >= ORDER[a[3]]
    assert b[0] <= a[0] * (1.0 + 1e-15)


@pytest.mark.req("P-006-12")
@CI
@given(c=CONC, d=DIST)
def test_p_006_12_the_low_reflectivity_target_is_never_better_than_the_retroreflective_one(c: float, d: float) -> None:
    retro, low = _ret(d, KM * c, "retroreflective"), _ret(d, KM * c, "low_reflectivity")
    assert ORDER[low[3]] >= ORDER[retro[3]]
    np.testing.assert_allclose(low[0], retro[0], rtol=0, atol=0)  # the transmittance does not depend on the target


@pytest.mark.req("P-006-12")
@pytest.mark.req("P-006-10")
@CI
@given(c=CONC, d=DIST, target=TARGET)
def test_p_006_10_two_way_transmittance_is_the_square_of_the_one_way_one(c: float, d: float, target: str) -> None:
    r = _ret(d, KM * c, target)
    np.testing.assert_allclose(r[1], r[0] ** 2, rtol=1e-12, atol=1e-300)
    assert isinstance(r[0], np.float64) and r[3] in ORDER

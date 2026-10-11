"""T-006-052 (NFR-006-03, FR-000-25): one worked-example oracle per function family in the Pyodide smoke subset.

Marked `pyodide`: the CI Pyodide job runs these tests inside Pyodide; they are excluded from the CPython wheel run by
`-m "not gpu and not pyodide and not kit"` (FR-000-24) and also run unchanged on CPython (`pytest -m pyodide`).
One published or hand-derived value per family (API as in the unit tests of T-006-010 to T-006-031):
- AP-42: Table 13.2.2-5 controlled factor (7.1 lb/VMT at 74 % control -> 1.8, `epa2006ap42s1322` p. 13.2.2-16), the fleet-mean
  example 2.36 short tons, and the emission factor at the reference point s = 12 %, W = 3 short tons (exactly k);
- dispersion: ISC3 class D at 1 km (68.126741, 32.093; Tables 1-1 and 1-2) and urban D at 1,000 m (135.224681, 122.788123);
- plume: q = 1e-3, u = 3, sigma_y = 36, sigma_z = 20 at ground level gives 1.47365688e-7 kg/m^3 (hand calculation of plan 006);
- Beer-Lambert and lidar: 1.132075e-4 1/m over 50 m gives T = 0.994356; uniform beta = 0.01 1/m over 300 m is "degraded" for
  the retroreflective target and "lost" for the low-reflectivity one.
"""

from __future__ import annotations

import dataclasses
import importlib
import math

import numpy as np
import pytest

pytestmark = [pytest.mark.pyodide, pytest.mark.req("NFR-006-03")]
ST = 907.18474


def _e():
    return importlib.import_module("minephys.environment")


def _state(result) -> str:
    if isinstance(result, tuple):
        return result[3]
    return getattr(result, dataclasses.fields(result)[3].name)


@pytest.mark.oracle("worked-example", "epa2006ap42s1322 Table 13.2.2-5 (p. 13.2.2-16), the fleet example (p. 13.2.2-6) and the eq. 1a reference point")
def test_nfr_006_03_ap42_family() -> None:
    e = _e()
    assert abs(e.controlled_emission_factor(7.1, 0.74) - 1.8) <= 0.05
    assert abs(e.fleet_mean_vehicle_weight(np.array([2.0 * ST, 20.0 * ST]), np.array([0.98, 0.02])) / ST - 2.4) <= 0.05
    np.testing.assert_allclose(
        e.ap42_unpaved_emission_factor(0.12, 3.0 * ST, "PM10"), 1.5 * 0.45359237 / 1609.344, rtol=1e-12
    )


@pytest.mark.oracle("hand-calculation", "ISC3 Tables 1-1, 1-2 (D at 1 km) and Briggs urban D at 1,000 m")
def test_nfr_006_03_dispersion_family() -> None:
    e = _e()
    sy, sz = e.pasquill_sigmas(1000.0, "D")
    np.testing.assert_allclose([sy, sz], [68.126741, 32.093], rtol=0, atol=6e-7)
    sy, sz = e.pasquill_sigmas(1000.0, "D", terrain="urban")
    np.testing.assert_allclose([sy, sz], [135.224681, 122.788123], rtol=0, atol=6e-7)


@pytest.mark.oracle("hand-calculation", "q / (pi u sigma_y sigma_z) = 1.47365688e-7 kg/m^3")
def test_nfr_006_03_plume_family() -> None:
    e = _e()
    np.testing.assert_allclose(e.gaussian_plume(1e-3, 3.0, 0.0, 0.0, 0.0, 36.0, 20.0), 1.47365688e-7, rtol=1e-8)
    np.testing.assert_allclose(
        e.line_source_plume(6.497274e-6, 3.0, 0.0, 0.0, 20.0), math.sqrt(2 / math.pi) * 6.497274e-6 / 60.0, rtol=1e-12
    )


@pytest.mark.oracle("analytical", "T = exp(-beta L) = 0.994356; lidar states at 300 m with beta = 0.01 1/m")
def test_nfr_006_03_optics_and_lidar_family() -> None:
    e = _e()
    np.testing.assert_allclose(e.beer_lambert_transmittance(1.132075e-4, 50.0), 0.994356, rtol=0, atol=6e-7)
    assert _state(e.lidar_dust_return(300.0, 0.01)) == "degraded"
    assert _state(e.lidar_dust_return(300.0, 0.01, target="low_reflectivity")) == "lost"

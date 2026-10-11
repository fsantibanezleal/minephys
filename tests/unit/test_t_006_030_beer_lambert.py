"""T-006-030 (FR-006-15, FR-006-16): mass extinction, extinction coefficient and path transmittance.

Expected public API (`minephys.environment`, SI):
    mass_extinction_coefficient(diameter, particle_density, extinction_efficiency=None) -> k_m = 3 Q / (2 rho D) [m^2/kg]
        (spheres of diameter D [m], density rho [kg/m^3]; `extinction_efficiency=None` reads the UNVERIFIED knowledge row
        `extinction_efficiency_large_particle` (2) and emits `minephys.knowledge.UnverifiedParameterWarning`)
    extinction_coefficient(mass_concentration, mass_extinction) -> beta = k_m C [1/m]   (C in kg/m^3)
    beer_lambert_transmittance(extinction, path_length)         -> T = exp(-beta L)
    path_transmittance(positions, extinction_profile)           -> T = exp(-integral of beta ds), trapezoid rule over the positions [m]
Arrays broadcast (`path_transmittance` reduces over the profile axis); scalars give `numpy.float64`.

Oracles
- analytical geometry: per particle the extinction cross-section is Q (pi D^2 / 4) and the mass is rho pi D^3 / 6, so
  k_m = 3 Q / (2 rho D): D = 10 um, rho = 2,650 kg/m^3, Q = 2 gives 113.207547 m^2/kg and 1 mg/m^3 gives beta = 1.132075e-4 1/m
  (plan 006); beta = 1.132075e-4 1/m over 50 m gives T = 0.994356;
- the trapezoid rule is exact for piecewise-linear profiles: a ramp beta = a s over [0, L] has the integral a L^2 / 2, and
  an arbitrary piecewise-linear profile is integrated by hand segment by segment.
"""

from __future__ import annotations

import importlib
import math
import warnings

import numpy as np
import pytest


def _e():
    return importlib.import_module("minephys.environment")


def _unverified():
    importlib.import_module("minephys.environment")
    from minephys.knowledge import UnverifiedParameterWarning

    return UnverifiedParameterWarning


@pytest.mark.req("FR-006-15")
@pytest.mark.oracle("analytical", "k_m = 3 Q / (2 rho D) = 113.207547 m^2/kg for D = 10 um, rho = 2,650, Q = 2")
def test_fr_006_15_mass_extinction_coefficient() -> None:
    e = _e()
    got = e.mass_extinction_coefficient(10e-6, 2650.0, 2.0)
    np.testing.assert_allclose(got, 3.0 * 2.0 / (2.0 * 2650.0 * 10e-6), rtol=1e-12, atol=0)
    np.testing.assert_allclose(got, 113.207547, rtol=0, atol=6e-7)
    assert isinstance(got, np.float64)
    # geometry: cross-section Q pi D^2 / 4 over mass rho pi D^3 / 6
    np.testing.assert_allclose(got, 2.0 * (math.pi * (10e-6) ** 2 / 4.0) / (2650.0 * math.pi * (10e-6) ** 3 / 6.0), rtol=1e-12)


@pytest.mark.req("FR-006-15")
@pytest.mark.knowledge("extinction_efficiency_large_particle")
def test_fr_006_15_default_efficiency_is_the_unverified_row_and_warns() -> None:
    e = _e()
    warning = _unverified()
    with pytest.warns(warning) as rec:
        got = e.mass_extinction_coefficient(10e-6, 2650.0)
    np.testing.assert_allclose(got, e.mass_extinction_coefficient(10e-6, 2650.0, 2.0), rtol=1e-12, atol=0)
    assert "extinction_efficiency_large_particle" in " ".join(str(r.message) for r in rec)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        e.mass_extinction_coefficient(10e-6, 2650.0, 2.0)  # an explicit value does not warn


@pytest.mark.req("FR-006-15")
@pytest.mark.oracle("analytical", "beta = k_m C: 1 mg/m^3 of 10 um quartz-density dust is 1.132075e-4 1/m")
def test_fr_006_15_extinction_coefficient() -> None:
    e = _e()
    km = 3.0 * 2.0 / (2.0 * 2650.0 * 10e-6)
    got = e.extinction_coefficient(1e-6, km)  # 1 mg/m^3 = 1e-6 kg/m^3
    np.testing.assert_allclose(got, 1e-6 * km, rtol=1e-12, atol=0)
    np.testing.assert_allclose(got, 1.132075e-4, rtol=0, atol=6e-11)
    out = e.extinction_coefficient(np.array([[0.0], [1e-6]]), np.array([50.0, 100.0]))
    assert out.shape == (2, 2) and out[0].tolist() == [0.0, 0.0]
    np.testing.assert_allclose(out[1], [5e-5, 1e-4], rtol=1e-12)


@pytest.mark.req("FR-006-15")
def test_fr_006_15_scaling_with_diameter_density_and_efficiency() -> None:
    e = _e()
    base = e.mass_extinction_coefficient(10e-6, 2650.0, 2.0)
    np.testing.assert_allclose(e.mass_extinction_coefficient(20e-6, 2650.0, 2.0), base / 2.0, rtol=1e-12)
    np.testing.assert_allclose(e.mass_extinction_coefficient(10e-6, 5300.0, 2.0), base / 2.0, rtol=1e-12)
    np.testing.assert_allclose(e.mass_extinction_coefficient(10e-6, 2650.0, 1.0), base / 2.0, rtol=1e-12)


@pytest.mark.req("FR-006-16")
@pytest.mark.oracle("analytical", "T = exp(-beta L): 1.132075e-4 1/m over 50 m gives 0.994356")
def test_fr_006_16_beer_lambert_transmittance() -> None:
    e = _e()
    got = e.beer_lambert_transmittance(1.132075e-4, 50.0)
    np.testing.assert_allclose(got, math.exp(-1.132075e-4 * 50.0), rtol=1e-12, atol=0)
    np.testing.assert_allclose(got, 0.994356, rtol=0, atol=6e-7)
    assert e.beer_lambert_transmittance(0.0, 100.0) == 1.0 and e.beer_lambert_transmittance(0.5, 0.0) == 1.0
    out = e.beer_lambert_transmittance(np.array([0.01, 0.02]), np.array([[10.0], [100.0]]))
    assert out.shape == (2, 2)
    np.testing.assert_allclose(out, np.exp(-np.array([[0.1, 0.2], [1.0, 2.0]])), rtol=1e-12)


@pytest.mark.req("FR-006-16")
@pytest.mark.oracle("analytical", "the trapezoid rule is exact for linear profiles: integral of a s over [0, L] is a L^2 / 2")
def test_fr_006_16_path_transmittance_of_a_ramp() -> None:
    e = _e()
    a = 2.0e-5
    positions = np.array([0.0, 10.0, 25.0, 60.0, 100.0])  # non-uniform spacing
    got = e.path_transmittance(positions, a * positions)
    np.testing.assert_allclose(got, math.exp(-a * 100.0**2 / 2.0), rtol=1e-12, atol=0)
    assert isinstance(got, np.float64)


@pytest.mark.req("FR-006-16")
@pytest.mark.oracle("hand-calculation", "piecewise-linear profile integrated segment by segment")
def test_fr_006_16_path_transmittance_of_a_piecewise_linear_profile() -> None:
    e = _e()
    positions = np.array([0.0, 5.0, 15.0, 40.0])
    beta = np.array([0.0, 0.01, 0.03, 0.005])
    area = 0.5 * (0.0 + 0.01) * 5.0 + 0.5 * (0.01 + 0.03) * 10.0 + 0.5 * (0.03 + 0.005) * 25.0
    np.testing.assert_allclose(e.path_transmittance(positions, beta), math.exp(-area), rtol=1e-12, atol=0)
    # a constant profile equals the uniform Beer-Lambert law
    np.testing.assert_allclose(
        e.path_transmittance(positions, np.full(4, 0.004)), e.beer_lambert_transmittance(0.004, 40.0), rtol=1e-12, atol=0
    )
    # reversing the sign convention of nothing: a zero profile transmits everything
    assert e.path_transmittance(positions, np.zeros(4)) == 1.0


@pytest.mark.req("FR-006-16")
def test_fr_006_16_inputs_not_modified() -> None:
    e = _e()
    positions = np.array([0.0, 10.0, 30.0])
    beta = np.array([0.001, 0.004, 0.002])
    p0, b0 = positions.copy(), beta.copy()
    e.path_transmittance(positions, beta)
    assert np.array_equal(positions, p0) and np.array_equal(beta, b0)

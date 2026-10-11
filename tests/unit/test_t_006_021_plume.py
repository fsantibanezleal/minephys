"""T-006-021 (FR-006-11, FR-006-12): the point-source Gaussian plume with ground reflection and the optional mixing lid.

Expected public API (`minephys.environment`, SI: q [kg/s], u [m/s], y, z, h, sigma_y, sigma_z, mixing_height [m], C [kg/m^3]):
    gaussian_plume(q, u, y, z, h, sigma_y, sigma_z, mixing_height=None)
        C = q / (2 pi u sigma_y sigma_z) exp(-y^2 / 2 sigma_y^2) V, V = exp(-(z-h)^2 / 2 sigma_z^2) + exp(-(z+h)^2 / 2 sigma_z^2);
        with mixing_height z_i the image series of ISC3 eq. 1-50 is added (terms i = 1, 2, ... until a term is below 1e-16 of the
        sum, at most 1,000 terms), V = sqrt(2 pi) sigma_z / z_i where sigma_z / z_i >= 1.6 (eq. 1-51; row `isc3_lid_uniform_ratio`),
        and C = 0 where h > z_i.
Arrays broadcast; scalars give `numpy.float64`.

Oracles
- hand calculation (plan 006): q = 1e-3 kg/s, u = 3 m/s, sigma_y = 36 m, sigma_z = 20 m, ground-level centreline receptor:
  h = 0 -> q / (pi u sigma_y sigma_z) = 1.47365688e-7 kg/m^3; h = 10 m -> 1.30049763e-7 kg/m^3;
- the image series of the lid written out here as the double-sided sum over i = -N..N of the two reflected Gaussians (an
  independent summation of the same physical image system as ISC3 eq. 1-50), with N large enough that the neglected terms vanish;
- the well-mixed limit: eq. 1-51 V = sqrt(2 pi) sigma_z / z_i, continuous with the series as sigma_z / z_i -> 1.6 (relative
  difference <= 1e-3, spec 006 plan).
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest


def _e():
    return importlib.import_module("minephys.environment")


def point(q, u, y, z, h, sy, sz):
    """Ground-reflection point source, written out."""
    v = math.exp(-((z - h) ** 2) / (2 * sz**2)) + math.exp(-((z + h) ** 2) / (2 * sz**2))
    return q / (2 * math.pi * u * sy * sz) * math.exp(-(y**2) / (2 * sy**2)) * v


def lid_v(z, h, sz, zi, n=60):
    """Image series with ground reflection and a lid at z_i: sum over i of the two reflected Gaussians."""
    return sum(
        math.exp(-((z - h + 2 * i * zi) ** 2) / (2 * sz**2)) + math.exp(-((z + h + 2 * i * zi) ** 2) / (2 * sz**2))
        for i in range(-n, n + 1)
    )


def lid_plume(q, u, y, z, h, sy, sz, zi):
    return q / (2 * math.pi * u * sy * sz) * math.exp(-(y**2) / (2 * sy**2)) * lid_v(z, h, sz, zi)


@pytest.mark.req("FR-006-11")
@pytest.mark.oracle("hand-calculation", "plan 006: q = 1e-3, u = 3, sigma_y = 36, sigma_z = 20: 1.47365688e-7 (h = 0), 1.30049763e-7 (h = 10)")
def test_fr_006_11_ground_level_centreline_hand_values() -> None:
    e = _e()
    c0 = e.gaussian_plume(1e-3, 3.0, 0.0, 0.0, 0.0, 36.0, 20.0)
    np.testing.assert_allclose(c0, 1e-3 / (math.pi * 3.0 * 36.0 * 20.0), rtol=1e-12, atol=0)
    np.testing.assert_allclose(c0, 1.47365688e-7, rtol=1e-8)
    c10 = e.gaussian_plume(1e-3, 3.0, 0.0, 0.0, 10.0, 36.0, 20.0)
    np.testing.assert_allclose(c10, point(1e-3, 3.0, 0.0, 0.0, 10.0, 36.0, 20.0), rtol=1e-12, atol=0)
    np.testing.assert_allclose(c10, 1.30049763e-7, rtol=1e-8)
    assert isinstance(c0, np.float64)


@pytest.mark.req("FR-006-11")
@pytest.mark.oracle("hand-calculation", "the point-source formula evaluated at off-axis, elevated receptors")
@pytest.mark.parametrize(
    ("y", "z", "h"),
    [(15.0, 1.5, 4.0), (-40.0, 30.0, 12.0), (0.0, 50.0, 0.0), (72.0, 0.0, 25.0), (-5.0, 200.0, 100.0)],
)
def test_fr_006_11_general_receptors(y: float, z: float, h: float) -> None:
    e = _e()
    got = e.gaussian_plume(2.5e-3, 4.2, y, z, h, 36.0, 20.0)
    np.testing.assert_allclose(got, point(2.5e-3, 4.2, y, z, h, 36.0, 20.0), rtol=1e-12, atol=1e-300)


@pytest.mark.req("FR-006-11")
def test_fr_006_11_zero_emission_gives_zero_and_arrays_broadcast() -> None:
    e = _e()
    assert e.gaussian_plume(0.0, 3.0, 1.0, 1.0, 5.0, 30.0, 15.0) == 0.0
    y = np.linspace(-90.0, 90.0, 7)[:, None]
    z = np.array([0.0, 2.0, 10.0])[None, :]
    out = e.gaussian_plume(1e-3, 3.0, y, z, 6.0, np.array([30.0]), 15.0)
    assert out.shape == (7, 3) and out.dtype == np.float64
    ref = [[point(1e-3, 3.0, float(yy), float(zz), 6.0, 30.0, 15.0) for zz in (0.0, 2.0, 10.0)] for yy in y[:, 0]]
    np.testing.assert_allclose(out, ref, rtol=1e-12, atol=1e-300)


@pytest.mark.req("FR-006-12")
@pytest.mark.oracle("analytical", "mixing-lid image series: double-sided sum of the reflected Gaussians over i = -60..60")
@pytest.mark.knowledge("isc3_lid_uniform_ratio")
@pytest.mark.parametrize(
    ("y", "z", "h", "sz", "zi"),
    [
        (0.0, 0.0, 10.0, 20.0, 80.0),  # sigma_z / z_i = 0.25
        (12.0, 5.0, 2.0, 40.0, 100.0),  # 0.4
        (0.0, 30.0, 30.0, 60.0, 100.0),  # 0.6
        (-8.0, 10.0, 25.0, 100.0, 100.0),  # 1.0
        (5.0, 60.0, 5.0, 150.0, 100.0),  # 1.5, just below the well-mixed switch
    ],
)
def test_fr_006_12_lid_series(y: float, z: float, h: float, sz: float, zi: float) -> None:
    e = _e()
    got = e.gaussian_plume(1e-3, 3.0, y, z, h, 36.0, sz, mixing_height=zi)
    np.testing.assert_allclose(got, lid_plume(1e-3, 3.0, y, z, h, 36.0, sz, zi), rtol=1e-10, atol=1e-300)
    # the lid can only add material to the unbounded plume
    assert got >= e.gaussian_plume(1e-3, 3.0, y, z, h, 36.0, sz) * (1.0 - 1e-12)


@pytest.mark.req("FR-006-12")
@pytest.mark.oracle("analytical", "eq. 1-51: V = sqrt(2 pi) sigma_z / z_i where sigma_z / z_i >= 1.6")
@pytest.mark.knowledge("isc3_lid_uniform_ratio")
@pytest.mark.parametrize("ratio", [1.6, 1.61, 2.0, 5.0])
def test_fr_006_12_well_mixed_limit(ratio: float) -> None:
    e = _e()
    zi, q, u, sy, y = 100.0, 1e-3, 3.0, 36.0, 10.0
    sz = ratio * zi
    got = e.gaussian_plume(q, u, y, 30.0, 10.0, sy, sz, mixing_height=zi)
    expected = q / (2 * math.pi * u * sy * sz) * math.exp(-(y**2) / (2 * sy**2)) * math.sqrt(2 * math.pi) * sz / zi
    np.testing.assert_allclose(got, expected, rtol=1e-12, atol=0)
    # the vertical coordinate no longer matters
    other = e.gaussian_plume(q, u, y, 0.0, 10.0, sy, sz, mixing_height=zi)
    np.testing.assert_allclose(other, got, rtol=1e-12, atol=0)


@pytest.mark.req("FR-006-12")
@pytest.mark.oracle("analytical", "the series is continuous with the well-mixed value as sigma_z / z_i -> 1.6 (<= 1e-3 relative)")
def test_fr_006_12_continuity_at_the_switch() -> None:
    e = _e()
    zi, q, u, sy = 100.0, 1e-3, 3.0, 36.0
    for z, h in ((0.0, 5.0), (40.0, 40.0), (90.0, 20.0)):
        below = e.gaussian_plume(q, u, 0.0, z, h, sy, 1.5999 * zi, mixing_height=zi)  # series branch
        above = e.gaussian_plume(q, u, 0.0, z, h, sy, 1.6 * zi, mixing_height=zi)  # well-mixed branch
        assert abs(below - above) <= 1e-3 * above


@pytest.mark.req("FR-006-12")
def test_fr_006_12_source_above_the_lid_gives_zero() -> None:
    e = _e()
    assert e.gaussian_plume(1e-3, 3.0, 0.0, 10.0, 150.0, 36.0, 20.0, mixing_height=100.0) == 0.0
    out = e.gaussian_plume(1e-3, 3.0, 0.0, 10.0, np.array([50.0, 150.0]), 36.0, 20.0, mixing_height=100.0)
    assert out[0] > 0.0 and out[1] == 0.0
    # a source exactly at the lid is not above it
    assert e.gaussian_plume(1e-3, 3.0, 0.0, 10.0, 100.0, 36.0, 20.0, mixing_height=100.0) > 0.0


@pytest.mark.req("FR-006-12")
def test_fr_006_12_without_a_lid_the_unbounded_formula_applies() -> None:
    e = _e()
    a = e.gaussian_plume(1e-3, 3.0, 5.0, 10.0, 4.0, 36.0, 20.0)
    b = e.gaussian_plume(1e-3, 3.0, 5.0, 10.0, 4.0, 36.0, 20.0, mixing_height=None)
    assert a == b
    far = e.gaussian_plume(1e-3, 3.0, 5.0, 10.0, 4.0, 36.0, 20.0, mixing_height=1e9)  # a very high lid changes nothing
    np.testing.assert_allclose(far, a, rtol=1e-12, atol=0)

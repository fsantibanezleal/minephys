"""T-006-022 (FR-006-13): infinite and finite crosswind line sources.

Expected public API (`minephys.environment`; q_line [kg/(m s)], u [m/s], y, z, h, y1, y2, sigma_y, sigma_z [m], C [kg/m^3]):
    line_source_plume(q_line, u, z, h, sigma_z)
        C = q_line / (sqrt(2 pi) u sigma_z) V,  V = exp(-(z-h)^2 / 2 sigma_z^2) + exp(-(z+h)^2 / 2 sigma_z^2)
    finite_line_source_plume(q_line, u, y, z, h, y1, y2, sigma_y, sigma_z)
        C = q_line / (2 sqrt(2 pi) u sigma_z) [erf((y2 - y) / (sqrt 2 sigma_y)) - erf((y1 - y) / (sqrt 2 sigma_y))] V
Arrays broadcast; scalars give `numpy.float64`.

Oracles
- analytical: integral of exp(-y^2 / 2 sigma_y^2) over the real line is sqrt(2 pi) sigma_y; the ground-level case (z = h = 0) is
  sqrt(2/pi) q_line / (u sigma_z) = 8.64012e-8 kg/m^3 for q_line = 6.497274e-6 kg/(m s), u = 3 m/s, sigma_z = 20 m (plan 006);
- the erf form against a direct composite-Simpson quadrature of the point-source kernel over the segment (written in the test,
  `math.erf` is not used for the quadrature); rtol 1e-8.
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest


def _e():
    return importlib.import_module("minephys.environment")


def v_term(z: float, h: float, sz: float) -> float:
    return math.exp(-((z - h) ** 2) / (2 * sz**2)) + math.exp(-((z + h) ** 2) / (2 * sz**2))


def point(q, u, y, z, h, sy, sz) -> float:
    return q / (2 * math.pi * u * sy * sz) * math.exp(-(y**2) / (2 * sy**2)) * v_term(z, h, sz)


def simpson(f, a: float, b: float, n: int = 2001) -> float:
    xs = np.linspace(a, b, n)
    fx = np.array([f(float(x)) for x in xs])
    h = (b - a) / (n - 1)
    return float(h / 3.0 * (fx[0] + fx[-1] + 4.0 * fx[1:-1:2].sum() + 2.0 * fx[2:-1:2].sum()))


@pytest.mark.req("FR-006-13")
@pytest.mark.oracle("analytical", "ground-level infinite line source: sqrt(2/pi) q_line / (u sigma_z) = 8.64012e-8 kg/m^3")
def test_fr_006_13_infinite_line_ground_level_case() -> None:
    e = _e()
    got = e.line_source_plume(6.497274e-6, 3.0, 0.0, 0.0, 20.0)
    np.testing.assert_allclose(got, math.sqrt(2.0 / math.pi) * 6.497274e-6 / (3.0 * 20.0), rtol=1e-12, atol=0)
    np.testing.assert_allclose(got, 8.64012e-8, rtol=1e-6)
    assert isinstance(got, np.float64)


@pytest.mark.req("FR-006-13")
@pytest.mark.oracle("hand-calculation", "C = q_line / (sqrt(2 pi) u sigma_z) V at elevated receptors")
@pytest.mark.parametrize(("z", "h", "sz"), [(1.5, 4.0, 12.0), (30.0, 30.0, 25.0), (0.0, 10.0, 8.0), (100.0, 20.0, 60.0)])
def test_fr_006_13_infinite_line_general_receptors(z: float, h: float, sz: float) -> None:
    e = _e()
    got = e.line_source_plume(5.0e-6, 2.5, z, h, sz)
    np.testing.assert_allclose(got, 5.0e-6 / (math.sqrt(2 * math.pi) * 2.5 * sz) * v_term(z, h, sz), rtol=1e-12, atol=1e-300)


@pytest.mark.req("FR-006-13")
@pytest.mark.oracle("reference-implementation", "composite Simpson quadrature of the point-source kernel over y")
def test_fr_006_13_infinite_line_equals_the_integral_of_the_point_kernel() -> None:
    e = _e()
    q, u, sy, sz, z, h = 4.0e-6, 3.0, 28.0, 17.0, 3.0, 6.0
    integral = simpson(lambda s: point(q, u, s, z, h, sy, sz), -12.0 * sy, 12.0 * sy)
    np.testing.assert_allclose(e.line_source_plume(q, u, z, h, sz), integral, rtol=1e-8)


@pytest.mark.req("FR-006-13")
@pytest.mark.oracle("reference-implementation", "composite Simpson quadrature of the point-source kernel over the segment")
@pytest.mark.parametrize(("y", "y1", "y2"), [(0.0, -50.0, 50.0), (30.0, 0.0, 80.0), (-120.0, -100.0, 40.0), (200.0, -10.0, 90.0)])
def test_fr_006_13_finite_line_equals_the_segment_integral(y: float, y1: float, y2: float) -> None:
    e = _e()
    q, u, sy, sz, z, h = 4.0e-6, 3.0, 28.0, 17.0, 3.0, 6.0
    segment = simpson(lambda s: point(q, u, y - s, z, h, sy, sz), y1, y2)
    got = e.finite_line_source_plume(q, u, y, z, h, y1, y2, sy, sz)
    np.testing.assert_allclose(got, segment, rtol=1e-8, atol=1e-300)


@pytest.mark.req("FR-006-13")
@pytest.mark.oracle("hand-calculation", "the erf expression with the standard library's math.erf")
def test_fr_006_13_finite_line_erf_form() -> None:
    e = _e()
    q, u, y, z, h, y1, y2, sy, sz = 6.0e-6, 2.0, 10.0, 2.0, 5.0, -30.0, 70.0, 35.0, 15.0
    erf_diff = math.erf((y2 - y) / (math.sqrt(2) * sy)) - math.erf((y1 - y) / (math.sqrt(2) * sy))
    expected = q / (2 * math.sqrt(2 * math.pi) * u * sz) * erf_diff * v_term(z, h, sz)
    np.testing.assert_allclose(e.finite_line_source_plume(q, u, y, z, h, y1, y2, sy, sz), expected, rtol=1e-12, atol=0)


@pytest.mark.req("FR-006-13")
@pytest.mark.oracle("analytical", "a segment much longer than sigma_y tends to the infinite line (<= 1e-12 relative)")
def test_fr_006_13_long_segment_limit() -> None:
    e = _e()
    q, u, z, h, sy, sz = 5.0e-6, 3.0, 2.0, 4.0, 30.0, 14.0
    infinite = e.line_source_plume(q, u, z, h, sz)
    for y in (-60.0, 0.0, 45.0):
        finite = e.finite_line_source_plume(q, u, y, z, h, y - 10.0 * sy, y + 10.0 * sy, sy, sz)
        np.testing.assert_allclose(finite, infinite, rtol=1e-12, atol=0)


@pytest.mark.req("FR-006-13")
@pytest.mark.oracle("analytical", "adjacent segments add: finite(y1, y2) + finite(y2, y3) = finite(y1, y3)")
def test_fr_006_13_adjacent_segments_are_additive() -> None:
    e = _e()
    args = (5.0e-6, 3.0, 12.0, 2.0, 4.0)
    sy, sz = 30.0, 14.0
    whole = e.finite_line_source_plume(*args, -40.0, 90.0, sy, sz)
    parts = e.finite_line_source_plume(*args, -40.0, 25.0, sy, sz) + e.finite_line_source_plume(*args, 25.0, 90.0, sy, sz)
    np.testing.assert_allclose(parts, whole, rtol=1e-12, atol=0)


@pytest.mark.req("FR-006-13")
def test_fr_006_13_arrays_broadcast() -> None:
    e = _e()
    z = np.array([0.0, 2.0, 10.0])
    out = e.line_source_plume(5.0e-6, np.array([[2.0], [4.0]]), z, 4.0, 14.0)
    assert out.shape == (2, 3) and out.dtype == np.float64
    np.testing.assert_allclose(out[0], 2.0 * out[1], rtol=1e-12)
    fin = e.finite_line_source_plume(5.0e-6, 3.0, np.linspace(-80, 80, 5)[:, None], z[None, :], 4.0, -30.0, 30.0, 25.0, 14.0)
    assert fin.shape == (5, 3)
    assert np.allclose(fin[:, 0], fin[::-1, 0], rtol=1e-12, atol=0)  # a symmetric segment gives a symmetric field

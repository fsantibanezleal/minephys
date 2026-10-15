# ruff: noqa: E501
"""T-004-011 (FR-004-03, FR-004-04): repose-angle stockpile geometry (cone and prismatic ridge).

Expected API, module `minephys.bulk` (elementwise, float64; a scalar call gives a NumPy float64):

    repose_cone_height(base_radius, repose_angle) -> r tan(phi)                [m]
    repose_cone_volume(base_radius, repose_angle) -> (pi / 3) r^3 tan(phi)     [m^3]
    repose_ridge_volume(base_half_width, repose_angle, length, end_cones=False) -> r^2 tan(phi) length  [m^3]
        plus (pi / 3) r^3 tan(phi) (the two half-cones of the ends) when `end_cones` is True.
    base_radius, base_half_width, length > 0 ([m]; `length` = 0 is allowed for the ridge: spec 7.2 gives length >=
    0), 0 < phi < pi / 2 [rad]; `end_cones` is a boolean flag (anything else is an `InputTypeError` naming it).

Oracles: spec 004 section 7.4 (r = 30 m, phi = 37 deg: height 22.606622 m, cone 21,306.239 m^3, ridge of
length 100 m 67,819.865 m^3 and 89,126.103 m^3 with end cones; TC-2), the geometry of the solids written
independently in this file (a numerical integral of the cone's cross-section areas with SciPy `quad` as the
reference implementation, the shoelace area of the ridge triangle, the 45-degree cone whose height equals its
radius), and the symmetry that two half-cones make one cone (TC-1).
"""

from __future__ import annotations

import inspect
import math

import numpy as np
import pytest

import minephys
from minephys import bulk as B

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

PHI37 = math.radians(37.0)


@pytest.mark.req("FR-004-03")
@pytest.mark.oracle("hand-calculation", "spec 004 7.4: r = 30 m, 37 deg: height 22.606622 m, volume 21,306.239 m^3")
def test_spec_cone() -> None:
    h = B.repose_cone_height(30.0, PHI37)
    v = B.repose_cone_volume(30.0, PHI37)
    assert type(h) is np.float64
    assert type(v) is np.float64
    assert h == pytest.approx(22.606622, abs=5e-7)  # TC-2
    assert v == pytest.approx(21_306.239, abs=5e-4)  # TC-2


@pytest.mark.req("FR-004-04")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 7.4: ridge of 30 m half-width, 37 deg, 100 m long: 67,819.865 m^3; with end cones 89,126.103 m^3",
)
def test_spec_ridge() -> None:
    plain = B.repose_ridge_volume(30.0, PHI37, 100.0)
    capped = B.repose_ridge_volume(30.0, PHI37, 100.0, end_cones=True)
    assert type(plain) is np.float64
    assert plain == pytest.approx(67_819.865, abs=5e-4)  # TC-2
    assert capped == pytest.approx(89_126.103, abs=5e-4)  # TC-2
    assert capped - plain == pytest.approx(float(B.repose_cone_volume(30.0, PHI37)), rel=1e-12)


@pytest.mark.req("FR-004-03")
@pytest.mark.oracle("analytical", "a 45 degree heap is as high as it is wide: height = radius (tan 45 deg = 1)")
@pytest.mark.parametrize("r", [0.1, 1.0, 30.0, 500.0])
def test_forty_five_degrees(r: float) -> None:
    assert B.repose_cone_height(r, math.pi / 4.0) == pytest.approx(r, rel=1e-15)
    assert B.repose_cone_volume(r, math.pi / 4.0) == pytest.approx(math.pi / 3.0 * r**3, rel=1e-15)


@pytest.mark.req("FR-004-03")
@pytest.mark.oracle(
    "reference-implementation",
    "scipy.integrate.quad of the cone's circular cross-sections: V = integral of pi (r (1 - z / h))^2 dz from 0 to h",
)
@pytest.mark.parametrize(("r", "phi"), [(30.0, PHI37), (2.5, 0.3), (120.0, 1.2), (0.4, 0.6)])
def test_cone_volume_by_numerical_integration(r: float, phi: float) -> None:
    from scipy.integrate import quad

    h = r * math.tan(phi)
    integral, _ = quad(lambda z: math.pi * (r * (1.0 - z / h)) ** 2, 0.0, h, epsabs=0.0, epsrel=1e-13)
    assert B.repose_cone_volume(r, phi) == pytest.approx(integral, rel=1e-10)
    assert B.repose_cone_height(r, phi) == pytest.approx(h, rel=1e-14)


@pytest.mark.req("FR-004-03")
@pytest.mark.oracle("analytical", "volume of a cone = one third of the base area times the height")
@pytest.mark.parametrize(("r", "phi"), [(30.0, PHI37), (2.5, 0.3), (120.0, 1.2), (0.4, 0.05), (7.0, 1.5)])
def test_cone_volume_is_base_area_times_height_over_three(r: float, phi: float) -> None:
    base_area = math.pi * r * r
    assert B.repose_cone_volume(r, phi) == pytest.approx(
        base_area * float(B.repose_cone_height(r, phi)) / 3.0, rel=1e-13
    )


@pytest.mark.req("FR-004-04")
@pytest.mark.oracle(
    "analytical",
    "the ridge cross-section is the triangle (-r, 0), (r, 0), (0, r tan phi): shoelace area r^2 tan phi; volume = area x length",
)
@pytest.mark.parametrize(
    ("r", "phi", "length"), [(30.0, PHI37, 100.0), (2.0, 0.5, 7.5), (15.0, 1.3, 1e3), (0.5, 0.1, 0.01)]
)
def test_ridge_by_shoelace(r: float, phi: float, length: float) -> None:
    h = r * math.tan(phi)
    pts = [(-r, 0.0), (r, 0.0), (0.0, h)]
    area = 0.5 * abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1], strict=True)))
    assert B.repose_ridge_volume(r, phi, length) == pytest.approx(area * length, rel=1e-13)
    assert B.repose_ridge_volume(r, phi, length, end_cones=True) == pytest.approx(
        area * length + math.pi / 3.0 * r**3 * math.tan(phi), rel=1e-13
    )


@pytest.mark.req("FR-004-04")
@pytest.mark.oracle(
    "analytical", "the two half-cones at the ends are one full cone: capped - plain = cone volume, for every length"
)
@pytest.mark.parametrize("length", [0.0, 1.0, 55.5, 1e4])
def test_end_cones_are_one_cone(length: float) -> None:
    r, phi = 12.0, 0.7
    diff = float(B.repose_ridge_volume(r, phi, length, True)) - float(B.repose_ridge_volume(r, phi, length, False))
    assert diff == pytest.approx(float(B.repose_cone_volume(r, phi)), rel=1e-12)


@pytest.mark.req("FR-004-04")
@pytest.mark.oracle(
    "analytical",
    "length = 0 is allowed (spec 7.2: length >= 0): a ridge without length is just its end cones or nothing",
)
def test_zero_length_ridge() -> None:
    assert B.repose_ridge_volume(12.0, 0.7, 0.0) == 0.0
    assert B.repose_ridge_volume(12.0, 0.7, 0.0, end_cones=True) == pytest.approx(
        float(B.repose_cone_volume(12.0, 0.7)), rel=1e-14
    )


@pytest.mark.req("FR-004-04")
@pytest.mark.oracle("analytical", "end_cones defaults to False and is a boolean flag")
def test_end_cones_flag() -> None:
    params = inspect.signature(B.repose_ridge_volume).parameters
    assert list(params) == ["base_half_width", "repose_angle", "length", "end_cones"]
    assert params["end_cones"].default is False
    assert B.repose_ridge_volume(30.0, PHI37, 100.0) == B.repose_ridge_volume(30.0, PHI37, 100.0, end_cones=False)
    for bad in (0, 1, 1.0, "yes", None, 2):
        with pytest.raises(minephys.InputTypeError) as ei:
            B.repose_ridge_volume(30.0, PHI37, 100.0, end_cones=bad)
        assert ei.value.argument == "end_cones"
    for ok in (True, False):
        assert B.repose_ridge_volume(30.0, PHI37, 100.0, end_cones=ok) > 0.0


@pytest.mark.req("FR-004-03")
@pytest.mark.req("FR-004-04")
@pytest.mark.oracle(
    "analytical", "elementwise over broadcast arrays; the heap grows with the angle and with the radius"
)
def test_arrays() -> None:
    r = np.array([[10.0], [20.0]])
    phi = np.array([0.4, 0.6, 0.8])
    h = B.repose_cone_height(r, phi)
    v = B.repose_cone_volume(r, phi)
    assert h.shape == v.shape == (2, 3)
    assert h.dtype == v.dtype == np.float64
    np.testing.assert_allclose(h, r * np.tan(phi), rtol=1e-14)
    np.testing.assert_allclose(v, np.pi / 3.0 * r**3 * np.tan(phi), rtol=1e-14)
    assert np.all(np.diff(v, axis=0) > 0)
    assert np.all(np.diff(v, axis=1) > 0)
    ridge = B.repose_ridge_volume(r, phi, np.array([100.0, 200.0, 300.0]), end_cones=True)
    assert ridge.shape == (2, 3)
    np.testing.assert_allclose(
        ridge, r**2 * np.tan(phi) * np.array([100.0, 200.0, 300.0]) + np.pi / 3.0 * r**3 * np.tan(phi), rtol=1e-14
    )


@pytest.mark.req("FR-004-03")
@pytest.mark.oracle("analytical", "very flat and very steep heaps stay finite and ordered (phi near 0 and near pi/2)")
def test_extreme_angles() -> None:
    flat = float(B.repose_cone_volume(10.0, 1e-9))
    assert flat == pytest.approx(math.pi / 3.0 * 1e3 * 1e-9, rel=1e-8)
    steep = float(B.repose_cone_volume(10.0, math.pi / 2.0 - 1e-9))
    assert math.isfinite(steep)
    assert steep > float(B.repose_cone_volume(10.0, 1.5))

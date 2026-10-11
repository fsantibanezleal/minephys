# ruff: noqa: E501
"""T-003-020 (FR-003-07, FR-003-08): circular slices from a ground polyline.

Expected API: `G.circular_slices(surface_x, surface_z, center_x, center_z, radius, n_slices, unit_weight,
pore_pressure_ratio=0)` (lengths in m, unit weight in N/m^3) cuts the mass between the ground polyline and the
circle into `n_slices` EQUAL-width vertical slices between the two intersection points and returns a named
result of float64 arrays of length `n_slices`:
    width          b = (x_exit - x_entry) / n                                    [m] weight         gamma * b * h,
    h the height at the slice MID-point (ground minus the lower arc)   [N/m] base_angle     alpha_i = -asin((x_mid
    - x_c) / R), the inclination of the circle at the slice mid-point; the global sign
                   is chosen so that the driving moment sum(W sin alpha) is positive                   [rad]
    base_length    b / cos(alpha)                                                [m]
    pore_pressure  r_u * gamma * h                                               [Pa]
FR-003-08: `surface_x` not strictly increasing, a circle that does not cut the polyline at exactly two points,
or `n_slices` outside 2..10,000 raises `InputError` naming the argument (for the circle: `center_x`,
`center_z` or `radius`).

Oracles (independent of the code): the area of a circular segment, A = R^2 acos(d/R) - d sqrt(R^2 - d^2) (flat
ground at distance d below the centre), against the sum of the slice weights (midpoint rule, rtol 1e-6 at
2,000 slices); the geometry of the Fredlund and Krahn (1977) problem as given in Slide verification problem
#21 (ground (0, 60), (60, 60), (140, 20), (180, 20) ft; circle centre (120, 90) ft, R = 80 ft; gamma = 120
pcf), converted with the exact definitions 1 ft = 0.3048 m and 1 lbf = 0.45359237 kg * 9.80665 m/s^2, whose
slices are recomputed here from first principles.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

import minephys
from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

FT = 0.3048
LBF = 0.45359237 * 9.80665
GAMMA = 120.0 * LBF / FT**3  # 120 pcf in N/m^3
FK_X = np.array([0.0, 60.0, 140.0, 180.0]) * FT
FK_Z = np.array([60.0, 60.0, 20.0, 20.0]) * FT
FK_CX, FK_CZ, FK_R = 120.0 * FT, 90.0 * FT, 80.0 * FT
X_ENTRY = (120.0 - math.sqrt(80.0**2 - 30.0**2)) * FT  # circle meets the crest z = 60 ft
X_EXIT = (120.0 + math.sqrt(80.0**2 - 70.0**2)) * FT  # circle meets the toe bench z = 20 ft


def fk(n: int = 100, ru: float = 0.0):
    return G.circular_slices(FK_X, FK_Z, FK_CX, FK_CZ, FK_R, n, GAMMA, ru)


@pytest.mark.req("FR-003-07")
@pytest.mark.oracle(
    "analytical",
    "flat ground 5 m below the centre of a 10 m circle: segment area R^2 acos(d/R) - d sqrt(R^2 - d^2) = 61.4185 m^2",
)
def test_slice_weights_add_up_to_the_circular_segment() -> None:
    r, d, gamma = 10.0, 5.0, 20000.0
    area = r * r * math.acos(d / r) - d * math.sqrt(r * r - d * d)
    s = G.circular_slices([-30.0, 30.0], [0.0, 0.0], 0.0, d, r, 2000, gamma)
    assert float(np.sum(s.weight)) == pytest.approx(gamma * area, rel=1e-6)
    chord = 2.0 * math.sqrt(r * r - d * d)
    assert float(np.sum(s.width)) == pytest.approx(chord, rel=1e-12)
    np.testing.assert_allclose(s.width, chord / 2000.0, rtol=1e-12)


@pytest.mark.req("FR-003-07")
@pytest.mark.oracle("analytical", "result arrays: float64, length n, and the closed relations between them")
def test_result_arrays_and_relations() -> None:
    s = G.circular_slices([-30.0, 30.0], [0.0, 0.0], 0.0, 5.0, 10.0, 40, 20000.0, 0.25)
    for name in ("width", "weight", "base_angle", "base_length", "pore_pressure"):
        a = getattr(s, name)
        assert isinstance(a, np.ndarray)
        assert a.dtype == np.float64
        assert a.shape == (40,)
    h = s.weight / (20000.0 * s.width)
    assert np.all(h > 0.0)
    np.testing.assert_allclose(s.base_length, s.width / np.cos(s.base_angle), rtol=1e-12)
    np.testing.assert_allclose(s.pore_pressure, 0.25 * 20000.0 * h, rtol=1e-12)
    assert np.all(np.abs(s.base_angle) < math.pi / 2.0)
    # flat ground: the slice heights follow the lower arc, symmetric about the centre
    np.testing.assert_allclose(h, h[::-1], rtol=1e-12)
    half = math.sqrt(75.0)  # half of the chord: sqrt(R^2 - d^2)
    mid_x = -half + (np.arange(40) + 0.5) * (2.0 * half / 40.0)
    np.testing.assert_allclose(np.abs(s.base_angle), np.arcsin(np.abs(mid_x) / 10.0), rtol=1e-12)
    np.testing.assert_allclose(h, np.sqrt(100.0 - mid_x**2) - 5.0, rtol=1e-12)


@pytest.mark.req("FR-003-07")
@pytest.mark.oracle(
    "analytical", "zero pore pressure ratio (the default) gives zero pore pressure; r_u scales it linearly"
)
def test_pore_pressure_ratio() -> None:
    dry = G.circular_slices([-30.0, 30.0], [0.0, 0.0], 0.0, 5.0, 10.0, 10, 20000.0)
    assert np.all(dry.pore_pressure == 0.0)
    wet = G.circular_slices([-30.0, 30.0], [0.0, 0.0], 0.0, 5.0, 10.0, 10, 20000.0, pore_pressure_ratio=0.5)
    np.testing.assert_allclose(wet.pore_pressure, 0.5 * 20000.0 * wet.weight / (20000.0 * wet.width), rtol=1e-12)
    np.testing.assert_array_equal(wet.weight, dry.weight)


@pytest.mark.req("FR-003-07")
@pytest.mark.oracle(
    "worked-example",
    "fredlund1977 as slide verification problem 21 pp. 91-92: entry x = 120 - sqrt(80^2 - 30^2) ft, exit x = 120 + sqrt(80^2 - 70^2) ft, 100 equal slices",
)
def test_fredlund_krahn_geometry() -> None:
    s = fk()
    b = (X_EXIT - X_ENTRY) / 100.0
    np.testing.assert_allclose(s.width, b, rtol=1e-12)
    xm = X_ENTRY + b * (np.arange(100) + 0.5)
    ground = np.interp(xm, FK_X, FK_Z)
    arc = FK_CZ - np.sqrt(FK_R**2 - (xm - FK_CX) ** 2)
    h = ground - arc
    np.testing.assert_allclose(s.weight, GAMMA * b * h, rtol=1e-12)
    np.testing.assert_allclose(np.abs(s.base_angle), np.arcsin(np.abs(xm - FK_CX) / FK_R), rtol=1e-12)
    np.testing.assert_allclose(s.base_length, b / np.cos(s.base_angle), rtol=1e-12)


@pytest.mark.req("FR-003-07")
@pytest.mark.oracle(
    "analytical",
    "sign convention: the driving moment sum(W sin alpha) is positive, the sliding side is the left (higher) side",
)
def test_base_angle_sign_makes_the_driving_moment_positive() -> None:
    s = fk()
    assert float(np.sum(s.weight * np.sin(s.base_angle))) > 0.0
    assert s.base_angle[0] > 0.0 > s.base_angle[-1]
    assert np.all(np.diff(s.base_angle) < 0.0), "the base inclination decreases monotonically along the circle"
    assert math.degrees(float(s.base_angle[0])) == pytest.approx(66.92, abs=0.05)  # steep entry flank
    assert math.degrees(float(s.base_angle[-1])) == pytest.approx(-28.49, abs=0.05)  # rising toe flank


@pytest.mark.req("FR-003-07")
@pytest.mark.oracle(
    "analytical",
    "mirroring the problem (x -> -x) reverses the slice order and keeps weights and signed base angles (the sign follows the sliding side)",
)
def test_mirror_symmetry() -> None:
    a = fk()
    b = G.circular_slices(-FK_X[::-1], FK_Z[::-1], -FK_CX, FK_CZ, FK_R, 100, GAMMA)
    np.testing.assert_allclose(b.weight, a.weight[::-1], rtol=1e-12)
    np.testing.assert_allclose(b.base_angle, a.base_angle[::-1], rtol=1e-12)
    np.testing.assert_allclose(b.width, a.width, rtol=1e-12)


@pytest.mark.req("FR-003-07")
@pytest.mark.oracle("analytical", "two slices and 10,000 slices are the allowed extremes")
def test_slice_count_extremes() -> None:
    two = fk(2)
    assert two.width.shape == (2,)
    many = fk(10_000)
    assert many.weight.shape == (10_000,)
    assert float(np.sum(many.weight)) == pytest.approx(float(np.sum(fk(1000).weight)), rel=1e-5)


@pytest.mark.req("FR-003-08")
@pytest.mark.oracle("analytical", "the abscissas of the ground must be strictly increasing")
@pytest.mark.parametrize(
    "xs",
    [
        [0.0, 0.0, 100.0],
        [0.0, 60.0, 50.0, 100.0],
        [100.0, 0.0],
        [0.0, 10.0, 10.0],
        [0.0, math.nan, 100.0],
        [0.0, 50.0, math.inf],
    ],
)
def test_surface_x_must_increase_strictly(xs: list[float]) -> None:
    zs = [0.0] * len(xs)
    with pytest.raises(minephys.InputError) as ei:
        G.circular_slices(xs, zs, 50.0, 5.0, 10.0, 20, 20000.0)
    assert ei.value.argument == "surface_x"


@pytest.mark.req("FR-003-08")
@pytest.mark.oracle("analytical", "at least two points, equal lengths, 1-D")
def test_surface_polyline_shape() -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.circular_slices([0.0], [0.0], 50.0, 5.0, 10.0, 20, 20000.0)
    assert ei.value.argument in {"surface_x", "surface_z"}
    with pytest.raises(minephys.InputError) as ei2:
        G.circular_slices([0.0, 50.0, 100.0], [0.0, 0.0], 50.0, 5.0, 10.0, 20, 20000.0)
    assert ei2.value.argument in {"surface_x", "surface_z"}
    with pytest.raises(minephys.InputError) as ei3:
        G.circular_slices([[0.0, 100.0]], [[0.0, 0.0]], 50.0, 5.0, 10.0, 20, 20000.0)
    assert ei3.value.argument in {"surface_x", "surface_z"}


@pytest.mark.req("FR-003-08")
@pytest.mark.oracle(
    "analytical", "a circle must cut the polyline at exactly two points: none, one (tangent) and four are errors"
)
@pytest.mark.parametrize(
    ("xs", "zs", "cx", "cz", "r"),
    [
        ([0.0, 100.0], [0.0, 0.0], 50.0, 5.0, 3.0),  # entirely above the ground: no cut
        ([0.0, 100.0], [0.0, 0.0], 50.0, 200.0, 10.0),  # far above
        ([0.0, 100.0], [0.0, 0.0], 50.0, 5.0, 5.0),  # tangent: one point
        ([0.0, 100.0], [0.0, 0.0], 500.0, 5.0, 10.0),  # beside the polyline
        ([-20.0, -5.0, 0.0, 5.0, 20.0], [0.0, 0.0, 12.0, 0.0, 0.0], 0.0, 2.0, 6.0),  # a spike makes four cuts
        ([0.0, 10.0], [0.0, 0.0], 5.0, 0.0, 50.0),  # the polyline lies inside the circle: no cut
    ],
)
def test_circle_must_cut_the_ground_twice(xs: list[float], zs: list[float], cx: float, cz: float, r: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.circular_slices(xs, zs, cx, cz, r, 20, 20000.0)
    assert ei.value.argument in {"center_x", "center_z", "radius"}


@pytest.mark.req("FR-003-08")
@pytest.mark.oracle("analytical", "n_slices is an integer from 2 to 10,000")
@pytest.mark.parametrize("n", [0, 1, -5, 10_001, 10**9, 2.5, math.nan])
def test_slice_count_domain(n: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.circular_slices([-30.0, 30.0], [0.0, 0.0], 0.0, 5.0, 10.0, n, 20000.0)
    assert ei.value.argument == "n_slices"


@pytest.mark.req("FR-003-08")
@pytest.mark.oracle("analytical", "a boolean or a string is not a count")
@pytest.mark.parametrize("n", [True, "20", None])
def test_slice_count_type(n) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        G.circular_slices([-30.0, 30.0], [0.0, 0.0], 0.0, 5.0, 10.0, n, 20000.0)
    assert ei.value.argument == "n_slices"


@pytest.mark.req("FR-003-08")
@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "spec 003 7.2: pore_pressure_ratio in [0, 1); radius and unit weight positive")
@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("pore_pressure_ratio", 1.0),
        ("pore_pressure_ratio", -0.1),
        ("pore_pressure_ratio", 3.0),
        ("radius", 0.0),
        ("radius", -10.0),
        ("unit_weight", 0.0),
        ("unit_weight", -1.0),
    ],
)
def test_other_domains(name: str, value: float) -> None:
    kw = {
        "surface_x": [-30.0, 30.0],
        "surface_z": [0.0, 0.0],
        "center_x": 0.0,
        "center_z": 5.0,
        "radius": 10.0,
        "n_slices": 20,
        "unit_weight": 20000.0,
        "pore_pressure_ratio": 0.0,
    }
    kw[name] = value
    with pytest.raises(minephys.InputError) as ei:
        G.circular_slices(**kw)
    assert ei.value.argument == name

"""T-003-040 (FR-003-18, FR-003-20, FR-000-12, FR-000-13): line-of-sight projection of a displacement for a slope
radar.

Expected API, module `minephys.geotech`:

    slope_radar_los(displacement, radar_position, target_position) -> float64 array (the broadcast of the three
    leading shapes)
        d = u . e with e = (target - radar) / |target - radar|, in metres, POSITIVE for motion AWAY from the radar
        (range increase). The three arguments are arrays of 3-vectors in the LAST axis (shape (..., 3)); the leading
        axes broadcast against each other; a single vector gives a NumPy float64 scalar. A last axis other than 3, a
        radar coinciding with the target (|target - radar| = 0), NaN or infinity, wrong dtypes, and leading shapes
        that cannot broadcast are `InputError` / `InputTypeError`s naming the argument (both names and both shapes for
        a broadcast failure). An empty leading shape gives an empty float64 array.

Oracles: spec 003 section 7.4 (radar at the origin, target at (1000, 0, 0) m, u = (-0.01, 0.01, 0) m gives d =
-0.01 m, toward the radar; u = 0.02 m at 60 deg to the line of sight gives d = 0.01 m), the Pythagorean unit
vector (1, 2, 2) / 3 worked by hand, Monserrat, Crosetto and Luzi (2014) eq. 4 for the sign convention
(positive phase = range increase), and NumPy `einsum` on explicitly broadcast arrays as the reference
implementation. Tolerance TC-1.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

import minephys
from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

ORIGIN = np.zeros(3)


def los(u, radar, target):
    return G.slope_radar_los(
        np.asarray(u, dtype=float), np.asarray(radar, dtype=float), np.asarray(target, dtype=float)
    )


@pytest.mark.req("FR-003-18")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: radar at the origin, target (1000, 0, 0), u = (-0.01, 0.01, 0): d = -0.01 m (toward the radar)",
)
def test_spec_toward_the_radar() -> None:
    d = los([-0.01, 0.01, 0.0], ORIGIN, [1000.0, 0.0, 0.0])
    assert type(d) is np.float64
    assert d == pytest.approx(-0.01, rel=1e-12)


@pytest.mark.req("FR-003-18")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: a 0.02 m displacement at 60 deg to the line of sight gives d = 0.01 m (cos 60 deg = 1/2)",
)
def test_spec_sixty_degrees() -> None:
    u = 0.02 * np.array([math.cos(math.radians(60.0)), math.sin(math.radians(60.0)), 0.0])
    assert los(u, ORIGIN, [1000.0, 0.0, 0.0]) == pytest.approx(0.01, rel=1e-12)
    # the same geometry rotated: the line of sight along y, the displacement at 60 deg from it
    v = 0.02 * np.array([math.sin(math.radians(60.0)), math.cos(math.radians(60.0)), 0.0])
    assert los(v, [10.0, 20.0, 5.0], [10.0, 820.0, 5.0]) == pytest.approx(0.01, rel=1e-12)


@pytest.mark.req("FR-003-18")
@pytest.mark.oracle(
    "hand-calculation", "e = (3, 6, 6) / 9 = (1, 2, 2) / 3; u = (0.3, -0.6, 0.9): d = (0.3 - 1.2 + 1.8) / 3 = 0.3 m"
)
def test_pythagorean_direction() -> None:
    assert los([0.3, -0.6, 0.9], [0.0, 0.0, 0.0], [3.0, 6.0, 6.0]) == pytest.approx(0.3, rel=1e-13)
    assert los([0.3, -0.6, 0.9], [10.0, -20.0, 5.0], [13.0, -14.0, 11.0]) == pytest.approx(0.3, rel=1e-13)  # translated


@pytest.mark.req("FR-003-18")
@pytest.mark.oracle(
    "analytical",
    "positive = away from the radar (range increase): moving the target along the line of sight away is +, toward is -",
)
def test_sign_convention() -> None:
    radar, target = np.array([100.0, 200.0, 50.0]), np.array([400.0, 600.0, 50.0])  # e = (0.6, 0.8, 0)
    away = los([0.006, 0.008, 0.0], radar, target)
    toward = los([-0.006, -0.008, 0.0], radar, target)
    assert away == pytest.approx(0.01, rel=1e-12)
    assert toward == pytest.approx(-0.01, rel=1e-12)
    # the range really grows when the target moves by u away from the radar: |t + u - r| - |t - r| = d to first order
    u = np.array([0.006, 0.008, 0.0])
    grown = float(np.linalg.norm(target + u - radar) - np.linalg.norm(target - radar))
    assert grown == pytest.approx(away, rel=1e-9)  # the two norms are about 500 m: rounding at 1e-13 m
    # below the radar: a radar above the wall sees downward motion of a point beneath it as range increase
    assert los([0.0, 0.0, -0.02], [0.0, 0.0, 0.0], [0.0, 0.0, -500.0]) == pytest.approx(0.02, rel=1e-13)
    assert los([0.0, 0.0, 0.02], [0.0, 0.0, 0.0], [0.0, 0.0, -500.0]) == pytest.approx(-0.02, rel=1e-13)


@pytest.mark.req("FR-003-18")
@pytest.mark.oracle(
    "analytical", "a displacement perpendicular to the line of sight has no line-of-sight component (atol 1e-15 |u|)"
)
def test_perpendicular_displacement() -> None:
    e = np.array([1.0, 2.0, 2.0]) / 3.0
    u = np.cross(e, [0.0, 0.0, 1.0]) * 0.05  # perpendicular to e, norm 0.05 * |e x z|
    assert los(u, [0.0, 0.0, 0.0], 450.0 * e) == pytest.approx(0.0, abs=1e-15 * float(np.linalg.norm(u)))


@pytest.mark.req("FR-003-18")
@pytest.mark.oracle(
    "analytical", "a displacement along the line of sight of length s gives d = +s (away) or -s (toward)"
)
@pytest.mark.parametrize("s", [1e-9, 0.003, 0.5, 40.0])
def test_parallel_displacement(s: float) -> None:
    radar, target = np.array([-120.0, 340.0, 15.0]), np.array([95.0, 505.0, -60.0])
    e = (target - radar) / np.linalg.norm(target - radar)
    assert los(s * e, radar, target) == pytest.approx(s, rel=1e-12)
    assert los(-s * e, radar, target) == pytest.approx(-s, rel=1e-12)


@pytest.mark.req("FR-003-18")
@pytest.mark.oracle(
    "reference-implementation", "numpy einsum on explicitly broadcast arrays; the leading axes broadcast"
)
@pytest.mark.parametrize(
    ("u_shape", "r_shape", "t_shape"),
    [
        ((3,), (3,), (3,)),
        ((5, 3), (3,), (3,)),
        ((5, 3), (3,), (5, 3)),
        ((5, 3), (5, 3), (5, 3)),
        ((2, 1, 3), (1, 4, 3), (3,)),
        ((2, 1, 3), (1, 4, 3), (2, 4, 3)),
        ((4, 3), (1, 3), (4, 3)),
        ((0, 3), (3,), (3,)),
        ((3, 0, 3), (3,), (3,)),
    ],
)
def test_broadcasting_against_einsum(u_shape: tuple, r_shape: tuple, t_shape: tuple) -> None:
    rng = np.random.default_rng(7)
    u = rng.normal(0.0, 0.02, u_shape)
    radar = rng.uniform(-50.0, 50.0, r_shape)
    target = radar + rng.uniform(100.0, 900.0, t_shape) if r_shape == t_shape else rng.uniform(100.0, 900.0, t_shape)
    d = G.slope_radar_los(u, radar, target)
    shape = np.broadcast_shapes(u_shape[:-1], radar.shape[:-1], target.shape[:-1])
    assert d.shape == shape
    assert d.dtype == np.float64
    diff = np.broadcast_to(target, (*shape, 3)) - np.broadcast_to(radar, (*shape, 3))
    e = diff / np.linalg.norm(diff, axis=-1, keepdims=True)
    ref = np.einsum("...i,...i->...", np.broadcast_to(u, (*shape, 3)), e)
    np.testing.assert_allclose(d, ref, rtol=1e-12, atol=1e-15 * 0.02)


@pytest.mark.req("FR-003-18")
@pytest.mark.oracle("analytical", "elementwise over the leading axes: each row equals the single-vector call")
def test_rows_equal_single_calls() -> None:
    rng = np.random.default_rng(11)
    u = rng.normal(0.0, 0.05, (6, 3))
    radar = rng.uniform(-30.0, 30.0, (6, 3))
    target = radar + rng.uniform(50.0, 500.0, (6, 3))
    batch = G.slope_radar_los(u, radar, target)
    for i in range(6):
        single = G.slope_radar_los(u[i], radar[i], target[i])
        assert single == pytest.approx(float(batch[i]), rel=1e-14, abs=1e-14 * float(np.max(np.abs(batch))))


@pytest.mark.req("FR-003-18")
@pytest.mark.oracle("analytical", "integer and float32 operands give the float64 result; inputs are not modified")
def test_dtypes_and_purity() -> None:
    u = np.array([-0.5, 0.25, 0.0])  # exactly representable in float32
    radar, target = np.array([0, 0, 0]), np.array([1000, 0, 0])
    ref = G.slope_radar_los(u, radar.astype(float), target.astype(float))
    assert ref == pytest.approx(-0.5, rel=1e-15)
    for dtype in (np.int64, np.int32):
        assert G.slope_radar_los(u, radar.astype(dtype), target.astype(dtype)) == ref
    assert G.slope_radar_los(u.astype(np.float32), radar.astype(np.float32), target.astype(np.float32)) == ref
    snap = (u.copy(), radar.copy(), target.copy())
    G.slope_radar_los(u, radar, target)
    assert np.array_equal(u, snap[0])
    assert np.array_equal(radar, snap[1])
    assert np.array_equal(target, snap[2])


@pytest.mark.req("FR-003-18")
@pytest.mark.oracle("analytical", "very close positions (1e-12 m apart) still define a direction")
def test_tiny_separation() -> None:
    assert los([1e-3, 0.0, 0.0], ORIGIN, [1e-12, 0.0, 0.0]) == pytest.approx(1e-3, rel=1e-12)
    assert los([1e-3, 5e-4, 0.0], ORIGIN, [0.0, 3e-12, 4e-12]) == pytest.approx(5e-4 * 0.6, rel=1e-12)


@pytest.mark.req("FR-003-18")
@pytest.mark.oracle(
    "analytical", "a radar 1e200 m away is correct or an InputError, never NaN or infinity (square overflow)"
)
def test_huge_coordinates() -> None:
    try:
        d = los([1.0, 0.0, 0.0], ORIGIN, [1e200, 0.0, 0.0])
    except minephys.InputError:
        return
    assert d == pytest.approx(1.0, rel=1e-12)


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "spec 003 7.2: radar and target positions must be distinct")
@pytest.mark.parametrize("p", [[0.0, 0.0, 0.0], [10.0, -20.0, 30.0], [1e6, 1e6, 1e6]])
def test_coincident_positions(p: list[float]) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.slope_radar_los(np.array([0.01, 0.0, 0.0]), np.array(p), np.array(p))
    assert ei.value.argument in {"radar_position", "target_position"}
    rows = np.array([[0.0, 0.0, 0.0], [5.0, 5.0, 5.0]])  # one good radar-target pair, one coincident
    radar = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    target = np.array([[10.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    with pytest.raises(minephys.InputError):
        G.slope_radar_los(rows, radar, target)


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "the last axis must have length 3: InputError naming the argument")
@pytest.mark.parametrize("arg", ["displacement", "radar_position", "target_position"])
@pytest.mark.parametrize("shape", [(2,), (4,), (1,), (0,), (5, 2), (5, 4), (3, 3, 2)])
def test_last_axis_length(arg: str, shape: tuple) -> None:
    kw = {
        "displacement": np.array([0.01, 0.0, 0.0]),
        "radar_position": ORIGIN,
        "target_position": np.array([1000.0, 0.0, 0.0]),
    }
    kw[arg] = np.ones(shape)
    with pytest.raises(minephys.InputError) as ei:
        G.slope_radar_los(**kw)
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "a scalar is not a 3-vector: InputError naming the argument")
@pytest.mark.parametrize("arg", ["displacement", "radar_position", "target_position"])
def test_scalar_is_not_a_vector(arg: str) -> None:
    kw = {
        "displacement": np.array([0.01, 0.0, 0.0]),
        "radar_position": ORIGIN,
        "target_position": np.array([1000.0, 0.0, 0.0]),
    }
    kw[arg] = 1.0
    with pytest.raises(minephys.InputError) as ei:
        G.slope_radar_los(**kw)
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.req("FR-000-10")
@pytest.mark.oracle("analytical", "NaN and infinity anywhere in an argument are InputError naming it")
@pytest.mark.parametrize("arg", ["displacement", "radar_position", "target_position"])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize("index", [0, 2])
def test_non_finite(arg: str, bad: float, index: int) -> None:
    kw = {
        "displacement": np.array([0.01, 0.0, 0.0]),
        "radar_position": ORIGIN.copy(),
        "target_position": np.array([1000.0, 0.0, 0.0]),
    }
    kw[arg] = kw[arg].copy()
    kw[arg][index] = bad
    with pytest.raises(minephys.InputError) as ei:
        G.slope_radar_los(**kw)
    assert ei.value.argument == arg


@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("analytical", "wrong dtypes are InputTypeError naming the argument")
@pytest.mark.parametrize("arg", ["displacement", "radar_position", "target_position"])
@pytest.mark.parametrize(
    "bad",
    [
        "abc",
        b"123",
        None,
        1 + 1j,
        object(),
        np.array(["a", "b", "c"]),
        np.array([1 + 1j, 0, 0]),
        np.datetime64("2026-01-01"),
    ],
)
def test_wrong_types(arg: str, bad) -> None:
    kw = {
        "displacement": np.array([0.01, 0.0, 0.0]),
        "radar_position": ORIGIN,
        "target_position": np.array([1000.0, 0.0, 0.0]),
    }
    kw[arg] = bad
    with pytest.raises(minephys.InputTypeError) as ei:
        G.slope_radar_los(**kw)
    assert ei.value.argument == arg


@pytest.mark.req("FR-000-12")
@pytest.mark.oracle(
    "analytical", "leading shapes (3,) and (4,) cannot broadcast: InputError naming both arguments and both shapes"
)
@pytest.mark.parametrize(
    ("a", "b"),
    [("displacement", "radar_position"), ("displacement", "target_position"), ("radar_position", "target_position")],
)
def test_shape_mismatch(a: str, b: str) -> None:
    kw = {
        "displacement": np.full((1, 3), 0.01),
        "radar_position": np.zeros((1, 3)),
        "target_position": np.full((1, 3), 100.0),
    }
    kw[a] = np.full((3, 3), kw[a][0, 0])
    kw[b] = np.full((4, 3), kw[b][0, 0])
    with pytest.raises(minephys.InputError) as ei:
        G.slope_radar_los(**kw)
    msg = str(ei.value)
    assert a in msg
    assert b in msg
    assert "(3,)" in msg or "(3, 3)" in msg
    assert "(4,)" in msg or "(4, 3)" in msg


@pytest.mark.req("FR-000-13")
@pytest.mark.oracle("analytical", "an empty leading shape gives an empty float64 array")
def test_empty() -> None:
    d = G.slope_radar_los(np.empty((0, 3)), ORIGIN, np.array([1000.0, 0.0, 0.0]))
    assert d.shape == (0,)
    assert d.dtype == np.float64

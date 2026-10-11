"""T-003-040 (P-003-11, FR-003-18): metamorphic properties of the line-of-sight projection.

P-003-11: `slope_radar_los` is invariant to a common rotation and translation of radar, target and
displacement (the displacement is rotated but not translated), linear in the displacement, bounded by |u| in
magnitude, zero for a displacement perpendicular to the line of sight, and changes sign with u. Additionally:
moving the radar along the line of sight does not change d; swapping radar and target flips the sign (the
direction reverses); scaling all positions by a positive factor does not change d (only the direction
matters).

Generators: positions in [-5e3, 5e3]^3 m, |u| <= 1 m, radar and target at least 1 m apart, random rotations
from the QR decomposition of a Gaussian matrix (proper, det = +1). Tolerance TC-1 (rtol 1e-12 with atol 1e-15
|u| absolute floor, the perpendicular case atol 1e-15 |u| as in the spec, rotations accumulate a few more ulp
so 1e-13 |u| is used there).

Oracle: analytical (dot-product geometry), NumPy `einsum` as the reference implementation.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import geotech as G

CFG = settings(deadline=None)
VEC = st.lists(st.floats(-5e3, 5e3), min_size=3, max_size=3).map(np.array)
DISP = st.lists(st.floats(-1.0, 1.0), min_size=3, max_size=3).map(np.array)


def rotation(seed: int) -> np.ndarray:
    q, r = np.linalg.qr(np.random.default_rng(seed).normal(size=(3, 3)))
    q = q * np.sign(np.diag(r))
    if np.linalg.det(q) < 0:
        q[:, 0] = -q[:, 0]
    return q


def apart(radar: np.ndarray, target: np.ndarray) -> None:
    assume(float(np.linalg.norm(target - radar)) >= 1.0)


def los(u, radar, target) -> float:
    return float(G.slope_radar_los(u, radar, target))


@pytest.mark.req("P-003-11")
@pytest.mark.oracle("reference-implementation", "numpy: u . (target - radar) / |target - radar|")
@CFG
@given(u=DISP, radar=VEC, target=VEC)
def test_matches_the_dot_product(u: np.ndarray, radar: np.ndarray, target: np.ndarray) -> None:
    apart(radar, target)
    e = (target - radar) / np.linalg.norm(target - radar)
    assert los(u, radar, target) == pytest.approx(float(np.dot(u, e)), rel=1e-12, abs=1e-15)


@pytest.mark.req("P-003-11")
@pytest.mark.oracle("analytical", "rigid-motion invariance: rotate everything, translate the positions")
@CFG
@given(u=DISP, radar=VEC, target=VEC, shift=VEC, seed=st.integers(0, 2**32 - 1))
def test_rigid_motion_invariance(u, radar, target, shift, seed) -> None:
    apart(radar, target)
    rot = rotation(seed)
    moved = los(rot @ u, rot @ radar + shift, rot @ target + shift)
    assert moved == pytest.approx(los(u, radar, target), rel=1e-9, abs=1e-12 * (1.0 + float(np.linalg.norm(u))))


@pytest.mark.req("P-003-11")
@pytest.mark.oracle("analytical", "linearity in the displacement: d(a u1 + b u2) = a d(u1) + b d(u2)")
@CFG
@given(u1=DISP, u2=DISP, radar=VEC, target=VEC, a=st.floats(-10.0, 10.0), b=st.floats(-10.0, 10.0))
def test_linearity(u1, u2, radar, target, a, b) -> None:
    apart(radar, target)
    lhs = los(a * u1 + b * u2, radar, target)
    rhs = a * los(u1, radar, target) + b * los(u2, radar, target)
    assert lhs == pytest.approx(rhs, rel=1e-9, abs=1e-14 * (abs(a) + abs(b)))


@pytest.mark.req("P-003-11")
@pytest.mark.oracle(
    "analytical", "Cauchy-Schwarz: |d| <= |u|, with equality for a displacement along the line of sight"
)
@CFG
@given(u=DISP, radar=VEC, target=VEC)
def test_bound(u, radar, target) -> None:
    apart(radar, target)
    norm = float(np.hypot(np.hypot(u[0], u[1]), u[2]))  # hypot does not underflow for tiny components
    assert abs(los(u, radar, target)) <= norm * (1.0 + 1e-14) + 1e-300
    e = (target - radar) / np.linalg.norm(target - radar)
    assert los(norm * e, radar, target) == pytest.approx(norm, rel=1e-12, abs=1e-15)


@pytest.mark.req("P-003-11")
@pytest.mark.oracle(
    "analytical",
    "a displacement perpendicular to the line of sight projects to zero (atol 1e-15 |u|, 1e-13 after rotation)",
)
@CFG
@given(w=DISP, radar=VEC, target=VEC)
def test_perpendicular(w, radar, target) -> None:
    apart(radar, target)
    e = (target - radar) / np.linalg.norm(target - radar)
    u = w - np.dot(w, e) * e  # remove the line-of-sight component
    assert los(u, radar, target) == pytest.approx(0.0, abs=1e-13 * (1.0 + float(np.linalg.norm(w))))


@pytest.mark.req("P-003-11")
@pytest.mark.oracle("analytical", "symmetry: d(-u) = -d(u), exactly")
@CFG
@given(u=DISP, radar=VEC, target=VEC)
def test_sign_symmetry(u, radar, target) -> None:
    apart(radar, target)
    assert los(-u, radar, target) == -los(u, radar, target)


@pytest.mark.req("P-003-11")
@pytest.mark.oracle(
    "analytical",
    "only the direction matters: moving the radar along the line of sight, or scaling the distance, keeps d",
)
@CFG
@given(u=DISP, radar=VEC, target=VEC, s=st.floats(0.1, 0.9), k=st.floats(0.01, 100.0))
def test_only_the_direction_matters(u, radar, target, s, k) -> None:
    apart(radar, target)
    base = los(u, radar, target)
    closer = radar + s * (target - radar)  # still on the same line of sight, same direction to the target
    assume(float(np.linalg.norm(target - closer)) >= 1.0)
    assert los(u, closer, target) == pytest.approx(base, rel=1e-8, abs=1e-12)
    assert los(u, radar, radar + k * (target - radar)) == pytest.approx(base, rel=1e-8, abs=1e-12)


@pytest.mark.req("P-003-11")
@pytest.mark.oracle("analytical", "swapping radar and target reverses the direction: the sign of d flips")
@CFG
@given(u=DISP, radar=VEC, target=VEC)
def test_swap_flips_the_sign(u, radar, target) -> None:
    apart(radar, target)
    assert los(u, target, radar) == pytest.approx(-los(u, radar, target), rel=1e-12, abs=1e-15)

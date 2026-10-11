"""T-004-011 (P-004-03, FR-004-03, FR-004-04): metamorphic properties of the repose-angle geometry.

P-004-03: the cone volume equals one third of the base area times the height, scales as r^3, and is strictly
increasing in the repose angle; the ridge cross-section scales as r^2 and the ridge volume is linear in
length. Further: the cone height is linear in r; the volume of the capped ridge is the plain ridge plus one cone.

Generators (spec 004 P-004-03): r in [0.1, 500] m, phi in (0.05, 1.5) rad, length in [0, 1e4] m, scale factors in
[1e-3, 1e3]. Tolerance TC-1 (rtol 1e-12); monotonicity compares angles at least 1e-6 rad apart.

Oracle: analytical (solid geometry).
"""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import bulk as B

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

CFG = settings(deadline=None)
R = st.floats(0.1, 500.0)
PHI = st.floats(0.05, 1.5)


@pytest.mark.req("P-004-03")
@pytest.mark.oracle("analytical", "cone volume = base area x height / 3")
@CFG
@given(r=R, phi=PHI)
def test_cone_is_a_third_of_base_times_height(r: float, phi: float) -> None:
    assert float(B.repose_cone_volume(r, phi)) == pytest.approx(
        math.pi * r * r * float(B.repose_cone_height(r, phi)) / 3.0, rel=1e-12
    )


@pytest.mark.req("P-004-03")
@pytest.mark.oracle("analytical", "the cone volume scales as r^3 and the height as r")
@CFG
@given(r=R, phi=PHI, lam=st.floats(1e-3, 1e3))
def test_cone_scaling(r: float, phi: float, lam: float) -> None:
    assert float(B.repose_cone_volume(lam * r, phi)) == pytest.approx(
        lam**3 * float(B.repose_cone_volume(r, phi)), rel=1e-12
    )
    assert float(B.repose_cone_height(lam * r, phi)) == pytest.approx(
        lam * float(B.repose_cone_height(r, phi)), rel=1e-12
    )


@pytest.mark.req("P-004-03")
@pytest.mark.oracle("analytical", "the cone volume and height are strictly increasing in the repose angle")
@CFG
@given(r=R, a=PHI, b=PHI)
def test_cone_increases_with_the_angle(r: float, a: float, b: float) -> None:
    assume(abs(a - b) > 1e-6)
    lo, hi = sorted((a, b))
    assert float(B.repose_cone_volume(r, lo)) < float(B.repose_cone_volume(r, hi))
    assert float(B.repose_cone_height(r, lo)) < float(B.repose_cone_height(r, hi))


@pytest.mark.req("P-004-03")
@pytest.mark.oracle(
    "analytical", "the ridge cross-section (volume per metre) scales as r^2; the ridge volume is linear in length"
)
@CFG
@given(r=R, phi=PHI, length=st.floats(1e-3, 1e4), lam=st.floats(1e-3, 1e3), mu=st.floats(1e-3, 1e3))
def test_ridge_scaling(r: float, phi: float, length: float, lam: float, mu: float) -> None:
    section = float(B.repose_ridge_volume(r, phi, 1.0))
    assert float(B.repose_ridge_volume(lam * r, phi, 1.0)) == pytest.approx(lam**2 * section, rel=1e-12)
    assert float(B.repose_ridge_volume(r, phi, length)) == pytest.approx(length * section, rel=1e-12)
    assert float(B.repose_ridge_volume(r, phi, mu * length)) == pytest.approx(
        mu * float(B.repose_ridge_volume(r, phi, length)), rel=1e-12
    )


@pytest.mark.req("P-004-03")
@pytest.mark.oracle("analytical", "the ridge volume is strictly increasing in the angle, the half-width and the length")
@CFG
@given(r=R, a=PHI, b=PHI, length=st.floats(1e-3, 1e4), grow=st.floats(1e-3, 2.0))
def test_ridge_monotonicity(r: float, a: float, b: float, length: float, grow: float) -> None:
    assume(abs(a - b) > 1e-6)
    lo, hi = sorted((a, b))
    assert float(B.repose_ridge_volume(r, lo, length)) < float(B.repose_ridge_volume(r, hi, length))
    base = float(B.repose_ridge_volume(r, lo, length))
    assert float(B.repose_ridge_volume(r * (1.0 + grow), lo, length)) > base
    assert float(B.repose_ridge_volume(r, lo, length * (1.0 + grow))) > base


@pytest.mark.req("FR-004-04")
@pytest.mark.oracle("analytical", "the capped ridge is the plain ridge plus one cone, whatever the length")
@CFG
@given(r=R, phi=PHI, length=st.floats(0.0, 1e4))
def test_end_cones_add_one_cone(r: float, phi: float, length: float) -> None:
    capped = float(B.repose_ridge_volume(r, phi, length, True))
    plain = float(B.repose_ridge_volume(r, phi, length, False))
    assert capped == pytest.approx(plain + float(B.repose_cone_volume(r, phi)), rel=1e-12)

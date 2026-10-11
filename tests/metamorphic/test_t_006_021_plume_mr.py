"""T-006-021 (P-006-05, P-006-06, P-006-07): metamorphic relations of the point-source Gaussian plume.

Public API under test (`minephys.environment`): `gaussian_plume(q, u, y, z, h, sigma_y, sigma_z, mixing_height=None)`
(see tests/unit/test_t_006_021_plume.py). Generators: u log-uniform in [0.5, 20] m/s, heights in [0, 200] m, sigma_y and
sigma_z in [1, 500] m, 200 examples.

Relations
- P-006-05 linearity and wind scaling: C is linear in q (two sources superpose) and C(lambda u) = C(u) / lambda (TC-1);
- P-006-06 symmetry and reciprocity: C(y) = C(-y) exactly (TC-0) and C is unchanged when h and z are exchanged (TC-1);
- P-006-07 mass conservation: u x the double integral of C over y in (-inf, inf) and z in [0, inf) equals q without a lid
  (and over z in [0, z_i] with a lid and h < z_i), by trapezoid quadrature on a 1,201 x 1,201 grid out to 10 sigma (the
  integrand is a smooth even function at the grid ends, so the trapezoid rule converges spectrally; rtol 1e-6).
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
LOGU = st.floats(math.log(0.5), math.log(20.0)).map(math.exp)
SIGMA = st.floats(1.0, 500.0)
HEIGHT = st.floats(0.0, 200.0)
Q = st.floats(1e-6, 1.0)


def _f():
    return importlib.import_module("minephys.environment").gaussian_plume


@pytest.mark.req("P-006-05")
@pytest.mark.oracle("analytical", "C is linear in the emission rate and inversely proportional to the wind speed")
@CI
@given(
    q1=Q, q2=Q, u=LOGU, lam=st.floats(0.1, 10.0), y=st.floats(-300.0, 300.0), z=HEIGHT, h=HEIGHT, sy=SIGMA, sz=SIGMA
)
def test_p_006_05_linearity_and_wind_scaling(q1: float, q2: float, u: float, lam: float, y: float, z: float, h: float, sy: float, sz: float) -> None:
    c = _f()
    np.testing.assert_allclose(
        c(q1 + q2, u, y, z, h, sy, sz), c(q1, u, y, z, h, sy, sz) + c(q2, u, y, z, h, sy, sz), rtol=1e-12, atol=1e-300
    )
    np.testing.assert_allclose(c(q1, lam * u, y, z, h, sy, sz), c(q1, u, y, z, h, sy, sz) / lam, rtol=1e-12, atol=1e-300)
    np.testing.assert_allclose(c(lam * q1, u, y, z, h, sy, sz), lam * c(q1, u, y, z, h, sy, sz), rtol=1e-12, atol=1e-300)


@pytest.mark.req("P-006-06")
@pytest.mark.oracle("analytical", "the plume is even in y; source and receptor heights are interchangeable")
@CI
@given(q=Q, u=LOGU, y=st.floats(0.0, 300.0), z=HEIGHT, h=HEIGHT, sy=SIGMA, sz=SIGMA)
def test_p_006_06_symmetry_and_reciprocity(q: float, u: float, y: float, z: float, h: float, sy: float, sz: float) -> None:
    c = _f()
    assert c(q, u, y, z, h, sy, sz) == c(q, u, -y, z, h, sy, sz)  # TC-0
    np.testing.assert_allclose(c(q, u, y, z, h, sy, sz), c(q, u, y, h, z, sy, sz), rtol=1e-12, atol=1e-300)


@pytest.mark.req("P-006-06")
@CI
@given(q=Q, u=LOGU, y=st.floats(0.0, 300.0), z=st.floats(0.0, 90.0), h=st.floats(0.0, 90.0), sy=SIGMA, sz=st.floats(5.0, 150.0))
def test_p_006_06_symmetry_and_reciprocity_with_a_lid(q: float, u: float, y: float, z: float, h: float, sy: float, sz: float) -> None:
    c = _f()
    zi = 100.0
    a = c(q, u, y, z, h, sy, sz, zi)
    np.testing.assert_allclose(a, c(q, u, -y, z, h, sy, sz, zi), rtol=1e-12, atol=1e-300)
    np.testing.assert_allclose(a, c(q, u, y, h, z, sy, sz, zi), rtol=1e-10, atol=1e-300)


def _flux(sy: float, sz: float, h: float, zi: float | None, u: float = 3.0, q: float = 2.5e-3) -> float:
    c = _f()
    y = np.linspace(-10.0 * sy, 10.0 * sy, 1201)
    top = zi if zi is not None else h + 10.0 * sz
    z = np.linspace(0.0, top, 1201)
    field = c(q, u, y[:, None], z[None, :], h, sy, sz) if zi is None else c(q, u, y[:, None], z[None, :], h, sy, sz, zi)
    return float(u * np.trapezoid(np.trapezoid(field, z, axis=1), y))


@pytest.mark.req("P-006-07")
@pytest.mark.oracle("analytical", "the integral of the Gaussian plume over the cross-section equals q / u")
@pytest.mark.parametrize(
    ("sy", "sz", "h"),
    [(36.0, 20.0, 0.0), (36.0, 20.0, 10.0), (80.0, 5.0, 30.0), (3.0, 40.0, 120.0), (200.0, 150.0, 60.0), (1.0, 1.0, 0.0)],
)
def test_p_006_07_mass_conservation_without_a_lid(sy: float, sz: float, h: float) -> None:
    np.testing.assert_allclose(_flux(sy, sz, h, None), 2.5e-3, rtol=1e-6)


@pytest.mark.req("P-006-07")
@pytest.mark.oracle("analytical", "with ground and lid reflections the cross-section integral up to z_i equals q / u")
@pytest.mark.parametrize(
    ("sy", "sz", "h", "zi"),
    [(36.0, 20.0, 10.0, 100.0), (60.0, 40.0, 30.0, 100.0), (50.0, 80.0, 50.0, 100.0), (30.0, 150.0, 20.0, 100.0), (45.0, 10.0, 90.0, 120.0)],
)
def test_p_006_07_mass_conservation_with_a_lid(sy: float, sz: float, h: float, zi: float) -> None:
    np.testing.assert_allclose(_flux(sy, sz, h, zi), 2.5e-3, rtol=1e-6)

"""T-006-030 (P-006-10, P-006-11): properties of the Beer-Lambert functions.

Public API under test (`minephys.environment`): `beer_lambert_transmittance`, `path_transmittance`,
`mass_extinction_coefficient`, `extinction_coefficient` (see tests/unit/test_t_006_030_beer_lambert.py).
Generators: optical depths in [0.01, 10], path lengths in [1, 1000] m (the concentration follows from them), diameters 1 um to
1 mm, densities 500 to 8,000 kg/m^3; 200 examples (the default efficiency is passed explicitly so that no warning is emitted).

Relations
- P-006-10 multiplicativity T(L1 + L2) = T(L1) T(L2); a constant profile gives the uniform law (TC-1);
- P-006-11 scaling: the optical depth is linear in the concentration and in the path length; k_m is proportional to 1/D and to 1/rho.
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
LENGTH = st.floats(0.1, 1000.0)
BETA = st.floats(1e-8, 0.5)
LAM = st.floats(0.1, 10.0)


def _e():
    return importlib.import_module("minephys.environment")


@pytest.mark.req("P-006-10")
@pytest.mark.oracle("analytical", "exp(-beta (L1 + L2)) = exp(-beta L1) exp(-beta L2)")
@CI
@given(b=BETA, l1=LENGTH, l2=LENGTH)
def test_p_006_10_multiplicativity(b: float, l1: float, l2: float) -> None:
    e = _e()
    np.testing.assert_allclose(
        e.beer_lambert_transmittance(b, l1 + l2),
        e.beer_lambert_transmittance(b, l1) * e.beer_lambert_transmittance(b, l2),
        rtol=1e-12,
        atol=1e-300,
    )


@pytest.mark.req("P-006-10")
@CI
@given(b=BETA, length=LENGTH, n=st.integers(2, 50), seed=st.integers(0, 2**32 - 1))
def test_p_006_10_constant_profile_equals_the_uniform_law(b: float, length: float, n: int, seed: int) -> None:
    e = _e()
    steps = np.random.default_rng(seed).uniform(0.1, 1.0, n - 1)
    positions = np.r_[0.0, np.cumsum(steps)] * length / steps.sum()
    positions[-1] = length
    np.testing.assert_allclose(
        e.path_transmittance(positions, np.full(n, b)), e.beer_lambert_transmittance(b, length), rtol=1e-12, atol=1e-300
    )


@pytest.mark.req("P-006-10")
@pytest.mark.oracle("analytical", "the trapezoid integral is additive over a split at an interior node: T(whole) = T(first) T(second)")
@CI
@given(b=BETA, n=st.integers(3, 40), seed=st.integers(0, 2**32 - 1), cut=st.integers(0, 10_000))
def test_p_006_10_path_transmittance_is_multiplicative_over_split_paths(b: float, n: int, seed: int, cut: int) -> None:
    e = _e()
    rng = np.random.default_rng(seed)
    positions = np.r_[0.0, np.cumsum(rng.uniform(0.1, 20.0, n - 1))]
    profile = b * rng.uniform(0.0, 2.0, n)
    k = 1 + cut % (n - 2)  # an interior node
    whole = e.path_transmittance(positions, profile)
    parts = e.path_transmittance(positions[: k + 1], profile[: k + 1]) * e.path_transmittance(positions[k:], profile[k:])
    np.testing.assert_allclose(whole, parts, rtol=1e-11, atol=1e-300)

@pytest.mark.req("P-006-11")
@pytest.mark.oracle("analytical", "optical depth beta L = k_m C L is linear in C and in L (depth chosen in [0.01, 10], scaled by up to 3)")
@CI
@given(
    d=st.floats(1e-6, 1e-3),
    rho=st.floats(500.0, 8000.0),
    tau=st.floats(0.01, 10.0),
    length=st.floats(1.0, 1000.0),
    lam=st.floats(0.1, 3.0),
)
def test_p_006_11_optical_depth_is_linear_in_concentration_and_length(d: float, rho: float, tau: float, length: float, lam: float) -> None:
    e = _e()
    km = e.mass_extinction_coefficient(d, rho, 2.0)
    conc = tau / (float(km) * length)  # the concentration that gives optical depth tau over `length`

    def depth(c: float, path: float) -> float:
        return float(-np.log(e.beer_lambert_transmittance(e.extinction_coefficient(c, km), path)))

    np.testing.assert_allclose(depth(conc, length), tau, rtol=1e-9, atol=0)
    np.testing.assert_allclose(depth(lam * conc, length), lam * tau, rtol=1e-9, atol=0)
    np.testing.assert_allclose(depth(conc, lam * length), lam * tau, rtol=1e-9, atol=0)

@pytest.mark.req("P-006-11")
@CI
@given(d=st.floats(1e-6, 1e-3), rho=st.floats(500.0, 8000.0), lam=LAM, q=st.floats(0.5, 4.0))
def test_p_006_11_mass_extinction_scales_as_the_inverse_diameter_and_density(d: float, rho: float, lam: float, q: float) -> None:
    e = _e()
    base = e.mass_extinction_coefficient(d, rho, q)
    np.testing.assert_allclose(e.mass_extinction_coefficient(lam * d, rho, q), base / lam, rtol=1e-12)
    np.testing.assert_allclose(e.mass_extinction_coefficient(d, lam * rho, q), base / lam, rtol=1e-12)
    np.testing.assert_allclose(e.mass_extinction_coefficient(d, rho, lam * q), base * lam, rtol=1e-12)

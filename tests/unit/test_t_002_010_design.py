"""T-002-010 (FR-002-01): charge per hole and powder factor.

Expected API (`from minephys import blasting as B`):
    `B.charge_per_hole(explosive_density, hole_diameter, charge_length)` -> rho_e * (pi / 4) * d^2 * L_c in kg;
    `B.powder_factor(charge, burden, spacing, bench_height)` -> Q / (B * S * H) in kg/m^3.
Oracles: spec 002 section 7.4 worked example 1 (rho_e = 850 kg/m^3, d = 0.25 m, L_c = 7.2 m, B = 6 m, S = 7 m,
H = 12 m: 300.41480 kg and 0.59606111 kg/m^3, TC-2) and hand calculations. Tolerance TC-1 otherwise.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from minephys import blasting as B

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


@pytest.mark.req("FR-002-01")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: 850 * (pi/4) * 0.25^2 * 7.2 = 300.41480 kg")
def test_charge_per_hole_printed_value() -> None:
    got = B.charge_per_hole(850.0, 0.25, 7.2)
    assert type(got) is np.float64
    assert got == pytest.approx(300.41480, abs=5e-6)  # TC-2: 8 significant figures
    assert got == pytest.approx(850.0 * math.pi / 4.0 * 0.25**2 * 7.2, rel=1e-12)


@pytest.mark.req("FR-002-01")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: 300.4148 / (6 * 7 * 12) = 0.59606111 kg/m^3")
def test_powder_factor_printed_value() -> None:
    got = B.powder_factor(300.41480, 6.0, 7.0, 12.0)
    assert type(got) is np.float64
    assert got == pytest.approx(0.59606111, abs=5e-9)
    assert B.powder_factor(B.charge_per_hole(850.0, 0.25, 7.2), 6.0, 7.0, 12.0) == pytest.approx(0.59606111, abs=5e-9)


@pytest.mark.req("FR-002-01")
@pytest.mark.oracle(
    "hand-calculation", "round numbers: 1000 kg/m^3 in a 0.2 m hole 10 m long = 1000 * 0.0314159... * 10 = 314.159 kg"
)
@pytest.mark.parametrize(
    ("rho", "d", "length", "expected"),
    [
        (1000.0, 0.2, 10.0, 1000.0 * math.pi * 0.01 * 10.0),
        (850.0, 0.1, 1.0, 850.0 * math.pi / 4.0 * 0.01),
        (1200.0, 0.311, 12.0, 1200.0 * math.pi / 4.0 * 0.311**2 * 12.0),
    ],
)
def test_charge_per_hole_values(rho: float, d: float, length: float, expected: float) -> None:
    assert B.charge_per_hole(rho, d, length) == pytest.approx(expected, rel=1e-12, abs=1e-300)


@pytest.mark.req("FR-002-01")
@pytest.mark.oracle("hand-calculation", "powder factor: 120 kg over a 4 x 5 x 10 m block = 0.6 kg/m^3")
def test_powder_factor_simple_block() -> None:
    assert B.powder_factor(120.0, 4.0, 5.0, 10.0) == pytest.approx(0.6, rel=1e-12)


@pytest.mark.req("FR-002-01")
@pytest.mark.oracle("hand-calculation", "broadcast over densities (column) and diameters (row)")
def test_charge_per_hole_broadcasts() -> None:
    rho = np.array([[800.0], [1000.0], [1200.0]])
    d = np.array([0.1, 0.2, 0.3, 0.4])
    out = B.charge_per_hole(rho, d, 8.0)
    assert out.shape == (3, 4)
    np.testing.assert_allclose(out, rho * math.pi / 4.0 * d**2 * 8.0, rtol=1e-14, atol=0.0)
    assert B.charge_per_hole(np.empty(0), 0.25, 7.2).shape == (0,)


@pytest.mark.req("FR-002-01")
@pytest.mark.oracle("analytical", "the charge is quadratic in the diameter and linear in the density and the length")
@settings(deadline=None)
@given(
    rho=st.floats(700.0, 1400.0),
    d=st.floats(0.05, 0.4),
    length=st.floats(0.5, 20.0),
    k=st.floats(1e-2, 1e2),
)
def test_charge_scaling(rho: float, d: float, length: float, k: float) -> None:
    base = float(B.charge_per_hole(rho, d, length))
    assert float(B.charge_per_hole(rho, k * d, length)) == pytest.approx(k * k * base, rel=1e-11)
    assert float(B.charge_per_hole(k * rho, d, length)) == pytest.approx(k * base, rel=1e-11)
    assert float(B.charge_per_hole(rho, d, k * length)) == pytest.approx(k * base, rel=1e-11)


@pytest.mark.req("FR-002-01")
@pytest.mark.oracle(
    "analytical", "the powder factor is linear in the charge and inversely proportional to each dimension"
)
@settings(deadline=None)
@given(
    q=st.floats(1.0, 1000.0),
    b=st.floats(1.0, 12.0),
    s=st.floats(1.0, 15.0),
    h=st.floats(2.0, 30.0),
    k=st.floats(1e-2, 1e2),
)
def test_powder_factor_scaling(q: float, b: float, s: float, h: float, k: float) -> None:
    base = float(B.powder_factor(q, b, s, h))
    assert base == pytest.approx(q / (b * s * h), rel=1e-12)
    assert float(B.powder_factor(k * q, b, s, h)) == pytest.approx(k * base, rel=1e-11)
    assert float(B.powder_factor(q, k * b, s, h)) == pytest.approx(base / k, rel=1e-11)
    assert float(B.powder_factor(q, b, k * s, k * h)) == pytest.approx(base / (k * k), rel=1e-11)

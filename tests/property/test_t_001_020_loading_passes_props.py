"""T-001-020 (P-001-13): properties of `loading_passes`.

P-001-13: non-decreasing in the target payload, non-increasing in bucket volume, fill factor and loose density, and the
bracket identity `n * V * k * rho >= M > (n - 1) * V * k * rho` up to the 1e-12 relative integer rule (exact ordering).
Generators: M in [1e3, 6e5] kg, V in [1, 60] m^3, fill factor in [0.5, 1.2], loose density in [1000, 3000] kg/m^3.

Oracle: `fractions.Fraction` arithmetic on the float64 inputs (every float is an exact rational), i.e. the definition of
the smallest n >= 1 with n * V * k * rho >= M, with the quotient within a relative 1e-12 of an integer taken as that
integer. Cases whose quotient lies within 10 % of the 1e-12 rule border are discarded (float rounding of ~1e-16 cannot
matter elsewhere).
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

payload = st.floats(1e3, 6e5)
volume = st.floats(1.0, 60.0)
fill = st.floats(0.5, 1.2)
density = st.floats(1000.0, 3000.0)
CFG = settings(deadline=None)
RULE = Fraction(1, 10**12)


def exact_passes(m: float, v: float, k: float, rho: float) -> int:
    q = Fraction(m) / (Fraction(v) * Fraction(k) * Fraction(rho))
    nearest = round(q)
    if nearest >= 1 and abs(q - nearest) <= RULE * q:
        return int(nearest)
    return max(1, math.ceil(q))


def near_border(m: float, v: float, k: float, rho: float) -> bool:
    q = Fraction(m) / (Fraction(v) * Fraction(k) * Fraction(rho))
    rel = abs(q - round(q)) / q
    return Fraction(9, 10) * RULE <= rel <= Fraction(11, 10) * RULE


def n_of(m, v, k, rho):
    return int(H.loading_passes(m, v, k, rho))


@pytest.mark.req("P-001-13")
@pytest.mark.oracle("analytical", "exact rational arithmetic gives the same pass count")
@CFG
@given(m=payload, v=volume, k=fill, rho=density)
def test_matches_exact_arithmetic(m: float, v: float, k: float, rho: float) -> None:
    assume(not near_border(m, v, k, rho))
    assert n_of(m, v, k, rho) == exact_passes(m, v, k, rho)


@pytest.mark.req("P-001-13")
@pytest.mark.oracle(
    "analytical", "an exact multiple of the pass capacity is that multiple, however the float product rounds"
)
@CFG
@given(j=st.integers(1, 40), v=volume, k=fill, rho=density)
def test_exact_multiples(j: int, v: float, k: float, rho: float) -> None:
    capacity = v * k * rho
    assert n_of(j * capacity, v, k, rho) == j


@pytest.mark.req("P-001-13")
@pytest.mark.oracle("analytical", "bracket identity: n * cap >= M > (n - 1) * cap up to the 1e-12 rule")
@CFG
@given(m=payload, v=volume, k=fill, rho=density)
def test_bracket_identity(m: float, v: float, k: float, rho: float) -> None:
    n = n_of(m, v, k, rho)
    cap = v * k * rho
    assert n >= 1
    assert n * cap >= m * (1.0 - 2e-12)
    assert (n - 1) * cap < m * (1.0 + 2e-12)


@pytest.mark.req("P-001-13")
@pytest.mark.oracle("analytical", "non-decreasing in the payload, non-increasing in volume, fill factor and density")
@CFG
@given(m1=payload, m2=payload, v1=volume, v2=volume, k1=fill, k2=fill, r1=density, r2=density)
def test_monotonicity(m1, m2, v1, v2, k1, k2, r1, r2) -> None:
    lo, hi = sorted((m1, m2))
    assert n_of(lo, 20.0, 0.9, 2000.0) <= n_of(hi, 20.0, 0.9, 2000.0)
    lo, hi = sorted((v1, v2))
    assert n_of(3e5, lo, 0.9, 2000.0) >= n_of(3e5, hi, 0.9, 2000.0)
    lo, hi = sorted((k1, k2))
    assert n_of(3e5, 20.0, lo, 2000.0) >= n_of(3e5, 20.0, hi, 2000.0)
    lo, hi = sorted((r1, r2))
    assert n_of(3e5, 20.0, 0.9, lo) >= n_of(3e5, 20.0, 0.9, hi)


@pytest.mark.req("P-001-13")
@pytest.mark.oracle("analytical", "scaling payload and capacity together leaves the count unchanged (up to the rule)")
@CFG
@given(m=payload, v=volume, k=fill, rho=density, s=st.floats(0.5, 4.0))
def test_common_scaling_of_payload_and_capacity(m: float, v: float, k: float, rho: float, s: float) -> None:
    assume(not near_border(m, v, k, rho) and not near_border(s * m, s * v, k, rho))
    assert n_of(s * m, s * v, k, rho) == n_of(m, v, k, rho)

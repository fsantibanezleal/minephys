"""T-002-030 (P-002-07): metamorphic properties of the PPV site law.

P-002-07: `ppv_scaled_distance` is unchanged when D -> lambda D and W -> lambda^2 W (square-root scaling),
strictly decreasing in D, strictly increasing in W, and gives the same PPV when D, W and K are expressed in
ft, lb and in/s with K_SI = 0.0254 * K_imp * c^(-beta), c = sqrt(0.45359237) / 0.3048 (unit-change
invariance). Generators (spec 002): D in [10, 1e4] m, W in [1, 5e3] kg, beta in [1, 2.5]. Tolerance TC-1 (rtol
1e-12); orderings on pairs with a relative gap of at least 1e-3.

Oracle: analytical. The imperial identity follows from the exact unit definitions (1 in = 0.0254 m, 1 ft = 0.3048 m,
1 lb = 0.45359237 kg): D_ft / sqrt(W_lb) = c * D / sqrt(W), hence K_imp (D_ft / sqrt(W_lb))^-beta [in/s] * 0.0254 =
K_SI (D / sqrt(W))^-beta. The imperial side is computed here from first principles, not by the code.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import blasting as B

CFG = settings(deadline=None)
dist = st.floats(10.0, 1e4)
charge = st.floats(1.0, 5e3)
beta_s = st.floats(1.0, 2.5)
k_s = st.floats(0.05, 50.0)
FT, LB, INCH = 0.3048, 0.45359237, 0.0254
C = math.sqrt(LB) / FT


@pytest.mark.req("P-002-07")
@pytest.mark.oracle("analytical", "square-root scaling: D -> lambda D with W -> lambda^2 W keeps the scaled distance")
@CFG
@given(d=dist, w=charge, b=beta_s, k=k_s, lam=st.floats(1e-2, 1e2))
def test_square_root_scaling(d: float, w: float, b: float, k: float, lam: float) -> None:
    assert float(B.scaled_distance(lam * d, lam * lam * w)) == pytest.approx(float(B.scaled_distance(d, w)), rel=1e-12)
    assert float(B.ppv_scaled_distance(lam * d, lam * lam * w, k, b)) == pytest.approx(
        float(B.ppv_scaled_distance(d, w, k, b)), rel=1e-11
    )


@pytest.mark.req("P-002-07")
@pytest.mark.oracle("analytical", "strictly decreasing in distance and strictly increasing in the charge per delay")
@CFG
@given(d1=dist, d2=dist, w1=charge, w2=charge, b=beta_s, k=k_s)
def test_monotonicity(d1: float, d2: float, w1: float, w2: float, b: float, k: float) -> None:
    assume(abs(d1 - d2) > 1e-3 * max(d1, d2) and abs(w1 - w2) > 1e-3 * max(w1, w2))
    near, far = sorted((d1, d2))
    light, heavy = sorted((w1, w2))
    assert float(B.ppv_scaled_distance(far, 100.0, k, b)) < float(B.ppv_scaled_distance(near, 100.0, k, b))
    assert float(B.ppv_scaled_distance(500.0, heavy, k, b)) > float(B.ppv_scaled_distance(500.0, light, k, b))
    assert float(B.scaled_distance(far, 50.0)) > float(B.scaled_distance(near, 50.0))
    assert float(B.scaled_distance(500.0, heavy)) < float(B.scaled_distance(500.0, light))


@pytest.mark.req("P-002-07")
@pytest.mark.oracle(
    "analytical", "unit-change invariance: ft, lb and in/s with K_SI = 0.0254 K_imp c^-beta give the same PPV"
)
@CFG
@given(d=dist, w=charge, b=beta_s, k_imp=st.floats(10.0, 1000.0))
def test_imperial_units_give_the_same_ppv(d: float, w: float, b: float, k_imp: float) -> None:
    d_ft, w_lb = d / FT, w / LB
    ppv_imp_in_s = k_imp * (d_ft / math.sqrt(w_lb)) ** -b  # the site law in Gy-free imperial units
    expected_m_s = INCH * ppv_imp_in_s
    k_si = INCH * k_imp * C**-b
    assert float(B.ppv_scaled_distance(d, w, k_si, b)) == pytest.approx(expected_m_s, rel=1e-11)


@pytest.mark.req("P-002-07")
@pytest.mark.oracle(
    "analytical", "linear in K and a pure power of the scaled distance: PPV(SD1) / PPV(SD2) = (SD2 / SD1)^beta"
)
@CFG
@given(d=dist, w=charge, b=beta_s, k=k_s, m=st.floats(0.1, 10.0))
def test_linear_in_k_and_power_law_in_scaled_distance(d: float, w: float, b: float, k: float, m: float) -> None:
    base = float(B.ppv_scaled_distance(d, w, k, b))
    assert float(B.ppv_scaled_distance(d, w, m * k, b)) == pytest.approx(m * base, rel=1e-12)
    assert float(B.ppv_scaled_distance(m * d, w, k, b)) == pytest.approx(base * m**-b, rel=1e-11)

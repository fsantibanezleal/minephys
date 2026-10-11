"""T-003-010 (P-003-01, P-003-02, P-003-03): metamorphic properties of the Hoek-Brown functions.

P-003-01: scaling sigma3 and sigma_ci by k scales sigma1, sigma_c, sigma_t, sigma_cm and the equivalent
cohesion (with sigma3_max scaled too) by k and leaves the friction angle unchanged (Pa <-> MPa unit-change
invariance; TC-1). P-003-02: mb and s strictly increase with GSI and strictly decrease with D; sigma1 strictly
increases with sigma3 and GSI and decreases with D; the equivalent friction angle does not increase with
sigma3_max (exact ordering, pairs with a relative gap of at least 1e-3). P-003-03: GSI = 100 gives s = 1, mb =
mi, a = 1/2 (any D), and sigma1(sigma_t) = sigma_t. Generators (spec 003): GSI in [10, 100], mi in [4, 33], D
in [0, 1], k in [1e-6, 1e6]; sigma3 in [0, 0.25 sigma_ci].

Oracle: analytical (homogeneity of degree one of the criterion in the stresses; signs of the derivatives of
the equations).
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

CFG = settings(deadline=None)
gsi_s = st.floats(10.0, 100.0)
mi_s = st.floats(4.0, 33.0)
d_s = st.floats(0.0, 1.0)
k_s = st.floats(1e-6, 1e6)
SCI = 50.0e6


def gapped(a: float, b: float, rel: float = 1e-3) -> bool:
    return abs(a - b) > rel * max(abs(a), abs(b), 1e-12)


@pytest.mark.req("P-003-01")
@pytest.mark.oracle(
    "analytical", "sigma1, sigma_c, sigma_t, sigma_cm are homogeneous of degree one in (sigma3, sigma_ci)"
)
@CFG
@given(gsi=gsi_s, mi=mi_s, d=d_s, k=k_s, frac=st.floats(0.0, 0.25))
def test_stress_scaling(gsi: float, mi: float, d: float, k: float, frac: float) -> None:
    mb, s, a = G.hoek_brown_parameters(gsi, mi, d)
    s3 = frac * SCI
    assert float(G.hoek_brown_sigma1(k * s3, k * SCI, mb, s, a)) == pytest.approx(
        k * float(G.hoek_brown_sigma1(s3, SCI, mb, s, a)), rel=1e-11
    )
    assert float(G.hoek_brown_uniaxial_strength(k * SCI, s, a)) == pytest.approx(
        k * float(G.hoek_brown_uniaxial_strength(SCI, s, a)), rel=1e-12
    )
    assert float(G.hoek_brown_tensile_strength(k * SCI, mb, s)) == pytest.approx(
        k * float(G.hoek_brown_tensile_strength(SCI, mb, s)), rel=1e-12
    )
    assert float(G.hoek_brown_rock_mass_strength(k * SCI, mb, s, a)) == pytest.approx(
        k * float(G.hoek_brown_rock_mass_strength(SCI, mb, s, a)), rel=1e-12
    )


@pytest.mark.req("P-003-01")
@pytest.mark.oracle(
    "analytical", "equivalent Mohr-Coulomb: cohesion scales with the stress unit, the friction angle does not"
)
@CFG
@given(gsi=gsi_s, mi=mi_s, d=d_s, k=k_s, frac=st.floats(0.002, 0.25))
def test_equivalent_mohr_coulomb_unit_change(gsi: float, mi: float, d: float, k: float, frac: float) -> None:
    mb, s, a = G.hoek_brown_parameters(gsi, mi, d)
    c1, phi1 = G.equivalent_mohr_coulomb(SCI, mb, s, a, frac * SCI)
    c2, phi2 = G.equivalent_mohr_coulomb(k * SCI, mb, s, a, k * frac * SCI)
    assert float(c2) == pytest.approx(k * float(c1), rel=1e-11)
    assert float(phi2) == pytest.approx(float(phi1), rel=1e-11)


@pytest.mark.req("P-003-02")
@pytest.mark.oracle("analytical", "mb and s increase with GSI and decrease with D")
@CFG
@given(g1=gsi_s, g2=gsi_s, d1=d_s, d2=d_s, mi=mi_s)
def test_parameters_are_monotone(g1: float, g2: float, d1: float, d2: float, mi: float) -> None:
    assume(gapped(g1, g2) and gapped(d1, d2, 1e-2))
    glo, ghi = sorted((g1, g2))
    dlo, dhi = sorted((d1, d2))
    mb_lo, s_lo, _ = G.hoek_brown_parameters(glo, mi, 0.4)
    mb_hi, s_hi, _ = G.hoek_brown_parameters(ghi, mi, 0.4)
    assert mb_lo < mb_hi
    assert s_lo < s_hi
    mb_d0, s_d0, _ = G.hoek_brown_parameters(60.0, mi, dlo)
    mb_d1, s_d1, _ = G.hoek_brown_parameters(60.0, mi, dhi)
    assert mb_d1 < mb_d0
    assert s_d1 < s_d0


@pytest.mark.req("P-003-02")
@pytest.mark.oracle("analytical", "sigma1 increases with sigma3 and with GSI, and decreases with the disturbance")
@CFG
@given(g1=gsi_s, g2=gsi_s, d1=d_s, d2=d_s, mi=mi_s, f1=st.floats(0.0, 0.25), f2=st.floats(0.0, 0.25))
def test_sigma1_is_monotone(g1: float, g2: float, d1: float, d2: float, mi: float, f1: float, f2: float) -> None:
    assume(gapped(g1, g2) and gapped(d1, d2, 1e-2) and gapped(f1, f2, 1e-2))
    mb, s, a = G.hoek_brown_parameters(60.0, mi, 0.3)
    lo, hi = sorted((f1, f2))
    assert float(G.hoek_brown_sigma1(lo * SCI, SCI, mb, s, a)) < float(G.hoek_brown_sigma1(hi * SCI, SCI, mb, s, a))
    glo, ghi = sorted((g1, g2))
    s3 = 0.1 * SCI
    low = G.hoek_brown_sigma1(s3, SCI, *G.hoek_brown_parameters(glo, mi, 0.3))
    high = G.hoek_brown_sigma1(s3, SCI, *G.hoek_brown_parameters(ghi, mi, 0.3))
    assert float(low) < float(high)
    dlo, dhi = sorted((d1, d2))
    undisturbed = G.hoek_brown_sigma1(s3, SCI, *G.hoek_brown_parameters(60.0, mi, dlo))
    disturbed = G.hoek_brown_sigma1(s3, SCI, *G.hoek_brown_parameters(60.0, mi, dhi))
    assert float(disturbed) < float(undisturbed)


@pytest.mark.req("P-003-02")
@pytest.mark.oracle("analytical", "the equivalent friction angle does not increase with the confining stress limit")
@CFG
@given(gsi=gsi_s, mi=mi_s, d=d_s, f1=st.floats(0.002, 0.25), f2=st.floats(0.002, 0.25))
def test_equivalent_friction_decreases_with_sigma3_max(gsi: float, mi: float, d: float, f1: float, f2: float) -> None:
    assume(gapped(f1, f2, 1e-2))
    mb, s, a = G.hoek_brown_parameters(gsi, mi, d)
    lo, hi = sorted((f1, f2))
    _, phi_lo = G.equivalent_mohr_coulomb(SCI, mb, s, a, lo * SCI)
    _, phi_hi = G.equivalent_mohr_coulomb(SCI, mb, s, a, hi * SCI)
    assert float(phi_hi) <= float(phi_lo)


@pytest.mark.req("P-003-03")
@pytest.mark.oracle("analytical", "identities of the intact-rock limit and of the tensile cut-off for arbitrary mi, D")
@CFG
@given(mi=mi_s, d=d_s, sci=st.floats(1e6, 5e8))
def test_intact_limit_and_tensile_identity(mi: float, d: float, sci: float) -> None:
    mb, s, a = G.hoek_brown_parameters(100.0, mi, d)
    assert (mb, s, a) == (mi, 1.0, 0.5)
    st_ = G.hoek_brown_tensile_strength(sci, mb, s)
    assert float(G.hoek_brown_sigma1(st_, sci, mb, s, a)) == pytest.approx(float(st_), rel=1e-12)

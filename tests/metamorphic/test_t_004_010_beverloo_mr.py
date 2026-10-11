"""T-004-010 (P-004-01, P-004-02, FR-004-01): metamorphic properties of Beverloo's discharge law.

P-004-01: the discharge is linear in bulk density and in the discharge coefficient C, scales as sqrt(g), and
scales by lambda^(5/2) when the orifice and particle diameters both scale by lambda (and hence is invariant
under the m <-> mm, kg <-> g unit change); P-004-02: it is strictly increasing in the orifice diameter and
strictly decreasing in the particle diameter and in the annulus coefficient k (exact ordering).

Generators (spec 004 P-004-01 and plan: the condition number (5/2) D / (D - k d) is kept at most 27.5 by D >=
1.1 k d): D in [0.05, 2] m, d in [1e-4, 0.05] m, k in [1, 3] with D >= 1.1 k d, rho_b in [300, 4000] kg/m^3, C
in [0.4, 0.8], g in [1, 25] m/s^2, lambda in [1e-3, 1e3]. Tolerance TC-1 (rtol 1e-12; the condition number
multiplies the 1e-16 rounding by at most 28 and by 2.5 for the power); monotonicity compares pairs whose free
opening differs by at least a relative 1e-6.

Oracle: analytical (dimensional analysis of the exponent 5/2: kg/s = (kg/m^3) (m/s^2)^(1/2) m^(5/2)).
"""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from minephys.knowledge import UnverifiedParameterWarning

from minephys import bulk as B

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

CFG = settings(deadline=None)
G0 = 9.80665


@st.composite
def case(draw):
    k = draw(st.floats(1.0, 3.0))
    d = draw(st.floats(1e-4, 0.05))
    orifice = draw(st.floats(0.05, 2.0))
    assume(orifice >= 1.1 * k * d)
    return {
        "orifice_diameter": orifice,
        "particle_diameter": d,
        "bulk_density": draw(st.floats(300.0, 4000.0)),
        "discharge_coefficient": draw(st.floats(0.4, 0.8)),
        "annulus_coefficient": k,
        "g": draw(st.floats(1.0, 25.0)),
    }


def q(c: dict, **over) -> float:
    return float(B.beverloo_discharge(**{**c, **over}))


@pytest.mark.req("P-004-01")
@pytest.mark.oracle("analytical", "independent recomputation C rho sqrt(g) (D - k d)^(5/2)")
@CFG
@given(c=case())
def test_closed_form(c: dict) -> None:
    ref = (
        c["discharge_coefficient"]
        * c["bulk_density"]
        * math.sqrt(c["g"])
        * (c["orifice_diameter"] - c["annulus_coefficient"] * c["particle_diameter"]) ** 2.5
    )
    assert q(c) == pytest.approx(ref, rel=1e-12)


@pytest.mark.req("P-004-01")
@pytest.mark.oracle("analytical", "linear in bulk density and in C; sqrt(g)")
@CFG
@given(c=case(), a=st.floats(1e-3, 1e3), b=st.floats(1e-3, 1e3), gm=st.floats(1e-2, 1e2))
def test_linear_and_root_scaling(c: dict, a: float, b: float, gm: float) -> None:
    base = q(c)
    assert q(c, bulk_density=a * c["bulk_density"]) == pytest.approx(a * base, rel=1e-12)
    assert q(c, discharge_coefficient=b * c["discharge_coefficient"]) == pytest.approx(b * base, rel=1e-12)
    assert q(c, g=gm * c["g"]) == pytest.approx(math.sqrt(gm) * base, rel=1e-12)


@pytest.mark.req("P-004-01")
@pytest.mark.oracle("analytical", "scaling both diameters by lambda scales the discharge by lambda^(5/2)")
@CFG
@given(c=case(), lam=st.floats(1e-3, 1e3))
def test_length_scaling(c: dict, lam: float) -> None:
    scaled = q(c, orifice_diameter=lam * c["orifice_diameter"], particle_diameter=lam * c["particle_diameter"])
    assert scaled == pytest.approx(lam**2.5 * q(c), rel=1e-12)


@pytest.mark.req("P-004-01")
@pytest.mark.oracle(
    "analytical", "unit-change invariance: lengths m -> mm, mass kg -> g (rho x 1e-6, g x 1e3, Q x 1e3)"
)
@CFG
@given(c=case())
def test_unit_change(c: dict) -> None:
    mm = q(
        c,
        orifice_diameter=1e3 * c["orifice_diameter"],
        particle_diameter=1e3 * c["particle_diameter"],
        bulk_density=1e-6 * c["bulk_density"],
        g=1e3 * c["g"],
    )
    assert mm == pytest.approx(1e3 * q(c), rel=1e-12)


@pytest.mark.req("P-004-01")
@pytest.mark.oracle("analytical", "exponents recovered from two evaluations: rho^1, C^1, g^(1/2), lambda^(5/2)")
@CFG
@given(c=case())
def test_exponents(c: dict) -> None:
    base = q(c)
    assert math.log(q(c, bulk_density=2.0 * c["bulk_density"]) / base) / math.log(2.0) == pytest.approx(1.0, rel=1e-10)
    assert math.log(q(c, discharge_coefficient=2.0 * c["discharge_coefficient"]) / base) / math.log(
        2.0
    ) == pytest.approx(1.0, rel=1e-10)
    assert math.log(q(c, g=4.0 * c["g"]) / base) / math.log(4.0) == pytest.approx(0.5, rel=1e-10)
    both = q(c, orifice_diameter=2.0 * c["orifice_diameter"], particle_diameter=2.0 * c["particle_diameter"])
    assert math.log(both / base) / math.log(2.0) == pytest.approx(2.5, rel=1e-10)


@pytest.mark.req("P-004-02")
@pytest.mark.oracle("analytical", "strictly increasing in the orifice diameter")
@CFG
@given(c=case(), grow=st.floats(1e-3, 3.0))
def test_increasing_in_orifice(c: dict, grow: float) -> None:
    wider = c["orifice_diameter"] * (1.0 + grow)
    assert q(c, orifice_diameter=wider) > q(c)


@pytest.mark.req("P-004-02")
@pytest.mark.oracle("analytical", "strictly decreasing in the particle diameter and in the annulus coefficient")
@CFG
@given(c=case(), grow=st.floats(1e-3, 0.5))
def test_decreasing_in_particle_and_k(c: dict, grow: float) -> None:
    d2 = c["particle_diameter"] * (1.0 + grow)
    k2 = c["annulus_coefficient"] * (1.0 + grow)
    assume(c["orifice_diameter"] > k2 * c["particle_diameter"] * (1.0 + 1e-6))
    assume(c["orifice_diameter"] > c["annulus_coefficient"] * d2 * (1.0 + 1e-6))
    base = q(c)
    assert q(c, particle_diameter=d2) < base
    assert q(c, annulus_coefficient=k2) < base


@pytest.mark.req("FR-004-01")
@pytest.mark.oracle("analytical", "the UNVERIFIED exponent row warns on every call, for any valid input")
@CFG
@given(c=case())
def test_always_warns_about_the_unverified_row(c: dict) -> None:
    with pytest.warns(UnverifiedParameterWarning):
        B.beverloo_discharge(**c)

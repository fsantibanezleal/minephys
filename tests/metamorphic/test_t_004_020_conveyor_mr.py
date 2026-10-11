# ruff: noqa: E501
"""T-004-020 (P-004-04, P-004-05, P-004-06, FR-004-05..07): metamorphic properties of the conveyor functions.

P-004-04: conveyor capacity is linear in each argument; `cema_effective_tension` is affine in the length and
strictly increasing in the lift (the material weight is positive) and in the material weight; the monotonicity
in the material weight needs L K_y + H > 0 (its coefficient), which the generator enforces: the spec states
the property for all H in [-500, 500] m, but for a steep enough decline the coefficient is negative. P-004-05:
with K_x = K_y = 0, no belt weight, no pulley, acceleration or accessory tension and W_m = m g0 / V,
`conveyor_power(cema_effective_tension(...), V)` equals m g0 H (efficiency 1, either sign of H). P-004-06: the
equation is dimensionally homogeneous: evaluated with ft, lbf/ft and lbf it gives the SI tension in lbf, 1 lbf
= 0.45359237 kg x 9.80665 m/s^2 = 4.4482216152605 N exactly. Power relations: linear in speed and in a
non-negative tension, regenerated power bounded in magnitude by T_e V.

Generators (spec 004 P-004-04..06): L in [1, 2e4] m, H in [-500, 500] m, m in [1, 3e3] kg/s, V in [0.5, 8]
m/s, W_b in [0, 300] N/m, W_m in [1, 5e3] N/m, K_t in [0.5, 2], K_x in [0, 50] N/m, K_y in [0.01, 0.05], extra
tensions in [0, 1e4] N, scale factors in [1e-3, 1e3]. Tolerance TC-1 (rtol 1e-12, with an absolute floor of
1e-12 times the sum of the absolute terms where terms of opposite sign cancel); monotonicity compares values
at least a relative 1e-6 apart.

Oracle: analytical (the equation of FR-004-06 recomputed in the test, conservation of energy, exact unit definitions).
"""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import bulk as B

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

CFG = settings(deadline=None)
G0 = 9.80665
FT = 0.3048
LBF = 0.45359237 * G0  # N, exact
LBF_PER_FT = LBF / FT  # N/m per lbf/ft


@st.composite
def belt(draw):
    return {
        "length": draw(st.floats(1.0, 2e4)),
        "lift": draw(st.floats(-500.0, 500.0)),
        "belt_weight": draw(st.floats(0.0, 300.0)),
        "material_weight": draw(st.floats(1.0, 5e3)),
        "kt": draw(st.floats(0.5, 2.0)),
        "kx": draw(st.floats(0.0, 50.0)),
        "ky": draw(st.floats(0.01, 0.05)),
        "pulley_tension": draw(st.floats(0.0, 1e4)),
        "acceleration_tension": draw(st.floats(0.0, 1e4)),
        "accessory_tension": draw(st.floats(0.0, 1e4)),
    }


def terms(c: dict) -> tuple[float, float]:
    """The equation recomputed independently: (value, sum of the absolute terms)."""
    first = c["length"] * c["kt"] * (c["kx"] + c["ky"] * c["belt_weight"] + 0.015 * c["belt_weight"])
    second = c["material_weight"] * (c["length"] * c["ky"] + c["lift"])
    extra = c["pulley_tension"] + c["acceleration_tension"] + c["accessory_tension"]
    return first + second + extra, abs(first) + abs(second) + abs(extra)


def te(c: dict, **over) -> float:
    return float(B.cema_effective_tension(**{**c, **over}))


@pytest.mark.req("P-004-04")
@pytest.mark.req("FR-004-06")
@pytest.mark.oracle("analytical", "the equation of FR-004-06 recomputed in the test")
@CFG
@given(c=belt())
def test_matches_the_equation(c: dict) -> None:
    value, scale = terms(c)
    assert te(c) == pytest.approx(value, rel=1e-12, abs=1e-12 * scale)


@pytest.mark.req("P-004-04")
@pytest.mark.req("FR-004-05")
@pytest.mark.oracle("analytical", "conveyor capacity is linear in each of its three arguments")
@CFG
@given(
    a=st.floats(0.01, 2.0),
    v=st.floats(0.1, 10.0),
    rho=st.floats(100.0, 5000.0),
    ka=st.floats(1e-3, 1e3),
    kv=st.floats(1e-3, 1e3),
    kr=st.floats(1e-3, 1e3),
)
def test_capacity_is_multilinear(a: float, v: float, rho: float, ka: float, kv: float, kr: float) -> None:
    base = float(B.conveyor_capacity(a, v, rho))
    assert base == pytest.approx(rho * a * v, rel=1e-14)
    assert float(B.conveyor_capacity(ka * a, v, rho)) == pytest.approx(ka * base, rel=1e-13)
    assert float(B.conveyor_capacity(a, kv * v, rho)) == pytest.approx(kv * base, rel=1e-13)
    assert float(B.conveyor_capacity(a, v, kr * rho)) == pytest.approx(kr * base, rel=1e-13)


@pytest.mark.req("P-004-04")
@pytest.mark.oracle("analytical", "affine in the length: equally spaced lengths have a constant first difference")
@CFG
@given(c=belt(), step=st.floats(1.0, 5e3))
def test_affine_in_length(c: dict, step: float) -> None:
    l0 = c["length"]
    t0, t1, t2 = (te(c, length=l0 + i * step) for i in range(3))
    scale = abs(t0) + abs(t1) + abs(t2) + 1.0
    assert (t2 - t1) == pytest.approx(t1 - t0, rel=1e-9, abs=1e-12 * scale)
    slope = c["kt"] * (c["kx"] + c["ky"] * c["belt_weight"] + 0.015 * c["belt_weight"]) + c["material_weight"] * c["ky"]
    assert (t1 - t0) == pytest.approx(step * slope, rel=1e-9, abs=1e-12 * scale)


@pytest.mark.req("P-004-04")
@pytest.mark.oracle(
    "analytical",
    "strictly increasing in the lift (positive material weight) and, when L Ky + H > 0, in the material weight",
)
@CFG
@given(c=belt(), dh=st.floats(1e-3, 100.0), grow=st.floats(1e-3, 3.0))
def test_monotonicity(c: dict, dh: float, grow: float) -> None:
    assert te(c, lift=c["lift"] + dh) > te(c)
    assume(c["length"] * c["ky"] + c["lift"] > 1e-3)
    assert te(c, material_weight=c["material_weight"] * (1.0 + grow)) > te(c)


@pytest.mark.req("P-004-04")
@pytest.mark.oracle(
    "analytical", "each extra tension and the kt group enter with a positive sign: raising any of them raises T_e"
)
@CFG
@given(c=belt(), extra=st.floats(1.0, 1e4))
def test_extra_tensions_add(c: dict, extra: float) -> None:
    base = te(c)
    for name in ("pulley_tension", "acceleration_tension", "accessory_tension"):
        assert te(c, **{name: c[name] + extra}) == pytest.approx(
            base + extra, rel=1e-9, abs=1e-12 * (abs(base) + extra)
        )


@pytest.mark.req("P-004-05")
@pytest.mark.req("FR-004-07")
@pytest.mark.oracle(
    "analytical", "conservation of energy: a frictionless, weightless belt needs exactly the lift power m g0 H"
)
@CFG
@given(
    mdot=st.floats(1.0, 3e3),
    v=st.floats(0.5, 8.0),
    h=st.floats(-500.0, 500.0),
    length=st.floats(1.0, 2e4),
    kt=st.floats(0.0, 3.0),
)
def test_lift_power_floor(mdot: float, v: float, h: float, length: float, kt: float) -> None:
    tension = B.cema_effective_tension(length, h, 0.0, mdot * G0 / v, kt, 0.0, 0.0)
    power = float(B.conveyor_power(tension, v))
    assert power == pytest.approx(mdot * G0 * h, rel=1e-12, abs=1e-9)


@pytest.mark.req("P-004-05")
@pytest.mark.req("FR-004-07")
@pytest.mark.oracle(
    "analytical", "with a drive efficiency the lift floor is divided (lifting) or multiplied (regenerating) by it"
)
@CFG
@given(mdot=st.floats(1.0, 3e3), v=st.floats(0.5, 8.0), h=st.floats(-500.0, 500.0), eta=st.floats(0.05, 1.0))
def test_lift_power_floor_with_efficiency(mdot: float, v: float, h: float, eta: float) -> None:
    tension = B.cema_effective_tension(1000.0, h, 0.0, mdot * G0 / v, 1.0, 0.0, 0.0)
    expected = mdot * G0 * h / eta if h >= 0 else mdot * G0 * h * eta
    assert float(B.conveyor_power(tension, v, eta)) == pytest.approx(expected, rel=1e-12, abs=1e-9)


@pytest.mark.req("P-004-06")
@pytest.mark.req("FR-004-06")
@pytest.mark.oracle(
    "analytical",
    "dimensional homogeneity: ft, lbf/ft, lbf in -> lbf out; times 4.4482216152605 N/lbf equals the SI call on the converted inputs",
)
@CFG
@given(c=belt())
def test_imperial_unit_invariance(c: dict) -> None:
    imperial = {
        "length": c["length"] / FT,
        "lift": c["lift"] / FT,
        "belt_weight": c["belt_weight"] / LBF_PER_FT,
        "material_weight": c["material_weight"] / LBF_PER_FT,
        "kt": c["kt"],
        "kx": c["kx"] / LBF_PER_FT,
        "ky": c["ky"],
        "pulley_tension": c["pulley_tension"] / LBF,
        "acceleration_tension": c["acceleration_tension"] / LBF,
        "accessory_tension": c["accessory_tension"] / LBF,
    }
    value, scale = terms(c)
    si = te(c)
    lbf = te(imperial)
    assert lbf * LBF == pytest.approx(si, rel=1e-11, abs=1e-11 * scale)
    assert si == pytest.approx(value, rel=1e-12, abs=1e-12 * scale)


@pytest.mark.req("FR-004-07")
@pytest.mark.oracle(
    "analytical",
    "power is linear in the belt speed and in a non-negative tension; the regenerated power is bounded by T V",
)
@CFG
@given(
    tension=st.floats(1.0, 1e6),
    v=st.floats(0.5, 8.0),
    eta=st.floats(0.05, 1.0),
    k=st.floats(1e-3, 1e3),
    t2=st.floats(1.0, 1e6),
)
def test_power_relations(tension: float, v: float, eta: float, k: float, t2: float) -> None:
    p = float(B.conveyor_power(tension, v, eta))
    assert p == pytest.approx(tension * v / eta, rel=1e-13)
    assert float(B.conveyor_power(tension, k * v, eta)) == pytest.approx(k * p, rel=1e-12)
    assert float(B.conveyor_power(tension + t2, v, eta)) == pytest.approx(
        p + float(B.conveyor_power(t2, v, eta)), rel=1e-12
    )
    regen = float(B.conveyor_power(-tension, v, eta))
    assert regen == pytest.approx(-tension * v * eta, rel=1e-13)
    assert -tension * v <= regen <= 0.0
    assert math.isclose(regen, -p * eta * eta, rel_tol=1e-12)

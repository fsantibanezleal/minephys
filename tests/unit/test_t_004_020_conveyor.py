# ruff: noqa: E501
"""T-004-020 (FR-004-05, FR-004-06, FR-004-07): belt-conveyor capacity, CEMA effective tension and drive power.

Expected API, module `minephys.bulk` (elementwise, float64; a scalar call gives a NumPy float64):

    conveyor_capacity(load_area, belt_speed, bulk_density) -> rho_b A V                                   [kg/s]
    cema_effective_tension(length, lift, belt_weight, material_weight, kt, kx, ky, pulley_tension=0,
                           acceleration_tension=0, accessory_tension=0) ->
        T_e = L K_t (K_x + K_y W_b + 0.015 W_b) + W_m (L K_y + H) + T_p + T_am + T_ac                      [N] with L,
        H [m] (H may be negative: a decline), W_b and W_m [N/m], K_x [N/m], K_t and K_y [1] and the extra tensions
        [N]; the coefficient 0.015 is the UNVERIFIED row `cema_return_belt_coefficient`, so every call emits
        `minephys.knowledge.UnverifiedParameterWarning` (spec 004 section 7.6).
    conveyor_power(effective_tension, belt_speed, drive_efficiency=1) -> T_e V / eta when T_e >= 0 and T_e V eta
    (<= 0, the
        regenerated power) when T_e < 0                                                                      [W]

Oracles: spec 004 section 7.4 (capacity of 0.25 m^2 at 4 m/s and 1600 kg/m^3 = 1600 kg/s = 5,760 t/h; the lift
floor of 2,000 t/h at 4 m/s over 30 m: material weight 1,362.0347 N/m, T_e = 40,861.042 N and P = 163,444.17 W
= m g0 H; the full case `cema_effective_tension(1000, 30, 300, 1362.0347, 1.0, 10, 0.03)` = 105,222.08 N and
`conveyor_power(., 4, 0.9)` = 467,653.70 W; TC-2), hand evaluation of each term of the CEMA equation written
in this file (the 0.015 term isolated with every other term zeroed; the decline case), and the lift-power
conservation identity (P-004-05). Closed forms TC-1.
"""

from __future__ import annotations

import inspect
import math
import warnings

import numpy as np
import pytest
from minephys.knowledge import UnverifiedParameterWarning

import minephys
from minephys import bulk as B

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

G0 = 9.80665
MDOT = 2000.0 / 3.6  # 2,000 t/h in kg/s
WM = MDOT * G0 / 4.0  # material weight per metre of belt, 1,362.0347... N/m


def tension(length=1000.0, lift=30.0, wb=300.0, wm=WM, kt=1.0, kx=10.0, ky=0.03, **extra):
    return B.cema_effective_tension(length, lift, wb, wm, kt, kx, ky, **extra)


@pytest.mark.req("FR-004-05")
@pytest.mark.oracle("hand-calculation", "spec 004 7.4: conveyor_capacity(0.25, 4, 1600) = 1,600 kg/s (5,760 t/h)")
def test_spec_capacity() -> None:
    q = B.conveyor_capacity(0.25, 4.0, 1600.0)
    assert type(q) is np.float64
    assert q == pytest.approx(1600.0, rel=1e-15)
    assert float(q) * 3.6 == pytest.approx(5760.0, rel=1e-14)


@pytest.mark.req("FR-004-05")
@pytest.mark.oracle(
    "analytical",
    "continuity: mass flow = density x cross-section x speed, linear in each factor; elementwise over arrays",
)
def test_capacity_continuity_and_arrays() -> None:
    a = np.array([[0.1], [0.2]])
    v = np.array([1.0, 2.0, 4.0])
    q = B.conveyor_capacity(a, v, 1500.0)
    assert q.shape == (2, 3)
    assert q.dtype == np.float64
    np.testing.assert_allclose(q, 1500.0 * a * v, rtol=1e-15)
    assert B.conveyor_capacity(0.25, 4.0, 3200.0) == pytest.approx(2.0 * 1600.0, rel=1e-15)


@pytest.mark.req("FR-004-06")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 7.4: cema_effective_tension(1000, 30, 300, 1362.0347..., 1.0, 10, 0.03) = 105,222.08 N; conveyor_power(., 4, 0.9) = 467,653.70 W",
)
def test_spec_full_case() -> None:
    te = tension()
    assert type(te) is np.float64
    assert te == pytest.approx(105_222.08, abs=5e-3)  # TC-2
    assert te == pytest.approx(
        1000.0 * 1.0 * (10.0 + 0.03 * 300.0 + 0.015 * 300.0) + WM * (1000.0 * 0.03 + 30.0), rel=1e-13
    )
    p = B.conveyor_power(te, 4.0, 0.9)
    assert type(p) is np.float64
    assert p == pytest.approx(467_653.70, abs=5e-3)  # TC-2
    assert p == pytest.approx(float(te) * 4.0 / 0.9, rel=1e-14)


@pytest.mark.req("FR-004-06")
@pytest.mark.req("FR-004-07")
@pytest.mark.req("P-004-05")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 7.4 lift floor: 2,000 t/h at 4 m/s, H = 30 m, no friction and no belt weight: T_e = 40,861.042 N, P = 163,444.17 W = m g0 H",
)
def test_spec_lift_floor() -> None:
    assert pytest.approx(1362.0347, abs=5e-5) == WM
    te = B.cema_effective_tension(1000.0, 30.0, 0.0, WM, 1.0, 0.0, 0.0)
    assert te == pytest.approx(40_861.042, abs=5e-4)  # TC-2
    p = B.conveyor_power(te, 4.0)
    assert p == pytest.approx(163_444.17, abs=5e-3)  # TC-2
    assert p == pytest.approx(MDOT * G0 * 30.0, rel=1e-13)  # the conservation identity


@pytest.mark.req("FR-004-06")
@pytest.mark.oracle(
    "hand-calculation",
    "each term of the equation isolated: L Kt Kx, L Kt Ky Wb, 0.015 L Kt Wb, Wm L Ky, Wm H, and the three extra tensions",
)
def test_terms_one_by_one() -> None:
    zero = {"kx": 0.0, "ky": 0.0, "wb": 0.0, "wm": 0.0}
    assert tension(lift=0.0, **zero) == 0.0
    assert tension(lift=0.0, **{**zero, "kx": 10.0}) == pytest.approx(1000.0 * 1.0 * 10.0, rel=1e-15)  # L Kt Kx
    assert tension(lift=0.0, **{**zero, "ky": 0.03, "wb": 300.0}) == pytest.approx(
        1000.0 * 0.03 * 300.0 + 0.015 * 1000.0 * 300.0, rel=1e-14
    )
    assert tension(lift=0.0, **{**zero, "wb": 300.0}) == pytest.approx(
        4500.0, rel=1e-14
    )  # the 0.015 term alone: 1000 x 0.015 x 300
    assert tension(lift=0.0, **{**zero, "wm": 1362.0, "ky": 0.03}) == pytest.approx(
        1362.0 * 1000.0 * 0.03, rel=1e-14
    )  # Wm L Ky
    assert tension(lift=30.0, **{**zero, "wm": 1362.0}) == pytest.approx(1362.0 * 30.0, rel=1e-14)  # Wm H
    base = tension()
    assert tension(pulley_tension=1000.0, acceleration_tension=2000.0, accessory_tension=3000.0) == pytest.approx(
        float(base) + 6000.0, rel=1e-13
    )
    assert tension(pulley_tension=1000.0) == pytest.approx(float(base) + 1000.0, rel=1e-13)
    assert tension(acceleration_tension=2000.0) == pytest.approx(float(base) + 2000.0, rel=1e-13)
    assert tension(accessory_tension=3000.0) == pytest.approx(float(base) + 3000.0, rel=1e-13)


@pytest.mark.req("FR-004-06")
@pytest.mark.oracle(
    "hand-calculation",
    "kt multiplies the first group only: doubling kt adds exactly L Kt (Kx + Ky Wb + 0.015 Wb) = 23,500 N",
)
def test_kt_scales_the_belt_group() -> None:
    assert tension(kt=2.0) == pytest.approx(float(tension(kt=1.0)) + 23_500.0, rel=1e-13)
    assert tension(kt=0.0) == pytest.approx(WM * (1000.0 * 0.03 + 30.0), rel=1e-13)


@pytest.mark.req("FR-004-06")
@pytest.mark.oracle(
    "hand-calculation",
    "a decline (negative lift) lowers the tension and may make it negative: H = -50 m gives 23,500 + 1362.0347 (30 - 50) = -3,740.69 N",
)
def test_decline() -> None:
    te = tension(lift=-50.0)
    assert te == pytest.approx(23_500.0 + WM * (30.0 - 50.0), rel=1e-12)
    assert te == pytest.approx(-3_740.69, abs=5e-3)
    assert float(te) < 0.0
    assert tension(lift=-50.0) < tension(lift=0.0) < tension(lift=50.0)


@pytest.mark.req("FR-004-06")
@pytest.mark.oracle("analytical", "the three extra tensions default to zero; kt, kx, ky have no default")
def test_defaults() -> None:
    params = inspect.signature(B.cema_effective_tension).parameters
    assert list(params) == [
        "length",
        "lift",
        "belt_weight",
        "material_weight",
        "kt",
        "kx",
        "ky",
        "pulley_tension",
        "acceleration_tension",
        "accessory_tension",
    ]
    for name in ("length", "lift", "belt_weight", "material_weight", "kt", "kx", "ky"):
        assert params[name].default is inspect.Parameter.empty, (
            f"{name} has no default (the factors come from the user's copy of the standard)"
        )
    for name in ("pulley_tension", "acceleration_tension", "accessory_tension"):
        assert params[name].default == 0
    with pytest.raises(TypeError):
        B.cema_effective_tension(1000.0, 30.0, 300.0, WM, 1.0, 10.0)  # type: ignore[call-arg]
    assert tension() == B.cema_effective_tension(1000.0, 30.0, 300.0, WM, 1.0, 10.0, 0.03, 0.0, 0.0, 0.0)


@pytest.mark.req("FR-004-06")
@pytest.mark.oracle(
    "analytical",
    "spec 004 7.6: the UNVERIFIED return-belt coefficient makes every call warn; the other conveyor functions do not",
)
def test_unverified_coefficient_warns_only_in_the_cema_function() -> None:
    with pytest.warns(UnverifiedParameterWarning):
        tension()
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        out = tension()
    assert any(issubclass(w.category, UnverifiedParameterWarning) for w in rec)
    assert math.isfinite(float(out))
    assert not any(issubclass(w.category, minephys.ValidityWarning) for w in rec)
    with warnings.catch_warnings(record=True) as rec2:
        warnings.simplefilter("always")
        B.conveyor_capacity(0.25, 4.0, 1600.0)
        B.conveyor_power(40_000.0, 4.0, 0.9)
    assert [w for w in rec2 if issubclass(w.category, UnverifiedParameterWarning)] == []


@pytest.mark.req("FR-004-06")
@pytest.mark.oracle("analytical", "elementwise over broadcast arrays: every element equals the scalar call")
def test_tension_arrays() -> None:
    length = np.array([[500.0], [1000.0], [2000.0]])
    lift = np.array([-20.0, 0.0, 30.0, 60.0])
    te = B.cema_effective_tension(length, lift, 300.0, WM, 1.0, 10.0, 0.03)
    assert te.shape == (3, 4)
    assert te.dtype == np.float64
    for i in range(3):
        for j in range(4):
            assert te[i, j] == pytest.approx(float(tension(length=float(length[i, 0]), lift=float(lift[j]))), rel=1e-13)


@pytest.mark.req("FR-004-07")
@pytest.mark.oracle(
    "hand-calculation", "T_e >= 0 divides by the efficiency, T_e < 0 multiplies by it (regenerated power, <= 0)"
)
@pytest.mark.parametrize(
    ("te", "v", "eta", "expected"),
    [
        (105_222.08, 4.0, 0.9, 105_222.08 * 4.0 / 0.9),
        (105_222.08, 4.0, 1.0, 105_222.08 * 4.0),
        (40_000.0, 2.5, 0.5, 200_000.0),  # 40000 x 2.5 / 0.5
        (-10_000.0, 4.0, 0.9, -36_000.0),  # -10000 x 4 x 0.9
        (-10_000.0, 4.0, 0.5, -20_000.0),
        (-10_000.0, 4.0, 1.0, -40_000.0),
        (0.0, 4.0, 0.7, 0.0),
    ],
)
def test_power_branches(te: float, v: float, eta: float, expected: float) -> None:
    p = B.conveyor_power(te, v, eta)
    assert type(p) is np.float64
    assert p == pytest.approx(expected, rel=1e-14, abs=0.0)


@pytest.mark.req("FR-004-07")
@pytest.mark.oracle(
    "analytical",
    "the default efficiency is 1; a loss always costs: positive power rises, negative power shrinks in magnitude",
)
def test_power_defaults_and_losses() -> None:
    assert inspect.signature(B.conveyor_power).parameters["drive_efficiency"].default == 1
    assert B.conveyor_power(50_000.0, 3.0) == pytest.approx(150_000.0, rel=1e-15)
    assert B.conveyor_power(-50_000.0, 3.0) == pytest.approx(-150_000.0, rel=1e-15)
    assert float(B.conveyor_power(50_000.0, 3.0, 0.8)) > float(B.conveyor_power(50_000.0, 3.0, 1.0))
    assert abs(float(B.conveyor_power(-50_000.0, 3.0, 0.8))) < abs(float(B.conveyor_power(-50_000.0, 3.0, 1.0)))
    assert float(B.conveyor_power(-50_000.0, 3.0, 0.8)) < 0.0


@pytest.mark.req("FR-004-07")
@pytest.mark.oracle(
    "analytical",
    "the branch is on the sign of T_e: the smallest positive and negative tensions fall on their own sides; arrays mix both",
)
def test_power_sign_branch_on_arrays() -> None:
    te = np.array([-5e3, -1e-9, 0.0, 1e-9, 5e3])
    p = B.conveyor_power(te, 2.0, 0.8)
    np.testing.assert_allclose(
        p, [-5e3 * 2.0 * 0.8, -1e-9 * 2.0 * 0.8, 0.0, 1e-9 * 2.0 / 0.8, 5e3 * 2.0 / 0.8], rtol=1e-14, atol=0.0
    )
    assert p.dtype == np.float64
    assert p.shape == (5,)


@pytest.mark.req("FR-004-07")
@pytest.mark.oracle(
    "analytical", "efficiency 1 makes the two branches one line: P = T_e V for every sign (continuity at T_e = 0)"
)
def test_power_is_continuous_at_unit_efficiency() -> None:
    te = np.linspace(-1e4, 1e4, 41)
    np.testing.assert_allclose(B.conveyor_power(te, 3.5, 1.0), te * 3.5, rtol=1e-15, atol=0.0)


@pytest.mark.req("P-004-05")
@pytest.mark.oracle(
    "analytical",
    "conservation: with efficiency 1 the drive power of a frictionless, weightless belt is the lift power m g0 H, for either sign of H",
)
@pytest.mark.parametrize("lift", [-250.0, -30.0, 0.0, 1.0, 30.0, 400.0])
def test_lift_floor_identity(lift: float) -> None:
    mdot, v = 750.0, 3.0
    te = B.cema_effective_tension(2000.0, lift, 0.0, mdot * G0 / v, 1.0, 0.0, 0.0)
    assert B.conveyor_power(te, v) == pytest.approx(mdot * G0 * lift, rel=1e-13, abs=0.0)
    # with a drive efficiency: divided when lifting, multiplied when regenerating
    eta = 0.85
    expected = mdot * G0 * lift / eta if lift >= 0 else mdot * G0 * lift * eta
    assert B.conveyor_power(te, v, eta) == pytest.approx(expected, rel=1e-13, abs=0.0)

# ruff: noqa: E501
"""T-003-021 (FR-003-09, FR-003-11, FR-003-22): Bishop's simplified method on slice data.

Expected API: `G.bishop_simplified_fos(width, weight, base_angle, pore_pressure, cohesion, friction_angle,
tol=1e-12, max_iter=200)` -> the factor of safety F (numpy.float64), the fixed point, iterated from F = 1
until the relative step is at most `tol`, of

    F = sum[ (c' b + (W - u b) tan(phi')) / m_alpha ] / sum[ W sin(alpha) ],   m_alpha = cos(alpha) (1 +
    tan(alpha) tan(phi') / F)

with `width` b [m], `weight` W [N/m], `base_angle` alpha [rad], `pore_pressure` u [Pa] 1-D per slice (1 to
10,000 slices) and `cohesion` c' [Pa] and `friction_angle` phi' [rad] per slice or scalars. FR-003-11: a
driving moment sum(W sin alpha) <= 0 raises `InputError` naming `base_angle`; a non-positive m_alpha during
the iteration raises `ConvergenceError` whose message names the first such slice index. FR-003-22: no
convergence within `max_iter` (<= 10,000) raises `ConvergenceError`.

Oracles: Rocscience Slide hand calculation #1 (Table 1 p. 1, result p. 9: F = 2.113, TC-2), the spec 003
section 7.4 hand calculations (TC-2 on their printed digits, an independent fixed-point reference written in
this file at TC-3), analytical limits (phi' = 0: F = sum c' l / sum W sin alpha; c' = 0, equal angles, dry: F
= tan phi' / tan beta) and the Fredlund and Krahn (1977) benchmark, Slide verification problem #21 pp. 91-92
(published F 2.080 dry and 1.766 with r_u = 0.25, |dF| <= 0.01; the spec writer's independent values for 100
slices 2.0753 and 1.7589 at TC-2), with imperial inputs converted by the exact definitions 1 ft = 0.3048 m and
1 lbf = 0.45359237 kg * 9.80665 m/s^2.
"""

from __future__ import annotations

import math
import re

import numpy as np
import pytest

import minephys
from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

FT = 0.3048
LBF = 0.45359237 * 9.80665
GAMMA_FK = 120.0 * LBF / FT**3
C_FK = 600.0 * LBF / FT**2
FK_X = np.array([0.0, 60.0, 140.0, 180.0]) * FT
FK_Z = np.array([60.0, 60.0, 20.0, 20.0]) * FT


def ref_bishop(b, w, alpha, u, c, phi):
    """Independent fixed-point reference of the equation in the module docstring (arrays in SI)."""
    b, w, alpha, u = (np.asarray(x, dtype=float) for x in (b, w, alpha, u))
    f = 1.0
    for _ in range(2000):
        m = np.cos(alpha) * (1.0 + np.tan(alpha) * np.tan(phi) / f)
        fn = float(np.sum((c * b + (w - u * b) * np.tan(phi)) / m) / np.sum(w * np.sin(alpha)))
        if abs(fn - f) <= 1e-14 * f:
            return fn
        f = fn
    raise AssertionError("reference did not converge")


def slide1():
    h = np.array([0.8, 2.3, 3.3, 3.9, 4.1, 3.6, 1.65])
    return {
        "width": np.full(7, 2.5),
        "weight": 20000.0 * 2.5 * h,
        "base_angle": np.radians([-9.0, 0.5, 9.0, 18.5, 28.0, 39.0, 52.0]),
        "pore_pressure": np.zeros(7),
        "cohesion": 20000.0,
        "friction_angle": math.radians(20.0),
    }


def three(u=(0.0, 0.0, 0.0)):
    return {
        "width": np.full(3, 2.0),
        "weight": np.array([60.0, 120.0, 80.0]) * 1e3,
        "base_angle": np.radians([5.0, 25.0, 50.0]),
        "pore_pressure": np.array(u) * 1e3,
        "cohesion": 5000.0,
        "friction_angle": math.radians(25.0),
    }


@pytest.mark.req("FR-003-09")
@pytest.mark.oracle(
    "worked-example", "rocscience2020slide hand calculation #1, Table 1 p. 1 and result p. 9: Bishop F = 2.113"
)
def test_slide_hand_calculation_1() -> None:
    kw = slide1()
    got = G.bishop_simplified_fos(**kw)
    assert type(got) is np.float64
    assert got == pytest.approx(2.113, abs=5e-4)  # TC-2: 4 significant figures
    assert got == pytest.approx(2.1129426616, rel=1e-9)  # independent fixed point (TC-3)
    assert got == pytest.approx(
        ref_bishop(
            kw["width"], kw["weight"], kw["base_angle"], kw["pore_pressure"], kw["cohesion"], kw["friction_angle"]
        ),
        rel=1e-9,
    )


@pytest.mark.req("FR-003-09")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: three slices, b = 2 m, W = (60, 120, 80) kN/m, alpha = (5, 25, 50) deg, c' = 5 kPa, phi' = 25 deg, dry: Bishop 1.2842941",
)
def test_three_slices_dry() -> None:
    got = G.bishop_simplified_fos(**three())
    assert got == pytest.approx(1.2842941, abs=5e-8)  # TC-2: 8 significant figures
    kw = three()
    assert got == pytest.approx(
        ref_bishop(kw["width"], kw["weight"], kw["base_angle"], kw["pore_pressure"], 5000.0, math.radians(25.0)),
        rel=1e-9,
    )


@pytest.mark.req("FR-003-09")
@pytest.mark.oracle("hand-calculation", "spec 003 7.4: with u = (0, 20, 10) kPa Bishop F = 1.0026751")
def test_three_slices_with_pore_pressure() -> None:
    got = G.bishop_simplified_fos(**three(u=(0.0, 20.0, 10.0)))
    assert got == pytest.approx(1.0026751, abs=5e-8)
    assert got < G.bishop_simplified_fos(**three())


@pytest.mark.req("FR-003-09")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: phi' = 0, W = (40, 80, 50) kN/m, alpha = (-10, 15, 40) deg, c' = 10 kPa: F = sum c' l / sum W sin(alpha) = 1.4623899",
)
def test_phi_zero_closed_form() -> None:
    alpha = np.radians([-10.0, 15.0, 40.0])
    w = np.array([40.0, 80.0, 50.0]) * 1e3
    b = np.full(3, 2.0)
    got = G.bishop_simplified_fos(b, w, alpha, np.zeros(3), 10000.0, 0.0)
    assert got == pytest.approx(1.4623899, abs=5e-8)
    assert got == pytest.approx(float(np.sum(10000.0 * b / np.cos(alpha)) / np.sum(w * np.sin(alpha))), rel=1e-12)


@pytest.mark.req("FR-003-09")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: c' = 0, phi' = 30 deg, all alpha = 20 deg, dry: F = tan 30 / tan 20 = 1.5862568, whatever the weights",
)
def test_cohesionless_infinite_slope() -> None:
    beta = math.radians(20.0)
    for w in (np.array([1e5, 2e5, 3e5]), np.array([5e4, 5e4, 1e6, 7e3, 2e5])):
        n = len(w)
        got = G.bishop_simplified_fos(
            np.linspace(1.0, 4.0, n), w, np.full(n, beta), np.zeros(n), 0.0, math.radians(30.0)
        )
        assert got == pytest.approx(1.5862568, abs=5e-8)
        assert got == pytest.approx(math.tan(math.radians(30.0)) / math.tan(beta), rel=1e-10)


@pytest.mark.req("FR-003-09")
@pytest.mark.oracle(
    "worked-example",
    "fredlund1977 benchmark as slide verification problem 21, pp. 91-92: dry Bishop F = 2.080 (Slide 2.079); 100 slices give 2.0753",
)
def test_fredlund_krahn_dry() -> None:
    s = G.circular_slices(FK_X, FK_Z, 120.0 * FT, 90.0 * FT, 80.0 * FT, 100, GAMMA_FK)
    got = G.bishop_simplified_fos(s.width, s.weight, s.base_angle, s.pore_pressure, C_FK, math.radians(20.0))
    assert got == pytest.approx(2.080, abs=0.01)  # published, discretisation and figure-read geometry
    assert got == pytest.approx(2.0753, abs=5e-5)  # the spec writer's independent value for 100 slices
    assert got == pytest.approx(
        ref_bishop(s.width, s.weight, s.base_angle, s.pore_pressure, C_FK, math.radians(20.0)), rel=1e-9
    )


@pytest.mark.req("FR-003-09")
@pytest.mark.oracle(
    "worked-example",
    "fredlund1977 as slide verification problem 21: r_u = 0.25 Bishop F = 1.766 (Slide 1.763); 100 slices give 1.7589",
)
def test_fredlund_krahn_with_pore_pressure_ratio() -> None:
    s = G.circular_slices(FK_X, FK_Z, 120.0 * FT, 90.0 * FT, 80.0 * FT, 100, GAMMA_FK, 0.25)
    got = G.bishop_simplified_fos(s.width, s.weight, s.base_angle, s.pore_pressure, C_FK, math.radians(20.0))
    assert got == pytest.approx(1.766, abs=0.01)
    assert got == pytest.approx(1.7589, abs=5e-5)


@pytest.mark.req("FR-003-09")
@pytest.mark.oracle(
    "reference-implementation", "an independent fixed-point reference with per-slice cohesion and friction angle"
)
def test_per_slice_strengths() -> None:
    kw = slide1()
    c = np.array([15e3, 20e3, 25e3, 30e3, 20e3, 10e3, 5e3])
    phi = np.radians([15.0, 20.0, 25.0, 30.0, 25.0, 20.0, 15.0])
    got = G.bishop_simplified_fos(kw["width"], kw["weight"], kw["base_angle"], kw["pore_pressure"], c, phi)
    assert got == pytest.approx(
        ref_bishop(kw["width"], kw["weight"], kw["base_angle"], kw["pore_pressure"], c, phi), rel=1e-9
    )
    same = G.bishop_simplified_fos(
        kw["width"],
        kw["weight"],
        kw["base_angle"],
        kw["pore_pressure"],
        np.full(7, 20e3),
        np.full(7, math.radians(20.0)),
    )
    assert same == pytest.approx(float(G.bishop_simplified_fos(**kw)), rel=1e-14)


@pytest.mark.req("FR-003-09")
@pytest.mark.oracle(
    "analytical", "the iteration stops at the tolerance: a looser tol gives a value within tol of the converged one"
)
def test_tolerance_is_honoured() -> None:
    kw = slide1()
    exact = float(G.bishop_simplified_fos(**kw))
    loose = float(G.bishop_simplified_fos(**kw, tol=1e-3))
    assert abs(loose - exact) <= 2e-3 * exact
    assert float(G.bishop_simplified_fos(**kw, tol=1e-15)) == pytest.approx(exact, rel=1e-12)


@pytest.mark.req("FR-003-11")
@pytest.mark.oracle(
    "analytical", "a driving moment of zero or below has no factor of safety: InputError naming base_angle"
)
@pytest.mark.parametrize("alpha", [[-0.2, -0.3, -0.1], [0.0, 0.0, 0.0], [-0.3, 0.0, 0.3]])
def test_non_positive_driving_moment(alpha: list[float]) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.bishop_simplified_fos(np.full(3, 2.0), np.full(3, 1e5), np.array(alpha), np.zeros(3), 5000.0, 0.4)
    assert ei.value.argument == "base_angle"


@pytest.mark.req("FR-003-11")
@pytest.mark.oracle(
    "analytical",
    "m_alpha = cos(alpha)(1 + tan(alpha) tan(phi')/F) <= 0 for a steep uphill base: ConvergenceError naming the slice",
)
def test_non_positive_m_alpha() -> None:
    alpha = np.radians([30.0, 25.0, 20.0, -80.0, 10.0, 15.0])  # at F = 1: m = cos(-80 deg)(1 - 5.67) < 0 for index 3
    w = np.array([100.0, 80.0, 60.0, 5.0, 20.0, 20.0]) * 1e3
    with pytest.raises(minephys.ConvergenceError) as ei:
        G.bishop_simplified_fos(np.full(6, 3.0), w, alpha, np.zeros(6), 1000.0, math.radians(45.0))
    assert ei.value.argument is None
    assert re.search(r"(?<![\d.])[34](?![\d.])", str(ei.value)), (
        "the message names the first offending slice (index 3, or 4 counted from 1)"
    )


@pytest.mark.req("FR-003-22")
@pytest.mark.oracle(
    "analytical", "one iteration cannot converge to 1e-12: ConvergenceError; max_iter above 10,000 is a domain error"
)
def test_iteration_cap() -> None:
    kw = slide1()
    with pytest.raises(minephys.ConvergenceError) as ei:
        G.bishop_simplified_fos(**kw, max_iter=1)
    assert ei.value.iterations == 1
    assert ei.value.argument is None
    assert math.isfinite(ei.value.last_iterate)
    assert ei.value.residual > 0.0
    assert math.isfinite(float(G.bishop_simplified_fos(**kw, max_iter=10_000)))
    for bad in (10_001, 10**6, 0, -3):
        with pytest.raises(minephys.InputError) as ei2:
            G.bishop_simplified_fos(**kw, max_iter=bad)
        assert ei2.value.argument == "max_iter"

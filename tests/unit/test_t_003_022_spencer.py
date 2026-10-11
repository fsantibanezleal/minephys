# ruff: noqa: E501
"""T-003-022 (FR-003-10, FR-003-11, FR-003-22): Spencer's method on slice data.

Expected API: `G.spencer_fos(width, weight, base_angle, pore_pressure, cohesion, friction_angle, tol=1e-12,
max_iter=200)` -> `(fos, theta)` (float64, theta the inclination of the interslice resultant in rad) such
that, with
    Q_i = [c' l_i / F + (W_i cos(alpha_i) - u_i l_i) tan(phi') / F - W_i sin(alpha_i)] / [cos(alpha_i - theta) +
    sin(alpha_i - theta) tan(phi') / F], l_i = b_i / cos(alpha_i),
both the force equation sum Q_i = 0 and the moment equation sum Q_i cos(alpha_i - theta) = 0 hold to a
relative residual of at most `tol` (2 to 10,000 slices, same arguments as `bishop_simplified_fos`). A driving
moment sum(W sin alpha) <= 0 raises `InputError` naming `base_angle` (FR-003-11); no convergence within
`max_iter` (<= 10,000) raises `ConvergenceError` (FR-003-22).

Oracles: the spec 003 section 7.4 three-slice hand calculation (F = 1.2775177 at theta = 27.0414 deg dry; F =
1.0013315 with u = (0, 20, 10) kPa; TC-2), the residuals of the two equations evaluated in this file
(analytical identity), the identity that Spencer's moment equation at theta = 0 is Bishop's equation (its root
is Bishop's F), the phi' = 0 limit (the moment equation gives F = sum c' l / sum W sin alpha whatever theta),
and the Fredlund and Krahn (1977) benchmark, Slide verification problem #21 pp. 91-92 (published Spencer F
2.073 / 2.075, |dF| <= 0.01; the spec writer's independent value 2.0715 at theta = 14.46 deg for 100 slices;
TC-2).
"""

from __future__ import annotations

import math

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


def three(u=(0.0, 0.0, 0.0)):
    return {
        "width": np.full(3, 2.0),
        "weight": np.array([60.0, 120.0, 80.0]) * 1e3,
        "base_angle": np.radians([5.0, 25.0, 50.0]),
        "pore_pressure": np.array(u) * 1e3,
        "cohesion": 5000.0,
        "friction_angle": math.radians(25.0),
    }


def residuals(kw, f: float, theta: float) -> tuple[float, float, float]:
    b, w, a, u = (np.asarray(kw[k], dtype=float) for k in ("width", "weight", "base_angle", "pore_pressure"))
    ell = b / np.cos(a)
    tp = math.tan(kw["friction_angle"])
    num = kw["cohesion"] * ell / f + (w * np.cos(a) - u * ell) * tp / f - w * np.sin(a)
    den = np.cos(a - theta) + np.sin(a - theta) * tp / f
    q = num / den
    return float(np.sum(q)), float(np.sum(q * np.cos(a - theta))), float(np.sum(np.abs(q)))


@pytest.mark.req("FR-003-10")
@pytest.mark.oracle("hand-calculation", "spec 003 7.4: three slices, dry: Spencer F = 1.2775177 at theta = 27.0414 deg")
def test_three_slices_dry() -> None:
    f, th = G.spencer_fos(**three())
    assert type(f) is np.float64
    assert type(th) is np.float64
    assert f == pytest.approx(1.2775177, abs=5e-8)  # TC-2: 8 significant figures
    assert math.degrees(th) == pytest.approx(27.0414, abs=5e-5)
    assert f < float(G.bishop_simplified_fos(**three()))  # 1.2843 for Bishop


@pytest.mark.req("FR-003-10")
@pytest.mark.oracle("hand-calculation", "spec 003 7.4: with u = (0, 20, 10) kPa Spencer F = 1.0013315")
def test_three_slices_with_pore_pressure() -> None:
    kw = three(u=(0.0, 20.0, 10.0))
    f, th = G.spencer_fos(**kw)
    assert f == pytest.approx(1.0013315, abs=5e-8)
    assert math.degrees(th) == pytest.approx(26.0350703, abs=5e-6)  # independent reference solution (TC-3)


@pytest.mark.req("FR-003-10")
@pytest.mark.oracle(
    "analytical", "the returned (F, theta) satisfies the force and the moment equations to the tolerance"
)
@pytest.mark.parametrize("u", [(0.0, 0.0, 0.0), (0.0, 20.0, 10.0), (5.0, 5.0, 5.0)])
def test_both_equations_are_satisfied(u: tuple[float, float, float]) -> None:
    kw = three(u=u)
    f, th = G.spencer_fos(**kw)
    force, moment, scale = residuals(kw, float(f), float(th))
    assert abs(force) <= 1e-9 * scale
    assert abs(moment) <= 1e-9 * scale


@pytest.mark.req("FR-003-10")
@pytest.mark.req("P-003-07")
@pytest.mark.oracle(
    "analytical", "Spencer's moment equation at theta = 0 is Bishop's equation: its root F is Bishop's factor of safety"
)
def test_moment_equation_at_theta_zero_has_bishops_root() -> None:
    kw = three()
    lo, hi = 0.2, 20.0

    def moment_at_zero(f: float) -> float:
        return residuals(kw, f, 0.0)[1]

    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if moment_at_zero(lo) * moment_at_zero(mid) <= 0.0:
            hi = mid
        else:
            lo = mid
    assert 0.5 * (lo + hi) == pytest.approx(float(G.bishop_simplified_fos(**kw)), rel=1e-9)


@pytest.mark.req("FR-003-10")
@pytest.mark.oracle(
    "analytical",
    "phi' = 0: the moment equation gives F = sum c' l / sum W sin(alpha) whatever theta (1.4623899 for the spec's slices)",
)
def test_phi_zero_gives_the_moment_only_value() -> None:
    kw = {
        "width": np.full(3, 2.0),
        "weight": np.array([40.0, 80.0, 50.0]) * 1e3,
        "base_angle": np.radians([-10.0, 15.0, 40.0]),
        "pore_pressure": np.zeros(3),
        "cohesion": 10000.0,
        "friction_angle": 0.0,
    }
    f, th = G.spencer_fos(**kw)
    assert f == pytest.approx(1.4623899, abs=5e-8)
    assert f == pytest.approx(float(G.bishop_simplified_fos(**kw)), rel=1e-9)
    force, moment, scale = residuals(kw, float(f), float(th))
    assert abs(force) <= 1e-9 * scale
    assert abs(moment) <= 1e-9 * scale
    assert math.degrees(th) == pytest.approx(12.8486048, abs=5e-6)  # independent reference solution (TC-3)


@pytest.mark.req("FR-003-10")
@pytest.mark.oracle(
    "worked-example",
    "fredlund1977 as slide verification problem 21 pp. 91-92: dry Spencer F = 2.073 (Slide 2.075); 100 slices give 2.0715 at 14.46 deg",
)
def test_fredlund_krahn_dry() -> None:
    s = G.circular_slices(FK_X, FK_Z, 120.0 * FT, 90.0 * FT, 80.0 * FT, 100, GAMMA_FK)
    f, th = G.spencer_fos(s.width, s.weight, s.base_angle, s.pore_pressure, C_FK, math.radians(20.0))
    assert f == pytest.approx(2.073, abs=0.01)
    assert f == pytest.approx(2.0715, abs=5e-5)
    assert math.degrees(th) == pytest.approx(14.46, abs=5e-3)
    bishop = G.bishop_simplified_fos(s.width, s.weight, s.base_angle, s.pore_pressure, C_FK, math.radians(20.0))
    assert abs(float(f) - float(bishop)) < 0.01, "Bishop and Spencer agree to a few thousandths on this benchmark"


@pytest.mark.req("FR-003-10")
@pytest.mark.oracle(
    "analytical", "per-slice cohesion and friction angle are accepted; equal arrays give the scalar result"
)
def test_per_slice_strengths() -> None:
    kw = three()
    f_scalar, th_scalar = G.spencer_fos(**kw)
    f_arr, th_arr = G.spencer_fos(
        **{**kw, "cohesion": np.full(3, 5000.0), "friction_angle": np.full(3, math.radians(25.0))}
    )
    assert float(f_arr) == pytest.approx(float(f_scalar), rel=1e-10)
    assert float(th_arr) == pytest.approx(float(th_scalar), rel=1e-8)


@pytest.mark.req("FR-003-11")
@pytest.mark.oracle(
    "analytical", "a driving moment of zero or below has no factor of safety: InputError naming base_angle"
)
@pytest.mark.parametrize("alpha", [[-0.2, -0.3, -0.1], [0.0, 0.0, 0.0], [-0.3, 0.0, 0.3]])
def test_non_positive_driving_moment(alpha: list[float]) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.spencer_fos(np.full(3, 2.0), np.full(3, 1e5), np.array(alpha), np.zeros(3), 5000.0, 0.4)
    assert ei.value.argument == "base_angle"


@pytest.mark.req("FR-003-11")
@pytest.mark.oracle("analytical", "Spencer needs at least two slices (spec 003 7.1): one slice is an InputError")
def test_a_single_slice_is_not_enough() -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.spencer_fos(np.array([2.0]), np.array([1e5]), np.array([0.3]), np.array([0.0]), 5000.0, 0.4)
    assert ei.value.argument in {"width", "weight", "base_angle", "pore_pressure"}


@pytest.mark.req("FR-003-22")
@pytest.mark.oracle(
    "analytical",
    "one iteration cannot converge to 1e-12: ConvergenceError with its attributes; max_iter above 10,000 is a domain error",
)
def test_iteration_cap() -> None:
    kw = three()
    with pytest.raises(minephys.ConvergenceError) as ei:
        G.spencer_fos(**kw, max_iter=1)
    assert ei.value.argument is None
    assert ei.value.iterations >= 1
    assert math.isfinite(float(np.asarray(ei.value.residual).ravel()[0]))
    assert float(G.spencer_fos(**kw, max_iter=10_000)[0]) == pytest.approx(1.2775177, abs=5e-8)
    for bad in (10_001, 10**6, 0, -1):
        with pytest.raises(minephys.InputError) as ei2:
            G.spencer_fos(**kw, max_iter=bad)
        assert ei2.value.argument == "max_iter"

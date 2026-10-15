"""T-003-022 (P-003-04, P-003-05, P-003-06, P-003-07): metamorphic properties of Spencer's method.

P-003-04: scaling weight, cohesion and pore pressure by the same k leaves F and theta unchanged (TC-3).
P-003-05: F is strictly increasing in cohesion and friction angle and strictly decreasing in pore pressure
(exact ordering, pairs with a relative gap of at least 1e-3). P-003-06: permuting the slices, or splitting a
slice into two of the same base angle with half its width, half its weight and the same pore pressure, leaves
F and theta unchanged (TC-3, rtol 1e-8 for the nested solvers). P-003-07: Spencer's moment equation at theta =
0 has Bishop's F as its root (analytical identity). Generators (spec 003: 3-200 slices, |alpha| < 60 deg, phi'
in [10, 45] deg), narrowed to well-posed data: alpha in [-5, 45] deg, widths 1-5 m, heights 2-15 m, unit
weight 20 kN/m^3, c' in [5, 50] kPa, phi' in [15, 40] deg, pore pressure up to 30 % of the overburden; cases
for which the independent Newton reference below does not converge to a plausible solution are discarded.

Oracle: analytical, and an independent damped Newton solution (numpy only) of the two Spencer equations.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

CFG = settings(deadline=None)
GAMMA = 20000.0


def equations(x, b, w, a, u, c, phi):
    f, th = x
    ell = b / np.cos(a)
    tp = math.tan(phi)
    q = (c * ell / f + (w * np.cos(a) - u * ell) * tp / f - w * np.sin(a)) / (np.cos(a - th) + np.sin(a - th) * tp / f)
    return np.array([np.sum(q), np.sum(q * np.cos(a - th))]) / max(float(np.sum(np.abs(w * np.sin(a)))), 1.0)


def ref_spencer(b, w, a, u, c, phi):
    """Damped Newton on (F, theta) with a numerical Jacobian; returns None when it does not converge."""
    f0 = 1.0
    for _ in range(100):
        m = np.cos(a) * (1.0 + np.tan(a) * math.tan(phi) / f0)
        if np.any(m <= 0):
            return None
        fn = float(np.sum((c * b + (w - u * b) * math.tan(phi)) / m) / np.sum(w * np.sin(a)))
        if abs(fn - f0) < 1e-12:
            break
        f0 = fn
    x = np.array([f0, 0.2])
    for _ in range(60):
        r = equations(x, b, w, a, u, c, phi)
        if float(np.max(np.abs(r))) < 1e-13:
            return float(x[0]), float(x[1])
        jac = np.empty((2, 2))
        for j in range(2):
            dx = np.zeros(2)
            dx[j] = 1e-7
            jac[:, j] = (equations(x + dx, b, w, a, u, c, phi) - r) / 1e-7
        try:
            step = np.linalg.solve(jac, -r)
        except np.linalg.LinAlgError:
            return None
        x = x + np.clip(step, -0.3, 0.3)
        if x[0] <= 0.05:
            return None
    return None


@st.composite
def slope_data(draw, min_n=3, max_n=40):
    n = draw(st.integers(min_n, max_n))
    b = np.array(draw(st.lists(st.floats(1.0, 5.0), min_size=n, max_size=n)))
    h = np.array(draw(st.lists(st.floats(2.0, 15.0), min_size=n, max_size=n)))
    alpha = np.radians(np.array(draw(st.lists(st.floats(-5.0, 45.0), min_size=n, max_size=n))))
    ur = np.array(draw(st.lists(st.floats(0.0, 0.3), min_size=n, max_size=n)))
    c = draw(st.floats(5e3, 5e4))
    phi = math.radians(draw(st.floats(15.0, 40.0)))
    w, u = GAMMA * b * h, ur * GAMMA * h
    sol = ref_spencer(b, w, alpha, u, c, phi)
    assume(sol is not None and 0.5 <= sol[0] <= 20.0 and abs(sol[1]) < 1.2)
    # theta must be determined by the data: shifting it by 0.05 rad must visibly break an equation
    shifted = equations(np.array([sol[0], sol[1] + 0.05]), b, w, alpha, u, c, phi)
    assume(float(np.max(np.abs(shifted))) > 1e-4)
    return {"width": b, "weight": w, "base_angle": alpha, "pore_pressure": u, "cohesion": c, "friction_angle": phi}


def spencer(d, **over):
    f, th = G.spencer_fos(**{**d, **over})
    return float(f), float(th)


@pytest.mark.req("FR-003-10")
@pytest.mark.oracle("reference-implementation", "an independent damped Newton solution of the two equations")
@CFG
@given(d=slope_data())
def test_matches_the_independent_newton_reference(d: dict) -> None:
    f_ref, th_ref = ref_spencer(
        d["width"], d["weight"], d["base_angle"], d["pore_pressure"], d["cohesion"], d["friction_angle"]
    )
    f, th = spencer(d)
    assert f == pytest.approx(f_ref, rel=1e-8)
    assert th == pytest.approx(th_ref, rel=1e-6, abs=1e-8)


@pytest.mark.req("P-003-04")
@pytest.mark.oracle(
    "analytical", "N <-> kN: scaling weight, cohesion and pore pressure together changes neither F nor theta"
)
@CFG
@given(d=slope_data(), k=st.floats(1e-3, 1e3))
def test_unit_change_invariance(d: dict, k: float) -> None:
    f, th = spencer(d)
    f2, th2 = spencer(
        {**d, "weight": k * d["weight"], "pore_pressure": k * d["pore_pressure"], "cohesion": k * d["cohesion"]}
    )
    assert f2 == pytest.approx(f, rel=1e-8)
    assert th2 == pytest.approx(th, rel=1e-6, abs=1e-8)


@pytest.mark.req("P-003-05")
@pytest.mark.oracle("analytical", "F increases with cohesion and friction angle, decreases with pore pressure")
@CFG
@given(d=slope_data(), c1=st.floats(5e3, 5e4), c2=st.floats(5e3, 5e4), s=st.floats(0.05, 0.5))
def test_monotonicity(d: dict, c1: float, c2: float, s: float) -> None:
    assume(abs(c1 - c2) > 1e-3 * max(c1, c2))
    lo, hi = sorted((c1, c2))
    assert spencer(d, cohesion=lo)[0] < spencer(d, cohesion=hi)[0]
    assert (
        spencer(d, friction_angle=d["friction_angle"] * 0.98)[0]
        < spencer(d, friction_angle=d["friction_angle"] * 1.02)[0]
    )
    wetter = {**d, "pore_pressure": d["pore_pressure"] + s * 0.3 * d["weight"] / d["width"]}
    assert spencer(wetter)[0] < spencer(d)[0]


@pytest.mark.req("P-003-06")
@pytest.mark.oracle("analytical", "permutation and refinement invariance")
@CFG
@given(d=slope_data(), seed=st.integers(0, 2**32 - 1), at=st.integers(0, 39))
def test_permutation_and_refinement(d: dict, seed: int, at: int) -> None:
    f, th = spencer(d)
    perm = np.random.default_rng(seed).permutation(len(d["width"]))
    p = {k: (v[perm] if isinstance(v, np.ndarray) else v) for k, v in d.items()}
    fp, thp = spencer(p)
    assert fp == pytest.approx(f, rel=1e-8)
    assert thp == pytest.approx(th, rel=1e-6, abs=1e-8)
    i = at % len(d["width"])

    def split(a: np.ndarray, halve: bool) -> np.ndarray:
        value = a[i] / 2.0 if halve else a[i]
        return np.concatenate([a[:i], [value, value], a[i + 1 :]])

    refined = {
        "width": split(d["width"], True),
        "weight": split(d["weight"], True),
        "base_angle": split(d["base_angle"], False),
        "pore_pressure": split(d["pore_pressure"], False),
        "cohesion": d["cohesion"],
        "friction_angle": d["friction_angle"],
    }
    fr, thr = spencer(refined)
    assert fr == pytest.approx(f, rel=1e-8)
    assert thr == pytest.approx(th, rel=1e-6, abs=1e-8)


@pytest.mark.req("P-003-07")
@pytest.mark.oracle("analytical", "the moment equation at theta = 0 has Bishop's F as its root, for random slice data")
@CFG
@given(d=slope_data())
def test_moment_root_at_theta_zero_is_bishops_factor(d: dict) -> None:
    b, w, a, u = d["width"], d["weight"], d["base_angle"], d["pore_pressure"]
    c, phi = d["cohesion"], d["friction_angle"]

    def moment(f: float) -> float:
        return float(equations(np.array([f, 0.0]), b, w, a, u, c, phi)[1])

    bishop = float(G.bishop_simplified_fos(**d))
    scale = max(abs(moment(0.5 * bishop)), abs(moment(2.0 * bishop)), 1e-30)
    assert abs(moment(bishop)) <= 1e-9 * scale
    assert moment(0.9 * bishop) * moment(1.1 * bishop) < 0.0, "the moment equation changes sign around Bishop's value"

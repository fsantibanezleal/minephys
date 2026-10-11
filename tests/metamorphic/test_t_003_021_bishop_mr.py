"""T-003-021 (P-003-04, P-003-05, P-003-06, P-003-07): metamorphic properties of Bishop's simplified method.

P-003-04: scaling weight, cohesion and pore pressure by the same k leaves F unchanged (N <-> kN unit-change
invariance; TC-3). P-003-05: F is strictly increasing in cohesion and in friction angle and strictly
decreasing in pore pressure (exact ordering, pairs with a relative gap of at least 1e-3). P-003-06: permuting
the slices, or splitting a slice into two of the same base angle with half its width, half its weight and the
same pore pressure, leaves F unchanged (TC-3). P-003-07: with phi' = 0, F = sum c' l / sum W sin(alpha); with
c' = 0, dry slices and all base angles equal to beta, F = tan(phi') / tan(beta) (analytical limits).
Generators (spec 003: 3-200 slices, |alpha| < 60 deg, phi' in [10, 45] deg), narrowed so that the iteration is
well posed: alpha in [-10, 55] deg, widths 1-5 m, heights 1-15 m, unit weight 20 kN/m^3, c' in [5, 50] kPa,
pore pressure up to 40 % of the overburden; cases whose independent reference factor of safety falls outside
[0.5, 20] are discarded.

Oracle: analytical, and an independent fixed-point reference of the Bishop equation written in this file.
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


def ref_bishop(b, w, alpha, u, c, phi):
    f = 1.0
    for _ in range(3000):
        m = np.cos(alpha) * (1.0 + np.tan(alpha) * np.tan(phi) / f)
        if np.any(m <= 0.0):
            return math.nan
        denominator = float(np.sum(w * np.sin(alpha)))
        if denominator <= 0.0:
            return math.nan
        fn = float(np.sum((c * b + (w - u * b) * np.tan(phi)) / m) / denominator)
        if abs(fn - f) <= 1e-14 * f:
            return fn
        f = fn
    return math.nan


@st.composite
def slope_data(draw, min_n=3, max_n=60):
    n = draw(st.integers(min_n, max_n))
    b = np.array(draw(st.lists(st.floats(1.0, 5.0), min_size=n, max_size=n)))
    h = np.array(draw(st.lists(st.floats(1.0, 15.0), min_size=n, max_size=n)))
    alpha = np.radians(np.array(draw(st.lists(st.floats(-10.0, 55.0), min_size=n, max_size=n))))
    ur = np.array(draw(st.lists(st.floats(0.0, 0.4), min_size=n, max_size=n)))
    c = draw(st.floats(5e3, 5e4))
    phi = math.radians(draw(st.floats(10.0, 45.0)))
    w = GAMMA * b * h
    u = ur * GAMMA * h
    f = ref_bishop(b, w, alpha, u, c, phi)
    assume(math.isfinite(f) and 0.5 <= f <= 20.0)
    return {"width": b, "weight": w, "base_angle": alpha, "pore_pressure": u, "cohesion": c, "friction_angle": phi}


def bishop(d, **over):
    return float(G.bishop_simplified_fos(**{**d, **over}))


@pytest.mark.req("P-003-04")
@pytest.mark.oracle("analytical", "N <-> kN: scaling weight, cohesion and pore pressure together does not change F")
@CFG
@given(d=slope_data(), k=st.floats(1e-3, 1e3))
def test_unit_change_invariance(d: dict, k: float) -> None:
    scaled = {**d, "weight": k * d["weight"], "pore_pressure": k * d["pore_pressure"], "cohesion": k * d["cohesion"]}
    assert bishop(scaled) == pytest.approx(bishop(d), rel=1e-9)


@pytest.mark.req("P-003-05")
@pytest.mark.oracle("analytical", "F increases with cohesion and with friction angle, decreases with pore pressure")
@CFG
@given(
    d=slope_data(),
    c1=st.floats(5e3, 5e4),
    c2=st.floats(5e3, 5e4),
    p1=st.floats(10.0, 45.0),
    p2=st.floats(10.0, 45.0),
    s=st.floats(0.05, 0.9),
)
def test_monotonicity(d: dict, c1: float, c2: float, p1: float, p2: float, s: float) -> None:
    assume(abs(c1 - c2) > 1e-3 * max(c1, c2) and abs(p1 - p2) > 1e-3 * max(p1, p2))
    lo, hi = sorted((c1, c2))
    assert bishop(d, cohesion=lo) < bishop(d, cohesion=hi)
    plo, phi_ = (math.radians(x) for x in sorted((p1, p2)))
    f_lo, f_hi = bishop(d, friction_angle=plo), bishop(d, friction_angle=phi_)
    assume(math.isfinite(f_lo) and math.isfinite(f_hi))
    assert f_lo < f_hi
    wetter = {
        **d,
        "pore_pressure": d["pore_pressure"] + s * 0.3 * d["weight"] / d["width"],
    }  # up to 27 % more of the overburden
    assert bishop(wetter) < bishop(d)


@pytest.mark.req("P-003-06")
@pytest.mark.oracle("analytical", "permutation invariance of the sum over slices")
@CFG
@given(d=slope_data(), seed=st.integers(0, 2**32 - 1))
def test_permutation_invariance(d: dict, seed: int) -> None:
    perm = np.random.default_rng(seed).permutation(len(d["width"]))
    p = {k: (v[perm] if isinstance(v, np.ndarray) else v) for k, v in d.items()}
    assert bishop(p) == pytest.approx(bishop(d), rel=1e-9)


@pytest.mark.req("P-003-06")
@pytest.mark.oracle(
    "analytical",
    "refinement invariance: a slice split in two (same angle, half width, half weight, same u) changes nothing",
)
@CFG
@given(d=slope_data(), at=st.integers(0, 59))
def test_refinement_invariance(d: dict, at: int) -> None:
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
    assert bishop(refined) == pytest.approx(bishop(d), rel=1e-9)


@pytest.mark.req("P-003-07")
@pytest.mark.oracle("analytical", "phi' = 0: F = sum c' l / sum W sin(alpha) in one step")
@CFG
@given(d=slope_data())
def test_phi_zero_limit(d: dict) -> None:
    got = bishop(d, friction_angle=0.0)
    expected = float(
        np.sum(d["cohesion"] * d["width"] / np.cos(d["base_angle"])) / np.sum(d["weight"] * np.sin(d["base_angle"]))
    )
    assert got == pytest.approx(expected, rel=1e-10)


@pytest.mark.req("P-003-07")
@pytest.mark.oracle("analytical", "c' = 0, dry, all base angles equal: the infinite-slope factor tan(phi') / tan(beta)")
@CFG
@given(n=st.integers(1, 100), beta=st.floats(5.0, 55.0), phi=st.floats(10.0, 45.0), seed=st.integers(0, 2**32 - 1))
def test_infinite_slope_limit(n: int, beta: float, phi: float, seed: int) -> None:
    rng = np.random.default_rng(seed)
    w = rng.uniform(1e4, 1e6, n)
    b = rng.uniform(0.5, 5.0, n)
    got = float(G.bishop_simplified_fos(b, w, np.full(n, math.radians(beta)), np.zeros(n), 0.0, math.radians(phi)))
    assert got == pytest.approx(math.tan(math.radians(phi)) / math.tan(math.radians(beta)), rel=1e-9)

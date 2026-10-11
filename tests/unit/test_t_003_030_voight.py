"""T-003-030 (FR-003-14): Voight's creep-failure law, velocity and displacement.

Expected API, module `minephys.geotech`:

    voight_creep_series(t, failure_time, a, alpha) -> (velocity, displacement)
        t [s] a 1-D float64 array of at least one time, every t < failure_time (negative times are allowed);
        failure_time [s] > 0; a > 0 (units (m/s)^(1 - alpha) / s); alpha > 1. failure_time, a and alpha are scalars (a
        rank-1 array is an `InputError` naming the argument). velocity v(t) = [a (alpha - 1) (t_f - t)]^(1 / (1 -
        alpha)) in m/s, the solution of Omega'' = a Omega'^alpha that blows up at t_f; displacement(t) = integral of v
        from t[0] to t (so displacement[0] = 0), in closed form: (1 / a) ln((t_f - t0) / (t_f - t)) for alpha = 2 and,
        with p = 1 / (1 - alpha) and q = p + 1, [a (alpha - 1)]^p ((t_f - t0)^q - (t_f - t)^q) / q otherwise. Both
        outputs are float64 arrays shaped like t.

Oracles: spec 003 section 7.4 (alpha = 2, a = 10 / m, t_f = 864,000 s: v(0) = 1.1574074e-7 m/s = 10 mm/day and
a displacement of 0.091629073 m from day 0 to day 6), hand integration for alpha = 3 and alpha = 1.5 (written
in the comments), an independent numerical solution of the two ordinary differential equations (SciPy
`solve_ivp`, DOP853, rtol 1e-13) as the reference implementation, and metamorphic relations (time shift, time
scaling, unit change of the velocity). Tolerances TC-1 unless stated; the printed spec values are TC-2.
"""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

import minephys
from minephys import geotech as G

DAY = 86400.0
CFG = settings(deadline=None)


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: alpha = 2, A = 10 / m, t_f = 864,000 s: v(0) = 1.1574074e-7 m/s, 0.091629073 m by day 6",
)
def test_spec_worked_values() -> None:
    t = np.arange(0.0, 7.0) * DAY
    v, d = G.voight_creep_series(t, 864_000.0, 10.0, 2.0)
    assert v.shape == d.shape == (7,)
    assert v.dtype == d.dtype == np.float64
    assert v[0] == pytest.approx(1.1574074e-7, abs=5e-15)  # TC-2: 8 significant figures, 10 mm/day
    assert v[0] * DAY == pytest.approx(0.01, rel=1e-12)
    assert d[0] == 0.0
    assert d[6] == pytest.approx(0.091629073, abs=5e-10)  # TC-2
    assert d[6] == pytest.approx(0.1 * math.log(10.0 / 4.0), rel=1e-13)  # (1 / A) ln((t_f - t0) / (t_f - t6))
    assert v[6] == pytest.approx(1.0 / (10.0 * (864_000.0 - 6.0 * DAY)), rel=1e-13)  # 2.8935185e-7 m/s


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle(
    "analytical", "alpha = 2 closed forms v = 1 / (A (t_f - t)), displacement (1 / A) ln(...) on a random-looking grid"
)
def test_alpha_two_closed_forms() -> None:
    a, tf = 3.5, 2.0e6
    t = np.array([-5.0e4, 0.0, 1.0e5, 7.5e5, 1.9e6, 1.99e6])
    v, d = G.voight_creep_series(t, tf, a, 2.0)
    np.testing.assert_allclose(v, 1.0 / (a * (tf - t)), rtol=1e-13)
    np.testing.assert_allclose(d, np.log((tf - t[0]) / (tf - t)) / a, rtol=1e-12, atol=1e-18)


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle(
    "hand-calculation",
    "alpha = 3, A = 2, t_f = 1e6 s: v = (4 (t_f - t))^(-1/2); displacement = sqrt(t_f - t0) - sqrt(t_f - t) "
    "(integral of 0.5 (t_f - s)^(-1/2) ds)",
)
def test_alpha_three_by_hand() -> None:
    t = np.array([0.0, 5.0e5, 9.0e5])
    v, d = G.voight_creep_series(t, 1.0e6, 2.0, 3.0)
    assert v.tolist() == pytest.approx(
        [5.0e-4, 7.0710678e-4, 1.5811388e-3], rel=1e-7
    )  # (4e6)^-.5, (2e6)^-.5, (4e5)^-.5
    assert d.tolist() == pytest.approx(
        [0.0, 292.89322, 683.77223], rel=1e-7, abs=1e-12
    )  # 1000 - 707.10678, 1000 - 316.22777
    np.testing.assert_allclose(d, 1000.0 - np.sqrt(1.0e6 - t), rtol=1e-12, atol=1e-12)


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle(
    "hand-calculation",
    "alpha = 1.5, A = 4, t_f = 500 s: v = (2 (t_f - t))^(-2); displacement = (1/4) (1/(t_f - t) - 1/(t_f - t0)) "
    "(it diverges at t_f for alpha < 2)",
)
def test_alpha_one_and_a_half_by_hand() -> None:
    t = np.array([0.0, 250.0, 400.0])
    v, d = G.voight_creep_series(t, 500.0, 4.0, 1.5)
    assert v.tolist() == pytest.approx([1.0e-6, 4.0e-6, 2.5e-5], rel=1e-12)
    assert d.tolist() == pytest.approx([0.0, 5.0e-4, 2.0e-3], rel=1e-12, abs=1e-18)


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle(
    "reference-implementation",
    "SciPy solve_ivp (DOP853, rtol 1e-13) on dv/dt = A v^alpha, dOmega/dt = v from v(t0) = v_voight(t0)",
)
@pytest.mark.parametrize(
    ("alpha", "a", "tf", "fractions"),
    [
        (2.0, 5.0, 1.0e6, (0.0, 0.2, 0.5, 0.8, 0.95)),
        (3.0, 2.0, 1.0e6, (0.0, 0.3, 0.6, 0.9)),
        (2.5, 1.0e3, 5.0e5, (0.0, 0.25, 0.5, 0.75)),
        (1.5, 4.0, 500.0, (0.0, 0.2, 0.5, 0.8)),
        (4.0, 0.5, 2.0e6, (0.0, 0.4, 0.7, 0.9)),
    ],
)
def test_matches_the_numerical_solution_of_the_ode(alpha: float, a: float, tf: float, fractions: tuple) -> None:
    from scipy.integrate import solve_ivp

    t = np.array(fractions) * tf
    v, d = G.voight_creep_series(t, tf, a, alpha)
    sol = solve_ivp(
        lambda _t, y: [a * y[0] ** alpha, y[0]],
        (t[0], t[-1]),
        [float(v[0]), 0.0],
        method="DOP853",
        t_eval=t,
        rtol=1e-13,
        atol=1e-30,
    )
    assert sol.success
    np.testing.assert_allclose(v, sol.y[0], rtol=1e-8)
    np.testing.assert_allclose(d, sol.y[1], rtol=1e-8, atol=1e-12 * float(np.max(np.abs(sol.y[1]))))


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle(
    "analytical", "v^(1 - alpha) is linear in t and vanishes at t_f: v^(1 - alpha) = A (alpha - 1) (t_f - t)"
)
@pytest.mark.parametrize("alpha", [1.1, 1.5, 2.0, 2.7, 3.0, 6.0, 25.0])
def test_linearised_velocity(alpha: float) -> None:
    a, tf = 0.8, 1.0e5
    t = np.linspace(0.0, 0.99 * tf, 40)
    v, _ = G.voight_creep_series(t, tf, a, alpha)
    np.testing.assert_allclose(v ** (1.0 - alpha), a * (alpha - 1.0) * (tf - t), rtol=1e-10)


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle("analytical", "the series accelerates: v strictly increases, the displacement increases from zero")
@pytest.mark.parametrize("alpha", [1.2, 2.0, 3.5])
def test_acceleration(alpha: float) -> None:
    t = np.linspace(0.0, 9.0e5, 30)
    v, d = G.voight_creep_series(t, 1.0e6, 0.3, alpha)
    assert np.all(v > 0.0)
    assert np.all(np.diff(v) > 0.0)
    assert d[0] == 0.0
    assert np.all(np.diff(d) > 0.0)


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle(
    "analytical",
    "continuity in alpha: alpha = 2 +- 1e-6 is the logarithmic displacement to within 1e-4 (no cancellation loss)",
)
@pytest.mark.parametrize("alpha", [2.0 - 1e-6, 2.0 + 1e-6])
def test_continuity_across_alpha_two(alpha: float) -> None:
    t = np.array([0.0, 2.0e5, 6.0e5])
    _, d2 = G.voight_creep_series(t, 1.0e6, 5.0, 2.0)
    v, d = G.voight_creep_series(t, 1.0e6, 5.0, alpha)
    np.testing.assert_allclose(d, d2, rtol=1e-4, atol=1e-18)
    assert np.all(np.isfinite(v))


@st.composite
def series(draw, integer: bool = False):
    """A Voight series: failure time, 1-30 sorted times before it (relative gaps > 1e-3), A and alpha."""
    tf = float(draw(st.integers(10_000, 10**8))) if integer else draw(st.floats(1e4, 1e8))
    fr = sorted(draw(st.lists(st.floats(0.0, 0.95), min_size=1, max_size=30, unique=True)))
    assume(all(hi - lo > 1e-3 for lo, hi in pairwise(fr)))
    t = np.array(fr) * tf
    if integer:
        t = np.floor(t)  # integer seconds: a shift by an integer is exact in floating point
    a = draw(st.floats(1e-3, 1e3))
    alpha = draw(st.floats(1.05, 8.0))
    assume(abs(alpha - 2.0) > 1e-3)  # the general formula cancels near alpha = 2; that region is tested separately
    return tf, t, a, alpha


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle(
    "analytical", "time shift: t -> t + tau and t_f -> t_f + tau change neither velocity nor displacement"
)
@CFG
@given(s=series(integer=True), tau=st.integers(-(10**7), 10**7))
def test_shift_invariance(s: tuple, tau: int) -> None:
    tf, t, a, alpha = s
    assume(tf + tau > 0.0)
    v, d = G.voight_creep_series(t, tf, a, alpha)
    v2, d2 = G.voight_creep_series(t + tau, tf + tau, a, alpha)
    np.testing.assert_allclose(v2, v, rtol=1e-12)
    np.testing.assert_allclose(d2, d, rtol=1e-10, atol=1e-12 * float(np.max(np.abs(d))))


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle(
    "analytical",
    "time scaling: (t, t_f, A) -> (k t, k t_f, A / k) leaves v unchanged and multiplies the displacement by k",
)
@CFG
@given(s=series(), k=st.floats(1e-3, 1e3))
def test_time_scaling(s: tuple, k: float) -> None:
    tf, t, a, alpha = s
    v, d = G.voight_creep_series(t, tf, a, alpha)
    v2, d2 = G.voight_creep_series(k * t, k * tf, a / k, alpha)
    np.testing.assert_allclose(v2, v, rtol=1e-9)
    np.testing.assert_allclose(d2, k * d, rtol=1e-6, atol=1e-8 * k * float(np.max(np.abs(d))))


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle(
    "analytical", "unit change of the velocity (m -> c m): A -> A c^(1 - alpha) multiplies v and the displacement by c"
)
@CFG
@given(s=series(), c=st.floats(1e-3, 1e3))
def test_unit_change(s: tuple, c: float) -> None:
    tf, t, a, alpha = s
    v, d = G.voight_creep_series(t, tf, a, alpha)
    v2, d2 = G.voight_creep_series(t, tf, a * c ** (1.0 - alpha), alpha)
    np.testing.assert_allclose(v2, c * v, rtol=1e-8)
    np.testing.assert_allclose(d2, c * d, rtol=1e-6, atol=1e-8 * c * float(np.max(np.abs(d))))


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle("analytical", "a single time gives a one-element series with zero displacement")
def test_single_time() -> None:
    v, d = G.voight_creep_series(np.array([100.0]), 1000.0, 2.0, 2.0)
    assert v.shape == d.shape == (1,)
    assert v[0] == pytest.approx(1.0 / (2.0 * 900.0), rel=1e-13)
    assert d[0] == 0.0


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle("analytical", "inputs are not modified and the call is pure")
def test_purity() -> None:
    t = np.array([0.0, 1.0e5, 2.0e5])
    before = t.copy()
    v1, d1 = G.voight_creep_series(t, 1.0e6, 2.0, 3.0)
    v2, d2 = G.voight_creep_series(t, 1.0e6, 2.0, 3.0)
    assert np.array_equal(t, before)
    assert v1.tobytes() == v2.tobytes()
    assert d1.tobytes() == d2.tobytes()


# ------------------------------------------------------------------ domain and hostile inputs (spec 003 7.2)

BASE = {"t": np.array([0.0, 1.0e5, 2.0e5]), "failure_time": 1.0e6, "a": 2.0, "alpha": 2.5}


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle(
    "analytical", "every t must lie before the failure time: t_f itself and later are InputError naming t"
)
@pytest.mark.parametrize("bad", [1.0e6, 1.0e6 + 1.0, 5.0e6, 1.0e300])
def test_times_at_or_after_failure(bad: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.voight_creep_series(np.array([0.0, 5.0e5, bad]), 1.0e6, 2.0, 2.5)
    assert ei.value.argument == "t"


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle(
    "analytical", "failure_time, a > 0 and alpha > 1: the boundary values are invalid, the next float is valid"
)
@pytest.mark.parametrize(
    ("arg", "bad"),
    [
        ("failure_time", 0.0),
        ("failure_time", -1.0),
        ("failure_time", -1e-300),
        ("a", 0.0),
        ("a", -1.0),
        ("a", -1e-300),
        ("alpha", 1.0),
        ("alpha", 0.5),
        ("alpha", 0.0),
        ("alpha", -2.0),
    ],
)
def test_scalar_domains(arg: str, bad: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.voight_creep_series(**{**BASE, arg: bad})
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "NaN and infinity are InputError naming the argument")
@pytest.mark.parametrize("arg", ["t", "failure_time", "a", "alpha"])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite(arg: str, bad: float) -> None:
    value = np.array([0.0, bad, 2.0e5]) if arg == "t" else bad
    with pytest.raises(minephys.InputError) as ei:
        G.voight_creep_series(**{**BASE, arg: value})
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "wrong dtypes are InputTypeError naming the argument")
@pytest.mark.parametrize("arg", ["t", "failure_time", "a", "alpha"])
@pytest.mark.parametrize("bad", ["1.0", b"1", None, 1 + 1j, object(), np.datetime64("2026-01-01")])
def test_wrong_types(arg: str, bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        G.voight_creep_series(**{**BASE, arg: bad})
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "t must be a non-empty 1-D array: empty and 2-D arrays are InputError naming t")
@pytest.mark.parametrize("bad", [np.empty(0), np.zeros((2, 2)), np.zeros((1, 3))])
def test_shape_of_t(bad: np.ndarray) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.voight_creep_series(**{**BASE, "t": bad})
    assert ei.value.argument == "t"


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle(
    "analytical", "the three scalars of the law are scalars: arrays are rank errors naming the argument"
)
@pytest.mark.parametrize("arg", ["failure_time", "a", "alpha"])
def test_scalars_reject_arrays(arg: str) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.voight_creep_series(**{**BASE, arg: np.array([BASE[arg], BASE[arg]])})
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-14")
@pytest.mark.oracle("analytical", "float32 and int64 times give the float64 result (dtype invariance, P-000-03)")
def test_dtype_invariance() -> None:
    t64 = np.array([0.0, 100000.0, 200000.0, 300000.0])
    ref = G.voight_creep_series(t64, 1.0e6, 2.0, 2.5)
    for dtype in (np.float32, np.int64, np.int32):
        out = G.voight_creep_series(t64.astype(dtype), 1.0e6, 2.0, 2.5)
        assert out[0].tobytes() == ref[0].tobytes()
        assert out[1].tobytes() == ref[1].tobytes()

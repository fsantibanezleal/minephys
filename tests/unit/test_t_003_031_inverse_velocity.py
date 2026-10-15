# ruff: noqa: E501
"""T-003-031 (FR-003-15, FR-003-16, FR-003-21, FR-003-23): inverse-velocity time of failure (Fukuzono).

Expected API, module `minephys.geotech`:

    inverse_velocity_ttf(t, velocity, window=None) -> result
        t [s] strictly increasing 1-D, velocity [m/s] > 0 (same length); `window` None or an integer >= 3 that selects
        the LAST `window` samples. Ordinary least squares of y = 1 / velocity on t over the used samples: y = b0 + b1
        t. The result carries the attributes `failure_time` (= -b0 / b1, s), `slope` (b1, 1/m), `intercept` (b0, s/m),
        `r_squared` (squared Pearson correlation of t and y), `accelerating` (bool: b1 < 0) and `n_used` (int). While
        b1 >= 0 the wall is not accelerating: `accelerating` is False and `failure_time` is +inf (the slope, intercept
        and r_squared are still reported). 3 to 10**6 used samples; fewer than 3, a non-strictly increasing t, or a
        window < 3 is an `InputError` naming the argument. A velocity above 1e-2 m/s emits `ValidityWarning` (row
        `tripwire_slope_velocity_max`, argument `velocity`) and the result is still returned.

Oracles: the spec 003 section 7.4 noise-free Voight alpha = 2 series (A = 10 / m, t_f = 864,000 s, days 0 to
6: failure time 864,000 s, slope -10 / m, intercept 8.64e6 s/m, r^2 = 1), a five-sample least-squares fit
worked in exact rational arithmetic in this file (Fraction), SciPy `linregress` as the reference
implementation on noisy data, and the closed-form inverse-velocity relation 1 / v = A (t_f - t) of the alpha =
2 law. Tolerances TC-1, the printed values TC-2.
"""

from __future__ import annotations

import math
import warnings
from fractions import Fraction

import numpy as np
import pytest

import minephys
from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

DAY = 86400.0
T5 = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
Y5 = np.array([1000.0, 820.0, 610.0, 430.0, 210.0])  # s/m; velocity = 1 / y, all below 1e-2 m/s


def ols_exact(t: list[int], y: list[int]) -> tuple[Fraction, Fraction, Fraction]:
    """Hand OLS in exact arithmetic: slope, intercept, r^2 (all Fractions)."""
    n = len(t)
    tb, yb = Fraction(sum(t), n), Fraction(sum(y), n)
    sxx = sum((Fraction(a) - tb) ** 2 for a in t)
    sxy = sum((Fraction(a) - tb) * (Fraction(b) - yb) for a, b in zip(t, y, strict=True))
    syy = sum((Fraction(b) - yb) ** 2 for b in y)
    slope = sxy / sxx
    return slope, yb - slope * tb, sxy * sxy / (sxx * syy)


@pytest.mark.req("FR-003-15")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: noise-free alpha = 2 series, days 0..6: failure time 864,000 s, slope -10 / m, intercept 8.64e6 s/m, r^2 = 1",
)
def test_spec_noise_free_series() -> None:
    t = np.arange(0.0, 7.0) * DAY
    v = 1.0 / (10.0 * (864_000.0 - t))
    r = G.inverse_velocity_ttf(t, v)
    assert r.failure_time == pytest.approx(864_000.0, rel=1e-12)
    assert r.slope == pytest.approx(-10.0, rel=1e-12)
    assert r.intercept == pytest.approx(8.64e6, rel=1e-12)
    assert r.r_squared == pytest.approx(1.0, abs=1e-12)
    assert r.accelerating
    assert r.n_used == 7


@pytest.mark.req("FR-003-15")
@pytest.mark.oracle(
    "hand-calculation",
    "five samples, y = 1000, 820, 610, 430, 210 s/m at t = 0..40 s: slope -19.7, intercept 1008, t_f = 1008 / 19.7 = 51.16751; "
    "r^2 = 19700^2 / (1000 * 388520) = 0.9988932",
)
def test_hand_fit() -> None:
    slope, intercept, r2 = ols_exact([0, 10, 20, 30, 40], [1000, 820, 610, 430, 210])
    assert slope == Fraction(-197, 10)
    assert intercept == 1008
    assert float(r2) == pytest.approx(0.99889324, abs=5e-9)  # the exact rational above, TC-2
    r = G.inverse_velocity_ttf(T5, 1.0 / Y5)
    assert r.slope == pytest.approx(-19.7, rel=1e-12)
    assert r.intercept == pytest.approx(1008.0, rel=1e-12)
    assert r.failure_time == pytest.approx(1008.0 / 19.7, rel=1e-12)
    assert r.failure_time == pytest.approx(51.16751, abs=5e-6)
    assert r.r_squared == pytest.approx(float(r2), rel=1e-12)
    assert r.accelerating
    assert r.n_used == 5


@pytest.mark.req("FR-003-15")
@pytest.mark.oracle(
    "hand-calculation",
    "window = 3 keeps the last three samples: slope -20, intercept 3050/3, t_f = 3050/60 = 50.8333 (Fractions)",
)
def test_window_selects_the_last_samples() -> None:
    slope, intercept, r2 = ols_exact([20, 30, 40], [610, 430, 210])
    assert slope == -20
    assert intercept == Fraction(3050, 3)
    r = G.inverse_velocity_ttf(T5, 1.0 / Y5, window=3)
    assert r.n_used == 3
    assert r.slope == pytest.approx(-20.0, rel=1e-12)
    assert r.intercept == pytest.approx(float(intercept), rel=1e-12)
    assert r.failure_time == pytest.approx(float(-intercept / slope), rel=1e-12)  # 50.83333
    assert r.r_squared == pytest.approx(float(r2), rel=1e-12)
    full = G.inverse_velocity_ttf(T5, 1.0 / Y5, window=5)
    assert full.n_used == 5
    assert full.failure_time == pytest.approx(1008.0 / 19.7, rel=1e-12)
    assert G.inverse_velocity_ttf(T5, 1.0 / Y5, window=None).n_used == 5


@pytest.mark.req("FR-003-15")
@pytest.mark.oracle(
    "reference-implementation", "scipy.stats.linregress on y = 1 / v over the same samples (noisy series)"
)
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_noisy_series_against_linregress(seed: int) -> None:
    from scipy.stats import linregress

    rng = np.random.default_rng(seed)
    t = np.sort(rng.uniform(0.0, 7.0e5, 60))
    y = 8.64e6 - 10.0 * t + rng.normal(0.0, 2.0e4, 60)
    assert float(np.min(y)) > 0.0
    v = 1.0 / y
    r = G.inverse_velocity_ttf(t, v)
    ref = linregress(t, 1.0 / v)
    assert r.slope == pytest.approx(ref.slope, rel=1e-9)
    assert r.intercept == pytest.approx(ref.intercept, rel=1e-9)
    assert r.r_squared == pytest.approx(ref.rvalue**2, rel=1e-9)
    assert r.failure_time == pytest.approx(-ref.intercept / ref.slope, rel=1e-9)
    w = G.inverse_velocity_ttf(t, v, window=20)
    refw = linregress(t[-20:], y[-20:])
    assert w.n_used == 20
    assert w.slope == pytest.approx(refw.slope, rel=1e-8)
    assert w.failure_time == pytest.approx(-refw.intercept / refw.slope, rel=1e-8)


@pytest.mark.req("FR-003-15")
@pytest.mark.oracle(
    "analytical",
    "centred least squares: times near 1e9 s with a spread of 1e3 s still give the exact line (no normal-equation cancellation)",
)
def test_large_time_origin() -> None:
    t = 1.0e9 + np.arange(0.0, 11.0) * 100.0
    tf = 1.0e9 + 2000.0
    y = 5.0 * (tf - t)
    r = G.inverse_velocity_ttf(t, 1.0 / y)
    assert r.failure_time == pytest.approx(
        tf, abs=1e-4
    )  # 1e-13 relative to t_f; uncentred normal equations lose 3 digits here
    assert r.slope == pytest.approx(-5.0, rel=1e-9)


@pytest.mark.req("FR-003-15")
@pytest.mark.oracle("analytical", "a result is a record of plain numbers with the six documented fields")
def test_result_fields_and_types() -> None:
    r = G.inverse_velocity_ttf(T5, 1.0 / Y5)
    for name in ("failure_time", "slope", "intercept", "r_squared", "accelerating", "n_used"):
        assert hasattr(r, name), name
    assert isinstance(r.failure_time, float | np.floating)
    assert isinstance(r.slope, float | np.floating)
    assert isinstance(r.intercept, float | np.floating)
    assert isinstance(r.r_squared, float | np.floating)
    assert isinstance(r.accelerating, bool | np.bool_)
    assert isinstance(r.n_used, int | np.integer)
    assert not isinstance(r.n_used, bool)


@pytest.mark.req("FR-003-15")
@pytest.mark.oracle("analytical", "inputs are never modified and the call is pure")
def test_purity() -> None:
    t, v = T5.copy(), 1.0 / Y5
    v0 = v.copy()
    a = G.inverse_velocity_ttf(t, v)
    b = G.inverse_velocity_ttf(t, v)
    assert np.array_equal(t, T5)
    assert np.array_equal(v, v0)
    assert (a.failure_time, a.slope, a.intercept, a.r_squared) == (b.failure_time, b.slope, b.intercept, b.r_squared)


@pytest.mark.req("FR-003-15")
@pytest.mark.oracle("analytical", "float32 and integer times give the float64 result")
def test_dtype_invariance() -> None:
    t = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
    v = 1.0 / Y5
    ref = G.inverse_velocity_ttf(t, v)
    for dtype in (np.float32, np.int64, np.int32):
        out = G.inverse_velocity_ttf(t.astype(dtype), v)
        assert out.failure_time == ref.failure_time
        assert out.slope == ref.slope


# ------------------------------------------------------------------ FR-003-16: not accelerating


@pytest.mark.req("FR-003-16")
@pytest.mark.oracle(
    "analytical",
    "a decelerating wall (1 / v = 1000 + 2 t, slope +2): not accelerating, failure time +inf, the fit is still reported",
)
def test_decelerating_series() -> None:
    t = np.array([0.0, 1.0, 2.0, 3.0, 4.0]) * 1000.0
    r = G.inverse_velocity_ttf(t, 1.0 / (1000.0 + 2.0 * t))
    assert not r.accelerating
    assert r.failure_time == math.inf
    assert r.slope == pytest.approx(2.0, rel=1e-12)
    assert r.intercept == pytest.approx(1000.0, rel=1e-9)
    assert r.r_squared == pytest.approx(1.0, abs=1e-12)
    assert r.n_used == 5


@pytest.mark.req("FR-003-16")
@pytest.mark.oracle(
    "analytical",
    "constant velocity 2^-10 m/s (1 / v = 1024 s/m exactly): slope exactly 0, which is >= 0, so not accelerating",
)
def test_constant_velocity_is_not_accelerating() -> None:
    t = np.array([0.0, 1.0e4, 2.0e4, 3.0e4])
    r = G.inverse_velocity_ttf(t, np.full(4, 2.0**-10))
    assert r.slope == 0.0
    assert not r.accelerating
    assert r.failure_time == math.inf
    assert r.intercept == pytest.approx(1024.0, rel=1e-12)


@pytest.mark.req("FR-003-16")
@pytest.mark.oracle(
    "analytical",
    "the state follows the used window: an accelerating tail inside a decelerating series, and the reverse",
)
def test_state_follows_the_window() -> None:
    t = np.arange(0.0, 10.0) * 1000.0
    y = np.concatenate([1.0e4 + 5.0 * t[:5], 4.6e4 - 4.0 * t[5:]])  # 1 / v rises, then falls
    v = 1.0 / y
    head = G.inverse_velocity_ttf(t, v, window=10)
    assert head.n_used == 10
    tail = G.inverse_velocity_ttf(t, v, window=5)
    assert tail.accelerating
    assert tail.slope == pytest.approx(-4.0, rel=1e-9)
    assert tail.failure_time == pytest.approx(11500.0, rel=1e-9)  # 4.6e4 - 4 t = 0
    first = G.inverse_velocity_ttf(t[:5], v[:5])
    assert not first.accelerating
    assert first.failure_time == math.inf


# ------------------------------------------------------------------ FR-003-21: velocity tripwire


@pytest.mark.req("FR-003-21")
@pytest.mark.oracle(
    "analytical", "spec 003 7.3: velocity above 1e-2 m/s warns (row tripwire_slope_velocity_max) and still returns"
)
@pytest.mark.parametrize("big", [0.0100001, 0.02, 1.0, 50.0])
def test_velocity_tripwire_warns(big: float) -> None:
    v = 1.0 / Y5
    v[0] = big
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        r = G.inverse_velocity_ttf(T5, v)
    hits = [w for w in rec if issubclass(w.category, minephys.ValidityWarning)]
    assert hits
    assert hits[0].message.row == "tripwire_slope_velocity_max"
    assert hits[0].message.argument == "velocity"
    assert math.isfinite(float(r.slope))


@pytest.mark.req("FR-003-21")
@pytest.mark.oracle("analytical", "velocities up to and including 1e-2 m/s stay silent")
@pytest.mark.parametrize("v_max", [0.01, 0.005, 1e-9])
def test_velocity_tripwire_is_silent_at_the_limit(v_max: float) -> None:
    v = np.linspace(v_max / 2.0, v_max, 6)
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        G.inverse_velocity_ttf(np.arange(6.0), v)
    assert [w for w in rec if issubclass(w.category, minephys.ValidityWarning)] == []


# ------------------------------------------------------------------ FR-003-23 and domain: hostile inputs


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle(
    "analytical", "t must be strictly increasing: duplicates, decreases and a flat start are InputError naming t"
)
@pytest.mark.parametrize(
    "t",
    [
        [0.0, 1.0, 1.0, 2.0],
        [0.0, 2.0, 1.0, 3.0],
        [3.0, 2.0, 1.0, 0.0],
        [0.0, 0.0, 1.0, 2.0],
        [0.0, 1.0, 2.0, 2.0],
        [0.0, 1.0, 2.0, math.nextafter(2.0, 0.0)],
    ],
)
def test_t_must_increase(t: list[float]) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.inverse_velocity_ttf(np.array(t), np.full(4, 1e-3))
    assert ei.value.argument == "t"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle(
    "analytical", "fewer than 3 samples used is an InputError (a series of 0, 1 or 2 points; window 1 or 2)"
)
@pytest.mark.parametrize("n", [0, 1, 2])
def test_too_few_samples(n: int) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.inverse_velocity_ttf(np.arange(float(n)), np.full(n, 1e-3))
    assert ei.value.argument in {"t", "velocity"}


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "a window below 3 (or not an integer) is an InputError naming window")
@pytest.mark.parametrize("window", [0, 1, 2, -1, -5, 2.5, math.nan, math.inf, -math.inf])
def test_bad_window(window) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.inverse_velocity_ttf(T5, 1.0 / Y5, window=window)
    assert ei.value.argument == "window"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "a window of the wrong type is an InputTypeError naming window")
@pytest.mark.parametrize("window", ["3", b"3", 1 + 1j, True, object(), np.array([3, 4])])
def test_bad_window_type(window) -> None:
    with pytest.raises((minephys.InputTypeError, minephys.InputError)) as ei:
        G.inverse_velocity_ttf(T5, 1.0 / Y5, window=window)
    assert ei.value.argument == "window"


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "velocity > 0: zero and negative values are InputError naming velocity")
@pytest.mark.parametrize("bad", [0.0, -1e-3, -1e-300, -1.0])
def test_velocity_must_be_positive(bad: float) -> None:
    v = 1.0 / Y5
    v[2] = bad
    with pytest.raises(minephys.InputError) as ei:
        G.inverse_velocity_ttf(T5, v)
    assert ei.value.argument == "velocity"


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "NaN and infinity in either series are InputError naming the argument")
@pytest.mark.parametrize("arg", ["t", "velocity"])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite(arg: str, bad: float) -> None:
    t, v = T5.copy(), 1.0 / Y5
    (t if arg == "t" else v)[1] = bad
    with pytest.raises(minephys.InputError) as ei:
        G.inverse_velocity_ttf(t, v)
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "wrong dtypes are InputTypeError naming the argument")
@pytest.mark.parametrize("arg", ["t", "velocity"])
@pytest.mark.parametrize("bad", ["1.0", b"1", None, 1 + 1j, object(), np.datetime64("2026-01-01")])
def test_wrong_types(arg: str, bad) -> None:
    kw = {"t": T5, "velocity": 1.0 / Y5}
    with pytest.raises(minephys.InputTypeError) as ei:
        G.inverse_velocity_ttf(**{**kw, arg: bad})
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "2-D arrays and mismatched lengths are InputError naming t or velocity")
def test_shapes() -> None:
    for kw in (
        {"t": np.zeros((2, 3)), "velocity": 1.0 / Y5},
        {"t": T5, "velocity": np.full((5, 1), 1e-3)},
        {"t": T5, "velocity": np.full(4, 1e-3)},
        {"t": T5[:4], "velocity": np.full(5, 1e-3)},
    ):
        with pytest.raises(minephys.InputError) as ei:
            G.inverse_velocity_ttf(**kw)
        assert ei.value.argument in {"t", "velocity"}


@pytest.mark.req("FR-003-15")
@pytest.mark.oracle("analytical", "a long noise-free series (1,000 samples) is recovered exactly")
def test_one_thousand_samples() -> None:
    t = np.linspace(0.0, 9.0e7, 1000)
    tf = 1.0e8
    r = G.inverse_velocity_ttf(t, 1.0 / (2.5e-6 * (tf - t)))
    assert r.n_used == 1000
    assert r.failure_time == pytest.approx(tf, rel=1e-12)

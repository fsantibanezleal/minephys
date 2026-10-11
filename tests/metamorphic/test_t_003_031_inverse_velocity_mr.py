"""T-003-031 (P-003-09, FR-003-15, FR-003-16): metamorphic properties of the inverse-velocity time of failure.

P-003-09: for a noise-free alpha = 2 Voight series the fit returns the true failure time; shifting all times
by tau shifts the failure time by tau; scaling times by k and velocities by 1/k scales the failure time by k;
scaling velocities by k leaves the failure time unchanged (the slope and intercept scale as stated below, r^2
never changes). Further relations on noisy series: the fit equals NumPy's reference `polyfit` and the squared
`corrcoef` on the used window, `window = w` equals the fit on the last w samples, the state flag and the
failure time follow the sign of the slope.

Generators: t_f in 1e4..1e8 s (integer), 3..300 distinct integer times in [0, 0.95 t_f] spanning at least 0.1
t_f, A in 1e-4..1e2 per metre (velocity = 1 / (A (t_f - t))), noise of up to 5 % on 1 / v for the noisy
relations. Tolerances: TC-1 with a x10 margin on the exact recovery (rtol 1e-11 of t_f; conditioning of the
generator is at most about 40), 1e-9 on the relations that go through the fit of noisy data.

Oracle: analytical (closed-form Voight inverse velocity), NumPy `polyfit` and `corrcoef` as reference implementations.
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


@st.composite
def series(draw, noisy: bool = False, min_n: int = 3):
    tf = float(draw(st.integers(10_000, 10**8)))
    n = draw(st.integers(min_n, 300))
    seed = draw(st.integers(0, 2**32 - 1))
    rng = np.random.default_rng(seed)
    t = np.sort(rng.choice(int(0.95 * tf), size=n, replace=False)).astype(np.float64)
    assume(t[-1] - t[0] >= 0.1 * tf)
    a = draw(st.floats(1e-4, 1e2))
    y = a * (tf - t)
    if noisy:
        y = y * (1.0 + 0.05 * rng.uniform(-1.0, 1.0, n))
    return tf, t, 1.0 / y


def fit(t, v, **kw):
    return G.inverse_velocity_ttf(t, v, **kw)


@pytest.mark.req("P-003-09")
@pytest.mark.req("FR-003-15")
@pytest.mark.oracle(
    "analytical", "a noise-free alpha = 2 Voight series gives back the true failure time (TC-1 relative to t_f)"
)
@CFG
@given(s=series())
def test_exact_recovery(s: tuple) -> None:
    tf, t, v = s
    r = fit(t, v)
    assert r.failure_time == pytest.approx(tf, rel=1e-11)
    assert r.accelerating
    assert r.r_squared == pytest.approx(1.0, abs=1e-9)
    assert r.n_used == len(t)


@pytest.mark.req("P-003-09")
@pytest.mark.oracle(
    "analytical", "shift: t -> t + tau shifts the failure time by tau; slope, intercept shift as y(t - tau)"
)
@CFG
@given(s=series(noisy=True), tau=st.integers(-(10**7), 10**7))
def test_time_shift(s: tuple, tau: int) -> None:
    tf, t, v = s
    r = fit(t, v)
    r2 = fit(t + tau, v)
    assume(r.accelerating)
    assert r2.slope == pytest.approx(r.slope, rel=1e-9)
    assert r2.failure_time == pytest.approx(r.failure_time + tau, abs=1e-10 * (tf + abs(tau)))
    assert r2.intercept == pytest.approx(r.intercept - r.slope * tau, rel=1e-9, abs=1e-9 * abs(r.intercept))
    assert r2.r_squared == pytest.approx(r.r_squared, rel=1e-9, abs=1e-12)


@pytest.mark.req("P-003-09")
@pytest.mark.oracle(
    "analytical", "time scale: (t, v) -> (k t, v / k) scales the failure time and the intercept by k, keeps the slope"
)
@CFG
@given(s=series(noisy=True), k=st.floats(1e-3, 1e3))
def test_time_scaling(s: tuple, k: float) -> None:
    _, t, v = s
    r = fit(t, v)
    r2 = fit(k * t, v / k)
    assume(r.accelerating)
    assert r2.slope == pytest.approx(r.slope, rel=1e-9)
    assert r2.intercept == pytest.approx(k * r.intercept, rel=1e-9, abs=1e-9 * k * abs(r.intercept))
    assert r2.failure_time == pytest.approx(k * r.failure_time, rel=1e-9)
    assert r2.r_squared == pytest.approx(r.r_squared, rel=1e-9, abs=1e-12)


@pytest.mark.req("P-003-09")
@pytest.mark.oracle(
    "analytical", "velocity scale: v -> k v leaves the failure time and r^2 unchanged, divides slope and intercept by k"
)
@CFG
@given(s=series(noisy=True), k=st.floats(1e-3, 1e3))
def test_velocity_scaling(s: tuple, k: float) -> None:
    _, t, v = s
    r = fit(t, v)
    r2 = fit(t, k * v)
    assert r2.accelerating == r.accelerating
    assert r2.slope == pytest.approx(r.slope / k, rel=1e-9)
    assert r2.intercept == pytest.approx(r.intercept / k, rel=1e-9)
    assert r2.r_squared == pytest.approx(r.r_squared, rel=1e-9, abs=1e-12)
    if r.accelerating:
        assert r2.failure_time == pytest.approx(r.failure_time, rel=1e-9)
    else:
        assert r2.failure_time == math.inf


@pytest.mark.req("FR-003-15")
@pytest.mark.oracle(
    "reference-implementation", "numpy.polyfit(t, 1 / v, 1) and numpy.corrcoef squared, on the used window"
)
@CFG
@given(s=series(noisy=True), frac=st.floats(0.0, 1.0))
def test_against_numpy(s: tuple, frac: float) -> None:
    tf, t, v = s
    n = len(t)
    w = 3 + int(frac * (n - 3))
    assume(t[-1] - t[n - w] >= 0.02 * tf)
    r = fit(t, v, window=w)
    y = 1.0 / v[n - w :]
    tt = t[n - w :]
    slope, intercept = np.polyfit(tt, y, 1)
    assert r.n_used == w
    assert r.slope == pytest.approx(slope, rel=1e-8)
    assert r.intercept == pytest.approx(intercept, rel=1e-8, abs=1e-8 * abs(float(np.mean(y))))
    assert r.r_squared == pytest.approx(float(np.corrcoef(tt, y)[0, 1] ** 2), rel=1e-8, abs=1e-12)


@pytest.mark.req("FR-003-15")
@pytest.mark.oracle("analytical", "window = w is the fit of the last w samples; window = n or None is the fit of all")
@CFG
@given(s=series(noisy=True), frac=st.floats(0.0, 1.0))
def test_window_is_a_tail_slice(s: tuple, frac: float) -> None:
    _, t, v = s
    n = len(t)
    w = 3 + int(frac * (n - 3))
    a = fit(t, v, window=w)
    b = fit(t[n - w :], v[n - w :])
    assert a.n_used == b.n_used == w
    assert a.slope == pytest.approx(b.slope, rel=1e-12)
    assert a.intercept == pytest.approx(b.intercept, rel=1e-12)
    assert a.failure_time == pytest.approx(b.failure_time, rel=1e-12) or a.failure_time == b.failure_time == math.inf
    assert fit(t, v, window=n).n_used == n
    assert fit(t, v).slope == pytest.approx(fit(t, v, window=n).slope, rel=1e-12)


@pytest.mark.req("FR-003-16")
@pytest.mark.req("FR-003-15")
@pytest.mark.oracle(
    "analytical", "failure time is -b0 / b1 when the slope is negative and +inf otherwise; r^2 is in [0, 1]"
)
@CFG
@given(s=series(noisy=True), flip=st.booleans())
def test_state_and_failure_time(s: tuple, flip: bool) -> None:
    _, t, v = s
    if flip:  # a decelerating series: 1 / v mirrored in time
        v = v[::-1].copy()
    r = fit(t, v)
    assert 0.0 <= r.r_squared <= 1.0 + 1e-12
    if r.slope < 0.0:
        assert r.accelerating
        assert r.failure_time == pytest.approx(-r.intercept / r.slope, rel=1e-12)
    else:
        assert not r.accelerating
        assert r.failure_time == math.inf

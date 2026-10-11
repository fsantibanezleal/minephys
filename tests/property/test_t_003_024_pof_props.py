"""T-003-024 (FR-003-12, FR-003-13, P-003-08): properties of the Monte-Carlo factor of safety and of the PoF helpers.

Expected API: see tests/unit/test_t_003_024_pof.py (`monte_carlo_fos`, `probability_of_failure`, `required_samples`).

P-003-08: zero standard deviations give the deterministic factor of safety for every sample; the same seed
gives the same samples (bitwise); for phi' = 0 (F linear in c') the sample mean of the factor of safety equals
k times the mean of the truncated normal of the cohesion (closed form, five standard errors). Metamorphic
relations on the Monte-Carlo run (same seed, so the same standard-normal stream): permuting the slices changes
nothing; scaling weight, pore pressure and the cohesion parameters by one factor changes nothing; raising the
cohesion mean or the friction mean raises every sample when truncation never triggers. Properties of the
helpers: the PoF is the exact fraction below the threshold, is non-decreasing in the threshold, is unchanged
and has its standard error divided by sqrt(2) when the sample set is duplicated; `required_samples` is the
least integer reaching the target relative error, monotone in both arguments.

Generators (spec 003: Bishop's slice data): 3-40 slices, alpha in [-10, 55] deg, widths 1-5 m, heights 1-15 m,
unit weight 20 kN/m^3, c' in [5, 50] kPa, phi' in [10, 45] deg, pore pressure up to 40 % of the overburden;
cases whose independent reference factor of safety falls outside [0.5, 20] are discarded.

Oracle: analytical (closed-form truncated-normal moments, binomial counting), independent fixed-point Bishop
reference.
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
        drive = float(np.sum(w * np.sin(alpha)))
        if drive <= 0.0:
            return math.nan
        fn = float(np.sum((c * b + (w - u * b) * np.tan(phi)) / m) / drive)
        if abs(fn - f) <= 1e-14 * f:
            return fn
        f = fn
    return math.nan


@st.composite
def slope_data(draw, min_n=3, max_n=40):
    n = draw(st.integers(min_n, max_n))
    b = np.array(draw(st.lists(st.floats(1.0, 5.0), min_size=n, max_size=n)))
    h = np.array(draw(st.lists(st.floats(1.0, 15.0), min_size=n, max_size=n)))
    alpha = np.radians(np.array(draw(st.lists(st.floats(-10.0, 55.0), min_size=n, max_size=n))))
    ur = np.array(draw(st.lists(st.floats(0.0, 0.4), min_size=n, max_size=n)))
    c = draw(st.floats(5e3, 5e4))
    phi = math.radians(draw(st.floats(10.0, 45.0)))
    w, u = GAMMA * b * h, ur * GAMMA * h
    f = ref_bishop(b, w, alpha, u, c, phi)
    assume(math.isfinite(f) and 0.5 <= f <= 20.0)
    return {"width": b, "weight": w, "base_angle": alpha, "pore_pressure": u, "cohesion": c, "friction_angle": phi}


def run(d, c_mean, c_sd, f_mean, f_sd, n, rng):
    return G.monte_carlo_fos(
        d["width"], d["weight"], d["base_angle"], d["pore_pressure"], c_mean, c_sd, f_mean, f_sd, n, rng
    )


def pdf(x: float) -> float:
    return 0.0 if math.isinf(x) else math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def truncated_at_zero(mu: float, sd: float) -> tuple[float, float]:
    """Mean and sd of N(mu, sd) truncated to [0, inf) (closed forms)."""
    a = -mu / sd
    z = 1.0 - cdf(a)
    shift = pdf(a) / z
    return mu + sd * shift, sd * math.sqrt(1.0 + a * pdf(a) / z - shift * shift)


@pytest.mark.req("FR-003-12")
@pytest.mark.req("P-003-08")
@pytest.mark.oracle("analytical", "zero standard deviations: every sample is the deterministic Bishop factor of safety")
@CFG
@given(d=slope_data(), n=st.integers(1, 20), seed=st.integers(0, 2**32 - 1))
def test_zero_spread_is_deterministic(d: dict, n: int, seed: int) -> None:
    out = run(d, d["cohesion"], 0.0, d["friction_angle"], 0.0, n, seed)
    assert out.shape == (n,)
    assert np.all(out == out[0])
    assert float(out[0]) == pytest.approx(float(G.bishop_simplified_fos(**d)), rel=1e-12)


@pytest.mark.req("P-003-08")
@pytest.mark.oracle("analytical", "determinism: same seed, same Generator state, bitwise-identical samples")
@CFG
@given(d=slope_data(max_n=12), n=st.integers(1, 60), seed=st.integers(0, 2**32 - 1))
def test_determinism(d: dict, n: int, seed: int) -> None:
    args = (d, d["cohesion"], 0.1 * d["cohesion"], d["friction_angle"], 0.02)
    a = run(*args, n, seed)
    b = run(*args, n, seed)
    c = run(*args, n, np.random.default_rng(seed))
    assert a.tobytes() == b.tobytes() == c.tobytes()
    if n >= 2:
        assert a.tobytes() != run(*args, n, (seed + 1) % 2**32).tobytes()


@pytest.mark.req("P-003-08")
@pytest.mark.oracle(
    "analytical",
    "phi' = 0: F = k c' with k = sum(l) / sum(W sin alpha); sample mean of c' is the truncated-normal mean",
)
@CFG
@given(
    d=slope_data(),
    mean=st.floats(0.0, 3e4),
    sd=st.floats(1e2, 2e4),
    seed=st.integers(0, 2**32 - 1),
)
def test_linear_case_mean(d: dict, mean: float, sd: float, seed: int) -> None:
    n = 4000
    k = float(np.sum(d["width"] / np.cos(d["base_angle"])) / np.sum(d["weight"] * np.sin(d["base_angle"])))
    out = run(d, mean, sd, 0.0, 0.0, n, seed)
    mu_t, sd_t = truncated_at_zero(mean, sd)
    assert float(np.min(out)) >= 0.0
    assert float(np.mean(out)) == pytest.approx(k * mu_t, abs=5.0 * k * sd_t / math.sqrt(n) + 1e-12)


@pytest.mark.req("FR-003-12")
@pytest.mark.req("P-003-08")
@pytest.mark.oracle("analytical", "permuting the slices changes no sample (same seed, same stream of draws)")
@CFG
@given(d=slope_data(), seed=st.integers(0, 2**32 - 1), perm_seed=st.integers(0, 2**32 - 1))
def test_slice_permutation(d: dict, seed: int, perm_seed: int) -> None:
    perm = np.random.default_rng(perm_seed).permutation(len(d["width"]))
    p = {k: (v[perm] if isinstance(v, np.ndarray) else v) for k, v in d.items()}
    args = (0.1 * d["cohesion"], d["friction_angle"], 0.01)
    a = run(d, d["cohesion"], *args, 40, seed)
    b = run(p, d["cohesion"], *args, 40, seed)
    np.testing.assert_allclose(b, a, rtol=1e-9)


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle(
    "analytical", "N <-> kN: scaling weight, pore pressure and the cohesion parameters by k changes nothing"
)
@CFG
@given(d=slope_data(), k=st.floats(1e-3, 1e3), seed=st.integers(0, 2**32 - 1))
def test_unit_change_invariance(d: dict, k: float, seed: int) -> None:
    c, sd_c = d["cohesion"], 0.2 * d["cohesion"]
    a = run(d, c, sd_c, d["friction_angle"], 0.02, 40, seed)
    scaled = {**d, "weight": k * d["weight"], "pore_pressure": k * d["pore_pressure"]}
    b = run(scaled, k * c, k * sd_c, d["friction_angle"], 0.02, 40, seed)
    np.testing.assert_allclose(b, a, rtol=1e-8)


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle(
    "analytical",
    "same z stream and no truncation: a larger cohesion mean, or a larger friction mean, raises every sample",
)
@CFG
@given(
    d=slope_data(),
    seed=st.integers(0, 2**32 - 1),
    dc=st.floats(0.05, 0.5),
    dphi=st.floats(0.01, 0.1),
)
def test_coupled_monotonicity(d: dict, seed: int, dc: float, dphi: float) -> None:
    c0, phi0 = d["cohesion"], d["friction_angle"]
    base = run(d, c0, 0.01 * c0, phi0, 0.005, 30, seed)
    more_c = run(d, c0 * (1.0 + dc), 0.01 * c0, phi0, 0.005, 30, seed)
    more_phi = run(d, c0, 0.01 * c0, phi0 + dphi, 0.005, 30, seed)
    assert np.all(more_c > base)
    assert np.all(more_phi > base)


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle("analytical", "the PoF is the exact count below the threshold over n; se = sqrt(p (1 - p) / n)")
@CFG
@given(
    x=st.lists(st.floats(0.05, 6.0), min_size=1, max_size=300),
    t=st.floats(0.05, 6.0),
)
def test_pof_is_a_fraction(x: list[float], t: float) -> None:
    arr = np.array(x)
    pof, se, n = G.probability_of_failure(arr, t)
    count = sum(1 for v in x if v < t)
    assert n == len(x)
    assert pof == count / len(x)
    assert 0.0 <= pof <= 1.0
    assert se == pytest.approx(math.sqrt(pof * (1.0 - pof) / len(x)), rel=1e-12, abs=1e-300)


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle("analytical", "the PoF never decreases when the threshold is raised")
@CFG
@given(x=st.lists(st.floats(0.05, 6.0), min_size=1, max_size=200), t1=st.floats(0.05, 6.0), t2=st.floats(0.05, 6.0))
def test_pof_is_monotone_in_the_threshold(x: list[float], t1: float, t2: float) -> None:
    lo, hi = sorted((t1, t2))
    arr = np.array(x)
    assert G.probability_of_failure(arr, lo)[0] <= G.probability_of_failure(arr, hi)[0]


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle(
    "analytical", "duplicating the samples keeps the PoF and divides the standard error by sqrt(2); order is irrelevant"
)
@CFG
@given(
    x=st.lists(st.floats(0.05, 6.0), min_size=1, max_size=200), t=st.floats(0.05, 6.0), seed=st.integers(0, 2**32 - 1)
)
def test_pof_duplication_and_order(x: list[float], t: float, seed: int) -> None:
    arr = np.array(x)
    pof, se, n = G.probability_of_failure(arr, t)
    pof2, se2, n2 = G.probability_of_failure(np.concatenate([arr, arr]), t)
    assert n2 == 2 * n
    assert pof2 == pof
    assert se2 == pytest.approx(se / math.sqrt(2.0), rel=1e-12, abs=1e-300)
    shuffled = np.random.default_rng(seed).permutation(arr)
    assert G.probability_of_failure(shuffled, t) == (pof, se, n)


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle(
    "analytical", "required_samples is the least n with sqrt((1 - p) / (p n)) <= eps, hence monotone in p and eps"
)
@CFG
@given(p=st.floats(1e-4, 0.999), eps=st.floats(0.01, 1.0), p2=st.floats(1e-4, 0.999), eps2=st.floats(0.01, 1.0))
def test_required_samples_is_the_least_sufficient_count(p: float, eps: float, p2: float, eps2: float) -> None:
    n = int(G.required_samples(p, eps))
    x = (1.0 - p) / (p * eps * eps)
    assert n >= x * (1.0 - 1e-12)
    assert n - 1 < x * (1.0 + 1e-12)
    assert n >= 1
    if eps2 <= eps:  # a tighter target needs at least as many samples
        assert int(G.required_samples(p, eps2)) >= n
    if p2 <= p:  # a rarer event needs at least as many samples
        assert int(G.required_samples(p2, eps)) >= n

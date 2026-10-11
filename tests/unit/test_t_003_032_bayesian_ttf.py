# ruff: noqa: E501
"""T-003-032 (FR-003-17, FR-003-21, FR-003-23, P-003-10): Bayesian time of failure by a conjugate Gaussian line fit.

Expected API, module `minephys.geotech`:

    bayesian_ttf(t, velocity, rng, noise_sd=None, prior_mean=None, prior_cov=None, n_draws=10_000, credible=0.9,
                 window=None) -> result
        y = 1 / velocity is fitted by y = b0 + b1 t on the used samples (all, or the last `window`, window >= 3; t
        strictly increasing 1-D [s], velocity [m/s] > 0). Posterior of (b0, b1): Sigma_N = (Sigma0^-1 + X'X /
        sigma^2)^-1, mu_N = Sigma_N (Sigma0^-1 mu0 + X'y / sigma^2) with X = [1, t]; a flat prior (Sigma0^-1 = 0) when
        `prior_cov` is None; sigma = `noise_sd` [s/m] when given, else sqrt(RSS / (n - 2)) of the ordinary
        least-squares residuals. `n_draws` (100..10**6) draws of (b0, b1) from N(mu_N, Sigma_N) are made from `rng`
        (Generator or integer seed, required, no default); t_f = -b0 / b1 is evaluated on the draws with b1 < 0.
    The result has these attributes (the spec leaves the names open, they are fixed here):
        posterior_mean   float64 array (2,)    mu_N
        posterior_cov    float64 array (2, 2)  Sigma_N (symmetric)
        failure_time_median, failure_time_lower, failure_time_upper
                         floats [s]: the median and the equal-tailed `credible` interval (quantiles (1 - credible) / 2 and (1 +
                         credible) / 2) of t_f over the draws with b1 < 0; not finite (NaN or +inf) when no draw has b1 < 0
        fraction_not_accelerating   float in [0, 1]: the fraction of all draws with b1 >= 0.
    `prior_cov` must be a symmetric positive-definite 2 x 2 matrix and `prior_mean` a length-2 vector (an
    `InputError` naming the argument otherwise); fewer than 3 used samples, t not strictly increasing, n_draws
    outside 100..10**6 and a window < 3 are `InputError`s; velocity above 1e-2 m/s warns
    (`tripwire_slope_velocity_max`).

Oracles: the spec 003 section 7.4 worked case (A = 10 / m, t_f = 864,000 s, days 0 to 6, flat prior, noise_sd
= 4.32e4 s/m: covariance diagonal (8.66468571e8, 8.92857143e-3), 5 % / median / 95 % quantiles 854,367.67 /
864,000 / 873,924.60 s), the exact rational solution of the conjugate update on a five-sample series
(`Fraction` arithmetic written in this file), the Fieller distribution of a ratio of jointly normal variables
(P(t_f <= tau) = Phi(-(mu0 + tau mu1) / sqrt(S00 + 2 tau S01
+ tau^2 S11)) when P(b1 >= 0) is negligible; the empirical CDF at the returned quantiles must hit the nominal
level within four binomial standard errors, TC-4) and the sequential-update identity (posterior after two
batches = batch posterior).
"""

from __future__ import annotations

import math
import warnings
from fractions import Fraction
from itertools import pairwise

import numpy as np
import pytest

import minephys
from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

DAY = 86400.0
T5 = np.array([0.0, 10.0, 20.0, 30.0, 40.0])
Y5 = np.array([1000.0, 820.0, 610.0, 430.0, 210.0])  # s/m; velocity 1 / y is below 1e-2 m/s
V5 = 1.0 / Y5


def phi_cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def cdf_tf(tau: float, mu: np.ndarray, cov: np.ndarray) -> float:
    """P(t_f <= tau) for t_f = -b0 / b1 with (b0, b1) ~ N(mu, cov), neglecting P(b1 >= 0) (Fieller)."""
    s = math.sqrt(cov[0, 0] + 2.0 * tau * cov[0, 1] + tau * tau * cov[1, 1])
    return phi_cdf(-(mu[0] + tau * mu[1]) / s)


def exact_posterior(t, y, sigma2, prior_mean=None, prior_cov=None):
    """Conjugate update in exact rational arithmetic (lists of Fractions / ints): returns (mean, cov) as Fractions."""
    n = len(t)
    xtx = [[Fraction(n), Fraction(sum(t))], [Fraction(sum(t)), Fraction(sum(a * a for a in t))]]
    xty = [Fraction(sum(y)), Fraction(sum(a * b for a, b in zip(t, y, strict=True)))]
    prec = [[xtx[i][j] / sigma2 for j in range(2)] for i in range(2)]
    rhs = [xty[i] / sigma2 for i in range(2)]
    if prior_cov is not None:
        (a, b), (c, d) = prior_cov
        det0 = Fraction(a) * Fraction(d) - Fraction(b) * Fraction(c)
        p0 = [[Fraction(d) / det0, -Fraction(b) / det0], [-Fraction(c) / det0, Fraction(a) / det0]]
        for i in range(2):
            for j in range(2):
                prec[i][j] += p0[i][j]
            rhs[i] += p0[i][0] * Fraction(prior_mean[0]) + p0[i][1] * Fraction(prior_mean[1])
    det = prec[0][0] * prec[1][1] - prec[0][1] * prec[1][0]
    cov = [[prec[1][1] / det, -prec[0][1] / det], [-prec[1][0] / det, prec[0][0] / det]]
    mean = [cov[i][0] * rhs[0] + cov[i][1] * rhs[1] for i in range(2)]
    return mean, cov


def bayes(t, v, rng=1, **kw):
    return G.bayesian_ttf(t, v, rng, **kw)


# ------------------------------------------------------------------ FR-003-17: the worked case of spec 7.4


@pytest.mark.req("FR-003-17")
@pytest.mark.req("P-003-10")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: A = 10 / m, t_f = 864,000 s, days 0..6, flat prior, sigma = 4.32e4 s/m: cov diag (8.66468571e8, 8.92857143e-3)",
)
def test_spec_posterior_moments() -> None:
    t = np.arange(0.0, 7.0) * DAY
    v = 1.0 / (10.0 * (864_000.0 - t))
    r = bayes(t, v, 12345, noise_sd=4.32e4, n_draws=1000)
    assert r.posterior_mean.shape == (2,)
    assert r.posterior_cov.shape == (2, 2)
    assert r.posterior_mean.dtype == r.posterior_cov.dtype == np.float64
    assert r.posterior_mean[0] == pytest.approx(8.64e6, rel=1e-9)
    assert r.posterior_mean[1] == pytest.approx(-10.0, rel=1e-9)
    assert r.posterior_cov[0, 0] == pytest.approx(
        8.66468571e8, abs=1.0
    )  # printed to 9 digits: one unit of the last digit
    sxx = sum(Fraction(int(a)) ** 2 for a in t)  # exact integers (seconds)
    det = 7 * sxx - Fraction(int(t.sum())) ** 2
    assert r.posterior_cov[0, 0] == pytest.approx(
        float(Fraction(43_200) ** 2 * sxx / det), rel=1e-9
    )  # sigma^2 sum(t^2) / det
    assert r.posterior_cov[1, 1] == pytest.approx(8.92857143e-3, abs=5e-12)
    assert r.posterior_cov[0, 1] == pytest.approx(-2314.285714285715, rel=1e-9)  # sigma^2 * (-sum t / det) by hand
    assert r.posterior_cov[1, 0] == pytest.approx(r.posterior_cov[0, 1], rel=1e-12)


@pytest.mark.req("FR-003-17")
@pytest.mark.req("P-003-10")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: median 864,000 s, 5 % and 95 % quantiles 854,367.67 s and 873,924.60 s; verified through the Fieller CDF (TC-4)",
)
def test_spec_quantiles() -> None:
    t = np.arange(0.0, 7.0) * DAY
    v = 1.0 / (10.0 * (864_000.0 - t))
    n = 200_000
    r = bayes(t, v, 2026, noise_sd=4.32e4, n_draws=n)
    assert r.fraction_not_accelerating == 0.0  # P(b1 >= 0) = Phi(-107): no draw
    mu = np.array([8.64e6, -10.0])
    cov = np.array([[8.66468571e8, -2314.285714285715], [-2314.285714285715, 8.92857143e-3]])
    for value, level in (
        (r.failure_time_lower, 0.05),
        (r.failure_time_median, 0.5),
        (r.failure_time_upper, 0.95),
    ):
        assert cdf_tf(value, mu, cov) == pytest.approx(level, abs=4.0 * math.sqrt(level * (1.0 - level) / n))
    # and the printed quantile values themselves, with four standard errors of a sample quantile (16 s median, 28 s tails)
    assert r.failure_time_median == pytest.approx(864_000.0, abs=70.0)
    assert r.failure_time_lower == pytest.approx(854_367.67, abs=120.0)
    assert r.failure_time_upper == pytest.approx(873_924.60, abs=120.0)
    assert r.failure_time_lower < r.failure_time_median < r.failure_time_upper


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle(
    "analytical",
    "Fieller quantiles of the spec case at other credible levels: 0.5 (25 / 75 %), 0.99 (0.5 / 99.5 %), TC-4",
)
@pytest.mark.parametrize("credible", [0.5, 0.8, 0.99])
def test_credible_level(credible: float) -> None:
    t = np.arange(0.0, 7.0) * DAY
    v = 1.0 / (10.0 * (864_000.0 - t))
    n = 200_000
    r = bayes(t, v, 7, noise_sd=4.32e4, n_draws=n, credible=credible)
    mu = np.array([8.64e6, -10.0])
    cov = np.array([[8.66468571e8, -2314.285714285715], [-2314.285714285715, 8.92857143e-3]])
    lo_level, hi_level = (1.0 - credible) / 2.0, (1.0 + credible) / 2.0
    assert cdf_tf(r.failure_time_lower, mu, cov) == pytest.approx(
        lo_level, abs=4.0 * math.sqrt(lo_level * (1.0 - lo_level) / n)
    )
    assert cdf_tf(r.failure_time_upper, mu, cov) == pytest.approx(
        hi_level, abs=4.0 * math.sqrt(hi_level * (1.0 - hi_level) / n)
    )
    assert cdf_tf(r.failure_time_median, mu, cov) == pytest.approx(0.5, abs=4.0 * math.sqrt(0.25 / n))


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle(
    "analytical", "the interval widens with the credible mass: 0.5 inside 0.9 inside 0.99, all around the same median"
)
def test_nested_intervals() -> None:
    t = np.arange(0.0, 7.0) * DAY
    v = 1.0 / (10.0 * (864_000.0 - t))
    spans = [bayes(t, v, 3, noise_sd=4.32e4, n_draws=50_000, credible=c) for c in (0.5, 0.9, 0.99)]
    assert spans[0].failure_time_lower > spans[1].failure_time_lower > spans[2].failure_time_lower
    assert spans[0].failure_time_upper < spans[1].failure_time_upper < spans[2].failure_time_upper


# ------------------------------------------------------------------ FR-003-17: exact conjugate algebra


@pytest.mark.req("FR-003-17")
@pytest.mark.req("P-003-10")
@pytest.mark.oracle(
    "hand-calculation",
    "flat prior, known sigma = 20 s/m on t = 0..40 s, y = 1000, 820, 610, 430, 210: mean (1008, -19.7), cov = 400 * [[.6, -.02], [-.02, .001]]",
)
def test_flat_prior_known_sigma_exact() -> None:
    mean, cov = exact_posterior([0, 10, 20, 30, 40], [1000, 820, 610, 430, 210], Fraction(400))
    assert mean == [Fraction(1008), Fraction(-197, 10)]
    assert cov == [[Fraction(240), Fraction(-8)], [Fraction(-8), Fraction(2, 5)]]
    r = bayes(T5, V5, noise_sd=20.0)
    np.testing.assert_allclose(r.posterior_mean, [1008.0, -19.7], rtol=1e-12)
    np.testing.assert_allclose(r.posterior_cov, [[240.0, -8.0], [-8.0, 0.4]], rtol=1e-12)


@pytest.mark.req("FR-003-17")
@pytest.mark.req("P-003-10")
@pytest.mark.oracle(
    "hand-calculation",
    "sigma from the residuals: RSS = 430 on 5 samples, s^2 = 430 / 3 = 143.33, cov = s^2 * [[.6, -.02], [-.02, .001]] = [[86, -43/15], [-43/15, 43/300]]",
)
def test_estimated_sigma_exact() -> None:
    r = bayes(T5, V5)
    np.testing.assert_allclose(r.posterior_mean, [1008.0, -19.7], rtol=1e-12)
    np.testing.assert_allclose(r.posterior_cov, [[86.0, -43.0 / 15.0], [-43.0 / 15.0, 43.0 / 300.0]], rtol=1e-11)


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle(
    "hand-calculation",
    "window = 3: the last three samples, known sigma = 20: mean (3050/3, -20), cov = [[5800/3, -60], [-60, 2]]",
)
def test_window_posterior_exact() -> None:
    mean, cov = exact_posterior([20, 30, 40], [610, 430, 210], Fraction(400))
    assert mean == [Fraction(3050, 3), Fraction(-20)]
    assert cov == [[Fraction(5800, 3), Fraction(-60)], [Fraction(-60), Fraction(2)]]
    r = bayes(T5, V5, noise_sd=20.0, window=3)
    np.testing.assert_allclose(r.posterior_mean, [3050.0 / 3.0, -20.0], rtol=1e-12)
    np.testing.assert_allclose(r.posterior_cov, [[5800.0 / 3.0, -60.0], [-60.0, 2.0]], rtol=1e-11)


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle(
    "hand-calculation",
    "informative prior N((1100, -25), diag(200^2, 5^2)) with sigma = 20: exact rational conjugate update (Fraction arithmetic in the test)",
)
def test_informative_prior_exact() -> None:
    prior_mean = [1100, -25]
    prior_cov = [[40_000, 0], [0, 25]]
    mean, cov = exact_posterior([0, 10, 20, 30, 40], [1000, 820, 610, 430, 210], Fraction(400), prior_mean, prior_cov)
    r = bayes(
        T5, V5, noise_sd=20.0, prior_mean=np.array(prior_mean, dtype=float), prior_cov=np.array(prior_cov, dtype=float)
    )
    np.testing.assert_allclose(r.posterior_mean, [float(m) for m in mean], rtol=1e-11)
    np.testing.assert_allclose(r.posterior_cov, [[float(c) for c in row] for row in cov], rtol=1e-11)
    # shrinkage: the posterior mean of the slope lies between the prior value and the data value
    assert -25.0 < float(mean[1]) < -19.7


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle("hand-calculation", "a correlated, non-diagonal prior (rho = 0.5): exact rational conjugate update")
def test_correlated_prior_exact() -> None:
    prior_mean = [900, -15]
    prior_cov = [[10_000, 100], [100, 4]]  # sd 100 and 2, correlation 0.5
    mean, cov = exact_posterior([0, 10, 20, 30, 40], [1000, 820, 610, 430, 210], Fraction(900), prior_mean, prior_cov)
    r = bayes(T5, V5, noise_sd=30.0, prior_mean=[900.0, -15.0], prior_cov=[[10_000.0, 100.0], [100.0, 4.0]])
    np.testing.assert_allclose(r.posterior_mean, [float(m) for m in mean], rtol=1e-10)
    np.testing.assert_allclose(r.posterior_cov, [[float(c) for c in row] for row in cov], rtol=1e-10)


@pytest.mark.req("FR-003-17")
@pytest.mark.req("P-003-10")
@pytest.mark.oracle(
    "analytical",
    "sequential identity: the posterior of the last five samples with the posterior of the first five as prior equals the batch posterior (known sigma)",
)
def test_sequential_update_equals_batch() -> None:
    t = np.arange(0.0, 10.0) * 1000.0
    y = np.array([5000.0, 4620.0, 4290.0, 3990.0, 3550.0, 3310.0, 2940.0, 2570.0, 2310.0, 1930.0])
    v = 1.0 / y
    sigma = 90.0
    batch = bayes(t, v, noise_sd=sigma)
    first = bayes(t[:5], v[:5], noise_sd=sigma)
    sym = 0.5 * (first.posterior_cov + first.posterior_cov.T)  # exactly symmetric prior
    second = bayes(t[5:], v[5:], noise_sd=sigma, prior_mean=first.posterior_mean, prior_cov=sym)
    np.testing.assert_allclose(second.posterior_mean, batch.posterior_mean, rtol=1e-8)
    np.testing.assert_allclose(second.posterior_cov, batch.posterior_cov, rtol=1e-8)


@pytest.mark.req("P-003-10")
@pytest.mark.oracle("analytical", "with known sigma, adding a sample never increases det(Sigma_N)")
def test_determinant_decreases_with_data() -> None:
    t = np.arange(0.0, 12.0) * 500.0
    y = 9000.0 - 1.0 * t + np.array([30, -20, 10, -40, 25, 5, -15, 35, -30, 0, 20, -10], dtype=float)
    dets = []
    for n in range(3, 13):
        r = bayes(t[:n], 1.0 / y[:n], noise_sd=40.0)
        dets.append(float(np.linalg.det(r.posterior_cov)))
    for a, b in pairwise(dets):
        assert b < a * (1.0 + 1e-9)
    assert dets[-1] < 0.1 * dets[0]


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle(
    "analytical", "time origin: shifting t by tau maps the posterior by (b0, b1) -> (b0 - tau b1, b1): J S J^T"
)
def test_shift_of_the_time_origin() -> None:
    tau = 1.0e6
    r = bayes(T5 * 1000.0, V5, noise_sd=20.0)
    s = bayes(T5 * 1000.0 + tau, V5, noise_sd=20.0)
    jac = np.array([[1.0, tau], [0.0, 1.0]])  # b0' = b0 - b1 tau  ->  b0 = b0' + b1 tau
    np.testing.assert_allclose(s.posterior_mean[1], r.posterior_mean[1], rtol=1e-9)
    np.testing.assert_allclose(s.posterior_mean[0] + s.posterior_mean[1] * tau, r.posterior_mean[0], rtol=1e-9)
    np.testing.assert_allclose(jac @ s.posterior_cov @ jac.T, r.posterior_cov, rtol=1e-7, atol=1e-12)


# ------------------------------------------------------------------ FR-003-17: the draws


@pytest.mark.req("FR-003-17")
@pytest.mark.req("P-003-10")
@pytest.mark.oracle(
    "analytical",
    "fraction of draws with b1 >= 0 is Phi(mu1 / sqrt(S11)) = Phi(-1) when sigma = 19.7 / sqrt(0.001) (TC-4)",
)
def test_fraction_not_accelerating() -> None:
    n = 100_000
    sigma = 19.7 / math.sqrt(0.001)
    r = bayes(T5, V5, 99, noise_sd=sigma, n_draws=n)
    assert r.posterior_mean[1] == pytest.approx(-19.7, rel=1e-12)
    assert math.sqrt(r.posterior_cov[1, 1]) == pytest.approx(19.7, rel=1e-12)
    p = phi_cdf(-1.0)  # 0.1586553
    assert r.fraction_not_accelerating == pytest.approx(p, abs=4.0 * math.sqrt(p * (1.0 - p) / n))
    assert math.isfinite(r.failure_time_median)
    assert r.failure_time_lower <= r.failure_time_median <= r.failure_time_upper


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle(
    "analytical",
    "a clearly decelerating series: every draw has b1 >= 0, the fraction is 1 and no finite failure time exists",
)
def test_decelerating_series_has_no_failure_time() -> None:
    y = 1000.0 + 10.0 * T5
    r = bayes(T5, 1.0 / y, noise_sd=1.0, n_draws=1000)
    assert r.fraction_not_accelerating == 1.0
    assert r.posterior_mean[1] == pytest.approx(10.0, rel=1e-12)
    for value in (r.failure_time_median, r.failure_time_lower, r.failure_time_upper):
        assert not math.isfinite(value)


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle("analytical", "an accelerating, well-determined series: the fraction is exactly 0")
def test_accelerating_series_has_no_non_accelerating_draw() -> None:
    n = 1000
    r = bayes(T5, V5, noise_sd=20.0, n_draws=n)
    assert r.fraction_not_accelerating == 0.0  # P(b1 >= 0) = Phi(-31)
    cov = np.array([[240.0, -8.0], [-8.0, 0.4]])
    assert cdf_tf(r.failure_time_median, np.array([1008.0, -19.7]), cov) == pytest.approx(
        0.5, abs=4.0 * math.sqrt(0.25 / n)
    )


@pytest.mark.req("FR-003-17")
@pytest.mark.req("P-000-04")
@pytest.mark.oracle(
    "analytical", "determinism: same integer seed or equal Generator, bitwise-identical result; other seeds differ"
)
def test_seeded_reproducibility() -> None:
    kw = {"noise_sd": 300.0, "n_draws": 500}
    a = bayes(T5, V5, 5, **kw)
    b = bayes(T5, V5, 5, **kw)
    c = bayes(T5, V5, np.random.default_rng(5), **kw)
    d = bayes(T5, V5, 6, **kw)
    for other in (b, c):
        assert other.failure_time_median == a.failure_time_median
        assert other.failure_time_lower == a.failure_time_lower
        assert other.failure_time_upper == a.failure_time_upper
        assert other.fraction_not_accelerating == a.fraction_not_accelerating
    assert (d.failure_time_median, d.failure_time_lower) != (a.failure_time_median, a.failure_time_lower)
    assert a.posterior_mean.tobytes() == d.posterior_mean.tobytes(), "the posterior does not depend on the seed"


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle("analytical", "a Generator advances: two calls on one Generator draw different samples")
def test_generator_advances() -> None:
    g = np.random.default_rng(1)
    a = bayes(T5, V5, g, noise_sd=300.0, n_draws=500)
    b = bayes(T5, V5, g, noise_sd=300.0, n_draws=500)
    assert a.failure_time_median != b.failure_time_median


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle("analytical", "inputs are never modified; float32 / int times give the float64 result")
def test_purity_and_dtypes() -> None:
    t, v = T5.copy(), V5.copy()
    ref = bayes(t, v, 4, noise_sd=20.0, n_draws=200)
    assert np.array_equal(t, T5)
    assert np.array_equal(v, V5)
    for dtype in (np.float32, np.int64):
        out = bayes(T5.astype(dtype), V5, 4, noise_sd=20.0, n_draws=200)
        assert out.posterior_mean.tobytes() == ref.posterior_mean.tobytes()
        assert out.failure_time_median == ref.failure_time_median


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle(
    "analytical",
    "the prior arguments accept lists and arrays alike; prior_mean without prior_cov leaves the prior flat",
)
def test_prior_argument_forms() -> None:
    kw = {"noise_sd": 20.0, "n_draws": 200}
    a = bayes(T5, V5, 1, prior_mean=[1100.0, -25.0], prior_cov=[[4e4, 0.0], [0.0, 25.0]], **kw)
    b = bayes(T5, V5, 1, prior_mean=np.array([1100.0, -25.0]), prior_cov=np.array([[4e4, 0.0], [0.0, 25.0]]), **kw)
    assert np.array_equal(a.posterior_mean, b.posterior_mean)
    flat = bayes(T5, V5, 1, **kw)
    only_mean = bayes(T5, V5, 1, prior_mean=[1100.0, -25.0], **kw)
    assert np.array_equal(only_mean.posterior_mean, flat.posterior_mean)


@pytest.mark.slow
@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "the limits of n_draws (100 and 10**6) are accepted")
@pytest.mark.parametrize("n", [100, 10**6])
def test_n_draws_limits_are_accepted(n: int) -> None:
    r = bayes(T5, V5, 1, noise_sd=20.0, n_draws=n)
    assert r.fraction_not_accelerating == 0.0


# ------------------------------------------------------------------ FR-003-21: tripwire


@pytest.mark.req("FR-003-21")
@pytest.mark.oracle(
    "analytical", "spec 003 7.3: velocity above 1e-2 m/s warns (tripwire_slope_velocity_max) and still returns"
)
def test_velocity_tripwire() -> None:
    v = V5.copy()
    v[0] = 0.02
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        r = bayes(T5, v, noise_sd=20.0, n_draws=200)
    hits = [w for w in rec if issubclass(w.category, minephys.ValidityWarning)]
    assert hits
    assert hits[0].message.row == "tripwire_slope_velocity_max"
    assert hits[0].message.argument == "velocity"
    assert r.posterior_cov.shape == (2, 2)
    with warnings.catch_warnings(record=True) as rec2:
        warnings.simplefilter("always")
        bayes(np.arange(6.0), np.linspace(0.005, 0.01, 6), noise_sd=20.0, n_draws=200)
    assert [w for w in rec2 if issubclass(w.category, minephys.ValidityWarning)] == []


# ------------------------------------------------------------------ FR-003-23 and the domain: hostile inputs


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle(
    "analytical", "prior_cov must be a symmetric positive-definite 2 x 2 matrix: InputError naming prior_cov"
)
@pytest.mark.parametrize(
    "cov",
    [
        [[1.0, 0.5], [0.4, 1.0]],  # not symmetric
        [[1.0, 2.0], [2.0, 1.0]],  # indefinite
        [[1.0, 0.0], [0.0, 0.0]],  # singular
        [[0.0, 0.0], [0.0, 0.0]],
        [[-1.0, 0.0], [0.0, -1.0]],  # negative definite
        [[1.0, 0.0], [0.0, -1e-9]],
        [[math.nan, 0.0], [0.0, 1.0]],
        [[math.inf, 0.0], [0.0, 1.0]],
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],  # 3 x 3
        [1.0, 0.0, 0.0, 1.0],  # flat
        [[1.0, 0.0]],  # 1 x 2
        [],
    ],
)
def test_bad_prior_cov(cov) -> None:
    with pytest.raises(minephys.InputError) as ei:
        bayes(T5, V5, noise_sd=20.0, prior_mean=[1000.0, -20.0], prior_cov=cov)
    assert ei.value.argument == "prior_cov"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "a symmetric positive-definite prior_cov of any scale is accepted")
@pytest.mark.parametrize("cov", [[[1.0, 0.0], [0.0, 1.0]], [[1e8, 1e3], [1e3, 1e0]], [[2.0, -1.5], [-1.5, 2.0]]])
def test_good_prior_cov(cov) -> None:
    r = bayes(T5, V5, noise_sd=20.0, prior_mean=[1000.0, -20.0], prior_cov=cov, n_draws=100)
    assert r.posterior_cov.shape == (2, 2)
    assert float(np.linalg.eigvalsh(r.posterior_cov)[0]) > 0.0


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "prior_mean must have length 2 and finite entries: InputError naming prior_mean")
@pytest.mark.parametrize(
    "mean", [[1000.0], [1000.0, -20.0, 1.0], [], [[1000.0, -20.0]], [math.nan, -20.0], [1000.0, math.inf], 5.0]
)
def test_bad_prior_mean(mean) -> None:
    with pytest.raises(minephys.InputError) as ei:
        bayes(T5, V5, noise_sd=20.0, prior_mean=mean, prior_cov=[[1e4, 0.0], [0.0, 1.0]])
    assert ei.value.argument == "prior_mean"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "wrong types for the prior arguments are InputTypeError")
@pytest.mark.parametrize("arg", ["prior_mean", "prior_cov"])
@pytest.mark.parametrize("bad", ["ab", b"12", 1 + 1j, object()])
def test_bad_prior_types(arg: str, bad) -> None:
    kw = {"prior_mean": [1000.0, -20.0], "prior_cov": [[1e4, 0.0], [0.0, 1.0]]}
    kw[arg] = bad
    with pytest.raises(minephys.InputTypeError) as ei:
        bayes(T5, V5, noise_sd=20.0, **kw)
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "t must be strictly increasing: InputError naming t")
@pytest.mark.parametrize(
    "t", [[0.0, 1.0, 1.0, 2.0], [0.0, 2.0, 1.0, 3.0], [3.0, 2.0, 1.0, 0.0], [0.0, 0.0, 1.0, 2.0], [0.0, 1.0, 2.0, 2.0]]
)
def test_t_must_increase(t: list[float]) -> None:
    with pytest.raises(minephys.InputError) as ei:
        bayes(np.array(t), np.full(4, 1e-3), noise_sd=20.0)
    assert ei.value.argument == "t"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "fewer than 3 samples used: InputError (series of 0, 1, 2 samples; window below 3)")
def test_too_few_samples() -> None:
    for n in (0, 1, 2):
        with pytest.raises(minephys.InputError) as ei:
            bayes(np.arange(float(n)), np.full(n, 1e-3), noise_sd=20.0)
        assert ei.value.argument in {"t", "velocity"}
    for window in (0, 1, 2, -3, 2.5):
        with pytest.raises(minephys.InputError) as ei2:
            bayes(T5, V5, noise_sd=20.0, window=window)
        assert ei2.value.argument == "window"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "n_draws outside 100..10**6 (or not an integer) is an InputError naming n_draws")
@pytest.mark.parametrize("bad", [0, 1, 99, 10**6 + 1, 2**40, -1, 100.5, math.nan, math.inf])
def test_bad_n_draws(bad) -> None:
    with pytest.raises(minephys.InputError) as ei:
        bayes(T5, V5, noise_sd=20.0, n_draws=bad)
    assert ei.value.argument == "n_draws"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "n_draws, window of the wrong type")
@pytest.mark.parametrize("arg", ["n_draws", "window"])
@pytest.mark.parametrize("bad", ["500", b"5", 1 + 1j, True, object()])
def test_bad_count_types(arg: str, bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        bayes(T5, V5, noise_sd=20.0, **{arg: bad})
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "credible in (0, 1) and noise_sd >= 0 (finite): InputError naming the argument")
@pytest.mark.parametrize(
    ("arg", "bad"),
    [
        ("credible", 0.0),
        ("credible", 1.0),
        ("credible", -0.1),
        ("credible", 1.5),
        ("credible", math.nan),
        ("credible", math.inf),
        ("noise_sd", -1.0),
        ("noise_sd", -1e-12),
        ("noise_sd", math.nan),
        ("noise_sd", math.inf),
        ("noise_sd", -math.inf),
    ],
)
def test_scalar_domains(arg: str, bad: float) -> None:
    kw = {"noise_sd": 20.0, "credible": 0.9, arg: bad}
    with pytest.raises(minephys.InputError) as ei:
        bayes(T5, V5, **kw)
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "wrong types for credible and noise_sd")
@pytest.mark.parametrize("arg", ["credible", "noise_sd"])
@pytest.mark.parametrize("bad", ["0.9", b"1", 1 + 1j, True, object()])
def test_scalar_types(arg: str, bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        bayes(T5, V5, **{"noise_sd": 20.0, "credible": 0.9, arg: bad})
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle(
    "analytical", "velocity > 0 and finite; t finite: InputError naming the argument; wrong dtypes InputTypeError"
)
def test_series_hostile() -> None:
    for bad in (0.0, -1e-3, math.nan, math.inf, -math.inf):
        v = V5.copy()
        v[2] = bad
        with pytest.raises(minephys.InputError) as ei:
            bayes(T5, v, noise_sd=20.0)
        assert ei.value.argument == "velocity"
    for bad in (math.nan, math.inf, -math.inf):
        t = T5.copy()
        t[1] = bad
        with pytest.raises(minephys.InputError) as ei2:
            bayes(t, V5, noise_sd=20.0)
        assert ei2.value.argument == "t"
    for arg in ("t", "velocity"):
        for bad in ("1.0", b"1", None, 1 + 1j, object(), np.datetime64("2026-01-01")):
            with pytest.raises(minephys.InputTypeError) as ei3:
                G.bayesian_ttf(**{"t": T5, "velocity": V5, "rng": 1, "noise_sd": 20.0, arg: bad})
            assert ei3.value.argument == arg
    for kw in ({"t": np.zeros((2, 3))}, {"velocity": np.full((5, 1), 1e-3)}, {"velocity": np.full(4, 1e-3)}):
        with pytest.raises(minephys.InputError) as ei4:
            G.bayesian_ttf(**{"t": T5, "velocity": V5, "rng": 1, "noise_sd": 20.0, **kw})
        assert ei4.value.argument in {"t", "velocity"}


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle(
    "analytical", "rng is required (no default) and must be a Generator or an integer seed in 0..2**32-1"
)
def test_rng_contract() -> None:
    with pytest.raises(TypeError):
        G.bayesian_ttf(T5, V5, noise_sd=20.0)  # type: ignore[call-arg]
    for bad in (None, 1.5, "7", b"7", True, np.array([1, 2]), np.random.RandomState(1), object()):
        with pytest.raises(minephys.InputTypeError) as ei:
            bayes(T5, V5, bad, noise_sd=20.0)
        assert ei.value.argument == "rng"
    for bad in (-1, 2**32, 2**64):
        with pytest.raises(minephys.InputError) as ei2:
            bayes(T5, V5, bad, noise_sd=20.0)
        assert ei2.value.argument == "rng"

# ruff: noqa: E501
"""T-003-032 (FR-003-17, P-003-10): properties of the Bayesian time of failure.

Expected API: see tests/unit/test_t_003_032_bayesian_ttf.py (`bayesian_ttf` and its result attributes
`posterior_mean`, `posterior_cov`, `failure_time_median`, `failure_time_lower`, `failure_time_upper`,
`fraction_not_accelerating`).

P-003-10: with a flat prior and known sigma the posterior mean equals the ordinary least-squares fit and the
covariance equals sigma^2 (X'X)^-1 (closed forms with the centred sums written in this file: S11 = sigma^2 /
Sxx, S00 = sigma^2 (1/n + tbar^2 / Sxx), S01 = -sigma^2 tbar / Sxx); with known sigma, adding a sample never
increases det(Sigma_N); when P(b1 >= 0) < 1e-9 the empirical CDF of the t_f draws at the analytical quantiles
is within four binomial standard errors of the nominal level (the Fieller distribution P(t_f <= tau) =
Phi(-(mu0 + tau mu1) / sqrt(S00 + 2 tau S01 + tau^2 S11))), checked here at the returned median and interval
ends. Further relations: the estimated sigma is sqrt(RSS / (n - 2)); the sequential identity (posterior of two
batches with the first posterior as prior equals the batch posterior); an informative prior matches the
precision-form update written here; the draws change with the seed but the posterior does not.

Generators: t_f in 1e4..1e8 s (integer), 3..60 distinct integer times in [0, 0.95 t_f] spanning at least 0.1
t_f, 1 / v = A (t_f - t) (1 + noise up to 3 %), A in 1e-4..1e2, known sigma between 0.1 % and 3 % of the
largest 1 / v. Tolerances: 1e-8 relative on the algebraic identities (the centred problem is well
conditioned), TC-4 on the draws.

Oracle: analytical (conjugate Gaussian algebra, Fieller ratio distribution), NumPy `polyfit` as the reference fit.
"""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

CFG = settings(deadline=None)


@st.composite
def series(draw, min_n: int = 3, max_n: int = 60):
    tf = float(draw(st.integers(10_000, 10**8)))
    n = draw(st.integers(min_n, max_n))
    rng = np.random.default_rng(draw(st.integers(0, 2**32 - 1)))
    t = np.sort(rng.choice(int(0.95 * tf), size=n, replace=False)).astype(np.float64)
    assume(t[-1] - t[0] >= 0.1 * tf)
    a = draw(st.floats(1e-4, 1e2))
    y = a * (tf - t) * (1.0 + 0.03 * rng.uniform(-1.0, 1.0, n))
    sigma = draw(st.floats(0.001, 0.03)) * float(np.max(y))
    return tf, t, y, sigma


def phi_cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def cdf_tf(tau: float, mu, cov) -> float:
    s = math.sqrt(cov[0][0] + 2.0 * tau * cov[0][1] + tau * tau * cov[1][1])
    return phi_cdf(-(mu[0] + tau * mu[1]) / s)


def flat_closed_form(t, y, sigma):
    n = len(t)
    tb = float(np.mean(t))
    sxx = float(np.sum((t - tb) ** 2))
    cov = sigma**2 * np.array([[1.0 / n + tb * tb / sxx, -tb / sxx], [-tb / sxx, 1.0 / sxx]])
    slope = float(np.sum((t - tb) * (y - np.mean(y))) / sxx)
    return np.array([float(np.mean(y)) - slope * tb, slope]), cov


def run(t, y, rng=1, **kw):
    return G.bayesian_ttf(t, 1.0 / y, rng, **kw)


@pytest.mark.req("FR-003-17")
@pytest.mark.req("P-003-10")
@pytest.mark.oracle(
    "analytical", "flat prior, known sigma: the posterior mean is the least-squares fit, cov = sigma^2 (X'X)^-1"
)
@CFG
@given(s=series())
def test_flat_prior_is_least_squares(s: tuple) -> None:
    _, t, y, sigma = s
    r = run(t, y, noise_sd=sigma, n_draws=100)
    mu, cov = flat_closed_form(t, y, sigma)
    slope, intercept = np.polyfit(t, y, 1)
    np.testing.assert_allclose(r.posterior_mean, mu, rtol=1e-8)
    np.testing.assert_allclose(r.posterior_mean, [intercept, slope], rtol=1e-7)
    np.testing.assert_allclose(r.posterior_cov, cov, rtol=1e-8, atol=1e-14 * float(np.max(np.abs(cov))))
    assert r.posterior_cov[0, 1] == pytest.approx(r.posterior_cov[1, 0], rel=1e-10)


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle(
    "analytical", "sigma from the residuals: s^2 = RSS / (n - 2) multiplies the unit covariance (X'X)^-1"
)
@CFG
@given(s=series())
def test_estimated_sigma(s: tuple) -> None:
    _, t, y, _ = s
    mu, unit = flat_closed_form(t, y, 1.0)
    rss = float(np.sum((y - (mu[0] + mu[1] * t)) ** 2))
    s2 = rss / (len(t) - 2)
    assume(rss > 1e-9 * float(np.sum(y * y)))  # a non-degenerate residual
    r = run(t, y, n_draws=100)
    np.testing.assert_allclose(r.posterior_cov, s2 * unit, rtol=1e-6, atol=1e-12 * s2 * float(np.max(np.abs(unit))))


@pytest.mark.req("P-003-10")
@pytest.mark.oracle("analytical", "with known sigma, every added sample lowers (never raises) det(Sigma_N)")
@CFG
@given(s=series(min_n=5, max_n=30))
def test_determinant_is_non_increasing(s: tuple) -> None:
    _, t, y, sigma = s
    dets = [
        float(np.linalg.det(run(t[:n], y[:n], noise_sd=sigma, n_draws=100).posterior_cov)) for n in range(3, len(t) + 1)
    ]
    for a, b in pairwise(dets):
        assert b <= a * (1.0 + 1e-8)


@pytest.mark.req("FR-003-17")
@pytest.mark.req("P-003-10")
@pytest.mark.oracle(
    "analytical",
    "sequential identity: posterior(2nd batch | posterior(1st batch)) = posterior(both batches), known sigma",
)
@CFG
@given(s=series(min_n=6, max_n=40), frac=st.floats(0.0, 1.0))
def test_sequential_update(s: tuple, frac: float) -> None:
    _, t, y, sigma = s
    n = len(t)
    cut = 3 + int(frac * (n - 6))  # first batch has 3.. n-3 samples, second batch at least 3
    batch = run(t, y, noise_sd=sigma, n_draws=100)
    first = run(t[:cut], y[:cut], noise_sd=sigma, n_draws=100)
    sym = 0.5 * (first.posterior_cov + first.posterior_cov.T)
    second = run(t[cut:], y[cut:], noise_sd=sigma, n_draws=100, prior_mean=first.posterior_mean, prior_cov=sym)
    np.testing.assert_allclose(second.posterior_mean, batch.posterior_mean, rtol=1e-6)
    np.testing.assert_allclose(
        second.posterior_cov, batch.posterior_cov, rtol=1e-6, atol=1e-12 * float(np.max(np.abs(batch.posterior_cov)))
    )


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle(
    "analytical", "informative prior: Sigma_N = (Sigma0^-1 + X'X / s^2)^-1, mu_N = Sigma_N (Sigma0^-1 mu0 + X'y / s^2)"
)
@CFG
@given(s=series(max_n=30), scale=st.floats(0.1, 10.0), rho=st.floats(-0.9, 0.9))
def test_informative_prior(s: tuple, scale: float, rho: float) -> None:
    _, t, y, sigma = s
    mu, flat_cov = flat_closed_form(t, y, sigma)
    prior_mean = mu * np.array([1.2, 0.7])
    sd = np.sqrt(np.diag(flat_cov)) * scale
    prior_cov = np.array([[sd[0] ** 2, rho * sd[0] * sd[1]], [rho * sd[0] * sd[1], sd[1] ** 2]])
    r = run(t, y, noise_sd=sigma, n_draws=100, prior_mean=prior_mean, prior_cov=prior_cov)
    tb = float(np.mean(t))
    jac = np.array([[1.0, -tb], [0.0, 1.0]])  # centre the time axis for the reference: b = J bc
    xc = np.c_[np.ones(len(t)), t - tb]
    p0c = jac.T @ np.linalg.inv(prior_cov) @ jac
    prec = p0c + xc.T @ xc / sigma**2
    covc = np.linalg.inv(prec)
    muc = covc @ (jac.T @ np.linalg.inv(prior_cov) @ prior_mean + xc.T @ y / sigma**2)
    ref_cov = jac @ covc @ jac.T
    ref_mean = jac @ muc
    np.testing.assert_allclose(r.posterior_mean, ref_mean, rtol=1e-6, atol=1e-9 * float(np.max(np.abs(ref_mean))))
    np.testing.assert_allclose(r.posterior_cov, ref_cov, rtol=1e-6, atol=1e-10 * float(np.max(np.abs(ref_cov))))
    assert float(np.linalg.eigvalsh(r.posterior_cov)[0]) > 0.0


@pytest.mark.req("P-003-10")
@pytest.mark.oracle(
    "analytical",
    "negligible P(b1 >= 0): the Fieller CDF at the returned median and credible-interval ends hits the nominal levels (TC-4)",
)
@settings(deadline=None, max_examples=40)
@given(s=series(), ratio=st.floats(6.6, 15.0), credible=st.floats(0.5, 0.98), seed=st.integers(0, 2**32 - 1))
def test_the_draws_follow_the_ratio_distribution(s: tuple, ratio: float, credible: float, seed: int) -> None:
    _, t, y, _ = s
    n = 20_000
    mu0, unit = flat_closed_form(t, y, 1.0)
    assume(mu0[1] < 0.0)
    sigma = abs(mu0[1]) / (ratio * math.sqrt(unit[1][1]))  # mu1 / sd(b1) = -ratio: P(b1 >= 0) < 1e-10
    mu, cov = flat_closed_form(t, y, sigma)
    r = run(t, y, seed, noise_sd=sigma, n_draws=n, credible=credible)
    assert r.fraction_not_accelerating == 0.0
    for value, level in (
        (r.failure_time_lower, (1.0 - credible) / 2.0),
        (r.failure_time_median, 0.5),
        (r.failure_time_upper, (1.0 + credible) / 2.0),
    ):
        assert cdf_tf(value, mu, cov) == pytest.approx(level, abs=4.0 * math.sqrt(level * (1.0 - level) / n))
    assert r.failure_time_lower < r.failure_time_median < r.failure_time_upper


@pytest.mark.req("P-003-10")
@pytest.mark.oracle("analytical", "the fraction of draws with b1 >= 0 is Phi(mu1 / sqrt(S11)) (TC-4)")
@settings(deadline=None, max_examples=40)
@given(s=series(), target=st.floats(0.2, 3.0), seed=st.integers(0, 2**32 - 1))
def test_fraction_not_accelerating(s: tuple, target: float, seed: int) -> None:
    _, t, y, _ = s
    n = 20_000
    mu, unit = flat_closed_form(t, y, 1.0)
    assume(mu[1] < 0.0)
    sigma = abs(mu[1]) / (target * math.sqrt(unit[1][1]))  # mu1 / sd(b1) = -target
    p = phi_cdf(-target)  # P(b1 >= 0) = Phi(mu1 / sd(b1))
    r = run(t, y, seed, noise_sd=sigma, n_draws=n)
    assert r.fraction_not_accelerating == pytest.approx(p, abs=4.0 * math.sqrt(p * (1.0 - p) / n))


@pytest.mark.req("FR-003-17")
@pytest.mark.oracle(
    "analytical",
    "the posterior is a function of the data: the seed changes the draws, never the posterior mean or covariance",
)
@CFG
@given(s=series(max_n=20), seeds=st.tuples(st.integers(0, 2**32 - 1), st.integers(0, 2**32 - 1)))
def test_posterior_does_not_depend_on_the_seed(s: tuple, seeds: tuple) -> None:
    _, t, y, sigma = s
    a = run(t, y, seeds[0], noise_sd=sigma, n_draws=100)
    b = run(t, y, seeds[1], noise_sd=sigma, n_draws=100)
    assert a.posterior_mean.tobytes() == b.posterior_mean.tobytes()
    assert a.posterior_cov.tobytes() == b.posterior_cov.tobytes()
    c = run(t, y, seeds[0], noise_sd=sigma, n_draws=100)
    assert (c.failure_time_median, c.failure_time_lower, c.failure_time_upper) == (
        a.failure_time_median,
        a.failure_time_lower,
        a.failure_time_upper,
    )

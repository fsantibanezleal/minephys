"""T-003-024 (FR-003-12, FR-003-13, FR-003-24, P-003-08): Monte-Carlo factor of safety and probability of failure.

Expected API, module `minephys.geotech`:

    monte_carlo_fos(width, weight, base_angle, pore_pressure, cohesion_mean, cohesion_sd, friction_mean,
                    friction_sd, n_samples, rng, method="bishop") -> float64 array of shape (n_samples,)
        cohesion ~ N(cohesion_mean, cohesion_sd) truncated to c' >= 0 and friction angle ~ N(friction_mean,
        friction_sd) truncated to 0 <= phi' < pi/2, both drawn independently from `rng` by RESAMPLING the rejected
        draws (never by clipping); each draw is evaluated on the fixed slices with Bishop's simplified method
        ("bishop") or Spencer's method ("spencer", the factor of safety only). `rng` is a Generator or an integer
        seed (no default); `n_samples` is an integer in 1..10**6; `method` is exactly "bishop" or "spencer".
    probability_of_failure(fos_samples, threshold=1) -> (pof, standard_error, n)
        pof = fraction of samples strictly below `threshold`; standard_error = sqrt(pof (1 - pof) / n); n = sample
        count (an integer).
    required_samples(pof, relative_error) -> integer count ceil((1 - p) / (p eps^2)) (numpy int64; an int64 array for
        array operands), 0 < p < 1, eps > 0.

Oracles: spec 003 section 7.4 hand calculations (phi' = 0 slices, c' ~ N(10 kPa, 2 kPa): mu_F = 1.4623899,
sigma_F = 0.2924780, PoF = Phi(-1.58094) = 0.056946; required_samples(0.05, 0.1) = 1,900), the closed-form
first two moments of a truncated normal distribution (Johnson, Kotz and Balakrishnan, Continuous Univariate
Distributions vol. 1, ch. 13.10.1), the infinite-slope identity F = tan(phi') / tan(beta) for c' = 0 (exact
for Bishop), binomial standard errors (TC-4: four standard errors of the Monte-Carlo estimate; seeds are fixed
so the runs are reproducible) and hand-counted fractions.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

import minephys
from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

SQRT2 = math.sqrt(2.0)


def pdf(x: float) -> float:
    return 0.0 if math.isinf(x) else math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def cdf(x: float) -> float:
    return 0.5 * math.erfc(-x / SQRT2)


def tail(x: float) -> float:
    return 0.0 if math.isinf(x) else x * pdf(x)


def truncated_moments(mu: float, sd: float, lo: float, hi: float) -> tuple[float, float]:
    """Mean and standard deviation of N(mu, sd) truncated to [lo, hi] (closed forms)."""
    a, b = (lo - mu) / sd, (hi - mu) / sd
    z = cdf(b) - cdf(a)
    shift = (pdf(a) - pdf(b)) / z
    mean = mu + sd * shift
    var = sd * sd * (1.0 + (tail(a) - tail(b)) / z - shift * shift)
    return mean, math.sqrt(var)


def phi0_slices() -> dict:
    """Spec 003 section 7.4: b = 2 m, W = (40, 80, 50) kN/m, alpha = (-10, 15, 40) deg; with phi' = 0, F = k c'."""
    return {
        "width": np.full(3, 2.0),
        "weight": np.array([40.0, 80.0, 50.0]) * 1e3,
        "base_angle": np.radians([-10.0, 15.0, 40.0]),
        "pore_pressure": np.zeros(3),
    }


def k_phi0() -> float:
    """F per pascal of cohesion at phi' = 0: sum(l) / sum(W sin alpha) with l = b / cos(alpha) (hand formula)."""
    s = phi0_slices()
    return float(np.sum(s["width"] / np.cos(s["base_angle"])) / np.sum(s["weight"] * np.sin(s["base_angle"])))


def three_slices() -> dict:
    return {
        "width": np.full(3, 2.0),
        "weight": np.array([60.0, 120.0, 80.0]) * 1e3,
        "base_angle": np.radians([5.0, 25.0, 50.0]),
        "pore_pressure": np.zeros(3),
    }


def infinite_slope_slices(beta_deg: float = 20.0) -> dict:
    return {
        "width": np.array([2.0, 3.0, 2.5, 1.5]),
        "weight": np.array([50.0, 80.0, 70.0, 30.0]) * 1e3,
        "base_angle": np.full(4, math.radians(beta_deg)),
        "pore_pressure": np.zeros(4),
    }


def mc(slices: dict, c_mean: float, c_sd: float, f_mean: float, f_sd: float, n: int, rng, method: str = "bishop"):
    return G.monte_carlo_fos(
        slices["width"],
        slices["weight"],
        slices["base_angle"],
        slices["pore_pressure"],
        c_mean,
        c_sd,
        f_mean,
        f_sd,
        n,
        rng,
        method=method,
    )


# ------------------------------------------------------------------ FR-003-12: sampling and evaluation


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle(
    "hand-calculation", "spec 003 7.4: the phi' = 0 factor of safety is F = sum c' l / sum W sin(alpha)"
)
def test_the_phi_zero_constant_matches_the_spec() -> None:
    assert k_phi0() * 10e3 == pytest.approx(1.4623899, abs=5e-8)  # the hand formula itself, TC-2


@pytest.mark.req("FR-003-12")
@pytest.mark.req("P-003-08")
@pytest.mark.oracle("analytical", "zero standard deviations: every sample is the deterministic factor of safety")
@pytest.mark.parametrize(
    ("method", "expected"), [("bishop", 1.2842941), ("spencer", 1.2775177)]
)  # spec 003 7.4 three-slice hand calculations
def test_zero_spread_is_the_deterministic_factor(method: str, expected: float) -> None:
    out = mc(three_slices(), 5000.0, 0.0, math.radians(25.0), 0.0, 25, 1, method)
    assert out.shape == (25,)
    assert out.dtype == np.float64
    assert np.all(out == out[0]), "no spread in, no spread out"
    assert float(out[0]) == pytest.approx(expected, abs=5e-8)


@pytest.mark.req("FR-003-12")
@pytest.mark.req("P-003-08")
@pytest.mark.oracle(
    "analytical",
    "phi' = 0: F = k c' is linear, so F ~ N(k mu, k sigma): mean 1.4623899, sd 0.2924780 (spec 003 7.4); TC-4",
)
def test_linear_case_moments() -> None:
    n = 20_000
    out = mc(phi0_slices(), 10e3, 2e3, 0.0, 0.0, n, 20261011)
    mu_f, sd_f = k_phi0() * 10e3, k_phi0() * 2e3
    assert mu_f == pytest.approx(1.4623899, abs=5e-8)
    assert sd_f == pytest.approx(0.2924780, abs=5e-8)
    assert float(np.mean(out)) == pytest.approx(mu_f, abs=4.0 * sd_f / math.sqrt(n))
    assert float(np.std(out, ddof=1)) == pytest.approx(sd_f, rel=4.0 / math.sqrt(2.0 * n))
    assert float(np.min(out)) >= 0.0


@pytest.mark.req("FR-003-12")
@pytest.mark.req("FR-003-13")
@pytest.mark.req("P-003-08")
@pytest.mark.oracle(
    "analytical",
    "phi' = 0: PoF = Phi((1 - mu_F) / sigma_F) = Phi(-1.58094) = 0.056946 (spec 003 7.4); within 4 SE = 0.0066",
)
def test_probability_of_failure_matches_the_normal_cdf() -> None:
    n = 20_000
    out = mc(phi0_slices(), 10e3, 2e3, 0.0, 0.0, n, 20261012)
    mu_f, sd_f = k_phi0() * 10e3, k_phi0() * 2e3
    exact = cdf((1.0 - mu_f) / sd_f)
    assert exact == pytest.approx(0.056946, abs=5e-7)
    pof, se, count = G.probability_of_failure(out)
    assert count == n
    assert pof == pytest.approx(exact, abs=4.0 * math.sqrt(exact * (1.0 - exact) / n))
    assert se == pytest.approx(math.sqrt(pof * (1.0 - pof) / n), rel=1e-12)
    assert se == pytest.approx(0.0016, abs=3e-4)


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle(
    "analytical",
    "cohesion truncated at 0 by RESAMPLING: the sample mean of c' is the truncated-normal mean, not the clipped one",
)
@pytest.mark.parametrize(("mean", "sd"), [(2000.0, 5000.0), (0.0, 3000.0), (500.0, 1500.0)])
def test_cohesion_is_truncated_not_clipped(mean: float, sd: float) -> None:
    n = 20_000
    out = mc(phi0_slices(), mean, sd, 0.0, 0.0, n, 77)
    cohesion = out / k_phi0()
    mu_t, sd_t = truncated_moments(mean, sd, 0.0, math.inf)
    assert float(np.min(cohesion)) >= 0.0
    assert int(np.count_nonzero(out == 0.0)) == 0, "clipping would pile up an atom at c' = 0"
    assert float(np.mean(cohesion)) == pytest.approx(mu_t, abs=4.0 * sd_t / math.sqrt(n))
    assert float(np.std(cohesion, ddof=1)) == pytest.approx(sd_t, rel=0.06)
    clipped_mean = mean * cdf(mean / sd) + sd * pdf(mean / sd)  # E[max(X, 0)] of the untruncated normal
    assert abs(mu_t - clipped_mean) > 8.0 * sd_t / math.sqrt(n), "this case separates truncation from clipping"


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle(
    "analytical",
    "c' = 0, dry, equal base angles: F = tan(phi') / tan(beta) exactly, so phi' = atan(F tan beta) is the draw; "
    "its moments are those of N(1.2, 0.35) truncated to [0, pi/2)",
)
def test_friction_angle_is_truncated_on_both_sides() -> None:
    n = 20_000
    beta = 20.0
    out = mc(infinite_slope_slices(beta), 0.0, 0.0, 1.2, 0.35, n, 4242)
    assert np.all(np.isfinite(out))
    assert float(np.min(out)) >= 0.0
    phi = np.arctan(out * math.tan(math.radians(beta)))
    assert float(np.max(phi)) < math.pi / 2.0
    mu_t, sd_t = truncated_moments(1.2, 0.35, 0.0, math.pi / 2.0)
    assert float(np.mean(phi)) == pytest.approx(mu_t, abs=4.0 * sd_t / math.sqrt(n))
    assert float(np.std(phi, ddof=1)) == pytest.approx(sd_t, rel=0.06)
    untruncated = 1.2
    assert abs(mu_t - untruncated) > 8.0 * sd_t / math.sqrt(n), "the upper cut-off is far from negligible here"


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle(
    "analytical",
    "delta method: independent draws give var(F) = (dF/dc sd_c)^2 + (dF/dphi sd_phi)^2; equal contributions make "
    "perfectly correlated draws give twice that and anti-correlated draws none (TC-4)",
)
def test_the_two_draws_are_independent() -> None:
    n = 20_000
    sl = three_slices()
    c0, phi0 = 5000.0, math.radians(25.0)

    def bishop(c: float, phi: float) -> float:
        return float(G.bishop_simplified_fos(sl["width"], sl["weight"], sl["base_angle"], sl["pore_pressure"], c, phi))

    d_c = (bishop(c0 + 1.0, phi0) - bishop(c0 - 1.0, phi0)) / 2.0  # central differences of the deterministic factor
    d_phi = (bishop(c0, phi0 + 1e-5) - bishop(c0, phi0 - 1e-5)) / 2e-5
    sd_c = 150.0
    sd_phi = d_c * sd_c / d_phi  # both contributions to the variance are equal
    out = mc(sl, c0, sd_c, phi0, sd_phi, n, 5)
    predicted = (d_c * sd_c) ** 2 + (d_phi * sd_phi) ** 2
    assert float(np.var(out, ddof=1)) == pytest.approx(predicted, rel=0.08)
    assert float(np.mean(out)) == pytest.approx(bishop(c0, phi0), abs=4.0 * math.sqrt(predicted / n))


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle("analytical", "spencer on phi' = 0 is the moment-only value: it equals Bishop draw for draw")
def test_spencer_equals_bishop_when_friction_is_zero() -> None:
    b = mc(phi0_slices(), 10e3, 2e3, 0.0, 0.0, 120, 31)
    s = mc(phi0_slices(), 10e3, 2e3, 0.0, 0.0, 120, 31, "spencer")
    np.testing.assert_allclose(s, b, rtol=1e-8)
    assert float(np.mean(s)) == pytest.approx(k_phi0() * 10e3, abs=4.0 * k_phi0() * 2e3 / math.sqrt(120))


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle(
    "analytical", "the two methods give close factors on the same draws (spec 003 7.4: 1.2843 against 1.2775)"
)
def test_spencer_samples_stay_close_to_bishop() -> None:
    b = mc(three_slices(), 5000.0, 1000.0, math.radians(25.0), math.radians(2.0), 200, 8)
    s = mc(three_slices(), 5000.0, 1000.0, math.radians(25.0), math.radians(2.0), 200, 8, "spencer")
    assert s.shape == (200,)
    assert float(np.max(np.abs(s / b - 1.0))) < 0.03


@pytest.mark.req("FR-003-12")
@pytest.mark.req("P-003-08")
@pytest.mark.oracle("analytical", "determinism: the same seed (integer or Generator) gives bitwise-identical samples")
def test_seeded_reproducibility() -> None:
    args = (three_slices(), 5000.0, 1000.0, math.radians(25.0), math.radians(2.0), 500)
    a = mc(*args, 1234)
    b = mc(*args, 1234)
    c = mc(*args, np.random.default_rng(1234))
    d = mc(*args, 1235)
    assert a.tobytes() == b.tobytes() == c.tobytes()
    assert a.tobytes() != d.tobytes()


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle("analytical", "a Generator is consumed: a second call on the same Generator draws new samples")
def test_a_generator_advances_and_global_state_is_untouched() -> None:
    gen = np.random.default_rng(9)
    args = (three_slices(), 5000.0, 1000.0, math.radians(25.0), math.radians(2.0), 100)
    state = np.random.get_state()[1].copy()  # noqa: NPY002 - the legacy global state is exactly what must stay untouched
    first = mc(*args, gen)
    second = mc(*args, gen)
    assert first.tobytes() != second.tobytes()
    assert np.array_equal(np.random.get_state()[1], state), "the global NumPy random state must not be used"  # noqa: NPY002


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle("analytical", "inputs are never modified")
def test_inputs_are_not_modified() -> None:
    sl = three_slices()
    before = {k: v.copy() for k, v in sl.items()}
    mc(sl, 5000.0, 1000.0, math.radians(25.0), math.radians(2.0), 50, 3)
    for k, v in before.items():
        assert np.array_equal(sl[k], v), k


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle("analytical", "one sample is allowed; the output is always a 1-D float64 array")
def test_single_sample() -> None:
    out = mc(three_slices(), 5000.0, 0.0, math.radians(25.0), 0.0, 1, 0)
    assert out.shape == (1,)
    assert out.dtype == np.float64
    assert float(out[0]) == pytest.approx(1.2842941, abs=5e-8)


@pytest.mark.slow
@pytest.mark.req("FR-003-12")
@pytest.mark.oracle("analytical", "the upper limit of n_samples (spec 003 FR-003-23): 10**6 draws are accepted")
def test_one_million_samples_are_accepted() -> None:
    out = mc(three_slices(), 5000.0, 0.0, math.radians(25.0), 0.0, 10**6, 0)
    assert out.shape == (10**6,)
    assert float(out[-1]) == pytest.approx(1.2842941, abs=5e-8)


# ------------------------------------------------------------------ FR-003-13: probability of failure


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle(
    "hand-calculation", "5 samples, 2 strictly below 1 (1.0 itself is not below): pof 0.4, se sqrt(.24/5)"
)
def test_pof_hand_counted() -> None:
    samples = np.array([0.5, 0.9, 1.0, 1.1, 1.5])
    pof, se, n = G.probability_of_failure(samples)
    assert n == 5
    assert pof == pytest.approx(0.4, abs=1e-15)
    assert se == pytest.approx(math.sqrt(0.4 * 0.6 / 5.0), rel=1e-14)  # 0.2190890
    assert se == pytest.approx(0.2190890, abs=5e-8)
    assert type(pof) is np.float64
    assert type(se) is np.float64
    assert isinstance(n, int | np.integer)
    assert not isinstance(n, bool)


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle("hand-calculation", "the threshold is an argument: 1.05 gives 3 of 5, 0.4 gives 0, 9 gives 5")
@pytest.mark.parametrize(("threshold", "count"), [(1.05, 3), (1.0, 2), (0.4, 0), (0.5, 0), (9.0, 5)])
def test_pof_threshold(threshold: float, count: int) -> None:
    pof, se, n = G.probability_of_failure(np.array([0.5, 0.9, 1.0, 1.1, 1.5]), threshold)
    assert n == 5
    assert pof == pytest.approx(count / 5.0, abs=1e-15)
    assert se == pytest.approx(math.sqrt(pof * (1.0 - pof) / 5.0), rel=1e-14, abs=1e-15)


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle("analytical", "all samples failed or none failed: the standard error is exactly zero")
def test_pof_degenerate() -> None:
    assert G.probability_of_failure(np.array([0.1, 0.2]))[:2] == (1.0, 0.0)
    assert G.probability_of_failure(np.array([2.0, 3.0, 4.0]))[:2] == (0.0, 0.0)
    pof, se, n = G.probability_of_failure(np.array([0.3]))
    assert (pof, se, n) == (1.0, 0.0, 1)


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle("analytical", "a list of floats is accepted like an array")
def test_pof_accepts_lists() -> None:
    assert G.probability_of_failure([0.5, 1.5, 2.0, 0.7])[0] == pytest.approx(0.5, abs=1e-15)


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle("hand-calculation", "spec 003 7.4: required_samples(0.05, 0.1) = 1,900")
def test_required_samples_worked_value() -> None:
    out = G.required_samples(0.05, 0.1)
    assert out == 1900
    assert type(out) is np.int64


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle(
    "hand-calculation", "ceil((1 - p) / (p eps^2)) on cases that are not integers: 233.33, 544.44, 11.11"
)
@pytest.mark.parametrize(("p", "eps", "expected"), [(0.3, 0.1, 234), (0.02, 0.3, 545), (0.5, 0.3, 12)])
def test_required_samples_rounds_up(p: float, eps: float, expected: int) -> None:
    assert int(G.required_samples(p, eps)) == expected


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle("analytical", "required_samples is elementwise over broadcast arrays and returns int64")
def test_required_samples_elementwise() -> None:
    out = G.required_samples(np.array([0.3, 0.02, 0.5]), np.array([0.1, 0.3, 0.3]))
    assert out.dtype == np.int64
    assert out.tolist() == [234, 545, 12]
    both = G.required_samples(np.array([[0.3], [0.6]]), np.array([0.1, 0.3]))  # 233.3, 25.93 / 66.67, 7.407
    assert both.shape == (2, 2)
    assert both.dtype == np.int64
    assert both.tolist() == [[234, 26], [67, 8]]


# ------------------------------------------------------------------ FR-003-12, FR-003-13, FR-003-24: hostile inputs


def mc_kwargs(**over):
    kw = {
        **three_slices(),
        "cohesion_mean": 5000.0,
        "cohesion_sd": 1000.0,
        "friction_mean": math.radians(25.0),
        "friction_sd": math.radians(2.0),
        "n_samples": 20,
        "rng": 1,
    }
    kw.update(over)
    return kw


@pytest.mark.req("FR-003-24")
@pytest.mark.oracle("analytical", "method is exactly 'bishop' or 'spencer'; the error lists both values")
@pytest.mark.parametrize("bad", ["Bishop", "SPENCER", "janbu", "", " bishop", "bishop ", "bïshop", None, 1, b"bishop"])
def test_bad_method(bad) -> None:
    with pytest.raises((minephys.InputError, minephys.InputTypeError)) as ei:
        G.monte_carlo_fos(**mc_kwargs(method=bad))
    assert ei.value.argument == "method"
    if isinstance(ei.value, minephys.InputError):
        assert "bishop" in str(ei.value)
        assert "spencer" in str(ei.value)


@pytest.mark.req("FR-003-24")
@pytest.mark.oracle("analytical", "a wrong string is a value error (InputError), not a type error")
def test_wrong_method_string_is_an_input_error() -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.monte_carlo_fos(**mc_kwargs(method="janbu"))
    assert ei.value.argument == "method"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "n_samples outside 1..10**6 is an InputError naming n_samples")
@pytest.mark.parametrize("bad", [0, -1, -(10**9), 10**6 + 1, 2**40, 2.5, math.nan, math.inf, -math.inf])
def test_bad_n_samples_value(bad) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.monte_carlo_fos(**mc_kwargs(n_samples=bad))
    assert ei.value.argument == "n_samples"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "n_samples must be a number: strings, None, complex and booleans are type errors")
@pytest.mark.parametrize("bad", ["20", b"20", None, 1 + 1j, True, object(), np.array([5, 6])])
def test_bad_n_samples_type(bad) -> None:
    with pytest.raises((minephys.InputTypeError, minephys.InputError)) as ei:
        G.monte_carlo_fos(**mc_kwargs(n_samples=bad))
    assert ei.value.argument == "n_samples"


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "spec 003 7.2: negative spreads, negative cohesion mean, friction outside [0, pi/2)")
@pytest.mark.parametrize(
    ("arg", "bad"),
    [
        ("cohesion_sd", -1.0),
        ("cohesion_sd", -1e-9),
        ("friction_sd", -0.01),
        ("cohesion_mean", -1.0),
        ("cohesion_mean", -1e-12),
        ("friction_mean", -0.01),
        ("friction_mean", math.pi / 2.0),
        ("friction_mean", 2.0),
        ("friction_mean", 90.0),
    ],
)
def test_domain_of_the_distribution_parameters(arg: str, bad: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.monte_carlo_fos(**mc_kwargs(**{arg: bad}))
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "NaN and infinity are never a mean or a spread")
@pytest.mark.parametrize("arg", ["cohesion_mean", "cohesion_sd", "friction_mean", "friction_sd"])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_distribution_parameters(arg: str, bad: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.monte_carlo_fos(**mc_kwargs(**{arg: bad}))
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "wrong types for the distribution parameters")
@pytest.mark.parametrize("arg", ["cohesion_mean", "cohesion_sd", "friction_mean", "friction_sd"])
@pytest.mark.parametrize("bad", ["1.0", b"1", None, 1 + 1j, True, object()])
def test_wrong_type_distribution_parameters(arg: str, bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        G.monte_carlo_fos(**mc_kwargs(**{arg: bad}))
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "rng has no default and must be a Generator or an integer seed in 0..2**32-1")
@pytest.mark.parametrize("bad", [None, 1.5, "7", b"7", True, np.array([1, 2]), np.random.RandomState(1), object()])
def test_bad_rng_type(bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        G.monte_carlo_fos(**mc_kwargs(rng=bad))
    assert ei.value.argument == "rng"


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "an integer seed outside 0..2**32-1 is an InputError naming rng")
@pytest.mark.parametrize("bad", [-1, 2**32, 2**64])
def test_bad_rng_value(bad: int) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.monte_carlo_fos(**mc_kwargs(rng=bad))
    assert ei.value.argument == "rng"


@pytest.mark.req("FR-003-12")
@pytest.mark.oracle("analytical", "rng is required: calling without it is a TypeError")
def test_rng_is_required() -> None:
    kw = mc_kwargs()
    del kw["rng"]
    with pytest.raises(TypeError):
        G.monte_carlo_fos(**kw)


@pytest.mark.req("FR-003-11")
@pytest.mark.oracle(
    "analytical", "the slice data are validated as for Bishop: a non-positive driving moment is an InputError"
)
def test_slice_errors_come_through() -> None:
    kw = mc_kwargs(base_angle=np.radians([-10.0, -20.0, -5.0]))
    with pytest.raises(minephys.InputError) as ei:
        G.monte_carlo_fos(**kw)
    assert ei.value.argument == "base_angle"
    with pytest.raises(minephys.InputError) as ei2:
        G.monte_carlo_fos(**mc_kwargs(width=np.full(4, 2.0)))
    assert ei2.value.argument in {"width", "weight", "base_angle", "pore_pressure"}
    with pytest.raises(minephys.InputError) as ei3:
        G.monte_carlo_fos(**mc_kwargs(weight=np.array([60e3, math.nan, 80e3])))
    assert ei3.value.argument == "weight"


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle("analytical", "empty, non-finite, ragged and wrongly typed sample sets")
def test_pof_hostile() -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.probability_of_failure(np.empty(0))
    assert ei.value.argument == "fos_samples"
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(minephys.InputError) as ei2:
            G.probability_of_failure(np.array([0.5, bad, 1.5]))
        assert ei2.value.argument == "fos_samples"
    with pytest.raises(minephys.InputError) as ei3:
        G.probability_of_failure(np.ones((2, 2)))
    assert ei3.value.argument == "fos_samples"
    for bad in ("1.0", b"1", None, 1 + 1j, object()):
        with pytest.raises(minephys.InputTypeError) as ei4:
            G.probability_of_failure(bad)
        assert ei4.value.argument == "fos_samples"
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(minephys.InputError) as ei5:
            G.probability_of_failure(np.array([0.5, 1.5]), bad)
        assert ei5.value.argument == "threshold"
    for bad in ("1.0", None, 1 + 1j, True):
        with pytest.raises(minephys.InputTypeError) as ei6:
            G.probability_of_failure(np.array([0.5, 1.5]), bad)
        assert ei6.value.argument == "threshold"


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle(
    "analytical", "spec 003 7.2: pof in (0, 1) and relative_error > 0; NaN, inf and bad types are errors"
)
@pytest.mark.parametrize(
    ("arg", "bad"),
    [
        ("pof", 0.0),
        ("pof", 1.0),
        ("pof", -0.1),
        ("pof", 1.5),
        ("pof", math.nan),
        ("pof", math.inf),
        ("relative_error", 0.0),
        ("relative_error", -0.1),
        ("relative_error", math.nan),
        ("relative_error", math.inf),
        ("relative_error", -math.inf),
    ],
)
def test_required_samples_domain(arg: str, bad: float) -> None:
    kw = {"pof": 0.05, "relative_error": 0.1, arg: bad}
    with pytest.raises(minephys.InputError) as ei:
        G.required_samples(**kw)
    assert ei.value.argument == arg
    with pytest.raises(minephys.InputError) as ei2:
        G.required_samples(**{**kw, arg: np.array([kw[arg], 0.05 if arg == "pof" else 0.1])})
    assert ei2.value.argument == arg


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "wrong types for required_samples")
@pytest.mark.parametrize("arg", ["pof", "relative_error"])
@pytest.mark.parametrize("bad", ["0.1", b"1", None, 1 + 1j, True, object()])
def test_required_samples_types(arg: str, bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        G.required_samples(**{"pof": 0.05, "relative_error": 0.1, arg: bad})
    assert ei.value.argument == arg


@pytest.mark.req("FR-003-13")
@pytest.mark.oracle("analytical", "a very small pof gives a very large (but finite, integer) count")
def test_required_samples_extreme() -> None:
    n = int(G.required_samples(1e-9, 0.01))
    assert n == pytest.approx((1 - 1e-9) / (1e-9 * 1e-4), rel=1e-12)  # 1e13 (integer valued)
    assert n > 10**12

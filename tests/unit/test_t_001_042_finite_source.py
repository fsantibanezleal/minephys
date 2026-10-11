"""T-001-042 (FR-001-20): the finite-source (machine-repairman) queue, one loader and N trucks.

Expected API: `H.finite_source_queue(n_trucks, travel_rate, service_rate)` (scalar inputs: N a count 1..100,000;
rates in 1/s, exponential times) returning a named result with float attributes
    idle_probability     pi0 = [sum_{n=0}^{N} N! / (N - n)! (lambda / mu)^n]^-1
    utilisation          1 - pi0
    throughput           X = mu (1 - pi0)                   [1/s]
    mean_at_loader       L = N - X / lambda                 [trucks at the loader, queue + service]
    mean_time_at_loader  L / X                              [s]
without overflow up to N = 100,000.

Formula read on Sztrik, "Basic Queueing Theory", section 3.2 (M/M/1/n/n queue), pp. 125-127; the oracles here are
independent of the code: the spec 001 section 7.4 table (rates per hour, TC-2), the exact N = 1 limit
X = lambda mu / (lambda + mu), the log-space evaluation of the same sum with `math.lgamma` (reference
computation), and the flow balance X = lambda (N - L).
"""

from __future__ import annotations

import math

import pytest

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

LAM = 3 / 3600
MU = 15 / 3600


def pi0_reference(n: int, lam: float, mu: float) -> float:
    """pi0 by a log-sum-exp of the terms t_k = N! / (N - k)! r^k (stable for any N)."""
    r = lam / mu
    logs = [math.lgamma(n + 1) - math.lgamma(n - k + 1) + k * math.log(r) for k in range(n + 1)]
    m = max(logs)
    return math.exp(-(m + math.log(math.fsum(math.exp(x - m) for x in logs))))


@pytest.mark.req("FR-001-20")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 001 7.4: X*3600 = 2.500000, 7.055085, 10.726983, 12.122291, 13.949282 for N = 1, 3, 5, 6, 8",
)
@pytest.mark.parametrize(
    ("n", "printed"),
    [(1, 2.500000), (3, 7.055085), (5, 10.726983), (6, 12.122291), (8, 13.949282)],
)
def test_printed_throughputs(n: int, printed: float) -> None:
    r = H.finite_source_queue(n, LAM, MU)
    assert r.throughput * 3600 == pytest.approx(printed, abs=5e-7)  # TC-2: 6 decimals


@pytest.mark.req("FR-001-20")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: N = 5: the sum is 3.5104, so pi0 = 1 / 3.5104 = 0.284868")
def test_idle_probability_of_five_trucks() -> None:
    r = H.finite_source_queue(5, LAM, MU)
    assert r.idle_probability == pytest.approx(0.284868, abs=5e-7)
    assert r.idle_probability == pytest.approx(1.0 / 3.5104, rel=1e-12)
    # the terms: 1 + 5(0.2) + 20(0.04) + 60(0.008) + 120(0.0016) + 120(0.00032) = 3.5104
    assert pytest.approx(3.5104, rel=1e-12) == 1 + 5 * 0.2 + 20 * 0.04 + 60 * 0.008 + 120 * 0.0016 + 120 * 0.00032
    assert r.utilisation == pytest.approx(1.0 - 1.0 / 3.5104, rel=1e-12)


@pytest.mark.req("FR-001-20")
@pytest.mark.oracle(
    "analytical", "N = 1: the single truck alternates travel and service: X = lambda mu / (lambda + mu)"
)
@pytest.mark.parametrize(("lam", "mu"), [(LAM, MU), (1.0, 1.0), (0.001, 0.5), (7.0, 0.25)])
def test_one_truck_limit(lam: float, mu: float) -> None:
    r = H.finite_source_queue(1, lam, mu)
    assert r.throughput == pytest.approx(lam * mu / (lam + mu), rel=1e-12)
    assert r.idle_probability == pytest.approx(mu / (lam + mu), rel=1e-12)
    # L = N - X / lambda cancels when lambda << mu (condition number mu / lambda), hence the looser bound
    cond = max(1.0, mu / lam)
    assert r.mean_at_loader == pytest.approx(lam / (lam + mu), rel=1e-12 * cond)
    assert r.mean_time_at_loader == pytest.approx(1.0 / mu, rel=1e-12 * cond)


@pytest.mark.req("FR-001-20")
@pytest.mark.oracle("analytical", "flow balance X = lambda (N - L) and Little's law at the loader")
@pytest.mark.parametrize("n", [1, 2, 3, 5, 8, 20, 100])
def test_balance_equations(n: int) -> None:
    r = H.finite_source_queue(n, LAM, MU)
    assert r.utilisation == pytest.approx(1.0 - r.idle_probability, rel=1e-12)
    assert r.throughput == pytest.approx(MU * (1.0 - r.idle_probability), rel=1e-12)
    assert r.mean_at_loader == pytest.approx(n - r.throughput / LAM, rel=1e-9, abs=1e-9)
    assert r.throughput == pytest.approx(LAM * (n - r.mean_at_loader), rel=1e-9, abs=1e-15)
    assert r.mean_time_at_loader == pytest.approx(r.mean_at_loader / r.throughput, rel=1e-12)
    assert r.mean_time_at_loader >= 1.0 / MU * (1.0 - 1e-12), (
        "a truck spends at least its own service time at the loader"
    )


@pytest.mark.req("FR-001-20")
@pytest.mark.oracle(
    "reference-implementation", "the same sum evaluated in log space with math.lgamma (independent algorithm)"
)
@pytest.mark.parametrize(
    ("n", "lam", "mu"),
    [
        (10, 1.0, 5.0),
        (50, 1.0, 20.0),
        (200, 3 / 3600, 15 / 3600),
        (1000, 0.01, 1.0),
        (5000, 1e-3, 1.0),
        (100_000, 1e-6, 1.0),
        (100_000, 0.2, 1.0),
    ],
)
def test_idle_probability_against_log_space_reference(n: int, lam: float, mu: float) -> None:
    r = H.finite_source_queue(n, lam, mu)
    ref = pi0_reference(n, lam, mu)
    assert math.isfinite(r.idle_probability)
    assert r.idle_probability == pytest.approx(ref, rel=1e-9, abs=1e-300)
    assert r.throughput == pytest.approx(mu * (1.0 - ref), rel=1e-9)
    assert 0.0 <= r.idle_probability <= 1.0


@pytest.mark.req("FR-001-20")
@pytest.mark.oracle(
    "analytical", "100,000 trucks saturate the loader: X -> mu and L -> N - mu / lambda (no overflow, no NaN)"
)
def test_one_hundred_thousand_trucks_saturate_the_loader() -> None:
    r = H.finite_source_queue(100_000, 0.2, 1.0)
    assert r.throughput == pytest.approx(1.0, rel=1e-12)
    assert r.utilisation == pytest.approx(1.0, abs=1e-12)
    assert r.mean_at_loader == pytest.approx(100_000 - 1.0 / 0.2, rel=1e-9)
    assert math.isfinite(r.mean_time_at_loader)
    assert r.mean_time_at_loader == pytest.approx(r.mean_at_loader / r.throughput, rel=1e-12)


@pytest.mark.req("FR-001-20")
@pytest.mark.oracle("analytical", "the result is a named record with float attributes")
def test_result_attributes_are_floats() -> None:
    r = H.finite_source_queue(5, LAM, MU)
    for name in ("idle_probability", "utilisation", "throughput", "mean_at_loader", "mean_time_at_loader"):
        assert isinstance(getattr(r, name), float), name

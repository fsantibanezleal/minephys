"""T-001-041 (FR-001-19, FR-001-24): the M/M/c queue.

Expected API: `H.mmc_queue(arrival_rate, service_rate, servers)` with scalar inputs (rates in 1/s, `servers` an
integer
1..10,000) returning a named result with float attributes
    utilisation          rho = lambda / (c mu)
    erlang_c             C(c, a), a = lambda / mu
    mean_wait            W_q = C / (c mu - lambda)           [s]
    mean_queue_length    L_q = lambda W_q
    mean_time_in_system  W = W_q + 1 / mu                    [s]
    mean_in_system       L = lambda W
computed without overflow for up to 10,000 servers. If lambda >= c * mu (rho >= 1, no steady state) it raises
`minephys.InputError` whose `argument` is `arrival_rate` (FR-001-24).

Oracles: the printed values of spec 001 section 7.4 (rates per hour converted to 1/s; TC-2), the closed form of the
M/M/1 queue (analytical), the Erlang-C formula evaluated with exact `fractions.Fraction` arithmetic (reference
computation, TC-1) and the stable Erlang-B recursion B_k = a B_{k-1} / (k + a B_{k-1}), C = B / (1 - rho (1 - B)).
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

import minephys
from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def erlang_c_exact(c: int, lam: Fraction, mu: Fraction) -> Fraction:
    a = lam / mu
    top = a**c / math.factorial(c) / (1 - a / c)
    bottom = sum(a**k / math.factorial(k) for k in range(c)) + top
    return top / bottom


def erlang_c_recursion(c: int, a: float) -> float:
    b = 1.0
    for k in range(1, c + 1):
        b = a * b / (k + a * b)
    rho = a / c
    return b / (1.0 - rho * (1.0 - b))


@pytest.mark.req("FR-001-19")
@pytest.mark.oracle(
    "hand-calculation", "spec 001 7.4: 24/h arrivals, 15/h service, 2 servers: rho 0.8, C 0.7111111, Wq 426.6667 s"
)
def test_printed_two_server_case() -> None:
    r = H.mmc_queue(24 / 3600, 15 / 3600, 2)
    assert r.utilisation == pytest.approx(0.8, rel=1e-12)
    assert r.erlang_c == pytest.approx(0.7111111, abs=5e-8)  # TC-2: 7 decimals
    assert r.mean_wait == pytest.approx(426.6667, abs=5e-5)
    assert r.mean_queue_length == pytest.approx(2.8444444, abs=5e-8)
    assert r.mean_time_in_system == pytest.approx(666.6667, abs=5e-5)
    assert r.mean_in_system == pytest.approx(4.4444444, abs=5e-8)
    # exact fractions: C = 32/45, Wq = 3840/9 s
    assert r.erlang_c == pytest.approx(32.0 / 45.0, rel=1e-12)
    assert r.mean_wait == pytest.approx(1280.0 / 3.0, rel=1e-12)


@pytest.mark.req("FR-001-19")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: M/M/1, 10/h and 15/h: C = rho = 0.6666667, Wq = 480 s")
def test_printed_single_server_case() -> None:
    r = H.mmc_queue(10 / 3600, 15 / 3600, 1)
    assert r.erlang_c == pytest.approx(0.6666667, abs=5e-8)
    assert r.utilisation == pytest.approx(2.0 / 3.0, rel=1e-12)
    assert r.mean_wait == pytest.approx(480.0, rel=1e-12)


@pytest.mark.req("FR-001-19")
@pytest.mark.oracle(
    "analytical", "M/M/1 closed forms: Wq = rho / (mu - lambda), W = 1 / (mu - lambda), L = rho / (1 - rho)"
)
@pytest.mark.parametrize("rho", [0.01, 0.3, 0.5, 0.9, 0.99, 0.999])
def test_mm1_closed_forms(rho: float) -> None:
    mu = 1.0 / 60.0
    lam = rho * mu
    r = H.mmc_queue(lam, mu, 1)
    assert r.utilisation == pytest.approx(rho, rel=1e-12)
    assert r.erlang_c == pytest.approx(rho, rel=1e-12)
    assert r.mean_wait == pytest.approx(rho / (mu - lam), rel=1e-12)
    assert r.mean_time_in_system == pytest.approx(1.0 / (mu - lam), rel=1e-12)
    assert r.mean_in_system == pytest.approx(rho / (1.0 - rho), rel=1e-12)
    assert r.mean_queue_length == pytest.approx(rho**2 / (1.0 - rho), rel=1e-12)


@pytest.mark.req("FR-001-19")
@pytest.mark.oracle("reference-implementation", "Erlang C by exact rational arithmetic (fractions.Fraction)")
@pytest.mark.parametrize(
    ("c", "lam", "mu"),
    [
        (2, Fraction(3), Fraction(2)),
        (3, Fraction(5), Fraction(2)),
        (5, Fraction(9), Fraction(2)),
        (8, Fraction(7), Fraction(1)),
        (20, Fraction(37, 2), Fraction(1)),
        (30, Fraction(29), Fraction(1)),
    ],
)
def test_erlang_c_against_exact_arithmetic(c: int, lam: Fraction, mu: Fraction) -> None:
    r = H.mmc_queue(float(lam), float(mu), c)
    exact = erlang_c_exact(c, lam, mu)
    assert r.erlang_c == pytest.approx(float(exact), rel=1e-12)
    wq = exact / (c * mu - lam)
    assert r.mean_wait == pytest.approx(float(wq), rel=1e-12)
    assert r.mean_queue_length == pytest.approx(float(lam * wq), rel=1e-12)
    assert r.mean_time_in_system == pytest.approx(float(wq + 1 / mu), rel=1e-12)
    assert r.mean_in_system == pytest.approx(float(lam * (wq + 1 / mu)), rel=1e-12)


@pytest.mark.req("FR-001-19")
@pytest.mark.oracle("reference-implementation", "stable Erlang-B recursion for 10,000 servers (no factorial overflow)")
@pytest.mark.parametrize(
    ("c", "rho"), [(100, 0.95), (1000, 0.9), (5000, 0.97), (10000, 0.5), (10000, 0.9), (10000, 0.995)]
)
def test_large_server_counts_do_not_overflow(c: int, rho: float) -> None:
    mu = 0.01
    lam = rho * c * mu
    r = H.mmc_queue(lam, mu, c)
    assert math.isfinite(r.erlang_c)
    assert 0.0 <= r.erlang_c <= 1.0
    assert r.erlang_c == pytest.approx(erlang_c_recursion(c, lam / mu), rel=1e-9, abs=1e-300)
    assert math.isfinite(r.mean_wait)
    assert math.isfinite(r.mean_in_system)


@pytest.mark.req("FR-001-19")
@pytest.mark.oracle("analytical", "the result is a named record with float attributes")
def test_result_attributes_are_floats() -> None:
    r = H.mmc_queue(24 / 3600, 15 / 3600, 2)
    for name in ("utilisation", "erlang_c", "mean_wait", "mean_queue_length", "mean_time_in_system", "mean_in_system"):
        assert isinstance(getattr(r, name), float), name  # numpy.float64 is a float subclass


@pytest.mark.req("FR-001-24")
@pytest.mark.oracle("analytical", "lambda >= c * mu has no steady state: InputError naming arrival_rate")
@pytest.mark.parametrize(
    ("lam", "mu", "c"),
    [(2.0, 1.0, 2), (2.0001, 1.0, 2), (5.0, 1.0, 2), (1.0, 1.0, 1), (100.0, 1.0, 10), (1e9, 1.0, 10000)],
)
def test_unstable_queue_is_an_error(lam: float, mu: float, c: int) -> None:
    with pytest.raises(minephys.InputError) as ei:
        H.mmc_queue(lam, mu, c)
    assert ei.value.argument == "arrival_rate"


@pytest.mark.req("FR-001-24")
@pytest.mark.oracle("analytical", "just below saturation the queue is stable and finite")
def test_just_below_saturation_is_accepted() -> None:
    r = H.mmc_queue(2.0 * (1.0 - 1e-9), 1.0, 2)
    assert r.utilisation < 1.0
    assert math.isfinite(r.mean_wait)
    assert r.mean_wait > 1e6

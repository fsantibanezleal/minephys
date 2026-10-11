"""T-001-041 (P-001-08, P-001-09): metamorphic properties of `mmc_queue`.

P-001-08 (unit-change invariance): scaling lambda and mu by k leaves rho, C, L_q and L unchanged and divides W_q
and W by k.
P-001-09: Little's law (L_q = lambda W_q, L = lambda W), 0 < C < 1, C = rho for c = 1, W_q strictly increasing
in lambda and
non-increasing in c, and C(c, a) equals the Erlang-B recursion form B / (1 - rho (1 - B)).
Generators (spec 001): c in 1..50, rho in (0, 0.99), k in [1e-4, 1e4]. Tolerance TC-1 (rtol 1e-12); the
orderings use pairs
with a relative gap of at least 1e-3.

Oracle: analytical identities (queueing theory) and the independent Erlang-B recursion written in this file.
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

servers = st.integers(1, 50)
rho = st.floats(0.01, 0.99)
CFG = settings(deadline=None)


def erlang_b_c(c: int, a: float) -> float:
    b = 1.0
    for k in range(1, c + 1):
        b = a * b / (k + a * b)
    return b / (1.0 - (a / c) * (1.0 - b))


def q(lam, mu, c):
    return H.mmc_queue(lam, mu, c)


@pytest.mark.req("P-001-08")
@pytest.mark.oracle("analytical", "unit-change invariance of a queue: seconds versus hours")
@CFG
@given(c=servers, r=rho, k=st.floats(1e-4, 1e4))
def test_time_unit_invariance(c: int, r: float, k: float) -> None:
    mu = 1.0 / 90.0
    lam = r * c * mu
    base = q(lam, mu, c)
    scaled = q(k * lam, k * mu, c)
    assert scaled.utilisation == pytest.approx(base.utilisation, rel=1e-12)
    assert scaled.erlang_c == pytest.approx(base.erlang_c, rel=1e-12)
    assert scaled.mean_queue_length == pytest.approx(base.mean_queue_length, rel=1e-12)
    assert scaled.mean_in_system == pytest.approx(base.mean_in_system, rel=1e-12)
    assert scaled.mean_wait == pytest.approx(base.mean_wait / k, rel=1e-12)
    assert scaled.mean_time_in_system == pytest.approx(base.mean_time_in_system / k, rel=1e-12)


@pytest.mark.req("P-001-09")
@pytest.mark.oracle("analytical", "Little's law and the bounds on the waiting probability")
@CFG
@given(c=servers, r=rho)
def test_littles_law_and_bounds(c: int, r: float) -> None:
    mu = 1.0 / 90.0
    lam = r * c * mu
    res = q(lam, mu, c)
    assert 0.0 < res.erlang_c < 1.0
    assert res.mean_queue_length == pytest.approx(lam * res.mean_wait, rel=1e-12)
    assert res.mean_in_system == pytest.approx(lam * res.mean_time_in_system, rel=1e-12)
    assert res.mean_time_in_system == pytest.approx(res.mean_wait + 1.0 / mu, rel=1e-12)
    assert res.utilisation == pytest.approx(r, rel=1e-12)
    assert res.mean_in_system == pytest.approx(res.mean_queue_length + lam / mu, rel=1e-12)


@pytest.mark.req("P-001-09")
@pytest.mark.oracle("analytical", "for a single server the probability of waiting is the utilisation")
@CFG
@given(r=rho)
def test_single_server_c_equals_rho(r: float) -> None:
    assert q(r, 1.0, 1).erlang_c == pytest.approx(r, rel=1e-12)


@pytest.mark.req("P-001-09")
@pytest.mark.oracle("reference-implementation", "Erlang-B recursion: C = B / (1 - rho (1 - B))")
@CFG
@given(c=servers, r=rho)
def test_erlang_c_equals_the_erlang_b_form(c: int, r: float) -> None:
    assert q(r * c, 1.0, c).erlang_c == pytest.approx(erlang_b_c(c, r * c), rel=1e-11)


@pytest.mark.req("P-001-09")
@pytest.mark.oracle("analytical", "the mean wait strictly increases with the arrival rate")
@CFG
@given(c=servers, r1=rho, r2=rho)
def test_wait_increases_with_the_arrival_rate(c: int, r1: float, r2: float) -> None:
    assume(abs(r1 - r2) > 1e-3 * max(r1, r2))
    lo, hi = sorted((r1, r2))
    assert q(lo * c, 1.0, c).mean_wait < q(hi * c, 1.0, c).mean_wait


@pytest.mark.req("P-001-09")
@pytest.mark.oracle("analytical", "adding a server never lengthens the wait at fixed lambda and mu")
@CFG
@given(c=st.integers(1, 49), r=st.floats(0.05, 0.98))
def test_wait_does_not_increase_with_the_number_of_servers(c: int, r: float) -> None:
    lam = r * c  # stable for c servers, so also for c + 1
    assert q(lam, 1.0, c + 1).mean_wait <= q(lam, 1.0, c).mean_wait
    assert q(lam, 1.0, c + 1).erlang_c <= q(lam, 1.0, c).erlang_c

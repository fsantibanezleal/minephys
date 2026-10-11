"""T-001-042 (P-001-10): metamorphic properties of `finite_source_queue`.

P-001-10: the throughput is non-decreasing in the number of trucks N and bounded by
min(N / (1/lambda + 1/mu), mu); the flow balance X = lambda (N - L) holds; scaling lambda and mu by k scales
X by k (and leaves L unchanged).
Generators (spec 001): N in 1..500, lambda / mu in [1e-3, 10]. Tolerance TC-1; the bound is an exact ordering
(a slack of 1e-12 relative covers the rounding of the bound itself).

Oracle: analytical (the bound is the minimum of the no-queueing demand N / (cycle time without waiting) and the loader
capacity mu).
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

trucks = st.integers(1, 500)
ratio = st.floats(1e-3, 10.0)
CFG = settings(deadline=None)


@pytest.mark.req("P-001-10")
@pytest.mark.oracle("analytical", "adding a truck never lowers the throughput")
@CFG
@given(n=st.integers(1, 499), r=ratio)
def test_throughput_is_non_decreasing_in_trucks(n: int, r: float) -> None:
    mu = 1.0 / 60.0
    lam = r * mu
    assert H.finite_source_queue(n + 1, lam, mu).throughput >= H.finite_source_queue(n, lam, mu).throughput


@pytest.mark.req("P-001-10")
@pytest.mark.oracle("analytical", "X <= min(N / (1/lambda + 1/mu), mu)")
@CFG
@given(n=trucks, r=ratio)
def test_throughput_bound(n: int, r: float) -> None:
    mu = 1.0 / 60.0
    lam = r * mu
    x = H.finite_source_queue(n, lam, mu).throughput
    bound = min(n / (1.0 / lam + 1.0 / mu), mu)
    assert x <= bound * (1.0 + 1e-12)
    assert x > 0.0


@pytest.mark.req("P-001-10")
@pytest.mark.oracle("analytical", "flow balance: X = lambda (N - L) and L = N - X / lambda")
@CFG
@given(n=trucks, r=ratio)
def test_flow_balance(n: int, r: float) -> None:
    mu = 1.0 / 60.0
    lam = r * mu
    res = H.finite_source_queue(n, lam, mu)
    assert res.throughput == pytest.approx(lam * (n - res.mean_at_loader), rel=1e-9, abs=1e-12 * lam * n)
    assert 0.0 <= res.mean_at_loader <= n * (1.0 + 1e-12)


@pytest.mark.req("P-001-10")
@pytest.mark.oracle("analytical", "unit-change invariance: scaling both rates by k scales X by k and keeps L")
@CFG
@given(n=trucks, r=ratio, k=st.floats(1e-4, 1e4))
def test_rate_scaling(n: int, r: float, k: float) -> None:
    mu = 1.0 / 60.0
    lam = r * mu
    base = H.finite_source_queue(n, lam, mu)
    scaled = H.finite_source_queue(n, k * lam, k * mu)
    assert scaled.throughput == pytest.approx(k * base.throughput, rel=1e-11)
    assert scaled.idle_probability == pytest.approx(base.idle_probability, rel=1e-11)
    assert scaled.mean_at_loader == pytest.approx(base.mean_at_loader, rel=1e-9, abs=1e-12 * n)
    assert scaled.mean_time_at_loader == pytest.approx(base.mean_time_at_loader / k, rel=1e-9)


@pytest.mark.req("P-001-10")
@pytest.mark.oracle("analytical", "a faster loader (larger mu) at fixed lambda and N never lowers the throughput")
@CFG
@given(n=trucks, r=st.floats(0.05, 5.0), boost=st.floats(1.01, 5.0))
def test_throughput_is_non_decreasing_in_the_service_rate(n: int, r: float, boost: float) -> None:
    lam = 1.0 / 600.0
    mu = lam / r
    assert H.finite_source_queue(n, lam, boost * mu).throughput >= H.finite_source_queue(n, lam, mu).throughput

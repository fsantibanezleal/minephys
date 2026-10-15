"""T-001-043 (P-001-11): metamorphic properties of `mean_value_analysis`.

P-001-11: the population is conserved (sum_k L_k(N) = N); the result is invariant to the order of the stations;
dividing X by k when all service times scale by k; X(n) is non-decreasing in n; and with one "queue" and one
"delay" station the network equals `finite_source_queue` (identity). Generators: N in 1..500, K in 1..20,
service times in [1, 1000] s, visit ratios in [0.1, 3]. Tolerance TC-1 (rtol 1e-9 for the cross-model identity,
whose two sides use different algorithms). Extra relations (analytical): the asymptotic bounds X(n) <= min(n /
sum D_k, 1 / max D_k over queue stations).

Oracle: analytical (product-form network identities) and `finite_source_queue` of the same module as the independent
closed form (machine-repairman model, Sztrik section 3.2) for the identity.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

CFG = settings(deadline=None)


@st.composite
def networks(draw, max_k=20):
    k = draw(st.integers(1, max_k))
    s = draw(st.lists(st.floats(1.0, 1000.0), min_size=k, max_size=k))
    v = draw(st.lists(st.floats(0.1, 3.0), min_size=k, max_size=k))
    t = draw(st.lists(st.sampled_from(["queue", "delay"]), min_size=k, max_size=k))
    n = draw(st.integers(1, 500))
    return n, np.array(s), np.array(v), t


@pytest.mark.req("P-001-11")
@pytest.mark.oracle("analytical", "conservation of customers: the queue lengths add up to the population")
@CFG
@given(net=networks())
def test_population_is_conserved(net) -> None:
    n, s, v, t = net
    r = H.mean_value_analysis(n, s, v, t)
    assert float(np.sum(r.queue_length)) == pytest.approx(n, rel=1e-9)
    assert r.throughput.shape == (n,)
    assert np.all(r.queue_length >= 0.0)


@pytest.mark.req("P-001-11")
@pytest.mark.oracle("analytical", "invariance to the order of the stations")
@CFG
@given(net=networks(), seed=st.integers(0, 2**32 - 1))
def test_station_order_is_irrelevant(net, seed: int) -> None:
    n, s, v, t = net
    perm = np.random.default_rng(seed).permutation(len(s))
    a = H.mean_value_analysis(n, s, v, t)
    b = H.mean_value_analysis(n, s[perm], v[perm], [t[i] for i in perm])
    np.testing.assert_allclose(b.throughput, a.throughput, rtol=1e-11)
    np.testing.assert_allclose(b.queue_length, a.queue_length[perm], rtol=1e-9, atol=1e-12)
    np.testing.assert_allclose(b.residence_time, a.residence_time[perm], rtol=1e-9, atol=1e-12)
    np.testing.assert_allclose(b.utilisation, a.utilisation[perm], rtol=1e-9, atol=1e-12)


@pytest.mark.req("P-001-11")
@pytest.mark.oracle("analytical", "unit-change invariance: all service times times k divides X by k")
@CFG
@given(net=networks(), k=st.floats(1e-3, 1e3))
def test_time_scaling(net, k: float) -> None:
    n, s, v, t = net
    a = H.mean_value_analysis(n, s, v, t)
    b = H.mean_value_analysis(n, k * s, v, t)
    np.testing.assert_allclose(b.throughput, a.throughput / k, rtol=1e-11)
    np.testing.assert_allclose(b.queue_length, a.queue_length, rtol=1e-9, atol=1e-12)
    np.testing.assert_allclose(b.residence_time, k * a.residence_time, rtol=1e-9)


@pytest.mark.req("P-001-11")
@pytest.mark.oracle("analytical", "X(n) is non-decreasing in n and obeys the asymptotic bounds")
@CFG
@given(net=networks())
def test_throughput_is_monotone_and_bounded(net) -> None:
    n, s, v, t = net
    x = H.mean_value_analysis(n, s, v, t).throughput
    assert np.all(x[1:] >= x[:-1] * (1.0 - 1e-12))
    d = s * v
    total = float(np.sum(d))
    idx = np.arange(1, n + 1)
    bound = idx / total
    queue_d = [d[i] for i in range(len(d)) if t[i] == "queue"]
    if queue_d:
        bound = np.minimum(bound, 1.0 / max(queue_d))
    assert np.all(x <= bound * (1.0 + 1e-9))


@pytest.mark.req("P-001-11")
@pytest.mark.oracle(
    "reference-implementation", "finite_source_queue (machine-repairman closed form) as the independent side"
)
@CFG
@given(n=st.integers(1, 400), s_load=st.floats(5.0, 600.0), s_travel=st.floats(5.0, 3000.0))
def test_one_queue_and_one_delay_station_equal_the_finite_source_queue(n: int, s_load: float, s_travel: float) -> None:
    mva = H.mean_value_analysis(n, [s_load, s_travel], [1.0, 1.0], ["queue", "delay"])
    fsq = H.finite_source_queue(n, 1.0 / s_travel, 1.0 / s_load)
    assert float(mva.throughput[-1]) == pytest.approx(fsq.throughput, rel=1e-9)
    assert float(mva.queue_length[0]) == pytest.approx(fsq.mean_at_loader, rel=1e-8, abs=1e-9)
    assume(fsq.mean_at_loader > 1e-6)
    assert float(mva.residence_time[0]) == pytest.approx(fsq.mean_time_at_loader, rel=1e-7)


@pytest.mark.req("P-001-11")
@pytest.mark.oracle("analytical", "adding a customer never lowers the throughput: X(N + 1) at N + 1 >= X(N)")
@CFG
@given(net=networks(max_k=6))
def test_prefix_consistency(net) -> None:
    n, s, v, t = net
    assume(n >= 2)
    full = H.mean_value_analysis(n, s, v, t).throughput
    short = H.mean_value_analysis(n - 1, s, v, t).throughput
    np.testing.assert_allclose(full[:-1], short, rtol=1e-12)

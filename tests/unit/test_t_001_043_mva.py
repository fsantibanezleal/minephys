"""T-001-043 (FR-001-21, FR-001-26): exact single-class mean-value analysis.

Expected API: `H.mean_value_analysis(population, service_time, visit_ratio, station_type)` with `population` a count
1..100,000, `service_time` [s] and `visit_ratio` [1] 1-D arrays of the same length K in 1..1,000 and `station_type` a
length-K sequence of the strings "queue" or "delay". It runs, for n = 1..N,

    W_k(n) = S_k (1 + L_k(n-1))   for "queue",  W_k = S_k   for "delay",
    X(n) = n / sum_k v_k W_k(n),     L_k(n) = v_k X(n) W_k(n)

and returns a named result (attribute names fixed by this test; the spec names the quantities only):
    throughput     X(1..N) as a float64 array [1/s],
    residence_time W_k(N) [s], queue_length L_k(N), utilisation v_k X(N) S_k   (float64 arrays of length K).

FR-001-26: a non-integer or out-of-range `population` (cap 100,000), more than 1,000 stations, a `station_type` other
than "queue" or "delay" (the error lists the allowed values), arrays of different lengths, or sum v_k S_k = 0 raise
`minephys.InputError` naming the argument.

Oracles: the printed values of spec 001 section 7.4 (TC-2) and the closed forms of one-station networks (analytical).
"""

from __future__ import annotations

import numpy as np
import pytest

import minephys
from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


@pytest.mark.req("FR-001-21")
@pytest.mark.oracle(
    "hand-calculation", "spec 001 7.4: loader + delay, N = 5: X*3600 = 10.726983, L = (1.4243391, 3.5756609)"
)
def test_two_station_printed_values() -> None:
    r = H.mean_value_analysis(5, [240.0, 1200.0], [1.0, 1.0], ["queue", "delay"])
    assert r.throughput.shape == (5,)
    assert r.throughput.dtype == np.float64
    assert r.throughput[-1] * 3600 == pytest.approx(10.726983, abs=5e-7)
    assert r.queue_length[0] == pytest.approx(1.4243391, abs=5e-8)
    assert r.queue_length[1] == pytest.approx(3.5756609, abs=5e-8)
    assert float(np.sum(r.queue_length)) == pytest.approx(5.0, rel=1e-12)


@pytest.mark.req("FR-001-21")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: three stations, N = 8: the printed X(n) and the residence times")
def test_three_station_printed_values() -> None:
    r = H.mean_value_analysis(8, [240.0, 60.0, 1200.0], [1.0, 1.0, 1.0], ["queue", "queue", "delay"])
    printed = [2.4000000, 4.6728972, 6.7856723, 8.7001686, 10.376463, 11.779540, 12.888759, 13.707006]
    half = [5e-8, 5e-8, 5e-8, 5e-8, 5e-7, 5e-7, 5e-7, 5e-7]  # TC-2: half a unit of the last printed decimal
    got = r.throughput * 3600
    assert got.shape == (8,)
    for n in range(8):
        assert got[n] == pytest.approx(printed[n], abs=half[n]), f"X({n + 1})"
    assert r.residence_time[0] == pytest.approx(825.18739, abs=5e-6)
    assert r.residence_time[1] == pytest.approx(75.927974, abs=5e-7)
    assert r.residence_time[2] == 1200.0  # a delay station: W = S exactly
    assert float(np.sum(r.queue_length)) == pytest.approx(8.0, rel=1e-12)


@pytest.mark.req("FR-001-21")
@pytest.mark.oracle("analytical", "utilisation of station k is v_k X S_k; queue-station utilisations stay below 1")
def test_utilisations() -> None:
    r = H.mean_value_analysis(8, [240.0, 60.0, 1200.0], [1.0, 1.0, 1.0], ["queue", "queue", "delay"])
    x = float(r.throughput[-1])
    np.testing.assert_allclose(r.utilisation, [x * 240.0, x * 60.0, x * 1200.0], rtol=1e-12)
    assert r.utilisation[0] == pytest.approx(0.91380, abs=5e-6)
    assert np.all(r.utilisation[:2] < 1.0)


@pytest.mark.req("FR-001-21")
@pytest.mark.oracle("analytical", "one delay station is an infinite server: X(n) = n / S and L = n")
def test_single_delay_station() -> None:
    r = H.mean_value_analysis(5, [100.0], [1.0], ["delay"])
    np.testing.assert_allclose(r.throughput, np.arange(1, 6) / 100.0, rtol=1e-14)
    assert r.queue_length[0] == pytest.approx(5.0, rel=1e-14)
    assert r.residence_time[0] == 100.0


@pytest.mark.req("FR-001-21")
@pytest.mark.oracle("analytical", "one queue station holding everybody: W(n) = n S, X(n) = 1 / S for every n")
def test_single_queue_station() -> None:
    r = H.mean_value_analysis(7, [50.0], [1.0], ["queue"])
    np.testing.assert_allclose(r.throughput, np.full(7, 1.0 / 50.0), rtol=1e-14)
    assert r.residence_time[0] == pytest.approx(7 * 50.0, rel=1e-14)
    assert r.queue_length[0] == pytest.approx(7.0, rel=1e-14)
    assert r.utilisation[0] == pytest.approx(1.0, rel=1e-14)


@pytest.mark.req("FR-001-21")
@pytest.mark.oracle("analytical", "the throughput depends on the demands v_k * S_k only")
def test_visit_ratio_and_service_time_enter_as_a_product_in_the_throughput() -> None:
    a = H.mean_value_analysis(6, [240.0, 1200.0], [1.0, 1.0], ["queue", "delay"])
    b = H.mean_value_analysis(6, [120.0, 400.0], [2.0, 3.0], ["queue", "delay"])
    np.testing.assert_allclose(a.throughput, b.throughput, rtol=1e-12)
    np.testing.assert_allclose(a.queue_length, b.queue_length, rtol=1e-12)
    np.testing.assert_allclose(a.utilisation, b.utilisation, rtol=1e-12)


@pytest.mark.req("FR-001-21")
@pytest.mark.oracle("hand-calculation", "population 1: X(1) = 1 / sum of the demands, a queue station residence W = S")
def test_population_one() -> None:
    r = H.mean_value_analysis(1, [240.0, 60.0, 1200.0], [1.0, 2.0, 1.0], ["queue", "queue", "delay"])
    demand = 240.0 + 2 * 60.0 + 1200.0
    assert r.throughput.shape == (1,)
    assert r.throughput[0] == pytest.approx(1.0 / demand, rel=1e-14)
    np.testing.assert_allclose(r.residence_time, [240.0, 60.0, 1200.0], rtol=1e-14)


@pytest.mark.req("FR-001-21")
@pytest.mark.oracle("analytical", "a station with zero service time or zero visits adds nothing")
def test_zero_demand_station_is_inert() -> None:
    base = H.mean_value_analysis(5, [240.0, 1200.0], [1.0, 1.0], ["queue", "delay"])
    padded = H.mean_value_analysis(5, [240.0, 1200.0, 0.0], [1.0, 1.0, 1.0], ["queue", "delay", "queue"])
    np.testing.assert_allclose(padded.throughput, base.throughput, rtol=1e-14)
    assert padded.queue_length[2] == 0.0


@pytest.mark.req("FR-001-21")
@pytest.mark.oracle("analytical", "list, tuple and array arguments are equivalent; the inputs are not modified")
def test_argument_containers() -> None:
    s = np.array([240.0, 60.0, 1200.0])
    v = np.array([1.0, 1.0, 1.0])
    types = ("queue", "queue", "delay")
    a = H.mean_value_analysis(8, s, v, types)
    b = H.mean_value_analysis(8, list(s), list(v), list(types))
    np.testing.assert_array_equal(a.throughput, b.throughput)
    np.testing.assert_array_equal(s, [240.0, 60.0, 1200.0])


# ---------------------------------------------------------------- FR-001-26


def call(**over):
    kw = {
        "population": 5,
        "service_time": [240.0, 1200.0],
        "visit_ratio": [1.0, 1.0],
        "station_type": ["queue", "delay"],
    }
    kw.update(over)
    return H.mean_value_analysis(**kw)


@pytest.mark.req("FR-001-26")
@pytest.mark.oracle("hand-calculation", "population must be an integer in 1..100,000")
@pytest.mark.parametrize("bad", [0, -1, 2.5, 100_001, 10**9, float("nan"), float("inf")])
def test_population_domain(bad: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        call(population=bad)
    assert ei.value.argument == "population"


@pytest.mark.req("FR-001-26")
@pytest.mark.oracle("hand-calculation", "a boolean or a string is not a count")
@pytest.mark.parametrize("bad", [True, "5", None])
def test_population_type(bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        call(population=bad)
    assert ei.value.argument == "population"


@pytest.mark.req("FR-001-26")
@pytest.mark.oracle("hand-calculation", "the cap is inclusive: 100,000 customers are accepted")
def test_population_cap_is_inclusive() -> None:
    r = call(population=100_000)
    assert r.throughput.shape == (100_000,)
    assert np.all(np.isfinite(r.throughput))
    assert float(np.sum(r.queue_length)) == pytest.approx(100_000.0, rel=1e-9)


@pytest.mark.req("FR-001-26")
@pytest.mark.oracle("hand-calculation", "at most 1,000 stations; exactly 1,000 are accepted")
def test_station_cap() -> None:
    ok = H.mean_value_analysis(3, np.full(1000, 10.0), np.ones(1000), ["queue"] * 1000)
    assert ok.queue_length.shape == (1000,)
    with pytest.raises(minephys.InputError) as ei:
        H.mean_value_analysis(3, np.full(1001, 10.0), np.ones(1001), ["queue"] * 1001)
    assert ei.value.argument in {"service_time", "visit_ratio", "station_type"}
    assert "1001" in str(ei.value) or "1,001" in str(ei.value)


@pytest.mark.req("FR-001-26")
@pytest.mark.oracle(
    "hand-calculation", "FR-000-15: an unknown station type lists the allowed values; matching is case-sensitive"
)
@pytest.mark.parametrize("bad", ["Queue", "QUEUE", "server", "", " queue", "delay ", "queue\n", "q"])
def test_station_type_options(bad: str) -> None:
    with pytest.raises(minephys.InputError) as ei:
        call(station_type=["queue", bad])
    assert ei.value.argument == "station_type"
    assert "queue" in str(ei.value)
    assert "delay" in str(ei.value)


@pytest.mark.req("FR-001-26")
@pytest.mark.oracle("hand-calculation", "arrays of different lengths are rejected")
def test_length_mismatch() -> None:
    for over in (
        {"service_time": [240.0]},
        {"visit_ratio": [1.0, 1.0, 1.0]},
        {"station_type": ["queue"]},
        {"station_type": ["queue", "delay", "delay"]},
    ):
        with pytest.raises(minephys.InputError) as ei:
            call(**over)
        assert ei.value.argument in {"service_time", "visit_ratio", "station_type"}


@pytest.mark.req("FR-001-26")
@pytest.mark.oracle("hand-calculation", "sum v_k S_k = 0 gives X = n / 0: rejected")
@pytest.mark.parametrize(
    "over",
    [
        {"service_time": [0.0, 0.0]},
        {"visit_ratio": [0.0, 0.0]},
        {"service_time": [0.0, 1200.0], "visit_ratio": [1.0, 0.0]},
    ],
)
def test_zero_total_demand(over: dict) -> None:
    with pytest.raises(minephys.InputError) as ei:
        call(**over)
    assert ei.value.argument in {"service_time", "visit_ratio"}


@pytest.mark.req("FR-001-26")
@pytest.mark.oracle("hand-calculation", "hostile station data: negative, NaN, infinite, 2-D, empty")
@pytest.mark.parametrize(
    "over",
    [
        {"service_time": [-1.0, 1200.0]},
        {"visit_ratio": [1.0, -0.5]},
        {"service_time": [float("nan"), 1200.0]},
        {"service_time": [240.0, float("inf")]},
        {"visit_ratio": [float("nan"), 1.0]},
        {"service_time": [[240.0, 1200.0]]},
        {"service_time": [], "visit_ratio": [], "station_type": []},
    ],
)
def test_hostile_station_data(over: dict) -> None:
    with pytest.raises(minephys.InputError) as ei:
        call(**over)
    assert ei.value.argument in {"service_time", "visit_ratio", "station_type"}

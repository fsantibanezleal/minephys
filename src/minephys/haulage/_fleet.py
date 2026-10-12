"""Closed analytical fleet models: M/M/c, finite-source queue and exact mean-value analysis (spec 001 FR-001-19,
FR-001-20, FR-001-21, FR-001-24, FR-001-26). They are exact oracles for a discrete-event simulation."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any, NamedTuple

import numpy as np

from .._errors import InputError, InputTypeError
from .._validate import (
    FloatArray,
    as_checked,
    as_count,
    as_float_array,
    as_scalar,
    check_finite,
    check_option,
    check_rank,
    check_size,
)

_MAX_SERVERS = 10_000
_MAX_TRUCKS = 100_000
_MAX_POPULATION = 100_000
_MAX_STATIONS = 1_000


class MMCResult(NamedTuple):
    """Steady-state M/M/c results (rates in 1/s, times in s)."""

    utilisation: float
    erlang_c: float
    mean_wait: float
    mean_queue_length: float
    mean_time_in_system: float
    mean_in_system: float


class FiniteSourceResult(NamedTuple):
    """Machine-repairman results for one loader and N trucks (rates in 1/s, times in s)."""

    idle_probability: float
    utilisation: float
    throughput: float
    mean_at_loader: float
    mean_time_at_loader: float


class MVAResult(NamedTuple):
    """Mean-value analysis: throughput X(1..N) and, at n = N, residence times, queue lengths and utilisations."""

    throughput: FloatArray
    residence_time: FloatArray
    queue_length: FloatArray
    utilisation: FloatArray


def mmc_queue(arrival_rate: Any, service_rate: Any, servers: Any) -> MMCResult:
    """Steady-state M/M/c queue (Erlang C) for scalar inputs.

    Parameters
    ----------
    arrival_rate : float [1/s]
        Poisson arrival rate lambda, > 0 and below servers times service_rate.
    service_rate : float [1/s]
        Exponential service rate mu of one server, > 0.
    servers : int [count]
        Number of servers c, an integer from 1 to 10,000.

    Returns
    -------
    MMCResult [s]
        Named result: utilisation [1], erlang_c [1], mean_wait [s], mean_queue_length [1], mean_time_in_system [s],
        mean_in_system [1].

    Equation
    --------
    a = lambda / mu, rho = a / c; C = B / (1 - rho (1 - B)) with the Erlang-B recursion
    B_k = a B_(k-1) / (k + a B_(k-1));
    W_q = C / (c mu - lambda), L_q = lambda W_q, W = W_q + 1 / mu, L = lambda W.

    Source
    ------
    wikipedia2026mmcqueue, section 3 (Erlang C and the waiting time; read as an encyclopedia page)

    Validity
    --------
    Exponential times, one class, no steady state for lambda >= c mu (InputError naming arrival_rate).

    Knowledge rows
    --------------
    none
    """
    lam = as_scalar(as_checked(arrival_rate, "arrival_rate", lo=0, lo_open=True), "arrival_rate")
    mu = as_scalar(as_checked(service_rate, "service_rate", lo=0, lo_open=True), "service_rate")
    c = int(as_scalar(as_count(servers, "servers", hi=_MAX_SERVERS), "servers"))
    if lam >= c * mu:
        raise InputError(
            f"argument 'arrival_rate' ({lam!r}) must be below servers * service_rate ({c * mu!r}): no steady state",
            argument="arrival_rate",
        )
    a = lam / mu
    b = 1.0
    for k in range(1, c + 1):
        b = a * b / (k + a * b)
    rho = a / c
    erlang_c = b / (1 - rho * (1 - b))
    wait = erlang_c / (c * mu - lam)
    system_time = wait + 1 / mu
    return MMCResult(
        np.float64(rho),
        np.float64(erlang_c),
        np.float64(wait),
        np.float64(lam * wait),
        np.float64(system_time),
        np.float64(lam * system_time),
    )


def _log_terms(n: int, ratio: float) -> FloatArray:
    """log of the terms n!/(n-k)! ratio^k for k = 0..n."""
    steps = np.log(np.arange(n, 0, -1, dtype=np.float64)) + math.log(ratio)
    return np.concatenate(([0.0], np.cumsum(steps)))


def _log_sum_exp(values: FloatArray) -> float:
    top = float(np.max(values))
    return top + math.log(math.fsum(np.exp(values - top)))


def finite_source_queue(n_trucks: Any, travel_rate: Any, service_rate: Any) -> FiniteSourceResult:
    """Machine-repairman (finite-source) queue: one loader, N trucks, exponential times.

    Parameters
    ----------
    n_trucks : int [count]
        Number of trucks N, an integer from 1 to 100,000.
    travel_rate : float [1/s]
        Rate lambda at which a truck returns to the loader after being served, > 0.
    service_rate : float [1/s]
        Loader service rate mu, > 0.

    Returns
    -------
    FiniteSourceResult [s]
        Named result: idle_probability [1], utilisation [1], throughput [1/s], mean_at_loader [count],
        mean_time_at_loader [s].

    Equation
    --------
    pi_0 = [sum_(n=0..N) N! / (N - n)! (lambda / mu)^n]^-1; U = 1 - pi_0; X = mu U; L = N - X / lambda; L / X.

    Source
    ------
    sztrik2012basic, pp. 125-127 (section 3.2, the M/M/1/n/n queue)

    Validity
    --------
    Exponential times, one loader; evaluated in log space, without overflow up to 100,000 trucks.

    Knowledge rows
    --------------
    none
    """
    n = int(as_scalar(as_count(n_trucks, "n_trucks", hi=_MAX_TRUCKS), "n_trucks"))
    lam = as_scalar(as_checked(travel_rate, "travel_rate", lo=0, lo_open=True), "travel_rate")
    mu = as_scalar(as_checked(service_rate, "service_rate", lo=0, lo_open=True), "service_rate")
    logs = _log_terms(n, lam / mu)
    busy = _log_sum_exp(logs[1:])  # log of the sum over n >= 1; the n = 0 term is 1
    total = float(np.logaddexp(0.0, busy))
    idle = math.exp(-total)
    utilisation = math.exp(busy - total)
    throughput = mu * utilisation
    at_loader = n - throughput / lam
    return FiniteSourceResult(
        np.float64(idle),
        np.float64(utilisation),
        np.float64(throughput),
        np.float64(at_loader),
        np.float64(at_loader / throughput),
    )


def _vector(value: Any, name: str) -> FloatArray:
    arr = as_float_array(value, name)
    check_rank(arr, name, 1)
    check_finite(arr, name)
    check_size(arr, name, min_size=1, max_size=_MAX_STATIONS)
    return as_checked(arr, name, lo=0)


def mean_value_analysis(population: Any, service_time: Any, visit_ratio: Any, station_type: Any) -> MVAResult:
    """Exact single-class mean-value analysis of a closed product-form network.

    Parameters
    ----------
    population : int [count]
        Number of customers N (trucks), an integer from 1 to 100,000.
    service_time : array_like [s]
        Mean service time S_k of each station, >= 0; 1-D of length K, 1 to 1,000.
    visit_ratio : array_like [1]
        Visit ratio v_k of each station, >= 0; 1-D of length K.
    station_type : sequence of {"queue", "delay"}
        Kind of each station: a single-server queue or an infinite-server delay; length K.

    Returns
    -------
    MVAResult [1/s]
        Named result: throughput X(1..N) [1/s], and at n = N the residence_time W_k [s], queue_length L_k [count] and
        utilisation v_k X S_k [1], each of length K.

    Equation
    --------
    W_k(n) = S_k (1 + L_k(n-1)) for a queue and W_k = S_k for a delay; X(n) = n / sum_k v_k W_k(n);
    L_k(n) = v_k X(n) W_k(n).

    Source
    ------
    wikipedia2026mva, section 2 (the recursion; the delay-station extension is the standard one)

    Validity
    --------
    Product-form network, one customer class; the demands v_k S_k must not all be zero.

    Knowledge rows
    --------------
    none
    """
    n = int(as_scalar(as_count(population, "population", hi=_MAX_POPULATION), "population"))
    service = _vector(service_time, "service_time")
    visits = _vector(visit_ratio, "visit_ratio")
    if isinstance(station_type, str | bytes) or not isinstance(station_type, Sequence | np.ndarray):
        raise InputTypeError("argument 'station_type' must be a sequence of strings", argument="station_type")
    kinds = list(station_type)
    if len(kinds) > _MAX_STATIONS:
        raise InputError(
            f"argument 'station_type' allows at most {_MAX_STATIONS} stations, got {len(kinds)}",
            argument="station_type",
        )
    for kind in kinds:
        check_option(kind, "station_type", ("queue", "delay"))
    k = service.size
    for name, size in (("visit_ratio", visits.size), ("station_type", len(kinds))):
        if size != k:
            raise InputError(f"argument '{name}' has {size} entries but service_time has {k}", argument=name)
    demand = visits * service
    if not np.any(demand > 0):
        raise InputError("the demands visit_ratio * service_time are all zero", argument="service_time")
    queue = np.array([kind == "queue" for kind in kinds])
    throughput = np.empty(n, dtype=np.float64)
    length = np.zeros(k)
    residence = service.copy()
    for customers in range(1, n + 1):
        residence = np.where(queue, service * (1 + length), service)
        x = customers / float(np.dot(visits, residence))
        length = visits * x * residence
        throughput[customers - 1] = x
    return MVAResult(throughput, residence, length, visits * throughput[-1] * service)

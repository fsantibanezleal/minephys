"""T-005-030 (FR-005-19, FR-005-20, FR-005-21): first-order, Klimpel and cells-in-series flotation recovery.

Expected public API (`minephys.comminution`; k [1/s], t and tau [s], R_inf a fraction):
    flotation_first_order(r_inf, k, t)                -> R = R_inf (1 - exp(-k t))
    klimpel_recovery(r_inf, k, t)                     -> R = R_inf [1 - (1 - exp(-k t)) / (k t)], 0 at t = 0, no cancellation for small k t
    flotation_cell_recovery(r_inf, k, tau, n_cells=1) -> R = R_inf [1 - (1 + k tau)^(-N)]
Scalars give `numpy.float64`, arrays the broadcast float64 array (FR-000-07).

Oracles
- hand calculation (plan 005): k = 1/60 1/s, R_inf = 0.9, t = 300 s: first order 0.9 (1 - e^-5) = 0.893936; one cell with
  tau = 300 s: 0.9 * 5/6 = 0.75;
- quadrature (Klimpel's form is the mean of the first-order recovery over a uniform rate distribution on [0, k]): the
  trapezoid rule on 2e5 panels written in the test (0.721213 at k t = 5, R_inf = 0.9; agreement 1e-9);
- series for small u = k t: R_inf (u/2 - u^2/6 + u^3/24), truncation error below 1e-14 relative for u <= 1e-4, rtol 1e-12.
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest


def _c():
    return importlib.import_module("minephys.comminution")


@pytest.mark.req("FR-005-19")
@pytest.mark.oracle("hand-calculation", "R = R_inf (1 - exp(-k t)): 0.9 (1 - e^-5) = 0.893936")
def test_fr_005_19_first_order_hand_calculation() -> None:
    c = _c()
    got = c.flotation_first_order(0.9, 1.0 / 60.0, 300.0)
    np.testing.assert_allclose(got, 0.9 * (1.0 - math.exp(-5.0)), rtol=1e-12, atol=0)
    np.testing.assert_allclose(got, 0.893936, rtol=0, atol=6e-7)
    assert isinstance(got, np.float64)


@pytest.mark.req("FR-005-19")
def test_fr_005_19_first_order_limits_and_broadcasting() -> None:
    c = _c()
    assert c.flotation_first_order(0.8, 0.01, 0.0) == 0.0
    np.testing.assert_allclose(c.flotation_first_order(0.8, 0.01, 1e9), 0.8, rtol=1e-12)
    t = np.array([[0.0], [60.0], [600.0]])
    k = np.array([0.001, 0.01])
    out = c.flotation_first_order(0.95, k, t)
    assert out.shape == (3, 2) and out.dtype == np.float64
    np.testing.assert_allclose(out, 0.95 * (1.0 - np.exp(-k * t)), rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-20")
@pytest.mark.oracle("analytical", "Klimpel = mean of R_inf (1 - exp(-k' t)) over k' uniform on [0, k], by trapezoid quadrature")
@pytest.mark.parametrize("kt", [0.1, 1.0, 5.0, 20.0])
def test_fr_005_20_klimpel_equals_the_average_over_a_uniform_rate_distribution(kt: float) -> None:
    c = _c()
    r_inf, k = 0.9, 1.0 / 60.0
    t = kt / k
    kp = np.linspace(0.0, k, 200_001)  # 2e5 panels
    mean = np.trapezoid(r_inf * (1.0 - np.exp(-kp * t)), kp) / k
    got = c.klimpel_recovery(r_inf, k, t)
    np.testing.assert_allclose(got, mean, rtol=1e-9, atol=0)
    np.testing.assert_allclose(got, r_inf * (1.0 - (1.0 - math.exp(-kt)) / kt), rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-20")
@pytest.mark.oracle("hand-calculation", "plan 005: 0.721213 at k t = 5, R_inf = 0.9")
def test_fr_005_20_klimpel_printed_value() -> None:
    c = _c()
    np.testing.assert_allclose(c.klimpel_recovery(0.9, 1.0 / 60.0, 300.0), 0.721213, rtol=0, atol=6e-7)


@pytest.mark.req("FR-005-20")
def test_fr_005_20_klimpel_is_zero_at_zero_time() -> None:
    c = _c()
    assert c.klimpel_recovery(0.9, 0.02, 0.0) == 0.0
    out = c.klimpel_recovery(0.9, 0.02, np.array([0.0, 10.0]))
    assert out[0] == 0.0 and out[1] > 0.0


@pytest.mark.req("FR-005-20")
@pytest.mark.oracle("analytical", "series R_inf (u/2 - u^2/6 + u^3/24) for small u = k t (expm1, no cancellation)")
@pytest.mark.parametrize("u", [1e-12, 1e-10, 1e-8, 1e-6, 1e-5, 1e-4])
def test_fr_005_20_klimpel_small_argument_series(u: float) -> None:
    c = _c()
    r_inf, k = 0.7, 0.5
    got = c.klimpel_recovery(r_inf, k, u / k)
    series = r_inf * (u / 2.0 - u**2 / 6.0 + u**3 / 24.0)
    np.testing.assert_allclose(got, series, rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-21")
@pytest.mark.oracle("hand-calculation", "one cell, k tau = 5: R = R_inf k tau / (1 + k tau) = 0.75")
def test_fr_005_21_single_cell() -> None:
    c = _c()
    got = c.flotation_cell_recovery(0.9, 1.0 / 60.0, 300.0)
    np.testing.assert_allclose(got, 0.75, rtol=1e-12, atol=0)
    assert isinstance(got, np.float64)
    np.testing.assert_allclose(c.flotation_cell_recovery(0.9, 1.0 / 60.0, 300.0, n_cells=1), got, rtol=0, atol=0)


@pytest.mark.req("FR-005-21")
@pytest.mark.oracle("analytical", "N cells in series, each of residence time tau: R = R_inf [1 - (1 + k tau)^-N]")
@pytest.mark.parametrize("n_cells", [2, 3, 4, 8, 20])
def test_fr_005_21_cells_in_series(n_cells: int) -> None:
    c = _c()
    r_inf, k, tau = 0.9, 1.0 / 60.0, 45.0
    got = c.flotation_cell_recovery(r_inf, k, tau, n_cells=n_cells)
    np.testing.assert_allclose(got, r_inf * (1.0 - (1.0 + k * tau) ** (-n_cells)), rtol=1e-12, atol=0)
    # more cells always recover more
    assert got > c.flotation_cell_recovery(r_inf, k, tau, n_cells=n_cells - 1)


@pytest.mark.req("FR-005-21")
@pytest.mark.oracle("analytical", "cells in series approach the first-order law as N grows with total time fixed")
def test_fr_005_21_many_small_cells_approach_first_order() -> None:
    c = _c()
    r_inf, k, total = 0.9, 0.02, 100.0
    cells = [c.flotation_cell_recovery(r_inf, k, total / n, n_cells=n) for n in (1, 10, 100, 1000)]
    first = r_inf * (1.0 - math.exp(-k * total))
    errors = [abs(x - first) for x in cells]
    assert errors == sorted(errors, reverse=True)
    assert errors[-1] < 1e-3

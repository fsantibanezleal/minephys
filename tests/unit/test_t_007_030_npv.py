"""T-007-030 (FR-007-11): NPV of a cash-flow series.

Expected public API (`minephys.planning`):
    npv(cash_flows, rate, timing="end") -> sum_{t=1}^{T} CF_t / (1 + r)^t for "end" (period t, 0-based index t - 1, is discounted by
        (1 + r)^(t)), and sum_{t=0}^{T-1} CF_t / (1 + r)^t for "start"; `rate` is the discount rate per period (a scalar, r > -1).
`cash_flows` is a 1-D array; the result is a `numpy.float64`.

Oracles (hand calculation, plan 007)
- annuity formula: 100 per period for 3 periods at 10 % -> 100 (1 - 1.1^-3) / 0.1 = 248.685199;
- (-500, 200, 300, 400) at 8 % -> 240.666415 (end-of-period discounting);
- "start" discounting multiplies the "end" value by (1 + r).
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest


def _f():
    return importlib.import_module("minephys.planning").npv


@pytest.mark.req("FR-007-11")
@pytest.mark.oracle("analytical", "annuity: A (1 - (1 + r)^-T) / r = 248.685199")
def test_fr_007_11_annuity() -> None:
    got = _f()(np.full(3, 100.0), 0.10)
    np.testing.assert_allclose(got, 100.0 * (1.0 - 1.1**-3) / 0.1, rtol=1e-12, atol=0)
    np.testing.assert_allclose(got, 248.685199, rtol=0, atol=6e-7)
    assert isinstance(got, np.float64)
    longer = _f()(np.full(40, 7.5), 0.07)
    np.testing.assert_allclose(longer, 7.5 * (1.0 - 1.07**-40) / 0.07, rtol=1e-12, atol=0)


@pytest.mark.req("FR-007-11")
@pytest.mark.oracle("hand-calculation", "(-500, 200, 300, 400) at 8 %: -500/1.08 + 200/1.08^2 + 300/1.08^3 + 400/1.08^4 = 240.666415")
def test_fr_007_11_hand_series() -> None:
    cf = np.array([-500.0, 200.0, 300.0, 400.0])
    got = _f()(cf, 0.08)
    np.testing.assert_allclose(got, -500 / 1.08 + 200 / 1.08**2 + 300 / 1.08**3 + 400 / 1.08**4, rtol=1e-12, atol=0)
    np.testing.assert_allclose(got, 240.666415, rtol=0, atol=6e-7)


@pytest.mark.req("FR-007-11")
@pytest.mark.oracle("hand-calculation", "start-of-period discounting: sum CF_t / (1 + r)^t for t = 0 .. T - 1")
def test_fr_007_11_timing_start_and_end() -> None:
    f = _f()
    cf = np.array([-500.0, 200.0, 300.0, 400.0])
    start = f(cf, 0.08, timing="start")
    np.testing.assert_allclose(start, -500 + 200 / 1.08 + 300 / 1.08**2 + 400 / 1.08**3, rtol=1e-12, atol=0)
    np.testing.assert_allclose(start, 1.08 * f(cf, 0.08), rtol=1e-12, atol=0)
    assert f(cf, 0.08, "start") == start  # timing is the third positional argument
    np.testing.assert_allclose(f(cf, 0.08, timing="end"), f(cf, 0.08), rtol=0, atol=0)  # "end" is the default


@pytest.mark.req("FR-007-11")
def test_fr_007_11_special_rates_and_single_flows() -> None:
    f = _f()
    cf = np.array([10.0, -3.0, 4.0])
    assert f(cf, 0.0) == pytest.approx(11.0, rel=1e-15)  # at r = 0 the NPV is the sum
    assert f(np.array([250.0]), 0.25) == pytest.approx(200.0, rel=1e-13)
    assert f(np.array([250.0]), 0.25, timing="start") == pytest.approx(250.0, rel=1e-15)
    np.testing.assert_allclose(f(cf, -0.5), 10 / 0.5 - 3 / 0.25 + 4 / 0.125, rtol=1e-12)  # negative rates down to > -1 are valid
    assert f(np.zeros(5), 0.1) == 0.0


@pytest.mark.req("FR-007-11")
def test_fr_007_11_inputs_are_not_modified_and_integer_flows_are_accepted() -> None:
    f = _f()
    cf = np.array([100, 200, 300])
    before = cf.copy()
    got = f(cf, 0.1)
    assert np.array_equal(cf, before)
    np.testing.assert_allclose(got, 100 / 1.1 + 200 / 1.21 + 300 / 1.331, rtol=1e-12)

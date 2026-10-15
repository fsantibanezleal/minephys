"""T-007-030 (P-007-06): properties of the NPV.

Public API under test (`minephys.planning`): `npv(cash_flows, rate, timing="end")` (see tests/unit/test_t_007_030_npv.py).
Generators: 1 to 30 cash flows in [-1e3, 1e3] (non-negative variants for the monotonicity), discount rates in (-0.5, 1], 200 examples.

Relations (TC-1)
- linearity: npv(a CF + b CF') = a npv(CF) + b npv(CF');
- at r = 0 the NPV is the sum of the flows;
- for non-negative flows with at least one positive flow the NPV is strictly decreasing in r;
- delaying every flow by one period (prepending a zero) divides the NPV by (1 + r);
- "start" = (1 + r) x "end".
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
RATE = st.floats(-0.49, 1.0)
FLOWS = st.lists(st.floats(-1e3, 1e3), min_size=1, max_size=30).map(np.array)


def _f():
    return importlib.import_module("minephys.planning").npv


@pytest.mark.req("P-007-06")
@pytest.mark.oracle("analytical", "the NPV is a linear functional of the cash flows")
@CI
@given(cf=FLOWS, other=st.integers(0, 2**32 - 1), a=st.floats(-10.0, 10.0), b=st.floats(-10.0, 10.0), r=RATE)
def test_p_007_06_linearity(cf: np.ndarray, other: int, a: float, b: float, r: float) -> None:
    f = _f()
    cf2 = np.random.default_rng(other).uniform(-1e3, 1e3, len(cf))
    lhs = f(a * cf + b * cf2, r)
    rhs = a * f(cf, r) + b * f(cf2, r)
    magnitude = abs(a * f(cf, r)) + abs(b * f(cf2, r))  # cancellation between the two terms limits the relative accuracy
    np.testing.assert_allclose(lhs, rhs, rtol=1e-11, atol=1e-11 * magnitude + 1e-300)


@pytest.mark.req("P-007-06")
@CI
@given(cf=FLOWS)
def test_p_007_06_zero_rate_is_the_sum(cf: np.ndarray) -> None:
    np.testing.assert_allclose(_f()(cf, 0.0), cf.sum(), rtol=1e-12, atol=1e-9)


@pytest.mark.req("P-007-06")
@CI
@given(
    cf=st.lists(st.floats(0.0, 1e3), min_size=1, max_size=30).map(np.array),
    r1=st.floats(-0.49, 1.0),
    gap=st.floats(0.01, 0.5),
    k=st.integers(0, 29),
)
def test_p_007_06_strictly_decreasing_in_the_rate_for_non_negative_flows(cf: np.ndarray, r1: float, gap: float, k: int) -> None:
    f = _f()
    cf = cf.copy()
    cf[k % len(cf)] = max(cf[k % len(cf)], 1.0)  # at least one positive flow
    assert f(cf, r1 + gap) < f(cf, r1)


@pytest.mark.req("P-007-06")
@pytest.mark.oracle("analytical", "delaying every flow by one period divides the NPV by (1 + r)")
@CI
@given(cf=FLOWS, r=RATE)
def test_p_007_06_delay_and_timing_conventions(cf: np.ndarray, r: float) -> None:
    f = _f()
    delayed = np.r_[0.0, cf]
    magnitude = float(np.abs(cf) @ (1.0 + r) ** -(np.arange(len(cf)) + 1.0))  # sum of |CF_t| discounted: bounds the rounding
    np.testing.assert_allclose(f(delayed, r), f(cf, r) / (1.0 + r), rtol=1e-11, atol=1e-11 * magnitude)
    np.testing.assert_allclose(f(cf, r, "start"), (1.0 + r) * f(cf, r), rtol=1e-11, atol=1e-11 * magnitude * (1.0 + r))

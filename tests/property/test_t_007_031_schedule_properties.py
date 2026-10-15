"""T-007-031 (P-007-07): properties of the schedule NPV.

Public API under test (`minephys.planning`): `schedule_npv(periods, block_values, rate, ...) -> ScheduleNPV(npv, cash_flows)` and
`npv(cash_flows, rate, timing="end")` (see tests/unit/test_t_007_031_schedule_npv.py and test_t_007_030_npv.py).
Schedules: 1 to 30 blocks, periods in {-1, 0, ..., 5} with at least one mined block, integer-valued block values in [-50, 50],
rates in (-0.5, 1]; 200 examples.

Relations (TC-1)
- `schedule_npv` equals `npv` of its own cash-flow array, and the cash flows equal the per-period sums computed here;
- moving a block of positive value to a later period (no precedence arcs, so the move stays feasible) lowers the NPV for r > 0
  and raises it for r < 0 (strictly, and by exactly v (1/(1+r)^(t+2) - 1/(1+r)^(t+1)) when the array length is unchanged).
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
SEEDS = st.integers(0, 2**32 - 1)


def _p():
    return importlib.import_module("minephys.planning")


def schedule(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    periods = rng.integers(-1, 6, n)
    values = rng.integers(-50, 51, n).astype(np.float64)
    return periods, values


@pytest.mark.req("P-007-07")
@pytest.mark.oracle("analytical", "schedule_npv is npv applied to the per-period sums")
@CI
@given(n=st.integers(1, 30), seed=SEEDS, r=st.floats(-0.49, 1.0))
def test_p_007_07_schedule_npv_equals_npv_of_its_cash_flows(n: int, seed: int, r: float) -> None:
    p = _p()
    periods, values = schedule(n, seed)
    assume(periods.max() >= 0)
    res = p.schedule_npv(periods, values, r)
    expected = np.array([values[periods == t].sum() for t in range(int(periods.max()) + 1)])
    np.testing.assert_allclose(np.asarray(res.cash_flows), expected, rtol=1e-12, atol=1e-12)
    magnitude = float(np.abs(expected) @ (1.0 + r) ** -(np.arange(len(expected)) + 1.0))
    np.testing.assert_allclose(res.npv, p.npv(np.asarray(res.cash_flows), r), rtol=1e-12, atol=1e-12 * magnitude)


@pytest.mark.req("P-007-07")
@pytest.mark.oracle("analytical", "delaying a positive cash flow lowers its present value when r > 0")
@CI
@given(n=st.integers(2, 30), seed=SEEDS, r=st.floats(0.01, 1.0), pick=st.integers(0, 10_000))
def test_p_007_07_a_later_period_for_a_positive_block_lowers_the_npv(n: int, seed: int, r: float, pick: int) -> None:
    p = _p()
    periods, values = schedule(n, seed)
    candidates = np.flatnonzero((periods >= 0) & (periods < 5) & (values > 0))
    assume(len(candidates) > 0)
    k = int(candidates[pick % len(candidates)])
    later = periods.copy()
    later[k] += 1
    before, after = p.schedule_npv(periods, values, r), p.schedule_npv(later, values, r)
    assert after.npv < before.npv
    t = int(periods[k])
    expected_delta = values[k] * ((1.0 + r) ** -(t + 2) - (1.0 + r) ** -(t + 1))
    magnitude = float(np.abs(values).sum())
    np.testing.assert_allclose(after.npv - before.npv, expected_delta, rtol=1e-9, atol=1e-11 * magnitude)


@pytest.mark.req("P-007-07")
@CI
@given(n=st.integers(2, 30), seed=SEEDS, r=st.floats(-0.49, -0.01), pick=st.integers(0, 10_000))
def test_p_007_07_with_a_negative_rate_delay_raises_the_present_value(n: int, seed: int, r: float, pick: int) -> None:
    p = _p()
    periods, values = schedule(n, seed)
    candidates = np.flatnonzero((periods >= 0) & (periods < 5) & (values > 0))
    assume(len(candidates) > 0)
    k = int(candidates[pick % len(candidates)])
    later = periods.copy()
    later[k] += 1
    assert p.schedule_npv(later, values, r).npv > p.schedule_npv(periods, values, r).npv

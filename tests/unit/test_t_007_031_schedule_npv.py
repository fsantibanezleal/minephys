"""T-007-031 (FR-007-12): schedule NPV and cash-flow aggregation.

Expected public API (`minephys.planning`):
    schedule_npv(periods, block_values, rate, arcs=None, tonnage=None, capacities=None) -> ScheduleNPV(npv, cash_flows)
`periods` is an integer array (the period of each block, t >= 0, or -1 for "not mined"), `block_values` the value of each block,
`rate` the discount rate per period. `cash_flows` is the float64 array of per-period sums of the mined blocks' values (length
max(periods) + 1; blocks with period -1 contribute nothing) and `npv` the end-of-period NPV of that array. `capacities` (one entry
per period, same length as `cash_flows`) is compared with the per-period sum of `tonnage` (FR-007-13, tested separately).

Oracles (hand calculation)
- a 6-block schedule into 3 periods: periods (0, 0, 1, 1, 2, -1), values (10, 20, 30, -5, 40, 100): cash flows (30, 25, 40), the
  100-valued block is not mined; NPV at 10 % = 30/1.1 + 25/1.1^2 + 40/1.1^3 = 77.986476 (end-of-period discounting);
- at r = 0 the NPV is the sum of the values of the mined blocks.
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest


def _p():
    return importlib.import_module("minephys.planning")


PERIODS = np.array([0, 0, 1, 1, 2, -1])
VALUES = np.array([10.0, 20.0, 30.0, -5.0, 40.0, 100.0])


@pytest.mark.req("FR-007-12")
@pytest.mark.oracle("hand-calculation", "6 blocks in 3 periods: cash flows (30, 25, 40), NPV 77.986476 at 10 %")
def test_fr_007_12_hand_aggregation_and_npv() -> None:
    res = _p().schedule_npv(PERIODS, VALUES, 0.10)
    cash = np.asarray(res.cash_flows)
    assert cash.dtype == np.float64
    np.testing.assert_allclose(cash, [30.0, 25.0, 40.0], rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.npv, 30 / 1.1 + 25 / 1.1**2 + 40 / 1.1**3, rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.npv, 77.986476, rtol=0, atol=6e-7)
    assert isinstance(res.npv, np.float64)


@pytest.mark.req("FR-007-12")
def test_fr_007_12_unmined_blocks_never_contribute_and_empty_periods_are_zero() -> None:
    p = _p()
    res = p.schedule_npv(np.array([0, 3, 3, -1]), np.array([5.0, 7.0, 1.0, 1e9]), 0.0)
    np.testing.assert_allclose(res.cash_flows, [5.0, 0.0, 0.0, 8.0], rtol=0, atol=0)  # periods 1 and 2 are empty
    assert res.npv == pytest.approx(13.0, rel=1e-15)  # at r = 0 the NPV is the sum of the mined values


@pytest.mark.req("FR-007-12")
@pytest.mark.oracle("analytical", "annuity: three periods with the same cash flow")
def test_fr_007_12_constant_cash_flow_equals_the_annuity() -> None:
    p = _p()
    res = p.schedule_npv(np.array([0, 1, 2]), np.array([100.0, 100.0, 100.0]), 0.10)
    np.testing.assert_allclose(res.npv, 100.0 * (1.0 - 1.1**-3) / 0.1, rtol=1e-12, atol=0)


@pytest.mark.req("FR-007-12")
def test_fr_007_12_feasible_arcs_and_capacities_do_not_change_the_result() -> None:
    p = _p()
    plain = p.schedule_npv(PERIODS, VALUES, 0.10)
    arcs = np.array([[2, 0], [3, 2], [4, 3]], dtype=np.int64)  # each block requires one mined no later than itself
    tonnage = np.full(6, 1.0)
    capacities = np.array([2.0, 2.0, 1.0])
    checked = p.schedule_npv(PERIODS, VALUES, 0.10, arcs=arcs, tonnage=tonnage, capacities=capacities)
    assert checked.npv == plain.npv and np.array_equal(checked.cash_flows, plain.cash_flows)
    # blocks of the same period may require each other (an arc is violated only by a LATER requirement)
    same = p.schedule_npv(PERIODS, VALUES, 0.10, arcs=np.array([[1, 0], [3, 2]], dtype=np.int64))
    assert same.npv == plain.npv
    # a block that is not mined may require anything
    unmined = p.schedule_npv(PERIODS, VALUES, 0.10, arcs=np.array([[5, 4], [5, 0]], dtype=np.int64))
    assert unmined.npv == plain.npv


@pytest.mark.req("FR-007-12")
def test_fr_007_12_inputs_are_not_modified() -> None:
    p = _p()
    periods, values = PERIODS.copy(), VALUES.copy()
    p.schedule_npv(periods, values, 0.05)
    assert np.array_equal(periods, PERIODS) and np.array_equal(values, VALUES)

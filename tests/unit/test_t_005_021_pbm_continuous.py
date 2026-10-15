"""T-005-021 (FR-005-14): the continuous perfectly mixed mill with N tanks in series.

Expected public API (`minephys.comminution`):
    pbm_continuous_mill(feed, selection, breakage, residence_time, n_tanks=1) -> float64 array, shape (n,)
the steady-state product m_out = (I - (tau/N) A)^(-N) m_in of `n_tanks` equal perfectly mixed tanks in series with total
mean residence time tau [s], A = -diag(S) + B diag(S) (inputs as in `pbm_batch_grinding`; `feed` is the mass flow [kg/s]
or any consistent mass of the feed).

Oracles (analytical, hand-derived in plan 005 and re-derived here)
- one tank, tau = 120 s, mill S = (0.5, 0.3, 0)/60 1/s, b21 = 0.6, b31 = 0.4, b32 = 1, feed (1, 0, 0):
      m1 = 1/(1 + S1 tau) = 0.5,  m2 = b21 S1 tau m1 / (1 + S2 tau) = 0.1875,  m3 = 1 - m1 - m2 = 0.3125;
- N tanks: the first class is only depleted, so m1 = (1 + S1 tau / N)^(-N); the second class follows the same
  recursion tank by tank, written out in the test (sequential solve of one tank at a time);
- N -> infinity tends to the batch solution at t = tau (the three-class analytical solution of tests/unit/
  test_t_005_020_pbm_batch.py), error 1/N.
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest


def _c():
    return importlib.import_module("minephys.comminution")


S3 = np.array([0.5, 0.3, 0.0]) / 60.0
B3 = np.array([[0.0, 0.0, 0.0], [0.6, 0.0, 0.0], [0.4, 1.0, 0.0]])
F3 = np.array([1.0, 0.0, 0.0])


def _tanks_by_hand(feed: np.ndarray, tau: float, n_tanks: int) -> np.ndarray:
    """Tank-by-tank balance of the three-class mill: x_i (1 + S_i t) = in_i + sum_j b_ij S_j t x_j."""
    t = tau / n_tanks
    inflow = feed.astype(float)
    for _ in range(n_tanks):
        x1 = inflow[0] / (1.0 + S3[0] * t)
        x2 = (inflow[1] + 0.6 * S3[0] * t * x1) / (1.0 + S3[1] * t)
        x3 = inflow[2] + 0.4 * S3[0] * t * x1 + 1.0 * S3[1] * t * x2  # S3 = 0: no loss
        inflow = np.array([x1, x2, x3])
    return inflow


@pytest.mark.req("FR-005-14")
@pytest.mark.oracle("analytical", "one perfectly mixed tank, tau = 120 s: (0.5, 0.1875, 0.3125)")
def test_fr_005_14_single_tank_hand_solution() -> None:
    c = _c()
    out = c.pbm_continuous_mill(F3, S3, B3, 120.0)
    assert out.shape == (3,) and out.dtype == np.float64
    np.testing.assert_allclose(out, [0.5, 0.1875, 0.3125], rtol=1e-12, atol=1e-15)
    out_n1 = c.pbm_continuous_mill(F3, S3, B3, 120.0, n_tanks=1)
    assert np.array_equal(out, out_n1)  # n_tanks defaults to 1


@pytest.mark.req("FR-005-14")
@pytest.mark.oracle("analytical", "N tanks in series: m1 = (1 + S1 tau / N)^-N and the sequential tank balance")
@pytest.mark.parametrize("n_tanks", [2, 3, 5, 10, 50])
def test_fr_005_14_n_tanks_closed_forms(n_tanks: int) -> None:
    c = _c()
    tau = 120.0
    out = c.pbm_continuous_mill(F3, S3, B3, tau, n_tanks=n_tanks)
    np.testing.assert_allclose(out[0], (1.0 + S3[0] * tau / n_tanks) ** (-n_tanks), rtol=1e-12, atol=0)
    np.testing.assert_allclose(out, _tanks_by_hand(F3, tau, n_tanks), rtol=1e-11, atol=1e-15)
    np.testing.assert_allclose(out.sum(), 1.0, rtol=0, atol=1e-12)


@pytest.mark.req("FR-005-14")
@pytest.mark.oracle("analytical", "tank balance with a non-trivial feed, written out tank by tank")
def test_fr_005_14_general_feed_sequential_balance() -> None:
    c = _c()
    feed = np.array([0.5, 0.3, 0.2])
    out = c.pbm_continuous_mill(feed, S3, B3, 200.0, n_tanks=4)
    np.testing.assert_allclose(out, _tanks_by_hand(feed, 200.0, 4), rtol=1e-11, atol=1e-15)


@pytest.mark.req("FR-005-14")
@pytest.mark.oracle("analytical", "N -> infinity: the series of tanks tends to the batch solution at t = tau")
def test_fr_005_14_many_tanks_approach_the_batch_mill() -> None:
    c = _c()
    tau = 120.0
    m1 = math.exp(-S3[0] * tau)
    m2 = 0.6 * S3[0] / (S3[1] - S3[0]) * (math.exp(-S3[0] * tau) - math.exp(-S3[1] * tau))
    batch = np.array([m1, m2, 1.0 - m1 - m2])
    errors = [np.abs(c.pbm_continuous_mill(F3, S3, B3, tau, n_tanks=n) - batch).max() for n in (1, 10, 100, 1000)]
    assert errors == sorted(errors, reverse=True)
    assert errors[-1] < 1e-3


@pytest.mark.req("FR-005-14")
def test_fr_005_14_tiny_residence_time_returns_the_feed() -> None:
    c = _c()
    feed = np.array([0.5, 0.3, 0.2])
    out = c.pbm_continuous_mill(feed, S3, B3, 1e-9, n_tanks=3)
    np.testing.assert_allclose(out, feed, rtol=0, atol=1e-10)


@pytest.mark.req("FR-005-14")
def test_fr_005_14_inputs_unchanged_and_deterministic() -> None:
    c = _c()
    feed, s, b = np.array([0.2, 0.5, 0.3]), S3.copy(), B3.copy()
    before = [x.copy() for x in (feed, s, b)]
    a1 = c.pbm_continuous_mill(feed, s, b, 90.0, 4)
    a2 = c.pbm_continuous_mill(feed, s, b, 90.0, 4)
    assert np.array_equal(a1, a2)
    for x, y in zip((feed, s, b), before, strict=True):
        assert np.array_equal(x, y)

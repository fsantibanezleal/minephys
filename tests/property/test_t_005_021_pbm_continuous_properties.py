"""T-005-021 (P-005-06, P-005-09): property tests of `pbm_continuous_mill`.

Public API under test (`minephys.comminution`): `pbm_continuous_mill(feed, selection, breakage, residence_time,
n_tanks=1)` and `pbm_batch_grinding(mass, selection, breakage, times)` (as in tests/unit/test_t_005_020_pbm_batch.py
and tests/unit/test_t_005_021_pbm_continuous.py).

Relations
- P-005-06 (continuous half): sum(m_out) = sum(m_in);
- P-005-09: tau -> 0 returns the feed; as the number of tanks grows through N = 1, 2, 4, ..., 1,024 the product
  converges to the batch result at t = tau, the maximum-norm error being non-increasing and below 1e-3 x total at
  N = 1,024 (tau S_max <= 10);
- the exact first-class law m_out,1 = m_in,1 (1 + S_1 tau / N)^(-N) and linearity in the feed.
Mills are generated from a Hypothesis seed as in tests/property/test_t_005_020_pbm_batch_properties.py.
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
SEEDS = st.integers(0, 2**32 - 1)
SIZES = st.integers(2, 30)


def _c():
    return importlib.import_module("minephys.comminution")


def mill(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    s = 10.0 ** rng.uniform(-4.0, 0.0, n)
    s[-1] = 0.0
    b = np.zeros((n, n))
    for j in range(n - 1):
        w = rng.random(n - 1 - j) + 1e-3
        b[j + 1 :, j] = w / w.sum()
    m = rng.random(n) + 0.01
    return m, s, b


@pytest.mark.req("P-005-06")
@pytest.mark.oracle("analytical", "tank balances with column-stochastic breakage conserve the total mass")
@CI
@given(n=SIZES, seed=SEEDS, u=st.floats(1e-3, 1.0), tanks=st.integers(1, 40))
def test_p_005_06_continuous_conserves_mass(n: int, seed: int, u: float, tanks: int) -> None:
    c = _c()
    m, s, b = mill(n, seed)
    tau = u * 10.0 / s.max()
    out = c.pbm_continuous_mill(m, s, b, tau, tanks)
    assert abs(out.sum() - m.sum()) <= 1e-12 * m.sum()
    assert out.min() >= -1e-14 * m.sum()


@pytest.mark.req("P-005-09")
@pytest.mark.oracle("analytical", "tau -> 0 gives the feed; N -> infinity gives the batch mill at t = tau")
@CI
@given(n=SIZES, seed=SEEDS)
def test_p_005_09_vanishing_residence_time_returns_the_feed(n: int, seed: int) -> None:
    c = _c()
    m, s, b = mill(n, seed)
    out = c.pbm_continuous_mill(m, s, b, 1e-10 / s.max(), 3)
    np.testing.assert_allclose(out, m, rtol=0, atol=1e-8 * m.sum())


@pytest.mark.req("P-005-09")
@settings(max_examples=60, deadline=None)
@given(n=SIZES, seed=SEEDS, u=st.floats(0.05, 1.0))
def test_p_005_09_error_against_the_batch_mill_shrinks_with_the_number_of_tanks(n: int, seed: int, u: float) -> None:
    c = _c()
    m, s, b = mill(n, seed)
    tau = u * 10.0 / s.max()
    batch = c.pbm_batch_grinding(m, s, b, [tau])[0]
    total = m.sum()
    errors = [
        np.abs(c.pbm_continuous_mill(m, s, b, tau, 2**k) - batch).max() for k in range(0, 11)
    ]  # N = 1, 2, 4, ..., 1,024
    for before, after in zip(errors, errors[1:], strict=False):
        assert after <= before * (1.0 + 1e-9) + 1e-14 * total
    assert errors[-1] < 1e-3 * total


@pytest.mark.req("P-005-09")
@CI
@given(n=SIZES, seed=SEEDS, u=st.floats(1e-3, 1.0), tanks=st.integers(1, 30))
def test_first_class_closed_form(n: int, seed: int, u: float, tanks: int) -> None:
    c = _c()
    m, s, b = mill(n, seed)
    tau = u * 10.0 / s.max()
    out = c.pbm_continuous_mill(m, s, b, tau, tanks)
    np.testing.assert_allclose(out[0], m[0] * (1.0 + s[0] * tau / tanks) ** (-tanks), rtol=1e-11, atol=1e-15)


@pytest.mark.req("P-005-09")
@CI
@given(n=SIZES, seed=SEEDS, other=SEEDS, a=st.floats(0.0, 10.0), b_=st.floats(0.0, 10.0))
def test_linearity_in_the_feed(n: int, seed: int, other: int, a: float, b_: float) -> None:
    c = _c()
    m, s, b = mill(n, seed)
    m2 = np.random.default_rng(other).random(n)
    tau = 5.0 / s.max()
    combo = c.pbm_continuous_mill(a * m + b_ * m2, s, b, tau, 3)
    split = a * c.pbm_continuous_mill(m, s, b, tau, 3) + b_ * c.pbm_continuous_mill(m2, s, b, tau, 3)
    np.testing.assert_allclose(combo, split, rtol=1e-10, atol=1e-13 * (a * m.sum() + b_ * m2.sum() + 1e-300))

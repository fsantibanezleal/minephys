"""T-005-020 (P-005-06, P-005-07, P-005-08): property and metamorphic tests of `pbm_batch_grinding`.

Public API under test (`minephys.comminution`): `pbm_batch_grinding(mass, selection, breakage, times)` (see
tests/unit/test_t_005_020_pbm_batch.py). Mills are generated from a Hypothesis seed: 2 to 30 classes, selection rates
log-uniform in [1e-4, 1] 1/s with S_n = 0 (sink), strictly lower-triangular breakage with every column summing to 1,
class masses in (0, 1.01]; times satisfy S_max t <= 50 (the stated range of the matrix-exponential tolerances).

Relations: mass conservation and non-negativity (P-005-06), the semigroup property and linearity (P-005-07), the
exact decay of the top class and time-scale invariance (P-005-08). Tolerances: atol 1e-12 x total (mass), rtol 1e-10
with atol 1e-13 x total (semigroup, linearity).
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
@pytest.mark.oracle("analytical", "every column of B sums to 1, so sum(m) is invariant; masses stay non-negative")
@CI
@given(n=SIZES, seed=SEEDS, u=st.floats(0.0, 1.0))
def test_p_005_06_batch_conserves_mass_and_stays_non_negative(n: int, seed: int, u: float) -> None:
    c = _c()
    m, s, b = mill(n, seed)
    t = u * 50.0 / s.max()
    out = c.pbm_batch_grinding(m, s, b, [t])
    total = m.sum()
    assert abs(out.sum() - total) <= 1e-12 * total
    assert out.min() >= -1e-14 * total


@pytest.mark.req("P-005-07")
@pytest.mark.oracle("analytical", "exp(A(t1+t2)) = exp(A t2) exp(A t1)")
@CI
@given(n=SIZES, seed=SEEDS, u1=st.floats(0.0, 1.0), u2=st.floats(0.0, 1.0))
def test_p_005_07_semigroup(n: int, seed: int, u1: float, u2: float) -> None:
    c = _c()
    m, s, b = mill(n, seed)
    t1, t2 = u1 * 25.0 / s.max(), u2 * 25.0 / s.max()
    direct = c.pbm_batch_grinding(m, s, b, [t1 + t2])[0]
    first = c.pbm_batch_grinding(m, s, b, [t1])[0]
    twice = c.pbm_batch_grinding(first, s, b, [t2])[0]
    np.testing.assert_allclose(twice, direct, rtol=1e-10, atol=1e-13 * m.sum())


@pytest.mark.req("P-005-07")
@CI
@given(
    n=SIZES,
    seed=SEEDS,
    other=SEEDS,
    a=st.floats(0.0, 10.0),
    b_=st.floats(0.0, 10.0),
    u=st.floats(0.0, 1.0),
)
def test_p_005_07_linearity_in_the_initial_masses(n: int, seed: int, other: int, a: float, b_: float, u: float) -> None:
    c = _c()
    m, s, b = mill(n, seed)
    m2 = np.random.default_rng(other).random(n)
    t = u * 50.0 / s.max()
    combo = c.pbm_batch_grinding(a * m + b_ * m2, s, b, [t])[0]
    split = a * c.pbm_batch_grinding(m, s, b, [t])[0] + b_ * c.pbm_batch_grinding(m2, s, b, [t])[0]
    np.testing.assert_allclose(combo, split, rtol=1e-10, atol=1e-13 * (a * m.sum() + b_ * m2.sum() + 1e-300))


@pytest.mark.req("P-005-08")
@pytest.mark.oracle("analytical", "the coarsest class has no feed: dm1/dt = -S1 m1")
@CI
@given(n=SIZES, seed=SEEDS, u=st.floats(0.0, 1.0))
def test_p_005_08_top_class_decays_exactly(n: int, seed: int, u: float) -> None:
    c = _c()
    m, s, b = mill(n, seed)
    t = u * 50.0 / s.max()
    out = c.pbm_batch_grinding(m, s, b, [t])[0]
    np.testing.assert_allclose(out[0], m[0] * np.exp(-s[0] * t), rtol=1e-12, atol=1e-14 * m.sum())


@pytest.mark.req("P-005-08")
@pytest.mark.oracle("analytical", "scaling S by lambda and t by 1/lambda leaves A t, hence m, unchanged")
@CI
@given(n=SIZES, seed=SEEDS, u=st.floats(0.0, 1.0), lam=st.floats(1e-3, 1e3))
def test_p_005_08_time_scale_invariance(n: int, seed: int, u: float, lam: float) -> None:
    c = _c()
    m, s, b = mill(n, seed)
    t = u * 50.0 / s.max()
    base = c.pbm_batch_grinding(m, s, b, [t])[0]
    scaled = c.pbm_batch_grinding(m, lam * s, b, [t / lam])[0]
    np.testing.assert_allclose(scaled, base, rtol=1e-10, atol=1e-13 * m.sum())

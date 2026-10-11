"""T-005-042 (P-005-13): property and metamorphic tests of `crusher_matrix_model`.

Public API under test (`minephys.comminution`): `crusher_matrix_model(feed, classification, breakage)` (see
tests/unit/test_t_005_042_crusher.py). Crushers are generated from a Hypothesis seed: 2 to 40 classes, classification
probabilities in [0, 1] with c_n = 0 (the finest class cannot be broken), strictly lower-triangular breakage whose column j
sums to 1 wherever c_j > 0, feed masses in (0, 1.01].

Relations: mass conservation (TC-1), C = 0 returns the feed exactly (TC-0), linearity in the feed (TC-1), the coarsest class
leaves the product when c_1 = 1, the product is non-negative, and the balance residual
p - (I - C)(f + B C x) vanishes for the recovered internal flow x = f + B C x (checked through the identity
p = (I - C) x with x solving the triangular system by forward substitution written in the test).
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
SEEDS = st.integers(0, 2**32 - 1)
SIZES = st.integers(2, 40)


def _c():
    return importlib.import_module("minephys.comminution")


def crusher(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    cl = rng.random(n)
    cl[rng.random(n) < 0.2] = 0.0
    cl[-1] = 0.0
    b = np.zeros((n, n))
    for j in range(n - 1):
        w = rng.random(n - 1 - j) + 1e-3
        b[j + 1 :, j] = w / w.sum()
    f = rng.random(n) + 0.01
    return f, cl, b


def forward_substitution(f: np.ndarray, cl: np.ndarray, b: np.ndarray) -> np.ndarray:
    """x = f + B C x solved class by class from the coarsest (B is strictly lower triangular)."""
    n = len(f)
    x = np.zeros(n)
    for i in range(n):
        x[i] = f[i] + sum(b[i, j] * cl[j] * x[j] for j in range(i))
    return x


@pytest.mark.req("P-005-13")
@pytest.mark.oracle("analytical", "p = (I - C) x with x = f + B C x solved by forward substitution")
@CI
@given(n=SIZES, seed=SEEDS)
def test_p_005_13_matches_the_forward_substitution_balance(n: int, seed: int) -> None:
    c = _c()
    f, cl, b = crusher(n, seed)
    x = forward_substitution(f, cl, b)
    np.testing.assert_allclose(c.crusher_matrix_model(f, cl, b), (1.0 - cl) * x, rtol=1e-12, atol=1e-14)


@pytest.mark.req("P-005-13")
@CI
@given(n=SIZES, seed=SEEDS)
def test_p_005_13_conserves_mass_and_is_non_negative(n: int, seed: int) -> None:
    c = _c()
    f, cl, b = crusher(n, seed)
    p = c.crusher_matrix_model(f, cl, b)
    np.testing.assert_allclose(p.sum(), f.sum(), rtol=1e-12, atol=0)
    assert p.min() >= 0.0


@pytest.mark.req("P-005-13")
@CI
@given(n=SIZES, seed=SEEDS)
def test_p_005_13_zero_classification_returns_the_feed_exactly(n: int, seed: int) -> None:
    c = _c()
    f, _, b = crusher(n, seed)
    assert np.array_equal(c.crusher_matrix_model(f, np.zeros(n), b), f)  # TC-0


@pytest.mark.req("P-005-13")
@pytest.mark.oracle("analytical", "the crusher is a linear operator on the feed")
@CI
@given(n=SIZES, seed=SEEDS, other=SEEDS, a=st.floats(0.0, 10.0), b_=st.floats(0.0, 10.0))
def test_p_005_13_linear_in_the_feed(n: int, seed: int, other: int, a: float, b_: float) -> None:
    c = _c()
    f, cl, b = crusher(n, seed)
    f2 = np.random.default_rng(other).random(n)
    combo = c.crusher_matrix_model(a * f + b_ * f2, cl, b)
    split = a * c.crusher_matrix_model(f, cl, b) + b_ * c.crusher_matrix_model(f2, cl, b)
    np.testing.assert_allclose(combo, split, rtol=1e-12, atol=1e-13 * (a * f.sum() + b_ * f2.sum() + 1e-300))


@pytest.mark.req("P-005-13")
@CI
@given(n=SIZES, seed=SEEDS)
def test_p_005_13_certain_breakage_of_the_coarsest_class_empties_it(n: int, seed: int) -> None:
    c = _c()
    f, cl, b = crusher(n, seed)
    cl[0] = 1.0
    p = c.crusher_matrix_model(f, cl, b)
    assert p[0] == 0.0
    np.testing.assert_allclose(p.sum(), f.sum(), rtol=1e-12, atol=0)

"""T-005-022 (FR-005-16, FR-005-17): the Austin selection and breakage forms.

Expected public API (`minephys.comminution`):
    austin_selection(sizes, a, alpha, mu, lam, x0=None) -> float64 array of S_i [1/s]
        S_i = a (x_i / x0)^alpha / (1 + (x_i / mu)^lam), representative class sizes x_i [m]; x0=None reads the knowledge row
        `austin_reference_size` (1 mm) and then emits `minephys.knowledge.UnverifiedParameterWarning` (the row is UNVERIFIED,
        spec 008 FR-008-12);
    austin_breakage(sizes, phi, gamma, beta) -> (n, n) float64 strictly lower-triangular matrix b_ij
        b_ij = B_j(s_i) - B_j(s_{i+1}) for j < i < n, b_nj = B_j(s_n), B_j(s) = phi (s/s_{j+1})^gamma + (1-phi)(s/s_{j+1})^beta,
        s_1 > ... > s_n the upper class sizes [m]; every column j < n sums to 1 within 1e-12.

Oracles
- hand calculation of the written forms (spec 005 FR-005-16/17: the attribution to Austin is UNVERIFIED, so the oracle is
  the form itself, evaluated with plain Python loops below at three sizes);
- a pure hand case: phi = 1, gamma = 1 and sizes halving, s = (8, 4, 2, 1) mm, gives B_j(s) = s / s_{j+1} and the matrix
  [[0,0,0,0],[.5,0,0,0],[.25,.5,0,0],[.25,.5,1,0]] (telescoping);
- structural properties: strictly lower-triangular, non-negative, columns sum to 1 (Hypothesis).
"""

from __future__ import annotations

import importlib
import warnings

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


def _c():
    return importlib.import_module("minephys.comminution")


def _unverified_warning():
    importlib.import_module("minephys.comminution")
    from minephys.knowledge import UnverifiedParameterWarning

    return UnverifiedParameterWarning


@pytest.mark.req("FR-005-16")
@pytest.mark.oracle("hand-calculation", "S = a (x/x0)^alpha / (1 + (x/mu)^lam) evaluated size by size")
def test_fr_005_16_selection_hand_calculation() -> None:
    c = _c()
    sizes = [2.0e-3, 1.0e-3, 5.0e-4, 2.5e-4]
    a, alpha, mu, lam, x0 = 0.5, 1.2, 1.5e-3, 3.0, 1.0e-3
    got = c.austin_selection(np.array(sizes), a, alpha, mu, lam, x0=x0)
    expected = [a * (x / x0) ** alpha / (1.0 + (x / mu) ** lam) for x in sizes]
    assert got.shape == (4,) and got.dtype == np.float64
    np.testing.assert_allclose(got, expected, rtol=1e-12, atol=0)
    # at x = x0 = mu with lam = 2 the denominator is exactly 2: S = a / 2
    np.testing.assert_allclose(c.austin_selection(np.array([1e-3]), 0.8, 1.0, 1e-3, 2.0, x0=1e-3), [0.4], rtol=1e-12)


@pytest.mark.req("FR-005-16")
@pytest.mark.oracle("hand-calculation", "a = 0 gives zero rates; lam = 0 gives S = a (x/x0)^alpha / 2")
def test_fr_005_16_selection_special_cases() -> None:
    c = _c()
    sizes = np.array([4e-3, 2e-3, 1e-3])
    assert np.all(c.austin_selection(sizes, 0.0, 1.0, 1e-3, 2.0, x0=1e-3) == 0.0)
    got = c.austin_selection(sizes, 0.6, 0.9, 2e-3, 0.0, x0=1e-3)
    np.testing.assert_allclose(got, 0.6 * (sizes / 1e-3) ** 0.9 / 2.0, rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-16")
@pytest.mark.knowledge("austin_reference_size")
def test_fr_005_16_default_reference_size_is_the_unverified_row_and_warns() -> None:
    c = _c()
    warning = _unverified_warning()
    sizes = np.array([2e-3, 1e-3, 5e-4])
    with pytest.warns(warning) as rec:
        got = c.austin_selection(sizes, 0.5, 1.2, 1.5e-3, 3.0)
    explicit = c.austin_selection(sizes, 0.5, 1.2, 1.5e-3, 3.0, x0=1e-3)
    np.testing.assert_allclose(got, explicit, rtol=1e-12, atol=0)
    text = " ".join(str(r.message) for r in rec)
    assert "austin_reference_size" in text


@pytest.mark.req("FR-005-16")
def test_fr_005_16_explicit_reference_size_does_not_warn() -> None:
    c = _c()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        c.austin_selection(np.array([2e-3, 1e-3]), 0.5, 1.2, 1.5e-3, 3.0, x0=1e-3)


@pytest.mark.req("FR-005-17")
@pytest.mark.oracle("hand-calculation", "phi = 1, gamma = 1, sizes halving: B_j(s) = s/s_{j+1}, telescoping matrix")
def test_fr_005_17_pure_hand_matrix() -> None:
    c = _c()
    s = np.array([8.0, 4.0, 2.0, 1.0]) * 1e-3
    b = c.austin_breakage(s, 1.0, 1.0, 2.0)  # beta is multiplied by (1 - phi) = 0
    expected = np.array(
        [
            [0.0, 0.0, 0.0, 0.0],
            [0.5, 0.0, 0.0, 0.0],
            [0.25, 0.5, 0.0, 0.0],
            [0.25, 0.5, 1.0, 0.0],
        ]
    )
    assert b.shape == (4, 4) and b.dtype == np.float64
    np.testing.assert_allclose(b, expected, rtol=1e-12, atol=1e-15)


@pytest.mark.req("FR-005-17")
@pytest.mark.oracle("hand-calculation", "b_ij = B_j(s_i) - B_j(s_{i+1}), b_nj = B_j(s_n), written as loops")
def test_fr_005_17_breakage_hand_calculation_and_structure() -> None:
    c = _c()
    s = [4e-3, 2e-3, 1e-3, 5e-4, 2.5e-4]
    phi, gamma, beta = 0.35, 0.75, 3.2
    got = c.austin_breakage(np.array(s), phi, gamma, beta)

    def cum(j: int, x: float) -> float:
        r = x / s[j + 1]
        return phi * r**gamma + (1.0 - phi) * r**beta

    n = len(s)
    expected = np.zeros((n, n))
    for j in range(n - 1):
        for i in range(j + 1, n):
            expected[i, j] = cum(j, s[i]) - cum(j, s[i + 1]) if i < n - 1 else cum(j, s[i])
    np.testing.assert_allclose(got, expected, rtol=1e-12, atol=1e-15)
    assert np.all(np.triu(got) == 0.0)  # strictly lower triangular, last column zero
    np.testing.assert_allclose(got[:, : n - 1].sum(axis=0), 1.0, rtol=0, atol=1e-12)
    assert np.all(got >= 0.0)


@pytest.mark.req("FR-005-17")
def test_fr_005_17_two_class_breakage_sends_everything_to_the_fine_class() -> None:
    c = _c()
    b = c.austin_breakage(np.array([2e-3, 1e-3]), 0.4, 0.8, 2.5)
    np.testing.assert_allclose(b, [[0.0, 0.0], [1.0, 0.0]], rtol=0, atol=1e-12)


@pytest.mark.req("FR-005-17")
@pytest.mark.oracle("analytical", "the cumulative form telescopes: every column j < n sums to 1")
@settings(max_examples=200, deadline=None)
@given(
    n=st.integers(2, 30),
    ratio=st.floats(1.1, 4.0),
    phi=st.floats(1e-3, 1.0),
    gamma=st.floats(0.1, 3.0),
    beta=st.floats(0.5, 8.0),
)
def test_fr_005_17_columns_sum_to_one_and_matrix_is_strictly_lower_triangular(
    n: int, ratio: float, phi: float, gamma: float, beta: float
) -> None:
    c = _c()
    s = 0.05 / ratio ** np.arange(n)
    b = c.austin_breakage(s, phi, gamma, beta)
    assert b.shape == (n, n)
    assert np.all(np.triu(b) == 0.0)
    assert np.all(b >= -1e-15)
    np.testing.assert_allclose(b[:, : n - 1].sum(axis=0), 1.0, rtol=0, atol=1e-12)

"""T-005-042 (FR-005-27, FR-005-28): the steady-state crusher matrix model and the classification function.

Expected public API (`minephys.comminution`; sizes in m):
    crusher_matrix_model(feed, classification, breakage) -> product masses p = (I - C)(I - B C)^-1 f, float64 array (n,)
        `classification` = diagonal of C (probabilities c_i in [0, 1] of a class-i particle being broken), `breakage` = strictly
        lower-triangular B whose column j (with c_j > 0) sums to 1; total mass is conserved within rtol 1e-12.
    whiten_classification(sizes, k1, k2, k3)             -> c(x) = 0 (x < k1); 1 - ((k2 - x)/(k2 - k1))^k3 (k1 <= x < k2); 1 (x >= k2)

Oracles (spec 005 section 7: the attribution to Whiten (1972) is UNVERIFIED, so the oracle is the steady-state balance itself)
- hand calculation of the sequential balance x = f + B C x, p = (I - C) x for f = (0.6, 0.3, 0.1), c = (0.8, 0.4, 0),
  b21 = 0.7, b31 = 0.3, b32 = 1:  x1 = 0.6, x2 = 0.3 + 0.7 (0.8 x 0.6) = 0.636, x3 = 0.1 + 0.3 (0.8 x 0.6) + 0.4 x 0.636 = 0.4984,
  p = (1 - c) x = (0.12, 0.3816, 0.4984), the plan's printed values;
- two classes with c_1 = 0.5 and everything breaking into class 2: p = (0.5, 0.5);
- Whiten's form at the midpoint with k3 = 2 gives 1 - 0.5^2 = 0.75; at k1 it is 0 and at k2 it is 1.
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest


def _c():
    return importlib.import_module("minephys.comminution")


F3 = np.array([0.6, 0.3, 0.1])
C3 = np.array([0.8, 0.4, 0.0])
B3 = np.array([[0.0, 0.0, 0.0], [0.7, 0.0, 0.0], [0.3, 1.0, 0.0]])


@pytest.mark.req("FR-005-27")
@pytest.mark.oracle("hand-calculation", "sequential steady-state balance of the plan: p = (0.12, 0.3816, 0.4984)")
def test_fr_005_27_three_class_hand_balance() -> None:
    c = _c()
    # sequential balance written out: class 1 has no feed from above, then each class receives what finer-bound breakage sends
    x1 = 0.6
    broken1 = 0.8 * x1  # 0.48
    x2 = 0.3 + 0.7 * broken1  # 0.636
    broken2 = 0.4 * x2  # 0.2544
    x3 = 0.1 + 0.3 * broken1 + 1.0 * broken2  # 0.4984
    expected = np.array([(1 - 0.8) * x1, (1 - 0.4) * x2, (1 - 0.0) * x3])
    assert expected == pytest.approx([0.12, 0.3816, 0.4984], abs=1e-15)
    p = c.crusher_matrix_model(F3, C3, B3)
    assert p.shape == (3,) and p.dtype == np.float64
    np.testing.assert_allclose(p, expected, rtol=1e-12, atol=1e-15)
    np.testing.assert_allclose(p.sum(), F3.sum(), rtol=1e-12, atol=0)  # mass conservation


@pytest.mark.req("FR-005-27")
@pytest.mark.oracle("hand-calculation", "two classes, c_1 = 0.5, all broken mass to class 2: (0.5, 0.5)")
def test_fr_005_27_two_class_case() -> None:
    c = _c()
    p = c.crusher_matrix_model(np.array([1.0, 0.0]), np.array([0.5, 0.0]), np.array([[0.0, 0.0], [1.0, 0.0]]))
    np.testing.assert_allclose(p, [0.5, 0.5], rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-27")
@pytest.mark.oracle("analytical", "C = 0 passes the feed unchanged (exactly); c_1 = 1 removes the coarsest class from the product")
def test_fr_005_27_limits() -> None:
    c = _c()
    p0 = c.crusher_matrix_model(F3, np.zeros(3), B3)
    assert np.array_equal(p0, F3)  # TC-0
    p1 = c.crusher_matrix_model(F3, np.array([1.0, 0.0, 0.0]), B3)
    assert p1[0] == 0.0
    np.testing.assert_allclose(p1.sum(), 1.0, rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-27")
@pytest.mark.oracle("analytical", "cascade: material broken out of class 1 can be broken again in class 2")
def test_fr_005_27_cascade_of_two_breakages() -> None:
    """Three classes, b21 = 1 and b32 = 1; c1 = c2 = 0.5.  Class 2 receives 0.5 x1 and breaks half of it into class 3."""
    c = _c()
    f = np.array([1.0, 0.0, 0.0])
    p = c.crusher_matrix_model(f, np.array([0.5, 0.5, 0.0]), np.array([[0, 0, 0], [1.0, 0, 0], [0, 1.0, 0]]))
    x1 = 1.0
    x2 = 0.5 * x1
    x3 = 0.5 * x2
    np.testing.assert_allclose(p, [0.5 * x1, 0.5 * x2, x3], rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-27")
def test_fr_005_27_inputs_not_modified_and_deterministic() -> None:
    c = _c()
    f, cl, b = F3.copy(), C3.copy(), B3.copy()
    a = c.crusher_matrix_model(f, cl, b)
    assert np.array_equal(a, c.crusher_matrix_model(f, cl, b))
    assert np.array_equal(f, F3) and np.array_equal(cl, C3) and np.array_equal(b, B3)


@pytest.mark.req("FR-005-28")
@pytest.mark.oracle("hand-calculation", "c(x) = 1 - ((k2 - x)/(k2 - k1))^k3 between k1 and k2; 0.75 at the midpoint for k3 = 2")
def test_fr_005_28_whiten_classification() -> None:
    c = _c()
    k1, k2 = 0.02, 0.10
    sizes = np.array([0.001, 0.02, 0.04, 0.06, 0.0999999, 0.10, 0.5])
    got = c.whiten_classification(sizes, k1, k2, 2.0)
    expected = []
    for x in sizes:
        if x < k1:
            expected.append(0.0)
        elif x < k2:
            expected.append(1.0 - ((k2 - x) / (k2 - k1)) ** 2.0)
        else:
            expected.append(1.0)
    assert got.shape == sizes.shape and got.dtype == np.float64
    np.testing.assert_allclose(got, expected, rtol=1e-12, atol=1e-15)
    assert c.whiten_classification(np.array([(k1 + k2) / 2.0]), k1, k2, 2.0)[0] == pytest.approx(0.75, rel=1e-12)
    assert c.whiten_classification(np.array([k1]), k1, k2, 2.0)[0] == 0.0
    assert c.whiten_classification(np.array([k2]), k1, k2, 2.0)[0] == 1.0


@pytest.mark.req("FR-005-28")
def test_fr_005_28_exponent_and_scalar_input() -> None:
    c = _c()
    k1, k2, x = 0.01, 0.09, 0.05
    for k3 in (0.5, 1.0, 3.0):
        got = c.whiten_classification(x, k1, k2, k3)
        assert isinstance(got, np.float64)
        np.testing.assert_allclose(got, 1.0 - ((k2 - x) / (k2 - k1)) ** k3, rtol=1e-12, atol=0)
    # c is non-decreasing in size and stays in [0, 1]
    xs = np.linspace(0.0005, 0.2, 400)
    cs = c.whiten_classification(xs, k1, k2, 2.5)
    assert np.all(np.diff(cs) >= 0.0) and cs.min() >= 0.0 and cs.max() <= 1.0

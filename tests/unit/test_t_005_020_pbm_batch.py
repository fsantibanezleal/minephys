"""T-005-020 (FR-005-13): batch grinding against analytical solutions and a Runge-Kutta reference.

Expected public API (`minephys.comminution`):
    pbm_batch_grinding(mass, selection, breakage, times) -> float64 array, shape (len(times), n)
with classes ordered coarse to fine, `mass` the class masses at t = 0 [kg], `selection` S_i [1/s], `breakage` the
n x n strictly lower-triangular matrix b_ij (fraction of broken class-j material entering finer class i) and `times` a
1-D array of non-negative instants [s]. The result row k is m(t_k) = expm(A t_k) m(0) with
A = -diag(S) + B diag(S) (FR-005-13); the order of `times` is preserved.

Oracles (all independent of the code under test)
- analytical solution of the three-class batch grinding equation (Reid 1965, `reid1965batch`; derived by hand in
  plan 005): for S1 != S2, S3 = 0, input (1, 0, 0), b21 = 0.6, b31 = 0.4, b32 = 1:
      m1 = e^{-S1 t},  m2 = b21 S1 / (S2 - S1) (e^{-S1 t} - e^{-S2 t}),  m3 = 1 - m1 - m2;
  with the numbers S = (0.5, 0.3, 0)/60 1/s the plan prints 60, 120, 300 s values (6 decimals) that are also pinned;
- repeated selection values (S1 = S2 = S): m1 = e^{-St}, m2 = b21 S t e^{-St} (confluent case, where an
  eigen-decomposition of A fails);
- fixed-step classical Runge-Kutta (RK4) integration of dm/dt = A m written in the test, step 1e-3 / S_max (TC-5:
  rtol 1e-6) on seeded random mills with 8 classes.
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
M3 = np.array([1.0, 0.0, 0.0])


def _analytic3(t: float, s1: float, s2: float) -> np.ndarray:
    m1 = math.exp(-s1 * t)
    m2 = 0.6 * s1 / (s2 - s1) * (math.exp(-s1 * t) - math.exp(-s2 * t))
    return np.array([m1, m2, 1.0 - m1 - m2])


def _rk4(selection: np.ndarray, breakage: np.ndarray, m0: np.ndarray, t: float) -> np.ndarray:
    a = -np.diag(selection) + breakage @ np.diag(selection)
    h0 = 1e-3 / float(selection.max())
    steps = max(1, math.ceil(t / h0))
    h = t / steps
    m = m0.astype(float).copy()
    for _ in range(steps):
        k1 = a @ m
        k2 = a @ (m + 0.5 * h * k1)
        k3 = a @ (m + 0.5 * h * k2)
        k4 = a @ (m + h * k3)
        m = m + h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    return m


def _random_mill(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    s = 10.0 ** rng.uniform(-3, -1, n)
    s[-1] = 0.0
    b = np.zeros((n, n))
    for j in range(n - 1):
        w = rng.random(n - 1 - j) + 1e-3
        b[j + 1 :, j] = w / w.sum()
    m = rng.random(n) + 0.01
    return m, s, b


@pytest.mark.req("FR-005-13")
@pytest.mark.oracle("analytical", "reid1965batch three-class batch grinding equation solved by hand (plan 005)")
def test_fr_005_13_three_class_analytical_solution() -> None:
    c = _c()
    times = np.array([60.0, 120.0, 300.0])
    out = c.pbm_batch_grinding(M3, S3, B3, times)
    assert out.shape == (3, 3) and out.dtype == np.float64
    for k, t in enumerate(times):
        np.testing.assert_allclose(out[k], _analytic3(t, S3[0], S3[1]), rtol=1e-10, atol=1e-13)


@pytest.mark.req("FR-005-13")
@pytest.mark.oracle("hand-calculation", "plan 005 printed values at 60, 120 and 300 s")
def test_fr_005_13_printed_values_of_the_plan() -> None:
    c = _c()
    out = c.pbm_batch_grinding(M3, S3, B3, [60.0, 120.0, 300.0])
    printed = np.array(
        [
            [0.606531, 0.201431, 0.192038],
            [0.367879, 0.271398, 0.360722],
            [0.082085, 0.211568, 0.706347],
        ]
    )
    np.testing.assert_allclose(out, printed, rtol=0, atol=6e-7)


@pytest.mark.req("FR-005-13")
@pytest.mark.oracle("analytical", "confluent case S1 = S2: m2 = b21 S t exp(-S t) m1(0)")
def test_fr_005_13_repeated_selection_values() -> None:
    c = _c()
    s = np.array([0.01, 0.01, 0.0])
    times = np.array([0.0, 30.0, 100.0, 250.0, 700.0])
    out = c.pbm_batch_grinding(M3, s, B3, times)
    for k, t in enumerate(times):
        m1 = math.exp(-0.01 * t)
        m2 = 0.6 * 0.01 * t * math.exp(-0.01 * t)
        np.testing.assert_allclose(out[k], [m1, m2, 1.0 - m1 - m2], rtol=1e-10, atol=1e-13)


@pytest.mark.req("FR-005-13")
def test_fr_005_13_time_zero_returns_the_initial_masses_and_order_is_preserved() -> None:
    c = _c()
    m0 = np.array([0.5, 0.3, 0.2])
    out = c.pbm_batch_grinding(m0, S3, B3, [0.0])
    np.testing.assert_allclose(out[0], m0, rtol=1e-13, atol=1e-15)
    forward = c.pbm_batch_grinding(M3, S3, B3, [60.0, 120.0, 300.0])
    shuffled = c.pbm_batch_grinding(M3, S3, B3, [300.0, 60.0, 120.0])
    np.testing.assert_allclose(shuffled, forward[[2, 0, 1]], rtol=1e-12, atol=1e-15)


@pytest.mark.req("FR-005-13")
@pytest.mark.oracle("reference-implementation", "classical fixed-step Runge-Kutta (RK4) integration of dm/dt = A m written in the test")
@pytest.mark.parametrize("seed", [3, 11, 2026])
def test_fr_005_13_matches_runge_kutta_on_random_mills(seed: int) -> None:
    c = _c()
    m, s, b = _random_mill(8, seed)
    times = np.array([0.5 / s.max(), 2.0 / s.max(), 5.0 / s.max()])
    out = c.pbm_batch_grinding(m, s, b, times)
    total = m.sum()
    for k, t in enumerate(times):
        np.testing.assert_allclose(out[k], _rk4(s, b, m, float(t)), rtol=1e-6, atol=1e-9 * total)


@pytest.mark.req("FR-005-13")
@pytest.mark.oracle("analytical", "class 1 is only depleted: m1(t) = m1(0) exp(-S1 t) for any breakage")
def test_fr_005_13_top_class_decays_exponentially_in_a_larger_mill() -> None:
    c = _c()
    m, s, b = _random_mill(12, 7)
    times = np.array([0.0, 1.0, 10.0, 50.0]) / s.max()  # S_max t <= 50: the stated range of the matrix exponential
    out = c.pbm_batch_grinding(m, s, b, times)
    np.testing.assert_allclose(out[:, 0], m[0] * np.exp(-s[0] * times), rtol=1e-10, atol=1e-14)


@pytest.mark.req("FR-005-13")
def test_fr_005_13_mass_is_conserved_and_all_classes_stay_non_negative() -> None:
    c = _c()
    m, s, b = _random_mill(20, 99)
    times = np.linspace(0.0, 50.0 / s.max(), 7)
    out = c.pbm_batch_grinding(m, s, b, times)
    np.testing.assert_allclose(out.sum(axis=1), m.sum(), rtol=0, atol=1e-12 * m.sum())
    assert out.min() >= -1e-14 * m.sum()


@pytest.mark.req("FR-005-13")
def test_fr_005_13_inputs_are_not_modified_and_result_is_deterministic() -> None:
    c = _c()
    m, s, b = _random_mill(6, 5)
    t = np.array([10.0, 20.0])
    copies = [x.copy() for x in (m, s, b, t)]
    first = c.pbm_batch_grinding(m, s, b, t)
    second = c.pbm_batch_grinding(m, s, b, t)
    assert np.array_equal(first, second)
    for x, y in zip((m, s, b, t), copies, strict=True):
        assert np.array_equal(x, y)

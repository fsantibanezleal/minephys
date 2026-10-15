"""T-007-022 (P-007-04, FR-007-06): properties of the nested pits.

Public API under test (`minephys.planning`): `nested_pits(tonnage, grade, price, selling_cost, recovery, processing_cost,
mining_cost, arcs, revenue_factors)` -> one boolean mask per factor (see tests/unit/test_t_007_022_nested_pits.py).
Instances: random acyclic precedence on up to 12 blocks (i requires j < i), tonnages 1 to 5 x 1e4 kg, grades in [0, 0.05], price 10,
selling cost 2, recovery 0.85, processing cost in [0, 0.02], mining cost in [1e-4, 5e-3] per kg, revenue factors in [0, 2]; 200 examples.

Relations
- P-007-04 nesting: for lambda_1 <= lambda_2, pit(lambda_1) is contained in pit(lambda_2); pit(0) is empty when every block has a
  positive mining cost;
- FR-007-06 oracle: each mask equals the smallest optimal closure found by exhaustive enumeration for the values
  v_i(lambda) = max(T_i [lambda g_i y (p - s_r) - c_p], 0) - T_i c_m written out in the test (real values; exact ties have
  probability zero for these continuous generators).
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
SEEDS = st.integers(0, 2**32 - 1)


def _f():
    return importlib.import_module("minephys.planning").nested_pits


def instance(n: int, seed: int, density: float):
    rng = np.random.default_rng(seed)
    arcs = np.array([(i, j) for i in range(n) for j in range(i) if rng.random() < density], dtype=np.int64).reshape(-1, 2)
    tonnage = rng.integers(1, 6, n) * 1.0e4
    grade = rng.uniform(0.0, 0.05, n)
    cp, cm = rng.uniform(0.0, 0.02), rng.uniform(1e-4, 5e-3)
    return tonnage, grade, cp, cm, arcs


def block_values(tonnage, grade, cp, cm, lam):
    return np.maximum(tonnage * (lam * grade * 0.85 * (10.0 - 2.0) - cp), 0.0) - tonnage * cm


def exhaustive_mask(values: np.ndarray, arcs: np.ndarray) -> np.ndarray:
    n = len(values)
    masks = ((np.arange(1 << n)[:, None] >> np.arange(n)) & 1).astype(bool)
    closed = np.ones(1 << n, dtype=bool)
    for i, j in arcs:
        closed &= ~masks[:, i] | masks[:, j]
    totals = masks.astype(np.float64) @ values
    totals[~closed] = -np.inf
    return masks[totals == totals.max()].all(axis=0)


def run(n: int, seed: int, density: float, lams: np.ndarray):
    tonnage, grade, cp, cm, arcs = instance(n, seed, density)
    out = _f()(tonnage, grade, 10.0, 2.0, 0.85, cp, cm, arcs, lams)
    return np.asarray(out, dtype=bool), (tonnage, grade, cp, cm, arcs)


@pytest.mark.req("P-007-04")
@pytest.mark.oracle("analytical", "v_i(lambda) is non-decreasing in lambda, so the smallest optimal closures are nested")
@CI
@given(n=st.integers(1, 40), seed=SEEDS, density=st.floats(0.0, 0.3), lams=st.lists(st.floats(0.0, 2.0), min_size=2, max_size=8))
def test_p_007_04_pits_are_nested(n: int, seed: int, density: float, lams: list[float]) -> None:
    lams_sorted = np.sort(np.array(lams))
    masks, _ = run(n, seed, density, lams_sorted)
    assert masks.shape == (len(lams_sorted), n)
    for smaller, larger in zip(masks, masks[1:], strict=False):
        assert np.all(larger[smaller])  # pit(lambda_1) is a subset of pit(lambda_2)


@pytest.mark.req("P-007-04")
@CI
@given(n=st.integers(1, 40), seed=SEEDS, density=st.floats(0.0, 0.3))
def test_p_007_04_the_zero_revenue_factor_gives_an_empty_pit(n: int, seed: int, density: float) -> None:
    masks, _ = run(n, seed, density, np.array([0.0]))
    assert not masks[0].any()


@pytest.mark.req("FR-007-06")
@pytest.mark.oracle("reference-implementation", "exhaustive enumeration on the hand-computed values v_i(lambda)")
@CI
@given(n=st.integers(1, 12), seed=SEEDS, density=st.floats(0.0, 0.5), lams=st.lists(st.floats(0.0, 2.0), min_size=1, max_size=4))
def test_fr_007_06_masks_equal_the_enumerated_pits(n: int, seed: int, density: float, lams: list[float]) -> None:
    masks, (tonnage, grade, cp, cm, arcs) = run(n, seed, density, np.array(lams))
    for lam, got in zip(lams, masks, strict=True):
        expected = exhaustive_mask(block_values(tonnage, grade, cp, cm, lam), arcs)
        assert np.array_equal(got, expected), f"lambda = {lam}"

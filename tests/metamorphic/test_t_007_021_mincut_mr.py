"""T-007-021 (P-007-03): metamorphic relations of the min-cut pit.

Public API under test (`minephys.planning`): `ultimate_pit_mincut(values, arcs) -> UltimatePit(mask, value)` (see
tests/unit/test_t_007_021_mincut.py). Instances: random acyclic precedence (i requires j < i) on 2 to 60 blocks, integer values in
[-50, 50], 200 examples; exact (TC-0) comparisons because every partial sum is an integer below 2^53.

Relations
- scaling all values by an integer lambda >= 1 leaves the pit unchanged and scales its value by lambda;
- adding delta > 0 to one block's value never removes a block from the pit (the smallest optimal closure grows with the values);
- raising the mining cost (lowering the values of the blocks by non-negative amounts) never adds a block;
- relabelling the blocks by a permutation (arcs relabelled accordingly) permutes the mask and keeps the value.
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
    return importlib.import_module("minephys.planning").ultimate_pit_mincut


def instance(n: int, seed: int, density: float) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    arcs = [(i, j) for i in range(n) for j in range(i) if rng.random() < density]
    values = rng.integers(-50, 51, n).astype(np.float64)
    return values, np.array(arcs, dtype=np.int64).reshape(-1, 2)


@pytest.mark.req("P-007-03")
@pytest.mark.oracle("analytical", "the optimum closure is invariant to positive scaling of the objective")
@CI
@given(n=st.integers(2, 60), seed=SEEDS, density=st.floats(0.0, 0.3), lam=st.integers(1, 20))
def test_p_007_03_scaling(n: int, seed: int, density: float, lam: int) -> None:
    f = _f()
    values, arcs = instance(n, seed, density)
    base, scaled = f(values, arcs), f(lam * values, arcs)
    assert np.array_equal(base.mask, scaled.mask)
    assert float(scaled.value) == lam * float(base.value)


@pytest.mark.req("P-007-03")
@pytest.mark.oracle("analytical", "monotone comparative statics: the smallest optimal closure is non-decreasing in the values")
@CI
@given(n=st.integers(2, 60), seed=SEEDS, density=st.floats(0.0, 0.3), k=st.integers(0, 10_000), delta=st.integers(1, 200))
def test_p_007_03_raising_one_value_never_removes_a_block(n: int, seed: int, density: float, k: int, delta: int) -> None:
    f = _f()
    values, arcs = instance(n, seed, density)
    raised = values.copy()
    raised[k % n] += delta
    before, after = np.asarray(f(values, arcs).mask), np.asarray(f(raised, arcs).mask)
    assert np.all(after[before])  # before is a subset of after


@pytest.mark.req("P-007-03")
@CI
@given(n=st.integers(2, 60), seed=SEEDS, density=st.floats(0.0, 0.3), cost=st.integers(0, 30))
def test_p_007_03_raising_the_mining_cost_never_adds_a_block(n: int, seed: int, density: float, cost: int) -> None:
    f = _f()
    values, arcs = instance(n, seed, density)
    tonnage = np.random.default_rng(seed + 5).integers(1, 4, n).astype(np.float64)
    costlier = values - cost * tonnage  # every block loses cost x tonnage
    before, after = np.asarray(f(values, arcs).mask), np.asarray(f(costlier, arcs).mask)
    assert np.all(before[after])  # after is a subset of before


@pytest.mark.req("P-007-03")
@pytest.mark.oracle("analytical", "relabelling the blocks permutes the mask")
@CI
@given(n=st.integers(2, 60), seed=SEEDS, density=st.floats(0.0, 0.3))
def test_p_007_03_permutation_equivariance(n: int, seed: int, density: float) -> None:
    f = _f()
    values, arcs = instance(n, seed, density)
    perm = np.random.default_rng(seed + 11).permutation(n)  # block i becomes block perm[i]
    new_values = np.empty_like(values)
    new_values[perm] = values
    new_arcs = perm[arcs] if len(arcs) else arcs
    base, moved = f(values, arcs), f(new_values, new_arcs)
    expected = np.empty(n, dtype=bool)
    expected[perm] = np.asarray(base.mask)
    assert np.array_equal(np.asarray(moved.mask), expected)
    assert float(moved.value) == float(base.value)

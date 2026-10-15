"""T-007-012 (P-007-05): properties of the strip ratio.

Public API under test (`minephys.planning`): `strip_ratio(pit, tonnage, is_ore)` (see tests/unit/test_t_007_012_strip_ratio.py).
Generators: 2 to 40 blocks with tonnage log-uniform in [1e3, 1e8] kg, random ore labels and pit masks that contain ore;
200 examples.

Relations (TC-1)
- invariance to scaling every tonnage by lambda;
- swapping the ore and waste labels gives the reciprocal ratio (when the swapped selection has ore as well);
- for disjoint pushbacks the total ratio is (W1 + W2) / (O1 + O2).
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
SEEDS = st.integers(0, 2**32 - 1)


def _f():
    return importlib.import_module("minephys.planning").strip_ratio


def blocks(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    tonnage = np.exp(rng.uniform(math.log(1e3), math.log(1e8), n))
    is_ore = rng.random(n) < 0.5
    pit = rng.random(n) < 0.7
    return tonnage, is_ore, pit


@pytest.mark.req("P-007-05")
@pytest.mark.oracle("analytical", "the ratio is homogeneous of degree 0 in the tonnage")
@CI
@given(n=st.integers(2, 40), seed=SEEDS, lam=st.floats(math.log(1e-3), math.log(1e3)).map(math.exp))
def test_p_007_05_invariance_to_the_tonnage_scale(n: int, seed: int, lam: float) -> None:
    f = _f()
    tonnage, is_ore, pit = blocks(n, seed)
    assume(np.any(pit & is_ore))
    np.testing.assert_allclose(f(pit, lam * tonnage, is_ore), f(pit, tonnage, is_ore), rtol=1e-12, atol=0)


@pytest.mark.req("P-007-05")
@pytest.mark.oracle("analytical", "swapping ore and waste gives 1/SR")
@CI
@given(n=st.integers(2, 40), seed=SEEDS)
def test_p_007_05_swapping_labels_gives_the_reciprocal(n: int, seed: int) -> None:
    f = _f()
    tonnage, is_ore, pit = blocks(n, seed)
    assume(np.any(pit & is_ore) and np.any(pit & ~is_ore))
    np.testing.assert_allclose(f(pit, tonnage, ~is_ore), 1.0 / f(pit, tonnage, is_ore), rtol=1e-12, atol=0)


@pytest.mark.req("P-007-05")
@pytest.mark.oracle("analytical", "(W1 + W2) / (O1 + O2) for disjoint pushbacks")
@CI
@given(n=st.integers(4, 40), seed=SEEDS)
def test_p_007_05_disjoint_pushbacks_combine_by_their_tonnages(n: int, seed: int) -> None:
    f = _f()
    tonnage, is_ore, _ = blocks(n, seed)
    owner = np.random.default_rng(seed + 1).integers(0, 3, n)  # 0: neither, 1: pushback 1, 2: pushback 2
    p1, p2 = owner == 1, owner == 2
    assume(np.any(p1 & is_ore) and np.any(p2 & is_ore))
    w1, o1 = tonnage[p1 & ~is_ore].sum(), tonnage[p1 & is_ore].sum()
    w2, o2 = tonnage[p2 & ~is_ore].sum(), tonnage[p2 & is_ore].sum()
    np.testing.assert_allclose(f(p1, tonnage, is_ore), w1 / o1, rtol=1e-12, atol=0)
    np.testing.assert_allclose(f(p1 | p2, tonnage, is_ore), (w1 + w2) / (o1 + o2), rtol=1e-12, atol=0)

"""T-007-021 (FR-007-04, FR-007-05): the min-cut ultimate pit on the worked example and small hand cases.

Expected public API (`minephys.planning`):
    ultimate_pit_mincut(values, arcs) -> UltimatePit(mask, value)
`values` [currency] per block (length n, 1 <= n <= 100,000), `arcs` an int64 (m, 2) array of (i, j) = "mining i requires j" (m <= 2e6);
`mask` is a boolean array of length n and `value` the sum of the values of the selected blocks (`numpy.float64`). The pit is the
SMALLEST maximum-weight closed set: the source side, reachable from s in the residual network, of the minimum cut of the network
s -> i (capacity v_i for v_i > 0), i -> t (capacity -v_i for v_i < 0), i -> j (infinite) for every arc.

Oracles
- the worked example of the PitStudio planning theory (spec 007 plan): three waste blocks of value -1 (a, b, c) over one ore block
  d with arcs (d, a), (d, b), (d, c): v_d = 5 -> the whole pit, value 2; v_d = 2 -> empty pit, value 0; v_d = 3 -> a tie between the
  empty pit and the whole pit, and the SMALLEST optimal pit (empty) is returned;
- hand cases on a few blocks (independent chains, a shared waste block, a waste block that pays for two ore blocks);
- exhaustive enumeration and `networkx` in tests/property/test_t_007_021_mincut_oracles.py.
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest


def _f():
    return importlib.import_module("minephys.planning").ultimate_pit_mincut


A_BCD = np.array([[3, 0], [3, 1], [3, 2]], dtype=np.int64)


@pytest.mark.req("FR-007-04")
@pytest.mark.oracle("hand-calculation", "PitStudio planning theory: three waste blocks over one ore block")
@pytest.mark.parametrize(
    ("vd", "mask", "value"),
    [
        (5.0, [True, True, True, True], 2.0),  # pays for the stripping
        (2.0, [False, False, False, False], 0.0),  # does not
        (3.0, [False, False, False, False], 0.0),  # tie: the smallest optimal pit is empty
        (3.0000001, [True, True, True, True], 3.0000001 - 3.0),
        (1e6, [True, True, True, True], 1e6 - 3.0),
    ],
)
def test_fr_007_04_worked_example(vd: float, mask: list[bool], value: float) -> None:
    res = _f()(np.array([-1.0, -1.0, -1.0, vd]), A_BCD)
    assert np.array_equal(np.asarray(res.mask), mask)
    assert np.asarray(res.mask).dtype == np.bool_
    assert float(res.value) == pytest.approx(value, rel=1e-12, abs=1e-12)
    assert isinstance(res.value, np.float64)


@pytest.mark.req("FR-007-04")
@pytest.mark.oracle("hand-calculation", "no precedence: the pit is exactly the blocks of positive value")
def test_fr_007_04_without_arcs_only_positive_blocks_are_mined() -> None:
    res = _f()(np.array([3.0, -2.0, 0.0, 7.0, -0.5, 0.0]), np.empty((0, 2), dtype=np.int64))
    assert np.array_equal(res.mask, [True, False, False, True, False, False])  # zero-value blocks are left out (smallest pit)
    assert float(res.value) == 10.0


@pytest.mark.req("FR-007-04")
@pytest.mark.oracle("hand-calculation", "a shared waste block paid for by two ore blocks, and a chain of dependencies")
def test_fr_007_04_hand_cases() -> None:
    f = _f()
    # blocks: 0 waste (-5) is required by 1 and 2 (ore +3 each): 3 + 3 - 5 = 1 > 0 -> mine all three
    res = f(np.array([-5.0, 3.0, 3.0]), np.array([[1, 0], [2, 0]], dtype=np.int64))
    assert np.array_equal(res.mask, [True, True, True]) and float(res.value) == 1.0
    # with +2 each: 2 + 2 - 5 = -1 < 0 -> mine nothing
    res = f(np.array([-5.0, 2.0, 2.0]), np.array([[1, 0], [2, 0]], dtype=np.int64))
    assert np.array_equal(res.mask, [False, False, False]) and float(res.value) == 0.0
    # chain 3 -> 2 -> 1 -> 0 with values (-4, -4, -4, +15): 15 - 12 = 3 > 0
    chain = np.array([[3, 2], [2, 1], [1, 0]], dtype=np.int64)
    res = f(np.array([-4.0, -4.0, -4.0, 15.0]), chain)
    assert np.array_equal(res.mask, [True, True, True, True]) and float(res.value) == 3.0
    # an ore block on top of the chain is mined alone when it needs nothing
    res = f(np.array([6.0, -4.0, -4.0, 5.0]), chain)
    assert np.array_equal(res.mask, [True, False, False, False]) and float(res.value) == 6.0
    # two independent pits: only the profitable one is selected
    res = f(np.array([-1.0, 4.0, -9.0, 5.0]), np.array([[1, 0], [3, 2]], dtype=np.int64))
    assert np.array_equal(res.mask, [True, True, False, False]) and float(res.value) == 3.0


@pytest.mark.req("FR-007-04")
def test_fr_007_04_closure_includes_everything_a_mined_block_requires() -> None:
    res = _f()(np.array([-1.0, -1.0, -1.0, 9.0]), np.array([[3, 2], [2, 1], [1, 0]], dtype=np.int64))
    assert np.array_equal(res.mask, [True, True, True, True])  # 9 - 3 = 6
    res = _f()(np.array([-1.0, -1.0, 0.0, 9.0]), np.array([[3, 2], [2, 1], [1, 0]], dtype=np.int64))
    assert np.array_equal(res.mask, [True, True, True, True])  # the zero-value block 2 is required by block 3


@pytest.mark.req("FR-007-05")
@pytest.mark.oracle("analytical", "integer values: exact mask and value; integer dtype and float dtype give the same answer")
def test_fr_007_05_integer_values_are_exact_for_every_dtype() -> None:
    f = _f()
    v = np.array([-3, -2, 8, -1, 4, -6, 2])
    arcs = np.array([[2, 0], [2, 1], [4, 3], [4, 1], [6, 5], [6, 4]], dtype=np.int64)
    ref = f(v.astype(np.float64), arcs)
    for dtype in (np.int64, np.int32, np.float32, np.float64):
        res = f(v.astype(dtype), arcs)
        assert np.array_equal(res.mask, ref.mask) and float(res.value) == float(ref.value)
    # {0, 1, 2}: 8 - 3 - 2 = 3; adding {3, 4} (block 4 needs 1 and 3): + 4 - 1 = +3 -> 6; adding {5, 6}: 2 - 6 = -4 (rejected)
    assert np.array_equal(ref.mask, [True, True, True, True, True, False, False]) and float(ref.value) == 6.0


@pytest.mark.req("FR-007-05")
def test_fr_007_05_real_values_agree_within_the_stated_tolerance() -> None:
    f = _f()
    v = np.array([-1.25, -0.75, 2.5, -0.5, 1.0, -3.3333333333, 4.0])
    arcs = np.array([[2, 0], [2, 1], [4, 3], [6, 5], [6, 4]], dtype=np.int64)
    res = f(v, arcs)
    expected = (v[2] + v[0] + v[1])  # {0, 1, 2} = 0.5
    # candidates: {0,1,2}: 0.5; {3,4}: 0.5; {3,4,5,6}: 1.0 - 0.5 - 3.3333333333 + 4 = 1.1666666667 -> best
    best = max(expected, v[3] + v[4], v[3] + v[4] + v[5] + v[6], expected + v[3] + v[4] + v[5] + v[6])
    assert float(res.value) == pytest.approx(best, abs=1e-9 * np.abs(v).sum())


@pytest.mark.req("FR-007-04")
def test_fr_007_04_inputs_are_not_modified_and_the_result_is_deterministic() -> None:
    f = _f()
    v = np.array([-1.0, -1.0, -1.0, 5.0])
    a = A_BCD.copy()
    v0, a0 = v.copy(), a.copy()
    r1, r2 = f(v, a), f(v, a)
    assert np.array_equal(r1.mask, r2.mask) and r1.value == r2.value
    assert np.array_equal(v, v0) and np.array_equal(a, a0)

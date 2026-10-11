"""T-007-022 (FR-007-06): nested pits over revenue factors.

Expected public API (`minephys.planning`):
    nested_pits(tonnage, grade, price, selling_cost, recovery, processing_cost, mining_cost, arcs, revenue_factors)
        -> one boolean pit mask per revenue factor lambda (a sequence of masks of length len(revenue_factors); the tests iterate it
           and stack the masks with `numpy.asarray`), each the FR-007-04 pit for
           v_i(lambda) = max(T_i [lambda g_i y (p - s_r) - c_p], 0) - T_i c_m.
`tonnage` and `grade` are per-block arrays; the economic arguments are scalars; `arcs` as in `ultimate_pit_mincut`.

Oracles
- the worked example of the PitStudio planning theory (spec 007 plan) as inputs: unit tonnages, c_p = 0, c_m = 1, grade 0 for a, b, c
  and g y (p - s_r) = 6 for d (g = 1, y = 1, p - s_r = 6), so v_d(lambda) = 6 lambda - 1 and v_a = v_b = v_c = -1: the pit is empty for
  lambda <= 2/3 (at 2/3 the full pit ties at value 0 and the smallest pit is empty) and full for lambda > 2/3;
- exhaustive enumeration of the closed subsets applied to the hand-computed values v_i(lambda) (tests/property/
  test_t_007_022_nested_properties.py);
- P-007-04: nestedness and pit(0) = empty.
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest


def _f():
    return importlib.import_module("minephys.planning").nested_pits


ARCS = np.array([[3, 0], [3, 1], [3, 2]], dtype=np.int64)
FACTORS = [0.0, 0.5, 2.0 / 3.0, 0.7, 1.0, 2.0]


def _call(factors=FACTORS):
    return _f()(
        tonnage=np.ones(4),
        grade=np.array([0.0, 0.0, 0.0, 1.0]),
        price=7.0,
        selling_cost=1.0,
        recovery=1.0,
        processing_cost=0.0,
        mining_cost=1.0,
        arcs=ARCS,
        revenue_factors=np.asarray(factors),
    )


@pytest.mark.req("FR-007-06")
@pytest.mark.oracle("worked-example", "PitStudio planning theory: v_d(lambda) = 6 lambda - 1, pit empty up to lambda = 2/3, full beyond")
def test_fr_007_06_worked_example() -> None:
    masks = [np.asarray(m, dtype=bool) for m in _call()]
    assert len(masks) == len(FACTORS)
    empty, full = np.zeros(4, dtype=bool), np.ones(4, dtype=bool)
    expected = [empty, empty, empty, full, full, full]  # lambda = 2/3 is the tie: the smallest pit is empty
    for lam, got, want in zip(FACTORS, masks, expected, strict=True):
        assert np.array_equal(got, want), f"lambda = {lam}"


@pytest.mark.req("FR-007-06")
def test_fr_007_06_the_zero_factor_pit_is_empty_and_masks_nest() -> None:
    masks = np.asarray(_call([2.0, 0.0, 1.0, 0.5]), dtype=bool)  # factors need not be sorted
    assert masks.shape == (4, 4)
    assert not masks[1].any()  # lambda = 0
    assert masks[0].all() and masks[2].all() and not masks[3].any()  # in the order given: 2 -> full, 1 -> full, 0.5 -> empty


@pytest.mark.req("FR-007-06")
@pytest.mark.oracle("hand-calculation", "single revenue factor, values written out: v = max(T [lambda g y (p - s_r) - c_p], 0) - T c_m")
def test_fr_007_06_values_use_the_revenue_factor_inside_the_processing_margin() -> None:
    f = _f()
    # two independent blocks: grade 0.02 (ore at lambda = 1) and 0.004 (waste at lambda = 1, ore at lambda = 3)
    kwargs = dict(
        tonnage=np.array([1.0e4, 1.0e4]),
        grade=np.array([0.02, 0.004]),
        price=10.0,
        selling_cost=2.0,
        recovery=0.85,
        processing_cost=0.02,
        mining_cost=0.001,
        arcs=np.empty((0, 2), dtype=np.int64),
    )
    # margin per kg = lambda g y (p - s_r) - c_p: block 1: 0.136 lambda - 0.02, block 2: 0.0272 lambda - 0.02;
    # value = 1e4 x max(margin, 0) - 1e4 x 0.001, positive iff margin > 0.001: block 1 for lambda > 0.1544, block 2 for lambda > 0.7721
    masks = np.asarray(f(revenue_factors=np.array([0.1, 0.2, 0.7, 0.8, 3.0]), **kwargs), dtype=bool)
    assert masks.tolist() == [[False, False], [True, False], [True, False], [True, True], [True, True]]

@pytest.mark.req("FR-007-06")
def test_fr_007_06_arrays_of_factors_of_any_length_and_inputs_not_modified() -> None:
    f = _f()
    factors = np.linspace(0.0, 2.0, 21)
    arcs = ARCS.copy()
    masks = np.asarray(
        f(np.ones(4), np.array([0.0, 0.0, 0.0, 1.0]), 7.0, 1.0, 1.0, 0.0, 1.0, arcs, factors), dtype=bool
    )
    assert masks.shape == (21, 4)
    assert np.array_equal(arcs, ARCS) and factors[0] == 0.0 and factors[-1] == 2.0
    # monotone in lambda: once the full pit appears it stays
    assert np.all(np.diff(masks.sum(axis=1)) >= 0)
    assert masks[6].tolist() == [False] * 4 and masks[7].tolist() == [True] * 4  # 6 x 0.6 - 1 = 2.6 < 3 ; 6 x 0.7 - 1 = 3.2 > 3

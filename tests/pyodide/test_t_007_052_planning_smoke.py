"""T-007-052 (NFR-007-03, FR-000-25): one worked-example oracle per function family in the Pyodide smoke subset.

Marked `pyodide`: the CI Pyodide job runs these tests inside Pyodide; they are excluded from the CPython wheel run by
`-m "not gpu and not pyodide and not kit"` (FR-000-24) and also run unchanged on CPython (`pytest -m pyodide`).
One hand-derived value per family (API as in the unit tests of T-007-010 to T-007-042):
- block value and cut-off: the ore block 56,000 and g_be = 1.470588e-3 (plan 007 hand values);
- precedence and pit: a 3 x 3 x 2 "1-5" grid has 33 arcs; the worked example (three waste blocks of -1 under an ore block of 5)
  gives the whole pit of value 2, and with 3 the tie resolves to the empty pit (smallest optimal closure);
- nested pits: v_d(lambda) = 6 lambda - 1 gives an empty pit at lambda = 0.5 and the full pit at lambda = 1;
- strip ratio: 3,000 t of waste over 1,000 t of ore = 3;
- NPV: the annuity 248.685199 and the 6-block schedule 77.986476;
- Lane: g_m = 2.777778e-4 and g_c = 1.111111e-3 on the single-bin histogram.
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest

pytestmark = [pytest.mark.pyodide, pytest.mark.req("NFR-007-03")]


def _p():
    return importlib.import_module("minephys.planning")


ARCS = np.array([[3, 0], [3, 1], [3, 2]], dtype=np.int64)


@pytest.mark.oracle("hand-calculation", "plan 007: ore block 56,000 and g_be = 1.470588e-3")
def test_nfr_007_03_block_value_family() -> None:
    p = _p()
    assert p.block_economic_value(1e6, 0.01, 10.0, 2.0, 0.85, 0.01, 0.002).value == pytest.approx(56_000.0, rel=1e-9)
    assert p.breakeven_cutoff_grade(0.01, 10.0, 2.0, 0.85) == pytest.approx(1.470588e-3, abs=6e-10)


@pytest.mark.oracle("worked-example", "PitStudio planning theory: three waste blocks over one ore block")
def test_nfr_007_03_precedence_and_min_cut_family() -> None:
    p = _p()
    assert p.regular_grid_precedence((3, 3, 2)).shape == (33, 2)
    whole = p.ultimate_pit_mincut(np.array([-1.0, -1.0, -1.0, 5.0]), ARCS)
    assert np.asarray(whole.mask).all() and float(whole.value) == 2.0
    tie = p.ultimate_pit_mincut(np.array([-1.0, -1.0, -1.0, 3.0]), ARCS)
    assert not np.asarray(tie.mask).any() and float(tie.value) == 0.0


@pytest.mark.oracle("worked-example", "v_d(lambda) = 6 lambda - 1")
def test_nfr_007_03_nested_pits_family() -> None:
    p = _p()
    masks = np.asarray(
        p.nested_pits(np.ones(4), np.array([0.0, 0.0, 0.0, 1.0]), 7.0, 1.0, 1.0, 0.0, 1.0, ARCS, np.array([0.5, 1.0])), dtype=bool
    )
    assert not masks[0].any() and masks[1].all()


@pytest.mark.oracle("worked-example", "3,000 t waste over 1,000 t ore")
def test_nfr_007_03_strip_ratio_family() -> None:
    p = _p()
    assert p.strip_ratio(np.ones(4, dtype=bool), np.full(4, 1e6), np.array([False, False, False, True])) == pytest.approx(3.0)


@pytest.mark.oracle("analytical", "annuity 248.685199; 6-block schedule 77.986476")
def test_nfr_007_03_npv_family() -> None:
    p = _p()
    assert p.npv(np.full(3, 100.0), 0.10) == pytest.approx(248.685199, abs=6e-7)
    res = p.schedule_npv(np.array([0, 0, 1, 1, 2, -1]), np.array([10.0, 20.0, 30.0, -5.0, 40.0, 100.0]), 0.10)
    assert res.npv == pytest.approx(77.986476, abs=6e-7)


@pytest.mark.oracle("analytical", "plan 007: g_m = 2.777778e-4, g_c = 1.111111e-3 on the single-bin histogram")
def test_nfr_007_03_lane_family() -> None:
    res = _p().lane_cutoff_grades(
        grade_edges=np.array([0.0, 0.01]),
        tonnage=np.array([1.0e6]),
        price=10_000.0,
        selling_cost=2_000.0,
        recovery=0.9,
        processing_cost=2.0,
        mining_cost=0.5,
        fixed_cost=300.0,
        mine_capacity=100.0,
        plant_capacity=50.0,
        market_capacity=1e9,
    )
    assert res.g_m == pytest.approx(2.777778e-4, abs=6e-11) and res.g_c == pytest.approx(1.111111e-3, abs=6e-10)

"""T-007-012 (FR-007-09): strip ratio of pits and pushbacks.

Expected public API (`minephys.planning`):
    strip_ratio(pit, tonnage, is_ore) -> sum of the waste tonnage / sum of the ore tonnage of the blocks selected by the boolean mask
        `pit` (t/t, dimensionless); a pushback's incremental ratio is the strip ratio of `outer & ~inner`.
`tonnage` is a float array [kg], `is_ore` a boolean mask. Returns `numpy.float64`.

Oracle: the worked example of the PitStudio planning theory (spec 007 plan): three waste blocks of 1,000 t over one ore block of
1,000 t, pit = {a, b, c, d}: 3,000 / 1,000 = 3; and hand calculations of pushbacks written out below.
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest


def _p():
    return importlib.import_module("minephys.planning")


@pytest.mark.req("FR-007-09")
@pytest.mark.oracle("worked-example", "plan 007: three waste blocks over one ore block of 1,000 t each: strip ratio 3")
def test_fr_007_09_worked_example() -> None:
    p = _p()
    tonnage = np.full(4, 1.0e6)  # 1,000 t in kg
    is_ore = np.array([False, False, False, True])
    got = p.strip_ratio(np.ones(4, dtype=bool), tonnage, is_ore)
    assert got == pytest.approx(3.0, rel=1e-12)
    assert isinstance(got, np.float64)
    # a pit without the waste blocks has no stripping, but it must contain ore
    assert p.strip_ratio(np.array([False, False, False, True]), tonnage, is_ore) == 0.0


@pytest.mark.req("FR-007-09")
@pytest.mark.oracle("hand-calculation", "sum of selected waste tonnage over sum of selected ore tonnage")
def test_fr_007_09_unequal_tonnages() -> None:
    p = _p()
    tonnage = np.array([5.0e5, 2.0e5, 3.0e5, 8.0e5, 1.0e6, 4.0e5])
    is_ore = np.array([False, True, False, True, False, True])
    pit = np.array([True, True, True, True, False, False])
    waste = 5.0e5 + 3.0e5  # selected non-ore blocks 0 and 2
    ore = 2.0e5 + 8.0e5  # selected ore blocks 1 and 3
    assert p.strip_ratio(pit, tonnage, is_ore) == pytest.approx(waste / ore, rel=1e-12)


@pytest.mark.req("FR-007-09")
@pytest.mark.oracle("hand-calculation", "incremental pushback ratio = strip ratio of outer & ~inner")
def test_fr_007_09_pushback_increment() -> None:
    p = _p()
    tonnage = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]) * 1e5
    is_ore = np.array([True, False, True, False, True, False])
    inner = np.array([True, True, False, False, False, False])
    outer = np.array([True, True, True, True, True, False])
    push = outer & ~inner  # blocks 2, 3, 4: ore 3 + 5, waste 4 (in units of 1e5)
    assert p.strip_ratio(push, tonnage, is_ore) == pytest.approx(4.0 / 8.0, rel=1e-12)
    assert p.strip_ratio(inner, tonnage, is_ore) == pytest.approx(2.0 / 1.0, rel=1e-12)
    assert p.strip_ratio(outer, tonnage, is_ore) == pytest.approx((2.0 + 4.0) / (1.0 + 3.0 + 5.0), rel=1e-12)


@pytest.mark.req("FR-007-09")
def test_fr_007_09_inputs_are_not_modified() -> None:
    p = _p()
    pit = np.array([True, False, True])
    tonnage = np.array([1.0, 2.0, 3.0])
    ore = np.array([True, False, False])
    copies = [pit.copy(), tonnage.copy(), ore.copy()]
    p.strip_ratio(pit, tonnage, ore)
    for a, b in zip((pit, tonnage, ore), copies, strict=True):
        assert np.array_equal(a, b)

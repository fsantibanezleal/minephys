"""T-007-010 (P-007-01): homogeneity and monotonicity of the block value.

Public API under test (`minephys.planning`): `block_economic_value(tonnage, grade, price, selling_cost, recovery, processing_cost,
mining_cost) -> BlockValue(value, processed)` and `breakeven_cutoff_grade(processing_cost, price, selling_cost, recovery)`
(see tests/unit/test_t_007_010_block_value.py). Generators: tonnage log-uniform in [1e3, 1e8] kg, grades in [0, 0.1], prices
5 to 50 per kg with the selling cost 5 to 40 % of the price, recovery in (0.3, 1], costs in [1e-4, 5e-2] per kg; 200 examples.

Relations (TC-1 unless stated)
- v is linear in the tonnage; expressing mass in tonnes instead of kg (tonnage / 1000, prices and costs per tonne x 1000) gives the
  same value;
- v is non-decreasing in grade, price and recovery and non-increasing in each cost;
- `processed` is true exactly where g > g_be (strictly, tested one part in 1e9 away from g_be).
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
TONNAGE = st.floats(math.log(1e3), math.log(1e8)).map(math.exp)
GRADE = st.floats(0.0, 0.1)
PRICE = st.floats(5.0, 50.0)
SELL_FRAC = st.floats(0.05, 0.4)
RECOVERY = st.floats(0.3, 1.0)
COST = st.floats(1e-4, 5e-2)


def _p():
    return importlib.import_module("minephys.planning")


@pytest.mark.req("P-007-01")
@pytest.mark.oracle("analytical", "v is linear in T; unit change (kg -> t) leaves v unchanged")
@CI
@given(t=TONNAGE, g=GRADE, p=PRICE, sf=SELL_FRAC, y=RECOVERY, cp=COST, cm=COST, lam=st.floats(0.1, 10.0))
def test_p_007_01_homogeneity(t: float, g: float, p: float, sf: float, y: float, cp: float, cm: float, lam: float) -> None:
    f = _p().block_economic_value
    sr = sf * p
    base = f(t, g, p, sr, y, cp, cm)
    scaled = f(lam * t, g, p, sr, y, cp, cm)
    np.testing.assert_allclose(scaled.value, lam * base.value, rtol=1e-12, atol=1e-9)
    assert bool(scaled.processed) == bool(base.processed)
    in_tonnes = f(t / 1000.0, g, 1000.0 * p, 1000.0 * sr, y, 1000.0 * cp, 1000.0 * cm)
    np.testing.assert_allclose(in_tonnes.value, base.value, rtol=1e-11, atol=1e-9)
    assert bool(in_tonnes.processed) == bool(base.processed)


@pytest.mark.req("P-007-01")
@pytest.mark.oracle("analytical", "the value is non-decreasing in grade, price, recovery; non-increasing in each cost")
@CI
@given(
    t=TONNAGE,
    g=GRADE,
    p=PRICE,
    sf=SELL_FRAC,
    y=st.floats(0.3, 0.9),
    cp=COST,
    cm=COST,
    dg=st.floats(0.0, 0.05),
    dp=st.floats(0.0, 10.0),
    dy=st.floats(0.0, 0.1),
    dc=st.floats(0.0, 1e-2),
)
def test_p_007_01_monotonicity(t, g, p, sf, y, cp, cm, dg, dp, dy, dc) -> None:
    f = _p().block_economic_value
    sr = sf * p
    base = float(f(t, g, p, sr, y, cp, cm).value)
    tol = 1e-12 * (abs(base) + t)
    assert float(f(t, g + dg, p, sr, y, cp, cm).value) >= base - tol
    assert float(f(t, g, p + dp, sr, y, cp, cm).value) >= base - tol
    assert float(f(t, g, p, sr, min(1.0, y + dy), cp, cm).value) >= base - tol
    assert float(f(t, g, p, sr, y, cp + dc, cm).value) <= base + tol
    assert float(f(t, g, p, sr, y, cp, cm + dc).value) <= base + tol
    assert float(f(t, g, p, sr + min(dp, 0.1 * p), y, cp, cm).value) <= base + tol  # a higher selling cost lowers the value


@pytest.mark.req("P-007-01")
@pytest.mark.oracle("analytical", "processed <=> g > g_be = c_p / (y (p - s_r))")
@CI
@given(t=TONNAGE, p=PRICE, sf=SELL_FRAC, y=RECOVERY, cp=COST, cm=COST, above=st.booleans())
def test_p_007_01_destination_follows_the_break_even_grade(t, p, sf, y, cp, cm, above) -> None:
    pl = _p()
    sr = sf * p
    g_be = float(pl.breakeven_cutoff_grade(cp, p, sr, y))
    np.testing.assert_allclose(g_be, cp / (y * (p - sr)), rtol=1e-12, atol=0)
    g = g_be * (1.0 + 1e-9) if above else g_be * (1.0 - 1e-9)
    assert bool(pl.block_economic_value(t, g, p, sr, y, cp, cm).processed) is above

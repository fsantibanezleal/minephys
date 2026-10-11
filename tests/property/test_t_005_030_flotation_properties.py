"""T-005-030 (P-005-10, P-005-11): property and metamorphic tests of the flotation recoveries.

Public API under test (`minephys.comminution`): `flotation_first_order(r_inf, k, t)`, `klimpel_recovery(r_inf, k, t)`,
`flotation_cell_recovery(r_inf, k, tau, n_cells=1)` (see tests/unit/test_t_005_030_flotation.py).

Relations
- P-005-10 ordering: 0 <= Klimpel <= first order <= R_inf and one cell (tau = t) <= first order, all non-decreasing in
  t; k t in [0, 50]; ordering tolerance atol 1e-15;
- P-005-11 time-scale invariance R(lambda k, t / lambda) = R(k, t) for every kinetic form, and the many-cell limit
  R_cell(k, tau/N, N) -> R_first(k, tau) with error < 1e-3 at N = 1,000 for k tau <= 5.
Generators: R_inf in (0, 1], rates log-uniform in [1e-4, 1] 1/s, 200 examples.
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
R_INF = st.floats(0.01, 1.0)
RATES = st.floats(math.log(1e-4), math.log(1.0)).map(math.exp)
KT = st.floats(1e-9, 50.0)  # tau = t must be > 0 for the cell form; t = 0 is covered by the unit tests


def _c():
    return importlib.import_module("minephys.comminution")


@pytest.mark.req("P-005-10")
@pytest.mark.oracle("analytical", "0 <= Klimpel <= first order <= R_inf and k tau/(1+k tau) <= 1 - exp(-k tau)")
@CI
@given(r=R_INF, k=RATES, kt=KT)
def test_p_005_10_ordering(r: float, k: float, kt: float) -> None:
    c = _c()
    t = kt / k
    first = c.flotation_first_order(r, k, t)
    klimpel = c.klimpel_recovery(r, k, t)
    cell = c.flotation_cell_recovery(r, k, t, 1)
    assert -1e-15 <= klimpel <= first + 1e-15
    assert first <= r + 1e-15
    assert cell <= first + 1e-15
    assert cell >= -1e-15


@pytest.mark.req("P-005-10")
@CI
@given(r=R_INF, k=RATES, kt1=KT, kt2=KT)
def test_p_005_10_every_form_is_non_decreasing_in_time(r: float, k: float, kt1: float, kt2: float) -> None:
    c = _c()
    t1, t2 = sorted((kt1 / k, kt2 / k))
    for f in (c.flotation_first_order, c.klimpel_recovery, lambda r_, k_, t_: c.flotation_cell_recovery(r_, k_, t_, 3)):
        assert f(r, k, t1) <= f(r, k, t2) + 1e-15


@pytest.mark.req("P-005-11")
@pytest.mark.oracle("analytical", "every recovery depends on k and t only through k t")
@CI
@given(r=R_INF, k=RATES, kt=st.floats(1e-2, 50.0), lam=st.floats(math.log(1e-3), math.log(1e3)).map(math.exp), n=st.integers(1, 12))
def test_p_005_11_time_scale_invariance(r: float, k: float, kt: float, lam: float, n: int) -> None:
    c = _c()
    t = kt / k
    pairs = [
        (c.flotation_first_order(r, lam * k, t / lam), c.flotation_first_order(r, k, t)),
        (c.klimpel_recovery(r, lam * k, t / lam), c.klimpel_recovery(r, k, t)),
        (c.flotation_cell_recovery(r, lam * k, t / lam, n), c.flotation_cell_recovery(r, k, t, n)),
    ]
    for got, ref in pairs:
        np.testing.assert_allclose(got, ref, rtol=1e-12, atol=1e-15)


@pytest.mark.req("P-005-11")
@pytest.mark.oracle("analytical", "(1 + x/N)^-N -> exp(-x): error below 1e-3 at N = 1,000 for x <= 5")
@CI
@given(r=R_INF, k=RATES, x=st.floats(1e-6, 5.0))
def test_p_005_11_many_cell_limit(r: float, k: float, x: float) -> None:
    c = _c()
    tau = x / k
    n = 1000
    cells = c.flotation_cell_recovery(r, k, tau / n, n)
    assert abs(cells - c.flotation_first_order(r, k, tau)) < 1e-3

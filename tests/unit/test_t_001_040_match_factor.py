"""T-001-040 (FR-001-18, P-001-12): the homogeneous match factor.

Expected API: `H.match_factor(n_trucks, n_loaders, load_time, cycle_time)` -> `n_trucks * load_time / (n_loaders *
cycle_time)`, dimensionless (float64), with `cycle_time` the truck cycle excluding waiting. Oracles: spec 001
section 7.4
(MF = 1.0 for 6 trucks, 1 loader, 240 s loading, 1440 s cycle), hand calculations, and the metamorphic relations of
P-001-12 (unchanged when both times scale by k; linear in the number of trucks), tolerance TC-1.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


@pytest.mark.req("FR-001-18")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: 6 * 240 / (1 * 1440) = 1.0")
def test_printed_value() -> None:
    got = H.match_factor(6, 1, 240.0, 1440.0)
    assert type(got) is np.float64
    assert got == pytest.approx(1.0, rel=1e-12)


@pytest.mark.req("FR-001-18")
@pytest.mark.oracle(
    "hand-calculation", "4 * 300 / (2 * 1500) = 0.4; 10 * 120 / (2 * 1800) = 1/3; 3 * 180 / (1 * 900) = 0.6"
)
@pytest.mark.parametrize(
    ("trucks", "loaders", "load", "cycle", "expected"),
    [
        (4, 2, 300.0, 1500.0, 0.4),
        (10, 2, 120.0, 1800.0, 1.0 / 3.0),
        (3, 1, 180.0, 900.0, 0.6),
        (1, 1, 100.0, 1000.0, 0.1),
    ],
)
def test_hand_values(trucks: int, loaders: int, load: float, cycle: float, expected: float) -> None:
    assert H.match_factor(trucks, loaders, load, cycle) == pytest.approx(expected, rel=1e-12)


@pytest.mark.req("FR-001-18")
@pytest.mark.oracle("hand-calculation", "more than one fleet at once: arrays of trucks against two cycle times")
def test_array_inputs() -> None:
    trucks = np.array([[2], [4], [8]])
    cycle = np.array([1200.0, 2400.0])
    out = H.match_factor(trucks, 2, 300.0, cycle)
    assert out.shape == (3, 2)
    np.testing.assert_allclose(out, trucks * 300.0 / (2 * cycle), rtol=1e-14, atol=0.0)
    assert H.match_factor(np.empty(0, dtype=np.int64), 1, 100.0, 1000.0).shape == (0,)


@pytest.mark.req("FR-001-18")
@pytest.mark.oracle("hand-calculation", "integer counts and float counts that are whole numbers give the same factor")
def test_count_dtypes() -> None:
    assert H.match_factor(np.int32(6), np.int64(1), 240.0, 1440.0) == pytest.approx(1.0, rel=1e-12)
    assert H.match_factor(6.0, 1.0, 240.0, 1440.0) == pytest.approx(1.0, rel=1e-12)


@pytest.mark.req("P-001-12")
@pytest.mark.oracle("analytical", "unit-change invariance: seconds, minutes or hours give the same factor")
@settings(deadline=None)
@given(
    n=st.integers(1, 200),
    c=st.integers(1, 20),
    load=st.floats(10.0, 600.0),
    extra=st.floats(1.0, 5000.0),
    k=st.floats(1e-3, 1e3),
)
def test_invariant_when_both_times_scale(n: int, c: int, load: float, extra: float, k: float) -> None:
    cycle = load + extra
    base = float(H.match_factor(n, c, load, cycle))
    assert float(H.match_factor(n, c, k * load, k * cycle)) == pytest.approx(base, rel=1e-12)
    assert base == pytest.approx(n * load / (c * cycle), rel=1e-12)


@pytest.mark.req("P-001-12")
@pytest.mark.oracle("analytical", "linear in the number of trucks, inversely proportional to the number of loaders")
@settings(deadline=None)
@given(
    n=st.integers(1, 200),
    c=st.integers(1, 20),
    m=st.integers(1, 50),
    load=st.floats(10.0, 600.0),
    extra=st.floats(1.0, 5000.0),
)
def test_linear_in_trucks(n: int, c: int, m: int, load: float, extra: float) -> None:
    cycle = load + extra
    base = float(H.match_factor(n, c, load, cycle))
    assert float(H.match_factor(m * n, c, load, cycle)) == pytest.approx(m * base, rel=1e-12)
    assert float(H.match_factor(n, m * c, load, cycle)) == pytest.approx(base / m, rel=1e-12)

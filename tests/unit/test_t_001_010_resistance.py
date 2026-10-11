"""T-001-010 (FR-001-01, FR-001-02): grade and total resistance of `minephys.haulage`.

Expected public API (spec 001 section 7.1), imported as `from minephys import haulage as H`:

    H.grade_resistance(grade, small_angle=False)                -> numpy.float64 or float64 ndarray [1]
    H.total_resistance(rolling_resistance, grade, small_angle=False)  -> same

`small_angle` is keyword-style optional. Grades are rise over run (tan theta), resistances fractions of the gross
weight. Oracles: sin(arctan(g)) = g / sqrt(1 + g**2) (analytical, written out here), the printed value
`grade_resistance(0.10) = 0.0995037190209989` of spec 001 section 7.4 and the small-angle identity (hand calculation).
Tolerance class TC-1 (rtol 1e-12) for closed forms; the printed value at its 16 digits.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def closed_form(x: float) -> float:
    return x / math.sqrt(1.0 + x * x)


@pytest.mark.req("FR-001-01")
@pytest.mark.oracle("hand-calculation", "spec 001 section 7.4: grade_resistance(0.10) = 0.0995037190209989")
def test_grade_resistance_printed_value() -> None:
    got = H.grade_resistance(0.10)
    assert type(got) is np.float64
    assert got == pytest.approx(0.0995037190209989, rel=1e-14)


@pytest.mark.req("FR-001-01")
@pytest.mark.oracle("analytical", "sin(arctan g) = g / sqrt(1 + g^2)")
@pytest.mark.parametrize("g", [-1.0, -0.5, -0.3, -0.05, -1e-9, 0.0, 1e-9, 0.01, 0.1, 0.25, 0.3, 0.75, 1.0, 3.0])
def test_grade_resistance_is_sin_of_arctan(g: float) -> None:
    assert H.grade_resistance(g) == pytest.approx(math.sin(math.atan(g)), rel=1e-12, abs=1e-300)
    assert H.grade_resistance(g) == pytest.approx(closed_form(g), rel=1e-12, abs=1e-300)


@pytest.mark.req("FR-001-01")
@pytest.mark.oracle("hand-calculation", "small_angle=True returns the grade itself, unchanged")
@pytest.mark.parametrize("g", [-0.4, -0.1, 0.0, 0.07, 0.1, 0.35])
def test_small_angle_returns_the_grade(g: float) -> None:
    assert H.grade_resistance(g, small_angle=True) == g


@pytest.mark.req("FR-001-01")
@pytest.mark.oracle("analytical", "huge grades must not overflow: g / sqrt(1 + g^2) -> +-1 (x*x would overflow)")
@pytest.mark.parametrize("g", [1e154, 1e200, 1e300, 1.7e308])
def test_huge_grade_saturates_at_one(g: float) -> None:
    assert H.grade_resistance(g) == pytest.approx(1.0, rel=1e-12)
    assert H.grade_resistance(-g) == pytest.approx(-1.0, rel=1e-12)


@pytest.mark.req("FR-001-01")
@pytest.mark.oracle("hand-calculation", "tiny grades keep their relative precision (no 1 + g^2 cancellation)")
@pytest.mark.parametrize("g", [1e-300, 1e-160, 5e-100, 1e-20])
def test_tiny_grade_keeps_relative_precision(g: float) -> None:
    assert H.grade_resistance(g) == pytest.approx(g, rel=1e-12)


@pytest.mark.req("FR-001-01")
@pytest.mark.oracle("analytical", "array in, array out; same values as the scalar closed form")
def test_grade_resistance_array() -> None:
    g = np.array([[-1.0, -0.1, 0.0], [0.1, 0.5, 1.0]])
    out = H.grade_resistance(g)
    assert out.shape == (2, 3)
    assert out.dtype == np.float64
    expected = np.array([[closed_form(float(v)) for v in row] for row in g])
    np.testing.assert_allclose(out, expected, rtol=1e-12, atol=1e-300)
    assert H.grade_resistance(np.empty(0)).shape == (0,)


@pytest.mark.req("FR-001-02")
@pytest.mark.oracle(
    "hand-calculation", "spec 001 7.4: RR 0.02 + small-angle grade 0.10 = 0.12; exact grade adds 0.0995037190209989"
)
def test_total_resistance_small_angle_and_exact() -> None:
    assert H.total_resistance(0.02, 0.10, small_angle=True) == pytest.approx(0.12, rel=1e-14)
    assert H.total_resistance(0.02, 0.10) == pytest.approx(0.02 + 0.0995037190209989, rel=1e-13)


@pytest.mark.req("FR-001-02")
@pytest.mark.oracle("analytical", "TR = RR + GR for downhill, level and uphill grades; RR = 0 is allowed")
@pytest.mark.parametrize(
    ("rr", "g"),
    [(0.0, 0.0), (0.0, -0.1), (0.02, -0.1), (0.05, 0.0), (0.03, 0.08), (0.2, 0.3), (0.999, -0.5)],
)
def test_total_resistance_is_the_sum(rr: float, g: float) -> None:
    assert H.total_resistance(rr, g) == pytest.approx(rr + closed_form(g), rel=1e-12, abs=1e-15)
    assert H.total_resistance(rr, g, small_angle=True) == pytest.approx(rr + g, rel=1e-12, abs=1e-15)


@pytest.mark.req("FR-001-02")
@pytest.mark.oracle("analytical", "elementwise broadcast of RR (column) and grade (row)")
def test_total_resistance_broadcasts() -> None:
    rr = np.array([[0.01], [0.02], [0.03]])
    g = np.array([-0.1, 0.0, 0.1, 0.2])
    out = H.total_resistance(rr, g)
    assert out.shape == (3, 4)
    for i in range(3):
        for j in range(4):
            assert out[i, j] == pytest.approx(rr[i, 0] + closed_form(float(g[j])), rel=1e-12, abs=1e-15)

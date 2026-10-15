"""T-002-013 (FR-002-04, FR-002-14): Cunningham's uniformity index (the 1987 form of Cunningham 2005, eq. 3, p. 202).

Expected API: `B.uniformity_index(burden, spacing, hole_diameter, drilling_deviation, charge_length, bench_height,
bottom_charge_length=None, column_charge_length=None)` (lengths in m) ->

    n = (2.2 - 14 B / d) * sqrt((1 + S / B) / 2) * (1 - W / B) * (|BCL - CCL| / L + 0.1)^0.1 * L / H

with B, S, W, L, BCL, CCL, H in m and the hole diameter d converted to MILLIMETRES inside the formula; for a single
explosive column (`bottom_charge_length` and `column_charge_length` both None) BCL = L and CCL = 0.
FR-002-14: if 14 B / d >= 2.2, or W >= B, or BCL + CCL > L (both given), the function raises `InputError` naming the
argument; giving only one of the two column lengths is an `InputError` too.

Oracles: spec 002 section 7.4 worked example 1 (n = 1.1164546, TC-2), the equation written out in this file (hand
transcription of the published form, TC-1), analytical domain limits.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from minephys.knowledge import UnverifiedParameterWarning  # noqa: F401  (the module must provide the class)

import minephys
from minephys import blasting as B

EXAMPLE = {
    "burden": 6.0,
    "spacing": 7.0,
    "hole_diameter": 0.25,
    "drilling_deviation": 0.3,
    "charge_length": 7.2,
    "bench_height": 12.0,
}


def formula(b, s, d_m, w, length, h, bcl=None, ccl=None):
    bcl = length if bcl is None else bcl
    ccl = 0.0 if ccl is None else ccl
    return (
        (2.2 - 14.0 * b / (d_m * 1000.0))
        * math.sqrt((1.0 + s / b) / 2.0)
        * (1.0 - w / b)
        * (abs(bcl - ccl) / length + 0.1) ** 0.1
        * length
        / h
    )


@pytest.mark.req("FR-002-04")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: uniformity_index of worked example 1 = 1.1164546")
def test_printed_value() -> None:
    got = B.uniformity_index(**EXAMPLE)
    assert type(got) is np.float64
    assert got == pytest.approx(1.1164546, abs=5e-8)  # TC-2: 8 significant figures
    assert got == pytest.approx(formula(6.0, 7.0, 0.25, 0.3, 7.2, 12.0), rel=1e-12)


@pytest.mark.req("FR-002-04")
@pytest.mark.oracle(
    "hand-calculation", "single column: BCL = L and CCL = 0 give |BCL - CCL| / L = 1, explicitly or by default"
)
def test_single_column_default_equals_explicit() -> None:
    default = B.uniformity_index(**EXAMPLE)
    explicit = B.uniformity_index(**EXAMPLE, bottom_charge_length=7.2, column_charge_length=0.0)
    assert explicit == pytest.approx(float(default), rel=1e-14)


@pytest.mark.req("FR-002-04")
@pytest.mark.oracle(
    "hand-calculation", "a deck-loaded column (BCL 3.0, CCL 4.2 in 7.2 m) lowers the last factor to (0.1667 + 0.1)^0.1"
)
def test_two_explosives() -> None:
    got = B.uniformity_index(**EXAMPLE, bottom_charge_length=3.0, column_charge_length=4.2)
    assert got == pytest.approx(formula(6.0, 7.0, 0.25, 0.3, 7.2, 12.0, bcl=3.0, ccl=4.2), rel=1e-12)
    assert got == pytest.approx(0.96894403, abs=5e-9)
    assert got < float(B.uniformity_index(**EXAMPLE))
    # symmetric in the two lengths: only |BCL - CCL| enters
    swapped = B.uniformity_index(**EXAMPLE, bottom_charge_length=4.2, column_charge_length=3.0)
    assert swapped == pytest.approx(float(got), rel=1e-14)


@pytest.mark.req("FR-002-04")
@pytest.mark.oracle(
    "hand-calculation", "the diameter enters in millimetres: 14 * 6 / 250 = 0.336, so 2.2 - 0.336 = 1.864"
)
def test_diameter_is_taken_in_millimetres() -> None:
    n = float(B.uniformity_index(**EXAMPLE))
    expected = 1.864 * math.sqrt((1.0 + 7.0 / 6.0) / 2.0) * (1.0 - 0.3 / 6.0) * 1.1**0.1 * 7.2 / 12.0
    assert n == pytest.approx(expected, rel=1e-12)


@pytest.mark.req("FR-002-04")
@pytest.mark.oracle("hand-calculation", "arrays broadcast: burdens (column) by diameters (row)")
def test_broadcasting() -> None:
    b = np.array([[4.0], [6.0]])
    d = np.array([0.15, 0.25, 0.311])
    out = B.uniformity_index(b, 7.0, d, 0.3, 7.2, 12.0)
    assert out.shape == (2, 3)
    for i in range(2):
        for j in range(3):
            assert out[i, j] == pytest.approx(formula(float(b[i, 0]), 7.0, float(d[j]), 0.3, 7.2, 12.0), rel=1e-12)
    assert B.uniformity_index(np.empty(0), 7.0, 0.25, 0.3, 7.2, 12.0).shape == (0,)


@pytest.mark.req("FR-002-04")
@pytest.mark.oracle(
    "analytical", "no drilling deviation and a square pattern: n = (2.2 - 14 B/d) * 1 * 1 * 1.1^0.1 * L/H"
)
def test_perfect_drilling_square_pattern() -> None:
    got = B.uniformity_index(5.0, 5.0, 0.2, 0.0, 6.0, 12.0)
    assert got == pytest.approx((2.2 - 14.0 * 5.0 / 200.0) * 1.1**0.1 * 6.0 / 12.0, rel=1e-12)


# ---------------------------------------------------------------- FR-002-14


@pytest.mark.req("FR-002-14")
@pytest.mark.oracle("analytical", "14 B / d >= 2.2 (d in mm) leaves the domain of the first factor")
@pytest.mark.parametrize(("burden", "d_m"), [(1.0, 0.005), (3.0, 0.017), (6.0, 0.03), (12.0, 0.05), (1.5, 0.0095)])
def test_first_factor_out_of_domain(burden: float, d_m: float) -> None:
    assert 14.0 * burden / (d_m * 1000.0) >= 2.2
    kw = {**EXAMPLE, "burden": burden, "hole_diameter": d_m}
    with pytest.raises(minephys.InputError) as ei:
        B.uniformity_index(**kw)
    assert ei.value.argument in {"burden", "hole_diameter"}


@pytest.mark.req("FR-002-14")
@pytest.mark.oracle("analytical", "just inside the domain the index is small but defined")
def test_first_factor_just_inside_the_domain() -> None:
    kw = {**EXAMPLE, "burden": 1.0, "hole_diameter": 0.0064}  # 14 / 6.4 = 2.1875 < 2.2
    got = B.uniformity_index(**kw)
    assert 0.0 < float(got) < 0.05


@pytest.mark.req("FR-002-14")
@pytest.mark.oracle("analytical", "W >= B makes (1 - W/B) <= 0: the deviation exceeds the burden")
@pytest.mark.parametrize("w", [6.0, 6.5, 100.0])
def test_deviation_not_below_the_burden(w: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        B.uniformity_index(**{**EXAMPLE, "drilling_deviation": w})
    assert ei.value.argument == "drilling_deviation"
    assert B.uniformity_index(**{**EXAMPLE, "drilling_deviation": 5.999}) > 0.0


@pytest.mark.req("FR-002-14")
@pytest.mark.oracle("analytical", "BCL + CCL > L is impossible; equality (a fully loaded hole) is allowed")
def test_charge_lengths_must_fit_in_the_charged_length() -> None:
    kw = {**EXAMPLE, "charge_length": 8.0}
    with pytest.raises(minephys.InputError) as ei:
        B.uniformity_index(**kw, bottom_charge_length=5.0, column_charge_length=3.5)
    assert ei.value.argument in {"bottom_charge_length", "column_charge_length"}
    ok = B.uniformity_index(**kw, bottom_charge_length=5.0, column_charge_length=3.0)  # 5 + 3 = 8: exactly full
    assert float(ok) > 0.0


@pytest.mark.req("FR-002-14")
@pytest.mark.oracle("analytical", "the two column lengths are given together or not at all")
@pytest.mark.parametrize("given", ["bottom_charge_length", "column_charge_length"])
def test_only_one_column_length_is_an_error(given: str) -> None:
    with pytest.raises(minephys.InputError) as ei:
        B.uniformity_index(**EXAMPLE, **{given: 3.0})
    assert ei.value.argument in {"bottom_charge_length", "column_charge_length"}


@pytest.mark.req("FR-002-14")
@pytest.mark.oracle("analytical", "an out-of-domain element of an array is enough to raise")
def test_one_bad_element_in_an_array() -> None:
    b = np.array([4.0, 6.0, 1.0])
    d = np.array([0.25, 0.25, 0.004])  # third: 14 * 1 / 4 = 3.5 >= 2.2
    with pytest.raises(minephys.InputError) as ei:
        B.uniformity_index(b, 7.0, d, 0.3, 7.2, 12.0)
    assert ei.value.argument in {"burden", "hole_diameter"}

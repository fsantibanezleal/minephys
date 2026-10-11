"""T-002-012 (FR-002-03): rock factor, hardness factor and rock density influence (Cunningham 2005).

Expected API:
    `B.rock_factor(rmd, rdi, hf)` -> A = 0.06 * (RMD + RDI + HF) (Cunningham 2005 eq. 4, p. 204);
    `B.hardness_factor(youngs_modulus, ucs)` (both in Pa) -> E / 3 with E in GPa when E < 50 GPa, else UCS / 5
    with UCS in
        MPa (p. 205);
    `B.rock_density_influence(density)` (kg/m^3) -> 0.025 * density - 50 (secondary transcription, rows
        `kuzram_rdi_density_coefficient` and `kuzram_rdi_offset` are UNVERIFIED, so each call emits
        `minephys.knowledge.UnverifiedParameterWarning`).

Oracles: spec 002 section 7.4 ("Other values": RDI = 17.5, HF = 10, A = 4.65; HF = 30 on the UCS branch) and hand
calculations; the verified rows are pinned with `knowledge` markers. Tolerance TC-1.
"""

from __future__ import annotations

import warnings

import numpy as np
import pytest
from _table_helpers_a import rows_by_id
from minephys.knowledge import UnverifiedParameterWarning

from minephys import blasting as B


def rdi(density):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return B.rock_density_influence(density)


@pytest.mark.req("FR-002-03")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: rock_factor(50, 17.5, 10) = 0.06 * 77.5 = 4.65")
def test_rock_factor_printed_value() -> None:
    got = B.rock_factor(50.0, 17.5, 10.0)
    assert type(got) is np.float64
    assert got == pytest.approx(4.65, rel=1e-12)


@pytest.mark.req("FR-002-03")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: HF = E / 3 = 30 / 3 = 10 for E = 30 GPa (< 50 GPa)")
def test_hardness_factor_modulus_branch() -> None:
    assert B.hardness_factor(30e9, 150e6) == pytest.approx(10.0, rel=1e-12)
    assert B.hardness_factor(12e9, 400e6) == pytest.approx(4.0, rel=1e-12)  # the UCS is ignored below 50 GPa


@pytest.mark.req("FR-002-03")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: hardness_factor(60e9, 150e6) = UCS / 5 = 150 / 5 = 30")
def test_hardness_factor_ucs_branch() -> None:
    assert B.hardness_factor(60e9, 150e6) == pytest.approx(30.0, rel=1e-12)
    assert B.hardness_factor(80e9, 250e6) == pytest.approx(50.0, rel=1e-12)  # the modulus is ignored from 50 GPa on


@pytest.mark.req("FR-002-03")
@pytest.mark.oracle("hand-calculation", "the switch is at 50 GPa: below it E / 3, at and above it UCS / 5")
def test_hardness_factor_switch() -> None:
    below = B.hardness_factor(49.999e9, 150e6)
    assert below == pytest.approx(49.999 / 3.0, rel=1e-12)  # 16.666333...
    assert B.hardness_factor(50e9, 150e6) == pytest.approx(30.0, rel=1e-12)
    assert B.hardness_factor(50.001e9, 150e6) == pytest.approx(30.0, rel=1e-12)


@pytest.mark.req("FR-002-03")
@pytest.mark.oracle(
    "hand-calculation", "spec 002 7.4: RDI(2700) = 0.025 * 2700 - 50 = 17.5; RDI(2000) = 0; RDI(1000) = -25"
)
@pytest.mark.parametrize(("density", "expected"), [(2700.0, 17.5), (2000.0, 0.0), (1000.0, -25.0), (2650.0, 16.25)])
def test_rock_density_influence(density: float, expected: float) -> None:
    got = rdi(density)
    assert type(got) is np.float64
    assert got == pytest.approx(expected, rel=1e-12, abs=1e-12)


@pytest.mark.req("FR-002-03")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: A = 4.65 for the chain RDI(2700), HF(30 GPa, 150 MPa)")
def test_the_chain_of_the_worked_example() -> None:
    a = B.rock_factor(50.0, rdi(2700.0), B.hardness_factor(30e9, 150e6))
    assert a == pytest.approx(4.65, rel=1e-12)


@pytest.mark.req("FR-002-03")
@pytest.mark.oracle("hand-calculation", "FR-008-12: the UNVERIFIED density rows are reported on use, naming both rows")
def test_rock_density_influence_warns_about_its_unverified_rows() -> None:
    with pytest.warns(UnverifiedParameterWarning) as rec:
        B.rock_density_influence(2700.0)
    text = " ".join(str(w.message) for w in rec)
    assert "kuzram_rdi_density_coefficient" in text
    assert "kuzram_rdi_offset" in text
    assert "mutinda2021" in text


@pytest.mark.req("FR-002-03")
@pytest.mark.oracle("hand-calculation", "the verified functions are silent about UNVERIFIED rows")
def test_rock_factor_and_hardness_factor_are_silent() -> None:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        B.rock_factor(50.0, 17.5, 10.0)
        B.hardness_factor(30e9, 150e6)
        B.hardness_factor(60e9, 150e6)
    assert [w for w in rec if issubclass(w.category, UnverifiedParameterWarning)] == []


@pytest.mark.req("FR-002-03")
@pytest.mark.oracle("hand-calculation", "arrays broadcast elementwise, and the branch is chosen per element")
def test_arrays_and_per_element_branch() -> None:
    e = np.array([20e9, 49e9, 50e9, 70e9])
    ucs = np.array([100e6, 100e6, 100e6, 300e6])
    out = B.hardness_factor(e, ucs)
    np.testing.assert_allclose(out, [20.0 / 3.0, 49.0 / 3.0, 20.0, 60.0], rtol=1e-12)
    a = B.rock_factor(np.array([[40.0], [60.0]]), np.array([0.0, 10.0]), 5.0)
    assert a.shape == (2, 2)
    np.testing.assert_allclose(a, 0.06 * np.array([[45.0, 55.0], [65.0, 75.0]]), rtol=1e-12)
    assert B.rock_factor(np.empty(0), 0.0, 0.0).shape == (0,)
    assert rdi(np.array([1000.0, 2000.0, 3000.0])).tolist() == pytest.approx([-25.0, 0.0, 25.0], abs=1e-12)


@pytest.mark.req("FR-002-03")
@pytest.mark.oracle(
    "analytical", "the rating RDI may be negative for light rock; the rock factor is linear in each rating"
)
def test_negative_rdi_and_linearity() -> None:
    assert B.rock_factor(50.0, -25.0, 10.0) == pytest.approx(0.06 * 35.0, rel=1e-12)
    base = B.rock_factor(30.0, 5.0, 8.0)
    assert B.rock_factor(31.0, 5.0, 8.0) - base == pytest.approx(0.06, rel=1e-9)
    assert B.rock_factor(30.0, 6.0, 8.0) - base == pytest.approx(0.06, rel=1e-9)
    assert B.rock_factor(30.0, 5.0, 9.0) - base == pytest.approx(0.06, rel=1e-9)


# ---------------------------------------------------------------- knowledge rows pinned (verified rows)


@pytest.mark.req("FR-002-03")
@pytest.mark.knowledge("kuzram_rock_factor_coefficient")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 204: A = 0.06 (RMD + RDI + HF), eq. 4")
def test_row_rock_factor_coefficient() -> None:
    assert rows_by_id("blasting")["kuzram_rock_factor_coefficient"]["value"] == 0.06
    assert B.rock_factor(100.0, 0.0, 0.0) == pytest.approx(6.0, rel=1e-12)


@pytest.mark.req("FR-002-03")
@pytest.mark.knowledge("kuzram_hardness_modulus_divisor")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 205: HF = E / 3 for a Young's modulus below 50 GPa")
def test_row_hardness_modulus_divisor() -> None:
    assert rows_by_id("blasting")["kuzram_hardness_modulus_divisor"]["value"] == 3
    assert B.hardness_factor(3e9, 1e12) == pytest.approx(1.0, rel=1e-12)


@pytest.mark.req("FR-002-03")
@pytest.mark.knowledge("kuzram_hardness_ucs_divisor")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 205: HF = UCS / 5 for a Young's modulus of 50 GPa or more")
def test_row_hardness_ucs_divisor() -> None:
    assert rows_by_id("blasting")["kuzram_hardness_ucs_divisor"]["value"] == 5
    assert B.hardness_factor(100e9, 5e6) == pytest.approx(1.0, rel=1e-12)


@pytest.mark.req("FR-002-03")
@pytest.mark.knowledge("kuzram_hardness_modulus_switch")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 205: the switch between the two branches is E = 50 GPa")
def test_row_hardness_modulus_switch() -> None:
    row = rows_by_id("blasting")["kuzram_hardness_modulus_switch"]
    assert row["value"] == 50
    assert row["units"] == "GPa"
    assert B.hardness_factor(row["value"] * 1e9 - 1e6, 100e6) != B.hardness_factor(row["value"] * 1e9, 100e6)

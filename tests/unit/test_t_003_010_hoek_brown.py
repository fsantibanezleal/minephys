# ruff: noqa: E501
"""T-003-010 (FR-003-01, FR-003-02, FR-003-03, FR-003-06): generalised Hoek-Brown parameters, sigma1, sigma_c,
sigma_t, sigma_cm.

Expected API (`from minephys import geotech as G`, stresses in Pa, GSI and D dimensionless, elementwise):
    `G.hoek_brown_parameters(gsi, mi, disturbance)` -> `(mb, s, a)`: mb = mi exp((GSI - 100)/(28 - 14 D)),
        s = exp((GSI - 100)/(9 - 3 D)), a = 1/2 + (exp(-GSI/15) - exp(-20/3))/6   (Hoek, Carranza-Torres and Corkum
        2002, eqs. 3-5)
    `G.hoek_brown_sigma1(sigma3, sigma_ci, mb, s, a)` -> sigma3 + sigma_ci (mb sigma3 / sigma_ci + s)^a     (eq.
    2) `G.hoek_brown_uniaxial_strength(sigma_ci, s, a)` -> sigma_ci s^a
    (eq. 6) `G.hoek_brown_tensile_strength(sigma_ci, mb, s)` -> -s sigma_ci / mb
    (eq. 7) `G.hoek_brown_rock_mass_strength(sigma_ci, mb, s, a)` -> sigma_ci (mb + 4s - a(mb - 8s)) (mb/4 +
    s)^(a-1) / (2 (1+a)(2+a))   (eq. 17)
FR-003-06: `sigma3` below the tensile strength -s sigma_ci / mb (the base of the power is negative) raises
`InputError` naming `sigma3`; exactly at the tensile strength the base is zero (up to rounding) and sigma1 =
sigma3 (P-003-03).

Oracles: spec 003 section 7.4 hand calculations for GSI = 50, mi = 10, sigma_ci = 50 MPA (TC-2: half a unit of
the last printed digit), the equations written out in this file (hand transcription, TC-1) and the identities
of P-003-03. The verified constants are pinned with `knowledge` markers.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from _table_helpers_a import rows_by_id

import minephys
from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

MPA = 1.0e6


def params(gsi: float, mi: float, d: float) -> tuple[float, float, float]:
    return (
        mi * math.exp((gsi - 100.0) / (28.0 - 14.0 * d)),
        math.exp((gsi - 100.0) / (9.0 - 3.0 * d)),
        0.5 + (math.exp(-gsi / 15.0) - math.exp(-20.0 / 3.0)) / 6.0,
    )


@pytest.mark.req("FR-003-01")
@pytest.mark.oracle(
    "hand-calculation", "spec 003 7.4: GSI = 50, mi = 10, D = 0: mb = 1.676772, s = 3.865920e-3, a = 0.505734"
)
def test_parameters_printed_values_undisturbed() -> None:
    mb, s, a = G.hoek_brown_parameters(50.0, 10.0, 0.0)
    assert (type(mb), type(s), type(a)) == (np.float64, np.float64, np.float64)
    assert mb == pytest.approx(1.676772, abs=5e-7)
    assert s == pytest.approx(3.865920e-3, abs=5e-10)
    assert a == pytest.approx(0.505734, abs=5e-7)  # TC-2: 6 decimals
    assert (mb, s, a) == pytest.approx(params(50.0, 10.0, 0.0), rel=1e-12)


@pytest.mark.req("FR-003-01")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: mb = 0.641037 for D = 0.7 and 0.281157 for D = 1 (GSI = 50, mi = 10); a does not depend on D",
)
@pytest.mark.parametrize(("d", "mb_printed"), [(0.7, 0.641037), (1.0, 0.281157)])
def test_parameters_printed_values_disturbed(d: float, mb_printed: float) -> None:
    mb, s, a = G.hoek_brown_parameters(50.0, 10.0, d)
    assert mb == pytest.approx(mb_printed, abs=5e-7)
    assert (mb, s, a) == pytest.approx(params(50.0, 10.0, d), rel=1e-12)
    assert a == G.hoek_brown_parameters(50.0, 10.0, 0.0)[2]


@pytest.mark.req("FR-003-03")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: sigma1(sigma3 = 1 MPA) = 10.48924 MPA (D = 0), 6.67494 (D = 0.7), 4.71751 (D = 1); sigma_ci = 50 MPA",
)
@pytest.mark.parametrize(("d", "printed"), [(0.0, 10.48924), (0.7, 6.67494), (1.0, 4.71751)])
def test_sigma1_printed_values(d: float, printed: float) -> None:
    mb, s, a = G.hoek_brown_parameters(50.0, 10.0, d)
    got = G.hoek_brown_sigma1(1.0 * MPA, 50.0 * MPA, mb, s, a)
    assert type(got) is np.float64
    assert got / MPA == pytest.approx(printed, abs=5e-6)  # TC-2: 7 significant figures
    assert got == pytest.approx(1.0 * MPA + 50.0 * MPA * (mb * 1.0 / 50.0 + s) ** a, rel=1e-12)


@pytest.mark.req("FR-003-03")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: sigma_c = 3.01136 MPA and sigma_t = -0.115279 MPA (GSI = 50, mi = 10, D = 0, sigma_ci = 50 MPA)",
)
def test_uniaxial_and_tensile_strength_printed_values() -> None:
    mb, s, a = G.hoek_brown_parameters(50.0, 10.0, 0.0)
    sc = G.hoek_brown_uniaxial_strength(50.0 * MPA, s, a)
    st = G.hoek_brown_tensile_strength(50.0 * MPA, mb, s)
    assert sc / MPA == pytest.approx(3.01136, abs=5e-6)
    assert st / MPA == pytest.approx(-0.115279, abs=5e-7)
    assert sc == pytest.approx(50.0 * MPA * s**a, rel=1e-12)
    assert st == pytest.approx(-s * 50.0 * MPA / mb, rel=1e-12)
    # sigma_c is sigma1 at sigma3 = 0
    assert G.hoek_brown_sigma1(0.0, 50.0 * MPA, mb, s, a) == pytest.approx(sc, rel=1e-12)


@pytest.mark.req("FR-003-03")
@pytest.mark.oracle(
    "hand-calculation",
    "eq. 17 written out: sigma_cm = sigma_ci (mb + 4s - a(mb - 8s)) (mb/4 + s)^(a-1) / (2 (1 + a)(2 + a))",
)
@pytest.mark.parametrize(
    ("gsi", "mi", "d"), [(50.0, 10.0, 0.0), (45.0, 10.0, 1.0), (75.0, 25.0, 0.7), (20.0, 5.0, 0.0), (100.0, 33.0, 0.0)]
)
def test_rock_mass_strength_equation(gsi: float, mi: float, d: float) -> None:
    mb, s, a = params(gsi, mi, d)
    sci = 80.0 * MPA
    expected = sci * (mb + 4 * s - a * (mb - 8 * s)) * (mb / 4 + s) ** (a - 1) / (2 * (1 + a) * (2 + a))
    got = G.hoek_brown_rock_mass_strength(sci, mb, s, a)
    assert type(got) is np.float64
    assert got == pytest.approx(expected, rel=1e-12)
    assert got > 0.0


@pytest.mark.req("FR-003-03")
@pytest.mark.oracle(
    "hand-calculation",
    "eq. 17 for intact rock with mi = 10 (mb = 10, s = 1, a = 1/2): sigma_cm = 13 * 3.5^-0.5 / 7.5 sigma_ci = 0.926506 sigma_ci",
)
def test_rock_mass_strength_of_intact_rock() -> None:
    expected = (10.0 + 4.0 - 0.5 * (10.0 - 8.0)) * 3.5**-0.5 / (2.0 * 1.5 * 2.5)  # 0.92651 sigma_ci for mi = 10
    assert G.hoek_brown_rock_mass_strength(1.0, 10.0, 1.0, 0.5) == pytest.approx(expected, rel=1e-12)
    assert expected == pytest.approx(0.926506, abs=5e-7)


@pytest.mark.req("P-003-03")
@pytest.mark.oracle("analytical", "GSI = 100 is intact rock: s = 1, mb = mi, a = 1/2 for every D (exponents vanish)")
@pytest.mark.parametrize("d", [0.0, 0.3, 0.7, 1.0])
def test_intact_rock_identities(d: float) -> None:
    mb, s, a = G.hoek_brown_parameters(100.0, 17.0, d)
    assert s == 1.0
    assert mb == 17.0
    assert a == 0.5


@pytest.mark.req("P-003-03")
@pytest.mark.oracle(
    "analytical", "sigma1 at the tensile strength returns the tensile strength (the base of the power is zero)"
)
@pytest.mark.parametrize(
    ("gsi", "mi", "d"), [(50.0, 10.0, 0.0), (45.0, 10.0, 1.0), (10.0, 4.0, 0.5), (100.0, 33.0, 0.0), (75.0, 20.0, 0.3)]
)
def test_sigma1_at_the_tensile_strength(gsi: float, mi: float, d: float) -> None:
    mb, s, a = G.hoek_brown_parameters(gsi, mi, d)
    st = G.hoek_brown_tensile_strength(50.0 * MPA, mb, s)
    assert st < 0.0
    got = G.hoek_brown_sigma1(st, 50.0 * MPA, mb, s, a)
    assert got == pytest.approx(st, rel=1e-12)


@pytest.mark.req("FR-003-06")
@pytest.mark.oracle(
    "analytical", "below the tensile cut-off the base of the power is negative: InputError naming sigma3"
)
@pytest.mark.parametrize("factor", [1.0 + 1e-9, 1.001, 1.5, 10.0, 1e6])
def test_sigma3_below_the_tensile_strength_is_an_error(factor: float) -> None:
    mb, s, a = G.hoek_brown_parameters(50.0, 10.0, 0.0)
    st = G.hoek_brown_tensile_strength(50.0 * MPA, mb, s)  # -0.115 MPA
    with pytest.raises(minephys.InputError) as ei:
        G.hoek_brown_sigma1(st * factor, 50.0 * MPA, mb, s, a)
    assert ei.value.argument == "sigma3"
    # and a value inside (between the cut-off and zero) is fine
    assert G.hoek_brown_sigma1(st * 0.5, 50.0 * MPA, mb, s, a) > st * 0.5


@pytest.mark.req("FR-003-06")
@pytest.mark.oracle("analytical", "one array element below the cut-off is enough")
def test_one_element_below_the_cut_off() -> None:
    mb, s, a = G.hoek_brown_parameters(50.0, 10.0, 0.0)
    sigma3 = np.array([0.0, 1.0 * MPA, -5.0 * MPA])
    with pytest.raises(minephys.InputError) as ei:
        G.hoek_brown_sigma1(sigma3, 50.0 * MPA, mb, s, a)
    assert ei.value.argument == "sigma3"


@pytest.mark.req("FR-003-01")
@pytest.mark.req("FR-003-02")
@pytest.mark.req("FR-003-03")
@pytest.mark.oracle("hand-calculation", "arrays broadcast elementwise; the tuple of FR-003-01 holds three arrays")
def test_arrays() -> None:
    gsi = np.array([[30.0], [50.0], [70.0]])
    d = np.array([0.0, 0.5, 1.0])
    mb, s, a = G.hoek_brown_parameters(gsi, 10.0, d)
    assert mb.shape == s.shape == (3, 3)
    assert a.shape in {(3, 1), (3, 3)}
    for i in range(3):
        for j in range(3):
            exp_mb, exp_s, exp_a = params(float(gsi[i, 0]), 10.0, float(d[j]))
            assert mb[i, j] == pytest.approx(exp_mb, rel=1e-12)
            assert s[i, j] == pytest.approx(exp_s, rel=1e-12)
            assert np.broadcast_to(a, (3, 3))[i, j] == pytest.approx(exp_a, rel=1e-12)
    sigma3 = np.linspace(0.0, 10.0 * MPA, 11)
    s1 = G.hoek_brown_sigma1(sigma3, 50.0 * MPA, 1.6767724875, 3.8659201e-3, 0.50573356)
    assert s1.shape == (11,)
    assert np.all(np.diff(s1) > 0)
    assert G.hoek_brown_sigma1(np.empty(0), 50.0 * MPA, 1.67, 3.8e-3, 0.5).shape == (0,)


# ---------------------------------------------------------------- knowledge rows pinned (verified)


def table() -> dict[str, dict]:
    return rows_by_id("geotech")


@pytest.mark.req("FR-003-01")
@pytest.mark.knowledge("hb_mb_gsi_denominator_constant")
@pytest.mark.oracle(
    "worked-example", "hoek2002 eq. 3, pp. 267-268: mb = mi exp((GSI - 100)/(28 - 14 D)); the constant 28"
)
def test_row_mb_gsi_denominator() -> None:
    assert table()["hb_mb_gsi_denominator_constant"]["value"] == 28
    mb, _, _ = G.hoek_brown_parameters(50.0, 10.0, 0.0)
    assert mb == pytest.approx(10.0 * math.exp(-50.0 / 28.0), rel=1e-12)


@pytest.mark.req("FR-003-01")
@pytest.mark.knowledge("hb_mb_disturbance_coefficient")
@pytest.mark.oracle("worked-example", "hoek2002 eq. 3, pp. 267-268: the coefficient 14 of D in the denominator of mb")
def test_row_mb_disturbance_coefficient() -> None:
    assert table()["hb_mb_disturbance_coefficient"]["value"] == 14
    mb, _, _ = G.hoek_brown_parameters(50.0, 10.0, 1.0)
    assert mb == pytest.approx(10.0 * math.exp(-50.0 / 14.0), rel=1e-12)


@pytest.mark.req("FR-003-01")
@pytest.mark.knowledge("hb_s_gsi_denominator_constant")
@pytest.mark.oracle("worked-example", "hoek2002 eq. 4, pp. 267-268: s = exp((GSI - 100)/(9 - 3 D)); the constant 9")
def test_row_s_gsi_denominator() -> None:
    assert table()["hb_s_gsi_denominator_constant"]["value"] == 9
    _, s, _ = G.hoek_brown_parameters(50.0, 10.0, 0.0)
    assert s == pytest.approx(math.exp(-50.0 / 9.0), rel=1e-12)


@pytest.mark.req("FR-003-01")
@pytest.mark.knowledge("hb_s_disturbance_coefficient")
@pytest.mark.oracle("worked-example", "hoek2002 eq. 4, pp. 267-268: the coefficient 3 of D in the denominator of s")
def test_row_s_disturbance_coefficient() -> None:
    assert table()["hb_s_disturbance_coefficient"]["value"] == 3
    _, s, _ = G.hoek_brown_parameters(50.0, 10.0, 1.0)
    assert s == pytest.approx(math.exp(-50.0 / 6.0), rel=1e-12)


@pytest.mark.req("FR-003-01")
@pytest.mark.knowledge("hb_a_gsi_scale")
@pytest.mark.oracle(
    "worked-example", "hoek2002 eq. 5, pp. 267-268: a = 1/2 + (exp(-GSI/15) - exp(-20/3))/6; the scale 15"
)
def test_row_a_gsi_scale() -> None:
    assert table()["hb_a_gsi_scale"]["value"] == 15
    _, _, a = G.hoek_brown_parameters(30.0, 10.0, 0.0)
    assert a == pytest.approx(0.5 + (math.exp(-30.0 / 15.0) - math.exp(-20.0 / 3.0)) / 6.0, rel=1e-12)


@pytest.mark.req("FR-003-01")
@pytest.mark.knowledge("hb_a_offset_exponent")
@pytest.mark.oracle(
    "worked-example", "hoek2002 eq. 5, pp. 267-268: the offset exponent 20/3 (exact rational, not 6.667)"
)
def test_row_a_offset_exponent() -> None:
    assert table()["hb_a_offset_exponent"]["value"] == "20/3"
    _, _, a = G.hoek_brown_parameters(30.0, 10.0, 0.0)
    assert a == pytest.approx(0.5 + (math.exp(-2.0) - math.exp(-20.0 / 3.0)) / 6.0, rel=1e-14)
    assert a != pytest.approx(0.5 + (math.exp(-2.0) - math.exp(-6.667)) / 6.0, rel=1e-14), (
        "the rounded 6.667 would differ"
    )

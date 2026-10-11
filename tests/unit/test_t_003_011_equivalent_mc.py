# ruff: noqa: E501
"""T-003-011 (FR-003-04, FR-003-05, FR-003-24): equivalent Mohr-Coulomb parameters and sigma3_max (Hoek et al.
2002 worked example).

Expected API (stresses in Pa, unit weight in N/m^3, height in m, angles in rad):
    `G.equivalent_mohr_coulomb(sigma_ci, mb, s, a, sigma3_max)` -> `(cohesion [Pa], friction_angle [rad])` from
    eqs. 12-13 of the
        2002 edition with sigma3n = sigma3_max / sigma_ci:
            phi' = asin( 6 a mb (s + mb sigma3n)^(a-1) / (2 (1+a)(2+a) + 6 a mb (s + mb sigma3n)^(a-1)) )
            c'   = sigma_ci [(1 + 2a) s + (1 - a) mb sigma3n] (s + mb sigma3n)^(a-1)
                   / ((1+a)(2+a) sqrt(1 + 6 a mb (s + mb sigma3n)^(a-1) / ((1+a)(2+a))))
    `G.sigma3_max(sigma_cm, unit_weight, height, application)` -> sigma_cm 0.72 (sigma_cm / (gamma H))^-0.91 for
    "slope" (eq. 19)
        and sigma_cm 0.47 (sigma_cm / (gamma H))^-0.94 for "tunnel" (eq. 18) in Pa; any other `application` raises
        `InputError` naming `application` and listing both values (FR-003-24).

Oracles: Hoek, Carranza-Torres and Corkum 2002, p. 271 (PDF p. 6): sigma_ci = 50 MPa, mi = 10, GSI = 45; a 100
m high slope with D = 1 gives phi' = 27.61 deg, c' = 0.35 MPa; a tunnel at 100 m depth with D = 0 gives phi' =
47.16 deg, c' = 0.58 MPa (TC-2). The paper prints no unit weight; gamma = 27,000 N/m^3 (0.027 MN/m^3)
reproduces all four values to their last digit and is an INFERRED input (spec 003 section 7.4); the spec
writer's independent calculation gives 27.610 deg, 0.3480 MPa, 47.155 deg and 0.5834 MPa (TC-2 on those
digits), and the intermediate chain below was recomputed independently from the equations (TC-3).
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
GAMMA = 27_000.0  # N/m^3, inferred (see the module docstring)
H = 100.0  # m


def chain(application: str, d: float) -> tuple[float, float, float, float]:
    mb, s, a = G.hoek_brown_parameters(45.0, 10.0, d)
    scm = G.hoek_brown_rock_mass_strength(50.0 * MPA, mb, s, a)
    s3 = G.sigma3_max(scm, GAMMA, H, application)
    c, phi = G.equivalent_mohr_coulomb(50.0 * MPA, mb, s, a, s3)
    return float(scm), float(s3), float(c), float(phi)


@pytest.mark.req("FR-003-04")
@pytest.mark.req("FR-003-05")
@pytest.mark.oracle(
    "worked-example",
    "hoek2002 p. 271: slope 100 m, D = 1: phi' = 27.61 deg, c' = 0.35 MPa (gamma = 27 kN/m^3 inferred)",
)
def test_slope_worked_example() -> None:
    scm, s3, c, phi = chain("slope", 1.0)
    assert math.degrees(phi) == pytest.approx(27.61, abs=5e-3)  # TC-2 on the published 4 significant figures
    assert c / MPA == pytest.approx(0.35, abs=5e-3)
    assert math.degrees(phi) == pytest.approx(27.610, abs=5e-4)  # spec writer's independent value
    assert c / MPA == pytest.approx(0.3480, abs=5e-5)
    # intermediate quantities recomputed independently from eqs. 17, 19, 12 and 13 (TC-3)
    assert scm / MPA == pytest.approx(2.836259616, rel=1e-9)
    assert s3 / MPA == pytest.approx(1.952633159, rel=1e-9)
    assert c / MPA == pytest.approx(0.3479540967, rel=1e-9)
    assert math.degrees(phi) == pytest.approx(27.61034745, rel=1e-9)


@pytest.mark.req("FR-003-04")
@pytest.mark.req("FR-003-05")
@pytest.mark.oracle("worked-example", "hoek2002 p. 271: tunnel at 100 m depth, D = 0: phi' = 47.16 deg, c' = 0.58 MPa")
def test_tunnel_worked_example() -> None:
    scm, s3, c, phi = chain("tunnel", 0.0)
    assert math.degrees(phi) == pytest.approx(47.16, abs=5e-3)
    assert c / MPA == pytest.approx(0.58, abs=5e-3)
    assert math.degrees(phi) == pytest.approx(47.155, abs=5e-4)
    assert c / MPA == pytest.approx(0.5834, abs=5e-5)
    assert scm / MPA == pytest.approx(7.809819707, rel=1e-9)
    assert s3 / MPA == pytest.approx(1.352503061, rel=1e-9)
    assert c / MPA == pytest.approx(0.5833982590, rel=1e-9)
    assert math.degrees(phi) == pytest.approx(47.15542157, rel=1e-9)


@pytest.mark.req("FR-003-05")
@pytest.mark.oracle(
    "hand-calculation",
    "eqs. 18 and 19 written out: sigma3max = sigma_cm * 0.72 (sigma_cm / (gamma H))^-0.91 (slope), 0.47 ... ^-0.94 (tunnel)",
)
@pytest.mark.parametrize(
    ("scm", "gamma", "height"),
    [(2.8e6, 27000.0, 100.0), (1.0e6, 25000.0, 300.0), (6.0e6, 27000.0, 40.0), (1.0e5, 20000.0, 10.0)],
)
def test_sigma3_max_equations(scm: float, gamma: float, height: float) -> None:
    ratio = scm / (gamma * height)
    got_slope = G.sigma3_max(scm, gamma, height, "slope")
    got_tunnel = G.sigma3_max(scm, gamma, height, "tunnel")
    assert type(got_slope) is np.float64
    assert got_slope == pytest.approx(scm * 0.72 * ratio**-0.91, rel=1e-12)
    assert got_tunnel == pytest.approx(scm * 0.47 * ratio**-0.94, rel=1e-12)


@pytest.mark.req("FR-003-05")
@pytest.mark.oracle(
    "hand-calculation",
    "sigma_cm = gamma H makes the power term 1: sigma3max = 0.72 sigma_cm (slope), 0.47 sigma_cm (tunnel)",
)
def test_unit_ratio_gives_the_bare_coefficients() -> None:
    assert G.sigma3_max(2.0e6, 20000.0, 100.0, "slope") == pytest.approx(0.72 * 2.0e6, rel=1e-12)
    assert G.sigma3_max(2.0e6, 20000.0, 100.0, "tunnel") == pytest.approx(0.47 * 2.0e6, rel=1e-12)


@pytest.mark.req("FR-003-05")
@pytest.mark.oracle("analytical", "arrays broadcast; the option is chosen once per call")
def test_sigma3_max_arrays() -> None:
    scm = np.array([[1.0e6], [3.0e6]])
    h = np.array([50.0, 100.0, 200.0])
    out = G.sigma3_max(scm, 27000.0, h, "slope")
    assert out.shape == (2, 3)
    np.testing.assert_allclose(out, scm * 0.72 * (scm / (27000.0 * h)) ** -0.91, rtol=1e-12)
    assert G.sigma3_max(np.empty(0), 27000.0, 100.0, "tunnel").shape == (0,)


@pytest.mark.req("FR-003-24")
@pytest.mark.oracle("hand-calculation", "FR-000-15: exact, case-sensitive options; the error lists the allowed values")
@pytest.mark.parametrize("bad", ["Slope", "TUNNEL", "slope ", " tunnel", "", "pit", "shaft", "slöpe"])
def test_unknown_application(bad: str) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.sigma3_max(2.8e6, GAMMA, H, bad)
    assert ei.value.argument == "application"
    assert "slope" in str(ei.value)
    assert "tunnel" in str(ei.value)


@pytest.mark.req("FR-003-24")
@pytest.mark.oracle("hand-calculation", "a non-string application is not an allowed value either")
@pytest.mark.parametrize("bad", [None, 1, b"slope", ("slope",)], ids=repr)
def test_non_string_application(bad) -> None:
    with pytest.raises((minephys.InputError, minephys.InputTypeError)) as ei:
        G.sigma3_max(2.8e6, GAMMA, H, bad)
    assert ei.value.argument == "application"


@pytest.mark.req("FR-003-04")
@pytest.mark.oracle(
    "analytical", "friction angle in (0, pi/2), cohesion positive; both arrays have the broadcast shape"
)
def test_equivalent_mohr_coulomb_shapes_and_ranges() -> None:
    mb, s, a = G.hoek_brown_parameters(np.array([30.0, 50.0, 70.0]), 10.0, 0.0)
    s3 = np.array([[0.5e6], [2.0e6]])
    c, phi = G.equivalent_mohr_coulomb(50.0 * MPA, mb, s, a, s3)
    assert c.shape == phi.shape == (2, 3)
    assert np.all(c > 0.0)
    assert np.all((phi > 0.0) & (phi < math.pi / 2.0))
    assert c.dtype == phi.dtype == np.float64
    assert np.all(phi[0] > phi[1]), "more confinement lowers the equivalent friction angle"
    c0, phi0 = G.equivalent_mohr_coulomb(50.0 * MPA, 1.6767724875, 3.8659201e-3, 0.50573356, 0.0)
    assert 0.0 < float(phi0) < math.pi / 2.0
    assert float(c0) > 0.0


@pytest.mark.req("FR-003-04")
@pytest.mark.oracle(
    "hand-calculation",
    "eq. 12 and 13 evaluated for sigma3n = 0.04 and intact-rock parameters (mb = 10, s = 1, a = 0.5)",
)
def test_equations_for_intact_rock() -> None:
    mb, s, a, sci = 10.0, 1.0, 0.5, 100.0 * MPA
    s3n = 0.04
    t = s + mb * s3n
    x = 6.0 * a * mb * t ** (a - 1.0)
    phi_expected = math.asin(x / (2.0 * (1 + a) * (2 + a) + x))
    c_expected = (
        sci
        * ((1 + 2 * a) * s + (1 - a) * mb * s3n)
        * t ** (a - 1.0)
        / ((1 + a) * (2 + a) * math.sqrt(1 + x / ((1 + a) * (2 + a))))
    )
    c, phi = G.equivalent_mohr_coulomb(sci, mb, s, a, s3n * sci)
    assert float(phi) == pytest.approx(phi_expected, rel=1e-12)
    assert float(c) == pytest.approx(c_expected, rel=1e-12)
    assert math.degrees(phi_expected) == pytest.approx(math.degrees(float(phi)), rel=1e-12)


# ---------------------------------------------------------------- knowledge rows pinned (verified)


def table() -> dict[str, dict]:
    return rows_by_id("geotech")


@pytest.mark.req("FR-003-05")
@pytest.mark.knowledge("hb_sigma3max_slope_coefficient")
@pytest.mark.oracle(
    "worked-example", "hoek2002 eq. 19, p. 270: sigma3max / sigma_cm = 0.72 (sigma_cm / (gamma H))^-0.91 for slopes"
)
def test_row_sigma3max_slope_coefficient() -> None:
    assert table()["hb_sigma3max_slope_coefficient"]["value"] == 0.72
    assert G.sigma3_max(2.0e6, 20000.0, 100.0, "slope") == pytest.approx(
        table()["hb_sigma3max_slope_coefficient"]["value"] * 2.0e6, rel=1e-12
    )


@pytest.mark.req("FR-003-05")
@pytest.mark.knowledge("hb_sigma3max_slope_exponent")
@pytest.mark.oracle("worked-example", "hoek2002 eq. 19, p. 270: the exponent -0.91")
def test_row_sigma3max_slope_exponent() -> None:
    assert table()["hb_sigma3max_slope_exponent"]["value"] == -0.91
    ratio_2 = G.sigma3_max(4.0e6, 20000.0, 100.0, "slope") / G.sigma3_max(2.0e6, 20000.0, 100.0, "slope")
    assert ratio_2 == pytest.approx(2.0 * 2.0**-0.91, rel=1e-12)


@pytest.mark.req("FR-003-05")
@pytest.mark.knowledge("hb_sigma3max_tunnel_coefficient")
@pytest.mark.oracle(
    "worked-example", "hoek2002 eq. 18, p. 270: sigma3max / sigma_cm = 0.47 (sigma_cm / (gamma H))^-0.94 for tunnels"
)
def test_row_sigma3max_tunnel_coefficient() -> None:
    assert table()["hb_sigma3max_tunnel_coefficient"]["value"] == 0.47
    assert G.sigma3_max(2.0e6, 20000.0, 100.0, "tunnel") == pytest.approx(
        table()["hb_sigma3max_tunnel_coefficient"]["value"] * 2.0e6, rel=1e-12
    )


@pytest.mark.req("FR-003-05")
@pytest.mark.knowledge("hb_sigma3max_tunnel_exponent")
@pytest.mark.oracle("worked-example", "hoek2002 eq. 18, p. 270: the exponent -0.94")
def test_row_sigma3max_tunnel_exponent() -> None:
    assert table()["hb_sigma3max_tunnel_exponent"]["value"] == -0.94
    ratio_2 = G.sigma3_max(4.0e6, 20000.0, 100.0, "tunnel") / G.sigma3_max(2.0e6, 20000.0, 100.0, "tunnel")
    assert ratio_2 == pytest.approx(2.0 * 2.0**-0.94, rel=1e-12)


@pytest.mark.req("FR-003-04")
@pytest.mark.knowledge("hb_disturbance_open_pit_production_blasting")
@pytest.mark.oracle(
    "worked-example",
    "hoek2002 Table 1, p. 272: D = 1.0 for production blasting in an open pit; a documented row, not a default",
)
def test_row_disturbance_production_blasting() -> None:
    row = table()["hb_disturbance_open_pit_production_blasting"]
    assert row["value"] == 1.0
    mb, _, _ = G.hoek_brown_parameters(45.0, 10.0, row["value"])
    assert mb == pytest.approx(10.0 * math.exp(-55.0 / 14.0), rel=1e-12)
    import inspect

    assert inspect.signature(G.hoek_brown_parameters).parameters["disturbance"].default is inspect.Parameter.empty


@pytest.mark.req("FR-003-04")
@pytest.mark.knowledge("hb_disturbance_open_pit_mechanical_excavation")
@pytest.mark.oracle(
    "worked-example",
    "hoek2002 Table 1, p. 272: D = 0.7 for mechanical excavation in an open pit; a documented row, not a default",
)
def test_row_disturbance_mechanical_excavation() -> None:
    row = table()["hb_disturbance_open_pit_mechanical_excavation"]
    assert row["value"] == 0.7
    mb, s, _ = G.hoek_brown_parameters(45.0, 10.0, row["value"])
    assert mb == pytest.approx(10.0 * math.exp(-55.0 / (28.0 - 14.0 * 0.7)), rel=1e-12)
    assert s == pytest.approx(math.exp(-55.0 / (9.0 - 3.0 * 0.7)), rel=1e-12)

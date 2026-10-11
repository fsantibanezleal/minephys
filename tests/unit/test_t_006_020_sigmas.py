"""T-006-020 (FR-006-08, FR-006-09, FR-006-10): line emission rate and ISC3 dispersion coefficients.

Expected public API (`minephys.environment`, SI at the boundary: distances in m, rates in kg/s or kg/(m s)):
    line_emission_rate(emission_factor, vehicles_per_second) -> q_l = E n [kg/(m s)]   (E in kg per vehicle-metre)
    pasquill_sigmas(x, stability_class, terrain="rural")     -> (sigma_y, sigma_z) [m] at downwind distance x [m]
        rural (Pasquill-Gifford as fitted in ISC3): sigma_y = 465.11628 x_km tan(0.017453293 (c - d ln x_km)), (c, d) of ISC3 Table 1-1;
        sigma_z = a x_km^b with the distance-band (a, b) of Table 1-2, band k applying for x_km in (upper_{k-1}, upper_k];
        sigma_z capped at 5,000 m for classes A, B and C and equal to 5,000 m for class A beyond 3.11 km;
        urban (Briggs): ISC3 Tables 1-3 and 1-4 with x in m.
    stability_class is exactly "A" to "F"; terrain is "rural" or "urban"; urban with x < 100 m emits `minephys.ValidityWarning`
    (argument "x", row `isc3_urban_min_distance`) and still returns.

Oracles
- plan 006 hand values from the ISC3 tables (`epa1995isc3v2`, Tables 1-1 and 1-2, evaluated with the pinned coefficients
  written below): D at 1 km (68.126741, 32.093), D at 0.5 km (36.146194, 18.296893), C at 1 km (103.113800, 61.141), F at 2 km
  (63.675319, 21.627177), A at 0.2 km (49.971379, 29.301954), A at 3.5 km (sigma_z = 5,000), urban D at 1,000 m
  (135.224681, 122.788123); printed to 6 decimals (atol 6e-7);
- hand calculation of the closed forms (rtol 1e-12);
- the Briggs urban coefficients of the other classes (A-B, C, E-F) are the standard ISC3 Table 1-3/1-4 forms and are listed in
  the red-phase report as transcribed from the usual reproduction of the table, to be re-read on the primary PDF;
- the band-edge convention is tested without coefficients: at an edge where the two bands differ, the value at the edge equals
  the lower band's left limit.
"""

from __future__ import annotations

import importlib
import math
import warnings

import numpy as np
import pytest

SY_SCALE, DEG = 465.11628, 0.017453293
# ISC3 Table 1-1 (c, d) pinned by the plan's hand values
CD = {"A": (24.1670, 2.5334), "C": (12.5000, 1.0857), "D": (8.3330, 0.72382), "F": (4.1667, 0.36191)}


def _e():
    return importlib.import_module("minephys.environment")


def _validity_warning():
    importlib.import_module("minephys.environment")
    import minephys

    return minephys.ValidityWarning


def sigma_y_hand(x_m: float, cls: str) -> float:
    c, d = CD[cls]
    x_km = x_m / 1000.0
    return SY_SCALE * x_km * math.tan(DEG * (c - d * math.log(x_km)))


@pytest.mark.req("FR-006-08")
@pytest.mark.oracle("hand-calculation", "q_l = E n: 2.806852e-3 kg/m x 200 vehicles/day")
def test_fr_006_08_line_emission_rate() -> None:
    e = _e()
    ef = 1.5 * (10.0 / 12.0) ** 0.9 * (290.0 / 3.0) ** 0.45 * 0.45359237 / 1609.344  # PM10, silt 10 %, 290 short tons, kg/m
    n = 200.0 / 86_400.0
    got = e.line_emission_rate(ef, n)
    np.testing.assert_allclose(got, ef * n, rtol=1e-12, atol=0)
    np.testing.assert_allclose(got, 6.497343e-6, rtol=1e-6)  # exact product; plan 006 prints 6.497274e-6 (see report)
    assert isinstance(got, np.float64)
    out = e.line_emission_rate(np.array([1e-3, 2e-3]), np.array([[0.0], [0.5]]))
    assert out.shape == (2, 2) and out[0].tolist() == [0.0, 0.0]
    np.testing.assert_allclose(out[1], [0.5e-3, 1.0e-3], rtol=1e-12)


@pytest.mark.req("FR-006-09")
@pytest.mark.oracle("hand-calculation", "ISC3 Tables 1-1 and 1-2 at the plan's hand points (6 decimals printed)")
@pytest.mark.knowledge("isc3_sigma_y_scale")
@pytest.mark.knowledge("isc3_deg_to_rad")
@pytest.mark.parametrize(
    ("cls", "x_m", "sy_printed", "sz_printed", "a", "b"),
    [
        ("D", 1000.0, 68.126741, 32.093, 32.093, 0.81066),
        ("D", 500.0, 36.146194, 18.296893, 32.093, 0.81066),
        ("C", 1000.0, 103.113800, 61.141, 61.141, 0.91465),
        ("F", 2000.0, 63.675319, 21.627177, 13.953, 0.63227),
        ("A", 200.0, 49.971379, 29.301954, 170.22, 1.0932),
    ],
)
def test_fr_006_09_rural_hand_points(cls: str, x_m: float, sy_printed: float, sz_printed: float, a: float, b: float) -> None:
    e = _e()
    sy, sz = e.pasquill_sigmas(x_m, cls)
    np.testing.assert_allclose(sy, sigma_y_hand(x_m, cls), rtol=1e-12, atol=0)
    np.testing.assert_allclose(sz, a * (x_m / 1000.0) ** b, rtol=1e-12, atol=0)
    np.testing.assert_allclose(sy, sy_printed, rtol=0, atol=6e-7)
    np.testing.assert_allclose(sz, sz_printed, rtol=0, atol=6e-7)
    assert isinstance(sy, np.float64) and isinstance(sz, np.float64)
    assert e.pasquill_sigmas(x_m, cls, terrain="rural") == (sy, sz)  # "rural" is the default terrain


@pytest.mark.req("FR-006-09")
@pytest.mark.oracle("hand-calculation", "class A beyond 3.11 km is 5,000 m; classes A, B, C are capped at 5,000 m")
@pytest.mark.knowledge("isc3_sigma_z_cap")
def test_fr_006_09_the_sigma_z_cap() -> None:
    e = _e()
    for x in (3500.0, 10_000.0, 100_000.0):
        assert e.pasquill_sigmas(x, "A")[1] == 5000.0
    assert e.pasquill_sigmas(50_000.0, "B")[1] == 5000.0  # 109.3 x_km^1.0971 is about 7,990 m uncapped
    for cls in "DEF":
        assert e.pasquill_sigmas(50_000.0, cls)[1] < 5000.0
    sy, _ = e.pasquill_sigmas(100_000.0, "A")
    np.testing.assert_allclose(sy, sigma_y_hand(100_000.0, "A"), rtol=1e-12)  # sigma_y has no cap


@pytest.mark.req("FR-006-09")
@pytest.mark.oracle("analytical", "band k applies for x_km in (upper_{k-1}, upper_k]: the edge belongs to the lower band")
def test_fr_006_09_band_edge_convention_at_300_m_for_class_d() -> None:
    e = _e()
    left = e.pasquill_sigmas(300.0 * (1.0 - 1e-9), "D")[1]
    at_edge = e.pasquill_sigmas(300.0, "D")[1]
    right = e.pasquill_sigmas(300.0 * (1.0 + 1e-9), "D")[1]
    assert abs(right - left) / left > 1e-7, "the two D bands differ slightly (about 2e-6 relative) at 0.30 km"
    assert abs(at_edge - left) < abs(at_edge - right)  # the edge itself belongs to the lower band
    np.testing.assert_allclose(at_edge, left, rtol=1e-8)


@pytest.mark.req("FR-006-09")
@pytest.mark.oracle("analytical", "class A: continuity at 3.11 km because of the cap, 5,000 m on both sides")
def test_fr_006_09_class_a_at_3_11_km() -> None:
    e = _e()
    assert e.pasquill_sigmas(3110.0, "A")[1] == pytest.approx(5000.0, rel=2e-3)  # 453.85 x^2.1166 is about 5,010 m, capped
    assert e.pasquill_sigmas(3111.0, "A")[1] == 5000.0


@pytest.mark.req("FR-006-09")
@pytest.mark.oracle("hand-calculation", "Briggs urban: D at 1,000 m, ISC3 Tables 1-3 and 1-4 -> 135.224681, 122.788123")
@pytest.mark.knowledge("isc3_briggs_urban_y_d_coef")
@pytest.mark.knowledge("isc3_briggs_urban_z_d_coef")
def test_fr_006_09_urban_class_d_hand_point() -> None:
    e = _e()
    sy, sz = e.pasquill_sigmas(1000.0, "D", terrain="urban")
    np.testing.assert_allclose(sy, 0.16 * 1000.0 / math.sqrt(1.0 + 0.0004 * 1000.0), rtol=1e-12, atol=0)
    np.testing.assert_allclose(sz, 0.14 * 1000.0 / math.sqrt(1.0 + 0.0003 * 1000.0), rtol=1e-12, atol=0)
    np.testing.assert_allclose([sy, sz], [135.224681, 122.788123], rtol=0, atol=6e-7)


@pytest.mark.req("FR-006-09")
@pytest.mark.oracle("hand-calculation", "Briggs urban formulas of ISC3 Tables 1-3 and 1-4 (A-B, C, D, E-F), x = 2,000 m")
def test_fr_006_09_urban_formulas_for_every_class() -> None:
    e = _e()
    x = 2000.0
    y_form = lambda c: c * x / math.sqrt(1.0 + 0.0004 * x)  # noqa: E731
    z_form = {
        "A": 0.24 * x * math.sqrt(1.0 + 0.001 * x),
        "B": 0.24 * x * math.sqrt(1.0 + 0.001 * x),
        "C": 0.20 * x,
        "D": 0.14 * x / math.sqrt(1.0 + 0.0003 * x),
        "E": 0.08 * x / math.sqrt(1.0 + 0.0015 * x),
        "F": 0.08 * x / math.sqrt(1.0 + 0.0015 * x),
    }
    y_coef = {"A": 0.32, "B": 0.32, "C": 0.22, "D": 0.16, "E": 0.11, "F": 0.11}
    for cls in "ABCDEF":
        sy, sz = e.pasquill_sigmas(x, cls, terrain="urban")
        np.testing.assert_allclose(sy, y_form(y_coef[cls]), rtol=1e-12, atol=0)
        np.testing.assert_allclose(sz, z_form[cls], rtol=1e-12, atol=0)


@pytest.mark.req("FR-006-09")
def test_fr_006_09_arrays_broadcast_and_return_float64() -> None:
    e = _e()
    x = np.array([[300.0], [1000.0]])
    sy, sz = e.pasquill_sigmas(x, "D")
    assert sy.shape == (2, 1) and sy.dtype == np.float64 and sz.shape == (2, 1)
    for i, xv in enumerate((300.0, 1000.0)):
        s1, s2 = e.pasquill_sigmas(xv, "D")
        np.testing.assert_allclose([sy[i, 0], sz[i, 0]], [s1, s2], rtol=1e-14, atol=0)


@pytest.mark.req("FR-006-10")
@pytest.mark.knowledge("isc3_urban_min_distance")
@pytest.mark.oracle("hand-calculation", "ISC3: concentrations closer than 100 m to an urban source may be suspect")
def test_fr_006_10_urban_near_field_warns_and_returns() -> None:
    e = _e()
    warning = _validity_warning()
    with pytest.warns(warning) as rec:
        sy, sz = e.pasquill_sigmas(50.0, "D", terrain="urban")
    np.testing.assert_allclose(sy, 0.16 * 50.0 / math.sqrt(1.0 + 0.0004 * 50.0), rtol=1e-12)
    np.testing.assert_allclose(sz, 0.14 * 50.0 / math.sqrt(1.0 + 0.0003 * 50.0), rtol=1e-12)
    msg = next(r.message for r in rec if isinstance(r.message, warning))
    assert msg.argument == "x" and msg.row == "isc3_urban_min_distance"
    assert "x" in str(msg) and "isc3_urban_min_distance" in str(msg)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        e.pasquill_sigmas(100.0, "D", terrain="urban")  # the limit itself is not a violation
        e.pasquill_sigmas(5000.0, "D", terrain="urban")
        e.pasquill_sigmas(50.0, "D", terrain="rural")  # the limit concerns the urban formulas only
    with pytest.warns(warning):
        e.pasquill_sigmas(np.array([500.0, 80.0]), "C", terrain="urban")

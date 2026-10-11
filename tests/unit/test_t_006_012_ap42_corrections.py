"""T-006-012 (FR-006-04, FR-006-05, FR-006-06, SC-006-01): fleet-mean weight, precipitation correction, watering control
efficiency and controlled factor against AP-42's printed numbers.

Expected public API (`minephys.environment`):
    fleet_mean_vehicle_weight(weights, traffic_fractions) -> sum(w_i f_i) / sum(f_i) [kg]
    precipitation_correction(emission_factor, wet_days)    -> E (365 - P) / 365, P = days a year with >= 0.254 mm of precipitation
    watering_control_efficiency(moisture_ratio)            -> CE [1], linear interpolation of Figure 13.2.2-2 between
                                                              (M, CE) = (0, 0), (1, 0), (2, 0.75), (5, 0.95)
    controlled_emission_factor(emission_factor, control_efficiency) -> E (1 - CE)
The emission-factor arguments are unit-agnostic (kg/m, lb/VMT, ...).

Oracles (`epa2006ap42s1322`)
- the fleet-mean example, p. 13.2.2-6: 98 % of 2-ton and 2 % of 20-ton vehicles give 2.36 short tons, printed "2.4 tons" (TC-2);
- Table 13.2.2-5, p. 13.2.2-16: 7.1 lb/VMT controlled at 0, 62, 68, 74, 80 % gives printed 7.1, 2.7, 2.3, 1.8, 1.4 (TC-2: 0.05);
- hand calculation: 9.958701 x 215/365 = 5.866084 for P = 150 days; Figure 13.2.2-2 vertices and interpolation: M = 1.5 ->
  0.375, M = 3.5 -> 0.85, M = 5 -> 0.95.
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest

ST = 907.18474


def _e():
    return importlib.import_module("minephys.environment")


@pytest.mark.req("FR-006-04")
@pytest.mark.req("SC-006-01")
@pytest.mark.oracle("worked-example", "epa2006ap42s1322 p. 13.2.2-6: 98 % 2-ton and 2 % 20-ton vehicles -> 2.4 tons")
def test_fr_006_04_the_printed_fleet_mean_example() -> None:
    e = _e()
    mean = e.fleet_mean_vehicle_weight(np.array([2.0 * ST, 20.0 * ST]), np.array([0.98, 0.02]))
    np.testing.assert_allclose(mean, (0.98 * 2.0 + 0.02 * 20.0) * ST, rtol=1e-12, atol=0)  # 2.36 short tons
    assert abs(mean / ST - 2.4) <= 0.05  # printed with one decimal
    assert isinstance(mean, np.float64)


@pytest.mark.req("FR-006-04")
@pytest.mark.oracle("hand-calculation", "sum(w f) / sum(f), invariant to the scale of the fractions")
def test_fr_006_04_traffic_weighted_mean_and_scale_invariance() -> None:
    e = _e()
    w = np.array([20_000.0, 60_000.0, 180_000.0])
    f = np.array([5.0, 3.0, 2.0])
    np.testing.assert_allclose(e.fleet_mean_vehicle_weight(w, f), (20_000 * 5 + 60_000 * 3 + 180_000 * 2) / 10.0, rtol=1e-12)
    np.testing.assert_allclose(e.fleet_mean_vehicle_weight(w, f / 10.0), e.fleet_mean_vehicle_weight(w, f), rtol=1e-12)
    np.testing.assert_allclose(e.fleet_mean_vehicle_weight(w, 100.0 * f), e.fleet_mean_vehicle_weight(w, f), rtol=1e-12)
    assert e.fleet_mean_vehicle_weight(np.array([1234.0]), np.array([0.4])) == pytest.approx(1234.0, rel=1e-13)
    # a class with zero traffic does not contribute
    np.testing.assert_allclose(
        e.fleet_mean_vehicle_weight(np.array([1e4, 9e4]), np.array([1.0, 0.0])), 1e4, rtol=1e-13
    )


@pytest.mark.req("FR-006-05")
@pytest.mark.oracle("hand-calculation", "E (365 - P) / 365 = 9.958701 x 215/365 = 5.866084 at P = 150")
@pytest.mark.knowledge("ap42_days_per_year")
@pytest.mark.knowledge("ap42_wet_day_threshold")
def test_fr_006_05_precipitation_correction() -> None:
    e = _e()
    got = e.precipitation_correction(9.958701, 150)
    np.testing.assert_allclose(got, 9.958701 * 215.0 / 365.0, rtol=1e-12, atol=0)
    np.testing.assert_allclose(got, 5.866084, rtol=0, atol=6e-7)
    assert isinstance(got, np.float64)
    assert e.precipitation_correction(2.5, 0) == pytest.approx(2.5, rel=1e-13)  # no wet days: unchanged
    assert e.precipitation_correction(2.5, 365) == 0.0  # wet every day: no dust
    arr = e.precipitation_correction(np.array([1.0, 2.0]), np.array([[0], [100]]))
    assert arr.shape == (2, 2) and arr.dtype == np.float64
    np.testing.assert_allclose(arr, [[1.0, 2.0], [265 / 365, 2 * 265 / 365]], rtol=1e-12)


@pytest.mark.req("FR-006-06")
@pytest.mark.oracle("hand-calculation", "Figure 13.2.2-2: vertices (0,0), (1,0), (2,0.75), (5,0.95) and linear interpolation")
@pytest.mark.knowledge("ap42_watering_m_1")
@pytest.mark.knowledge("ap42_watering_m_4")
@pytest.mark.knowledge("ap42_watering_ce_3")
@pytest.mark.knowledge("ap42_watering_ce_4")
@pytest.mark.parametrize(
    ("ratio", "ce"),
    [(0.0, 0.0), (0.5, 0.0), (1.0, 0.0), (1.5, 0.375), (2.0, 0.75), (3.5, 0.85), (5.0, 0.95), (4.0, 0.75 + 2.0 * 0.2 / 3.0)],
)
def test_fr_006_06_watering_control_efficiency(ratio: float, ce: float) -> None:
    e = _e()
    np.testing.assert_allclose(e.watering_control_efficiency(ratio), ce, rtol=1e-12, atol=1e-15)


@pytest.mark.req("FR-006-06")
def test_fr_006_06_watering_efficiency_arrays() -> None:
    e = _e()
    m = np.array([0.0, 1.5, 3.5, 5.0])
    out = e.watering_control_efficiency(m)
    assert out.shape == (4,) and out.dtype == np.float64
    np.testing.assert_allclose(out, [0.0, 0.375, 0.85, 0.95], rtol=1e-12, atol=1e-15)


@pytest.mark.req("FR-006-06")
@pytest.mark.req("SC-006-01")
@pytest.mark.oracle("worked-example", "epa2006ap42s1322 Table 13.2.2-5 p. 13.2.2-16: 7.1 lb/VMT at 0, 62, 68, 74, 80 % control")
@pytest.mark.parametrize(("ce", "printed"), [(0.0, 7.1), (0.62, 2.7), (0.68, 2.3), (0.74, 1.8), (0.80, 1.4)])
def test_fr_006_06_controlled_emission_factor_table_13_2_2_5(ce: float, printed: float) -> None:
    e = _e()
    got = e.controlled_emission_factor(7.1, ce)
    np.testing.assert_allclose(got, 7.1 * (1.0 - ce), rtol=1e-12, atol=1e-15)
    assert abs(got - printed) <= 0.05  # TC-2: one decimal printed
    assert isinstance(got, np.float64)


@pytest.mark.req("FR-006-06")
def test_fr_006_06_controlled_factor_broadcasts_and_bounds() -> None:
    e = _e()
    assert e.controlled_emission_factor(3.0, 1.0) == 0.0
    assert e.controlled_emission_factor(3.0, 0.0) == 3.0
    out = e.controlled_emission_factor(np.array([[1.0], [2.0]]), np.array([0.0, 0.5, 0.9]))
    assert out.shape == (2, 3)
    np.testing.assert_allclose(out, [[1.0, 0.5, 0.1], [2.0, 1.0, 0.2]], rtol=1e-12)

"""T-006-010 (FR-006-01): AP-42 equation 1a with SI arguments, against the published-unit form.

Expected public API (`minephys.environment`, SI at the boundary):
    ap42_unpaved_emission_factor(silt_fraction, mean_weight, size_class, mean_speed=None, mean_wheels=None,
                                 moisture_fraction=None, strict=False) -> E [kg per vehicle-metre travelled]
        E = k (s/12)^a (W/3)^b x 0.45359237 / 1609.344, s = 100 x silt_fraction [%], W = mean_weight / 907.18474 [short tons],
        (k, a, b) = (0.15, 0.9, 0.45), (1.5, 0.9, 0.45), (4.9, 0.7, 0.45) lb/VMT for size_class "PM2.5", "PM10", "PM30".
        mean_speed [m/s], mean_wheels [1] and moisture_fraction [1] enter only the validity check (FR-006-03).
Scalars give `numpy.float64`, arrays a float64 array of the broadcast shape.

Oracles
- hand calculation of the published-unit form (US EPA AP-42 section 13.2.2, November 2006, eq. 1a and Table 13.2.2-2,
  `epa2006ap42s1322`) written below with `math`, then converted with the exact definitions 1 lb = 0.45359237 kg and
  1 mile = 1,609.344 m (TC-1, rtol 1e-12);
- reference point: silt 12 % and 3 short tons give exactly k lb/VMT (analytical);
- plan 006 hand values in lb/VMT: silt 10 %, 290 short tons: 0.995870 / 9.958701 / 33.739896 (PM2.5 / PM10 / PM30); silt 8 %,
  200 short tons: PM10 6.892362. (The kg/m value printed in plan 006, 2.806822e-3, differs from the exact conversion
  2.806852e-3 in its 6th digit; the test uses the exact formula and records the discrepancy in the red-phase report.)
"""

from __future__ import annotations

import importlib
import math
import warnings

import numpy as np
import pytest

LB_PER_VMT = 0.45359237 / 1609.344  # (kg/m) per (lb/VMT): exact definitions of the pound and the mile
SHORT_TON = 907.18474  # kg, exact


def _e():
    return importlib.import_module("minephys.environment")


def _lb_vmt(k: float, a: float, b: float, silt_pct: float, weight_st: float) -> float:
    return k * (silt_pct / 12.0) ** a * (weight_st / 3.0) ** b


COEFFS = {"PM2.5": (0.15, 0.9, 0.45), "PM10": (1.5, 0.9, 0.45), "PM30": (4.9, 0.7, 0.45)}


def _quiet(fn, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return fn(*args, **kwargs)


@pytest.mark.req("FR-006-01")
@pytest.mark.oracle("hand-calculation", "AP-42 eq. 1a in lb/VMT, then converted: silt 10 %, 290 short tons")
@pytest.mark.knowledge("ap42_industrial_k_pm10")
@pytest.mark.knowledge("ap42_industrial_a_pm10")
@pytest.mark.knowledge("ap42_industrial_b_pm10")
@pytest.mark.parametrize(
    ("size_class", "lb_vmt_printed"),
    [("PM2.5", 0.995870), ("PM10", 9.958701), ("PM30", 33.739896)],
)
def test_fr_006_01_hand_calculation_at_the_upper_weight_bound(size_class: str, lb_vmt_printed: float) -> None:
    e = _e()
    k, a, b = COEFFS[size_class]
    expected_lb = _lb_vmt(k, a, b, 10.0, 290.0)
    np.testing.assert_allclose(expected_lb, lb_vmt_printed, rtol=0, atol=6e-7)  # plan 006 printed lb/VMT
    got = _quiet(e.ap42_unpaved_emission_factor, 0.10, 290.0 * SHORT_TON, size_class)
    np.testing.assert_allclose(got, expected_lb * LB_PER_VMT, rtol=1e-12, atol=0)
    assert isinstance(got, np.float64)


@pytest.mark.req("FR-006-01")
@pytest.mark.oracle("hand-calculation", "silt 8 %, 200 short tons, PM10: 6.892362 lb/VMT")
def test_fr_006_01_second_hand_point() -> None:
    e = _e()
    expected_lb = _lb_vmt(1.5, 0.9, 0.45, 8.0, 200.0)
    np.testing.assert_allclose(expected_lb, 6.892362, rtol=0, atol=6e-7)
    np.testing.assert_allclose(
        e.ap42_unpaved_emission_factor(0.08, 200.0 * SHORT_TON, "PM10"), expected_lb * LB_PER_VMT, rtol=1e-12, atol=0
    )


@pytest.mark.req("FR-006-01")
@pytest.mark.oracle("analytical", "at s = 12 % and W = 3 short tons both factors are 1: E = k exactly")
@pytest.mark.knowledge("ap42_silt_reference")
@pytest.mark.knowledge("ap42_weight_reference")
@pytest.mark.parametrize("size_class", ["PM2.5", "PM10", "PM30"])
def test_fr_006_01_reference_point_gives_k(size_class: str) -> None:
    e = _e()
    got = e.ap42_unpaved_emission_factor(0.12, 3.0 * SHORT_TON, size_class)
    np.testing.assert_allclose(got, COEFFS[size_class][0] * LB_PER_VMT, rtol=1e-12, atol=0)


@pytest.mark.req("FR-006-01")
@pytest.mark.oracle("analytical", "the SI factor equals AP-42's printed 1 lb/VMT = 281.9 g/VKT within rtol 2e-4")
@pytest.mark.knowledge("ap42_lb_per_vmt_in_g_per_vkt")
def test_fr_006_01_unit_factor_matches_the_printed_conversion() -> None:
    e = _e()
    one_lb_per_vmt = e.ap42_unpaved_emission_factor(0.12, 3.0 * SHORT_TON, "PM10") / 1.5  # kg per metre for 1 lb/VMT
    np.testing.assert_allclose(one_lb_per_vmt * 1e3 * 1e3, 281.9, rtol=2e-4)  # kg/m -> g/km
    np.testing.assert_allclose(one_lb_per_vmt, LB_PER_VMT, rtol=1e-12, atol=0)


@pytest.mark.req("FR-006-01")
def test_fr_006_01_arrays_broadcast_and_optional_arguments_only_enter_the_validity_check() -> None:
    e = _e()
    silt = np.array([[0.05], [0.10], [0.20]])
    weight = np.array([5_000.0, 50_000.0, 150_000.0, 250_000.0])
    got = e.ap42_unpaved_emission_factor(silt, weight, "PM10")
    assert got.shape == (3, 4) and got.dtype == np.float64
    ref = [[_lb_vmt(1.5, 0.9, 0.45, 100 * s, w / SHORT_TON) * LB_PER_VMT for w in weight] for s in (0.05, 0.10, 0.20)]
    np.testing.assert_allclose(got, ref, rtol=1e-12, atol=0)
    with_optional = e.ap42_unpaved_emission_factor(
        silt, weight, "PM10", mean_speed=12.0, mean_wheels=6, moisture_fraction=0.02
    )
    assert np.array_equal(with_optional, got)  # the optional arguments change no value


@pytest.mark.req("FR-006-01")
def test_fr_006_01_size_classes_are_ordered_and_pm25_is_a_tenth_of_pm10() -> None:
    e = _e()
    args = (0.08, 120_000.0)
    pm25, pm10, pm30 = (e.ap42_unpaved_emission_factor(*args, c) for c in ("PM2.5", "PM10", "PM30"))
    np.testing.assert_allclose(pm25, 0.1 * pm10, rtol=1e-12, atol=0)
    assert pm10 < pm30

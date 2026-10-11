"""T-006-040 (FR-006-19): every constant of FR-006-01 to FR-006-17 is read through `get_value`.

Method (fixture knowledge layout, implementation independent): each case runs a fresh interpreter in which
`minephys.knowledge.get_value` is replaced, before the first call of any environment function, by a wrapper that returns a
replacement value for the rows named in the case (a JSON list becomes the `(min, max)` tuple of a range row) and the real value
for every other row; the attribute is replaced in the package and in every already imported `minephys.*` module that bound the
name. A fresh interpreter makes the check independent of any lazy cache inside the module. The result with the replaced row
must change by the analytical amount (spec 006 plan, FR-006-19):
- `ap42_industrial_k_pm10` = 3.0 doubles E; `ap42_watering_ce_4` = 90 makes CE(5) = 0.90; an ISC3 (c, d) change moves sigma_y as
  the formula predicts; the sigma_z cap, the urban minimum distance, the lid ratio and the ranges move their thresholds.
Values are given in the units of the rows as published (percent, short tons, mph, km, degrees, ...).

Oracle: analytical sensitivity and the hand formulas written below; the baseline is the unmodified function in the same
interpreter, so only ratios and hand formulas enter the assertions.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]

PREAMBLE = """
import json, sys, warnings
import minephys.knowledge as K
import minephys.environment as E
OVER = json.loads(sys.argv[1])
orig = K.get_value
def patched(row_id):
    if row_id in OVER:
        v = OVER[row_id]
        return tuple(float(x) for x in v) if isinstance(v, list) else float(v)
    return orig(row_id)
K.get_value = patched
for name, mod in list(sys.modules.items()):
    if name.startswith("minephys") and getattr(mod, "get_value", None) is orig:
        mod.get_value = patched
import dataclasses
def field(res, i):
    if isinstance(res, tuple):
        return res[i]
    return getattr(res, dataclasses.fields(res)[i].name)
def count_validity(fn):
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        value = fn()
    return {"warnings": sum(1 for r in rec if r.category.__name__ == "ValidityWarning")}
def quiet(fn):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return fn()
"""


def run(expression: str, overrides: dict[str, Any] | None = None) -> Any:
    script = PREAMBLE + f"\nprint(json.dumps({expression}))\n"
    proc = subprocess.run(
        [sys.executable, "-c", script, json.dumps(overrides or {})], capture_output=True, text=True, cwd=ROOT, timeout=120
    )
    assert proc.returncode == 0, f"fresh interpreter failed:\n{proc.stderr[-1500:]}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


ST = 907.18474
EF = "float(quiet(lambda: E.ap42_unpaved_emission_factor(0.10, 100.0 * 907.18474, 'PM10')))"


@pytest.mark.req("FR-006-19")
@pytest.mark.oracle("analytical", "replacing k(PM10) by 3.0 doubles the emission factor")
def test_fr_006_19_ap42_coefficient_row() -> None:
    assert run(EF, {"ap42_industrial_k_pm10": 3.0}) == pytest.approx(2.0 * run(EF), rel=1e-12)


@pytest.mark.req("FR-006-19")
@pytest.mark.parametrize(
    ("row", "value", "factor"),
    [
        ("ap42_industrial_a_pm10", 1.8, (10.0 / 12.0) ** (1.8 - 0.9)),  # silt 10 %: (s/12)^a changes by (s/12)^(delta a)
        ("ap42_industrial_b_pm10", 0.9, (100.0 / 3.0) ** (0.9 - 0.45)),  # 100 short tons: (W/3)^b
        ("ap42_silt_reference", 24.0, (12.0 / 24.0) ** 0.9),  # (s / s_ref)^a with s_ref 12 -> 24
        ("ap42_weight_reference", 6.0, (3.0 / 6.0) ** 0.45),
        ("pound", 0.90718474, 2.0),  # the lb -> kg definition scales the SI result
    ],
)
def test_fr_006_19_ap42_exponent_reference_and_unit_rows(row: str, value: float, factor: float) -> None:
    assert run(EF, {row: value}) == pytest.approx(factor * run(EF), rel=1e-12)


@pytest.mark.req("FR-006-19")
@pytest.mark.oracle("analytical", "ap42_watering_ce_4 = 90 (percent) makes CE(5) = 0.90")
def test_fr_006_19_watering_vertices() -> None:
    expr = "float(E.watering_control_efficiency(5.0))"
    assert run(expr) == pytest.approx(0.95, rel=1e-12)
    assert run(expr, {"ap42_watering_ce_4": 90}) == pytest.approx(0.90, rel=1e-12)
    mid = "float(E.watering_control_efficiency(3.5))"  # on the segment (2, 0.75) - (5, 0.95)
    assert run(mid, {"ap42_watering_ce_4": 90}) == pytest.approx(0.75 + (3.5 - 2.0) * (0.90 - 0.75) / 3.0, rel=1e-12)


@pytest.mark.req("FR-006-19")
def test_fr_006_19_precipitation_days_per_year_row() -> None:
    expr = "float(E.precipitation_correction(10.0, 100))"
    assert run(expr) == pytest.approx(10.0 * 265.0 / 365.0, rel=1e-12)
    assert run(expr, {"ap42_days_per_year": 360}) == pytest.approx(10.0 * 260.0 / 360.0, rel=1e-12)


@pytest.mark.req("FR-006-19")
@pytest.mark.oracle("analytical", "an ISC3 (c, d) change moves sigma_y as 465.11628 x_km tan(0.017453293 (c - d ln x_km)) predicts")
def test_fr_006_19_isc3_sigma_y_rows() -> None:
    expr = "float(E.pasquill_sigmas(1000.0, 'D')[0])"
    hand = lambda c, d, x_km=1.0, scale=465.11628, rad=0.017453293: scale * x_km * math.tan(rad * (c - d * math.log(x_km)))  # noqa: E731
    assert run(expr) == pytest.approx(hand(8.3330, 0.72382), rel=1e-12)
    assert run(expr, {"isc3_pg_sigma_y_c_d": 9.0}) == pytest.approx(hand(9.0, 0.72382), rel=1e-12)
    expr_half = "float(E.pasquill_sigmas(500.0, 'D')[0])"
    assert run(expr_half, {"isc3_pg_sigma_y_d_d": 1.0}) == pytest.approx(hand(8.3330, 1.0, 0.5), rel=1e-12)
    assert run(expr, {"isc3_sigma_y_scale": 2.0 * 465.11628}) == pytest.approx(2.0 * run(expr), rel=1e-12)
    assert run(expr, {"isc3_deg_to_rad": 0.02}) == pytest.approx(hand(8.3330, 0.72382, rad=0.02), rel=1e-12)


@pytest.mark.req("FR-006-19")
def test_fr_006_19_isc3_urban_rows_and_the_sigma_z_cap() -> None:
    urban = "float(quiet(lambda: E.pasquill_sigmas(1000.0, 'D', terrain='urban')[0]))"
    assert run(urban) == pytest.approx(0.16 * 1000.0 / math.sqrt(1.4), rel=1e-12)
    assert run(urban, {"isc3_briggs_urban_y_d_coef": 0.32}) == pytest.approx(0.32 * 1000.0 / math.sqrt(1.4), rel=1e-12)
    assert run(urban, {"isc3_briggs_urban_y_d_slope": 0.001}) == pytest.approx(0.16 * 1000.0 / math.sqrt(2.0), rel=1e-12)
    assert run(urban, {"isc3_briggs_urban_y_d_exponent": -1.0}) == pytest.approx(0.16 * 1000.0 / 1.4, rel=1e-12)
    cap = "float(E.pasquill_sigmas(3500.0, 'A')[1])"
    assert run(cap) == 5000.0
    assert run(cap, {"isc3_sigma_z_cap": 4000}) == 4000.0


@pytest.mark.req("FR-006-19")
@pytest.mark.oracle("analytical", "the urban minimum-distance row moves the warning threshold")
def test_fr_006_19_urban_minimum_distance_row() -> None:
    expr = "count_validity(lambda: E.pasquill_sigmas(150.0, 'D', terrain='urban'))"
    assert run(expr)["warnings"] == 0
    assert run(expr, {"isc3_urban_min_distance": 200})["warnings"] >= 1


@pytest.mark.req("FR-006-19")
@pytest.mark.oracle("analytical", "the well-mixed switch ratio 1.6 is a row: at sigma_z / z_i = 0.6 a ratio of 0.5 selects the uniform profile")
def test_fr_006_19_lid_uniform_ratio_row() -> None:
    q, u, sy, y, z, h, zi, sz = 1e-3, 3.0, 36.0, 0.0, 0.0, 5.0, 100.0, 60.0
    expr = f"float(E.gaussian_plume({q}, {u}, {y}, {z}, {h}, {sy}, {sz}, mixing_height={zi}))"
    series = (
        q
        / (2 * math.pi * u * sy * sz)
        * sum(
            math.exp(-((z - h + 2 * i * zi) ** 2) / (2 * sz**2)) + math.exp(-((z + h + 2 * i * zi) ** 2) / (2 * sz**2))
            for i in range(-80, 81)
        )
    )
    well_mixed = q / (math.sqrt(2 * math.pi) * u * sy * zi)  # sqrt(2 pi) sigma_z / z_i inside q / (2 pi u sy sz)
    assert abs(series - well_mixed) > 1e-4 * well_mixed  # the two branches differ at this ratio (about 2e-3 relative)
    assert run(expr) == pytest.approx(series, rel=1e-9)  # 0.6 < 1.6: the image series
    assert run(expr, {"isc3_lid_uniform_ratio": 0.5}) == pytest.approx(well_mixed, rel=1e-12)  # 0.6 >= 0.5: uniform

@pytest.mark.req("FR-006-19")
@pytest.mark.oracle("analytical", "the AP-42 range rows are the validity thresholds (range rows are (min, max) pairs)")
def test_fr_006_19_range_rows_move_the_validity_thresholds() -> None:
    heavy = "count_validity(lambda: E.ap42_unpaved_emission_factor(0.10, 320.0 * 907.18474, 'PM10'))"
    assert run(heavy)["warnings"] >= 1  # 320 short tons is above the published 290
    assert run(heavy, {"ap42_range_weight": [2.0, 400.0]})["warnings"] == 0
    silt = "count_validity(lambda: E.ap42_unpaved_emission_factor(0.30, 100.0 * 907.18474, 'PM10'))"
    assert run(silt)["warnings"] >= 1
    assert run(silt, {"ap42_range_silt": [1.8, 40.0]})["warnings"] == 0


@pytest.mark.req("FR-006-19")
@pytest.mark.oracle("analytical", "the lidar threshold rows decide the state")
def test_fr_006_19_lidar_threshold_rows() -> None:
    def state(t: float, target: str = "retroreflective") -> str:
        beta = -math.log(t) / 100.0
        return f"field(E.lidar_dust_return(100.0, {beta!r}, target={target!r}), 3)"

    assert run(state(0.78)) == "unaffected"
    assert run(state(0.78), {"lidar_dust_onset_transmittance": [0.71, 0.80]}) == "degraded"  # the upper end is the onset
    assert run(state(0.05)) == "degraded"  # above the retroreflective minimum 0.02
    assert run(state(0.05), {"lidar_dust_min_transmittance_retroreflective": 0.10}) == "lost"
    assert run(state(0.10, "low_reflectivity")) == "degraded"  # above the low-reflectivity minimum 0.06
    assert run(state(0.10, "low_reflectivity"), {"lidar_dust_min_transmittance_low_reflectivity": 0.30}) == "lost"

@pytest.mark.req("FR-006-19")
def test_fr_006_19_extinction_efficiency_row() -> None:
    expr = "float(quiet(lambda: E.mass_extinction_coefficient(10e-6, 2650.0)))"
    assert run(expr) == pytest.approx(3.0 * 2.0 / (2.0 * 2650.0 * 10e-6), rel=1e-12)
    assert run(expr, {"extinction_efficiency_large_particle": 3.0}) == pytest.approx(1.5 * run(expr), rel=1e-12)

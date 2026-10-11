"""T-002-031 (FR-002-09, FR-002-18, P-002-08): 30 CFR 816.67 PPV limit and maximum charge per delay.

Expected API (distance in m, `standard` an option):
    `B.ppv_limit(distance, standard="30cfr816.67")` -> maximum PPV in m/s: 1.25, 1.00 and 0.75 in/s for D <= 300 ft,
        300 ft < D <= 5,000 ft and D > 5,000 ft (30 CFR 816.67(d)(2)(i));
    `B.max_charge_per_delay(distance, standard="30cfr816.67")` -> W = (D / Ds)^2 in lb per 8-ms period (D in ft,
        Ds = 50, 55, 65 in the same three bands, 816.67(d)(3)(i)) converted to kg.
Exact unit definitions: 1 ft = 0.3048 m, 1 lb = 0.45359237 kg, 1 in = 0.0254 m. Any other `standard` raises
`InputError` naming `standard` and listing `30cfr816.67`.

Oracles: published regulation values (the verified rows, pinned with `knowledge` markers), spec 002 section 7.4
(`ppv_limit(304.8) = 0.0254 m/s`; at 50 m 0.03175 m/s; at 2,000 m 0.01905 m/s; `max_charge_per_delay(304.8) =
(1000/55)^2 = 330.57851 lb = 149.94789 kg`; TC-2) and the formula evaluated in this file with exact unit definitions.
Band edges are tested with a relative margin of 1e-9 (the conversion m -> ft rounds at 1e-16).

Spec finding (P-002-08 versus FR-002-09): the regulation's divisor Ds grows from band to band (50, 55, 65), so
W = (D/Ds)^2 DROPS at 300 ft (36 lb -> 29.8 lb) and at 5,000 ft (10,000 lb -> 5,917 lb).
`max_charge_per_delay` is therefore non-decreasing only WITHIN a band; the property tests below say so and the
edge drops are pinned from the formula.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from _table_helpers_a import rows_by_id
from hypothesis import assume, given, settings
from hypothesis import strategies as st

import minephys
from minephys import blasting as B

FT, LB, INCH = 0.3048, 0.45359237, 0.0254
NEAR_EDGE_M = 300.0 * FT  # 91.44 m
MID_EDGE_M = 5000.0 * FT  # 1,524 m
EPS = 1e-9


def limit_in_s(d_m: float) -> float:
    d_ft = d_m / FT
    return 1.25 if d_ft <= 300.0 else (1.00 if d_ft <= 5000.0 else 0.75)


def charge_kg(d_m: float) -> float:
    d_ft = d_m / FT
    ds = 50.0 if d_ft <= 300.0 else (55.0 if d_ft <= 5000.0 else 65.0)
    return (d_ft / ds) ** 2 * LB


@pytest.mark.req("FR-002-09")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 002 7.4: ppv_limit(304.8 m = 1000 ft) = 1.00 in/s = 0.0254 m/s; 50 m: 0.03175; 2000 m: 0.01905",
)
def test_ppv_limit_printed_values() -> None:
    mid = B.ppv_limit(304.8)
    assert type(mid) is np.float64
    assert mid == pytest.approx(0.0254, rel=1e-12)
    assert B.ppv_limit(50.0) == pytest.approx(0.03175, rel=1e-12)
    assert B.ppv_limit(2000.0) == pytest.approx(0.01905, rel=1e-12)


@pytest.mark.req("FR-002-09")
@pytest.mark.oracle(
    "hand-calculation", "spec 002 7.4: max_charge_per_delay(304.8 m) = (1000/55)^2 lb = 330.57851 lb = 149.94789 kg"
)
def test_max_charge_printed_value() -> None:
    got = B.max_charge_per_delay(304.8)
    assert type(got) is np.float64
    assert got == pytest.approx(149.94789, abs=5e-6)  # TC-2: 8 significant figures
    assert got / LB == pytest.approx(330.57851, abs=5e-6)  # in pounds
    assert got == pytest.approx((1000.0 / 55.0) ** 2 * LB, rel=1e-12)


@pytest.mark.req("FR-002-09")
@pytest.mark.oracle(
    "hand-calculation", "the three bands of 816.67(d)(2)(i): 1.25, 1.00, 0.75 in/s, edges at 300 ft and 5,000 ft"
)
@pytest.mark.parametrize(
    ("d_m", "in_s"),
    [
        (1.0, 1.25),
        (50.0, 1.25),
        (NEAR_EDGE_M * (1 - EPS), 1.25),
        (NEAR_EDGE_M * (1 + EPS), 1.00),
        (304.8, 1.00),
        (1000.0, 1.00),
        (MID_EDGE_M * (1 - EPS), 1.00),
        (MID_EDGE_M * (1 + EPS), 0.75),
        (2000.0, 0.75),
        (50000.0, 0.75),
    ],
)
def test_ppv_limit_bands(d_m: float, in_s: float) -> None:
    assert B.ppv_limit(d_m) == pytest.approx(in_s * INCH, rel=1e-12)


@pytest.mark.req("FR-002-09")
@pytest.mark.oracle(
    "hand-calculation", "the three divisors of 816.67(d)(3)(i): Ds = 50, 55, 65 ft/lb^0.5 in the same bands"
)
@pytest.mark.parametrize(
    "d_m",
    [
        10.0,
        50.0,
        NEAR_EDGE_M * (1 - EPS),
        NEAR_EDGE_M * (1 + EPS),
        304.8,
        1000.0,
        MID_EDGE_M * (1 - EPS),
        MID_EDGE_M * (1 + EPS),
        2000.0,
        8000.0,
    ],
)
def test_max_charge_bands(d_m: float) -> None:
    assert B.max_charge_per_delay(d_m) == pytest.approx(charge_kg(d_m), rel=1e-12)


@pytest.mark.req("FR-002-09")
@pytest.mark.req("P-002-08")
@pytest.mark.oracle(
    "hand-calculation",
    "the regulation's band edges: W drops from 36 lb to 29.8 lb at 300 ft and from 10,000 lb to 5,917 lb at 5,000 ft",
)
def test_charge_limit_drops_at_the_band_edges() -> None:
    just_below = B.max_charge_per_delay(NEAR_EDGE_M * (1 - EPS))
    just_above = B.max_charge_per_delay(NEAR_EDGE_M * (1 + EPS))
    assert just_below / LB == pytest.approx((300.0 / 50.0) ** 2, rel=1e-6)  # 36 lb
    assert just_above / LB == pytest.approx((300.0 / 55.0) ** 2, rel=1e-6)  # 29.75 lb
    assert just_above < just_below
    below = B.max_charge_per_delay(MID_EDGE_M * (1 - EPS))
    above = B.max_charge_per_delay(MID_EDGE_M * (1 + EPS))
    assert below / LB == pytest.approx((5000.0 / 55.0) ** 2, rel=1e-6)
    assert above / LB == pytest.approx((5000.0 / 65.0) ** 2, rel=1e-6)
    assert above < below


@pytest.mark.req("FR-002-09")
@pytest.mark.oracle("hand-calculation", "arrays: the band is chosen per element")
def test_arrays_and_bands_per_element() -> None:
    d = np.array([10.0, 91.0, 92.0, 1000.0, 1523.0, 1525.0, 9000.0])
    lim = B.ppv_limit(d)
    np.testing.assert_allclose(lim, [limit_in_s(x) * INCH for x in d], rtol=1e-12)
    w = B.max_charge_per_delay(d)
    np.testing.assert_allclose(w, [charge_kg(x) for x in d], rtol=1e-12)
    assert B.ppv_limit(np.empty(0)).shape == (0,)
    assert B.max_charge_per_delay(np.empty(0)).dtype == np.float64


@pytest.mark.req("FR-002-18")
@pytest.mark.oracle(
    "hand-calculation", "FR-000-15: only '30cfr816.67' is a standard; the error lists it; matching is exact"
)
@pytest.mark.parametrize("bad", ["usbm8507", "30CFR816.67", "30cfr816.67 ", " 30cfr816.67", "", "30cfr816", "din4150"])
@pytest.mark.parametrize("fn", ["ppv_limit", "max_charge_per_delay"])
def test_unknown_standard(fn: str, bad: str) -> None:
    with pytest.raises(minephys.InputError) as ei:
        getattr(B, fn)(304.8, standard=bad)
    assert ei.value.argument == "standard"
    assert "30cfr816.67" in str(ei.value)
    assert getattr(B, fn)(304.8, standard="30cfr816.67") > 0.0


@pytest.mark.req("P-002-08")
@pytest.mark.oracle(
    "analytical", "the PPV limit never increases with distance; the charge limit never decreases within a band"
)
@settings(deadline=None)
@given(d1=st.floats(1e-3, 1e4), d2=st.floats(1e-3, 1e4))
def test_monotonicity(d1: float, d2: float) -> None:
    lo, hi = sorted((d1, d2))
    assert float(B.ppv_limit(hi)) <= float(B.ppv_limit(lo))
    same_band = (lo / FT <= 300.0) == (hi / FT <= 300.0) and (lo / FT <= 5000.0) == (hi / FT <= 5000.0)
    assume(same_band)
    assert float(B.max_charge_per_delay(hi)) >= float(B.max_charge_per_delay(lo))


# ---------------------------------------------------------------- knowledge rows pinned (all verified)

PPV_ROWS = [("near", 1.25, 10.0), ("mid", 1.00, 500.0), ("far", 0.75, 3000.0)]


@pytest.mark.req("FR-002-09")
@pytest.mark.knowledge("cfr_816_67_ppv_limit_near")
@pytest.mark.oracle("worked-example", "cfr30_816_67 816.67(d)(2)(i): 1.25 in/s for 0 to 300 ft")
def test_row_ppv_limit_near() -> None:
    row = rows_by_id("blasting")["cfr_816_67_ppv_limit_near"]
    assert (row["value"], row["units"]) == (1.25, "in/s")
    assert B.ppv_limit(10.0) == pytest.approx(row["value"] * INCH, rel=1e-12)


@pytest.mark.req("FR-002-09")
@pytest.mark.knowledge("cfr_816_67_ppv_limit_mid")
@pytest.mark.oracle("worked-example", "cfr30_816_67 816.67(d)(2)(i): 1.00 in/s for 301 to 5,000 ft")
def test_row_ppv_limit_mid() -> None:
    row = rows_by_id("blasting")["cfr_816_67_ppv_limit_mid"]
    assert (row["value"], row["units"]) == (1.00, "in/s")
    assert B.ppv_limit(500.0) == pytest.approx(row["value"] * INCH, rel=1e-12)


@pytest.mark.req("FR-002-09")
@pytest.mark.knowledge("cfr_816_67_ppv_limit_far")
@pytest.mark.oracle("worked-example", "cfr30_816_67 816.67(d)(2)(i): 0.75 in/s for 5,001 ft and beyond")
def test_row_ppv_limit_far() -> None:
    row = rows_by_id("blasting")["cfr_816_67_ppv_limit_far"]
    assert (row["value"], row["units"]) == (0.75, "in/s")
    assert B.ppv_limit(3000.0) == pytest.approx(row["value"] * INCH, rel=1e-12)


@pytest.mark.req("FR-002-09")
@pytest.mark.knowledge("cfr_816_67_distance_band_near_max")
@pytest.mark.oracle("worked-example", "cfr30_816_67 816.67(d)(2)(i): the first band ends at 300 ft")
def test_row_distance_band_near_max() -> None:
    row = rows_by_id("blasting")["cfr_816_67_distance_band_near_max"]
    assert (row["value"], row["units"]) == (300, "ft")
    edge = row["value"] * FT
    assert B.ppv_limit(edge * (1 - EPS)) > B.ppv_limit(edge * (1 + EPS))


@pytest.mark.req("FR-002-09")
@pytest.mark.knowledge("cfr_816_67_distance_band_mid_max")
@pytest.mark.oracle("worked-example", "cfr30_816_67 816.67(d)(2)(i): the second band ends at 5,000 ft")
def test_row_distance_band_mid_max() -> None:
    row = rows_by_id("blasting")["cfr_816_67_distance_band_mid_max"]
    assert (row["value"], row["units"]) == (5000, "ft")
    edge = row["value"] * FT
    assert B.ppv_limit(edge * (1 - EPS)) > B.ppv_limit(edge * (1 + EPS))


@pytest.mark.req("FR-002-09")
@pytest.mark.knowledge("cfr_816_67_scaled_distance_factor_near")
@pytest.mark.oracle("worked-example", "cfr30_816_67 816.67(d)(3)(i): Ds = 50 ft/lb^0.5 up to 300 ft")
def test_row_scaled_distance_factor_near() -> None:
    row = rows_by_id("blasting")["cfr_816_67_scaled_distance_factor_near"]
    assert row["value"] == 50
    assert B.max_charge_per_delay(50.0) == pytest.approx((50.0 / FT / row["value"]) ** 2 * LB, rel=1e-12)


@pytest.mark.req("FR-002-09")
@pytest.mark.knowledge("cfr_816_67_scaled_distance_factor_mid")
@pytest.mark.oracle("worked-example", "cfr30_816_67 816.67(d)(3)(i): Ds = 55 ft/lb^0.5 from 301 to 5,000 ft")
def test_row_scaled_distance_factor_mid() -> None:
    row = rows_by_id("blasting")["cfr_816_67_scaled_distance_factor_mid"]
    assert row["value"] == 55
    assert B.max_charge_per_delay(304.8) == pytest.approx((1000.0 / row["value"]) ** 2 * LB, rel=1e-12)


@pytest.mark.req("FR-002-09")
@pytest.mark.knowledge("cfr_816_67_scaled_distance_factor_far")
@pytest.mark.oracle("worked-example", "cfr30_816_67 816.67(d)(3)(i): Ds = 65 ft/lb^0.5 beyond 5,000 ft")
def test_row_scaled_distance_factor_far() -> None:
    row = rows_by_id("blasting")["cfr_816_67_scaled_distance_factor_far"]
    assert row["value"] == 65
    assert B.max_charge_per_delay(3000.0) == pytest.approx((3000.0 / FT / row["value"]) ** 2 * LB, rel=1e-12)
    assert math.isfinite(float(B.max_charge_per_delay(3000.0)))

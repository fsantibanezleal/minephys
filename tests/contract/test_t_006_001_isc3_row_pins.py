"""T-006-001 (DC-006-01): literal `@pytest.mark.knowledge("<row id>")` pins for the ISC3 rows that no other test pins literally.

The values below were read on the EPA ISC3 user's guide, volume II (EPA-454/B-95-003b, `epa1995isc3v2`), Table 1-1 (p. 1-16),
Table 1-2 (pp. 1-17 and 1-18), Table 1-3 and Table 1-4 (p. 1-19), and transcribed here by hand from the text of those pages.
Each test compares the value of one row of `src/minephys/knowledge/environment.yaml` (parsed with `yaml.safe_load`, independently
of the loader) with the printed one. Class A band 9 of Table 1-2 prints `**` (sigma_z equals 5000 m beyond 3.11 km), written as
a = 5000 m and b = 0; class C of Table 1-4 prints `0.20 x` with no correction term, written as slope 0 and exponent 0.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

TABLE = Path(__file__).resolve().parents[2] / "src" / "minephys" / "knowledge" / "environment.yaml"


def _row(row_id: str) -> dict[str, Any]:
    rows = {r["id"]: r for r in yaml.safe_load(TABLE.read_text(encoding="utf-8"))["rows"]}
    assert row_id in rows, f"{row_id} is not in the environment table"
    return rows[row_id]


def _check(row_id: str, printed: float) -> None:
    row = _row(row_id)
    assert row["value"] == printed
    assert row["verification"] == "verified" and row["citation"] == "epa1995isc3v2"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_y_c_b")
def test_pin_isc3_pg_sigma_y_c_b() -> None:
    _check("isc3_pg_sigma_y_c_b", 18.333)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_y_c_e")
def test_pin_isc3_pg_sigma_y_c_e() -> None:
    _check("isc3_pg_sigma_y_c_e", 6.25)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_y_d_b")
def test_pin_isc3_pg_sigma_y_d_b() -> None:
    _check("isc3_pg_sigma_y_d_b", 1.8096)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_y_d_e")
def test_pin_isc3_pg_sigma_y_d_e() -> None:
    _check("isc3_pg_sigma_y_d_e", 0.54287)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_1_xmax")
def test_pin_isc3_pg_sigma_z_a_1_xmax() -> None:
    _check("isc3_pg_sigma_z_a_1_xmax", 0.1)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_2_xmax")
def test_pin_isc3_pg_sigma_z_a_2_xmax() -> None:
    _check("isc3_pg_sigma_z_a_2_xmax", 0.15)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_3_xmax")
def test_pin_isc3_pg_sigma_z_a_3_xmax() -> None:
    _check("isc3_pg_sigma_z_a_3_xmax", 0.2)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_4_xmax")
def test_pin_isc3_pg_sigma_z_a_4_xmax() -> None:
    _check("isc3_pg_sigma_z_a_4_xmax", 0.25)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_5_xmax")
def test_pin_isc3_pg_sigma_z_a_5_xmax() -> None:
    _check("isc3_pg_sigma_z_a_5_xmax", 0.3)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_6_xmax")
def test_pin_isc3_pg_sigma_z_a_6_xmax() -> None:
    _check("isc3_pg_sigma_z_a_6_xmax", 0.4)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_7_xmax")
def test_pin_isc3_pg_sigma_z_a_7_xmax() -> None:
    _check("isc3_pg_sigma_z_a_7_xmax", 0.5)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_8_xmax")
def test_pin_isc3_pg_sigma_z_a_8_xmax() -> None:
    _check("isc3_pg_sigma_z_a_8_xmax", 3.11)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_1_a")
def test_pin_isc3_pg_sigma_z_a_1_a() -> None:
    _check("isc3_pg_sigma_z_a_1_a", 122.8)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_2_a")
def test_pin_isc3_pg_sigma_z_a_2_a() -> None:
    _check("isc3_pg_sigma_z_a_2_a", 158.08)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_3_a")
def test_pin_isc3_pg_sigma_z_a_3_a() -> None:
    _check("isc3_pg_sigma_z_a_3_a", 170.22)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_4_a")
def test_pin_isc3_pg_sigma_z_a_4_a() -> None:
    _check("isc3_pg_sigma_z_a_4_a", 179.52)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_5_a")
def test_pin_isc3_pg_sigma_z_a_5_a() -> None:
    _check("isc3_pg_sigma_z_a_5_a", 217.41)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_6_a")
def test_pin_isc3_pg_sigma_z_a_6_a() -> None:
    _check("isc3_pg_sigma_z_a_6_a", 258.89)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_7_a")
def test_pin_isc3_pg_sigma_z_a_7_a() -> None:
    _check("isc3_pg_sigma_z_a_7_a", 346.75)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_8_a")
def test_pin_isc3_pg_sigma_z_a_8_a() -> None:
    _check("isc3_pg_sigma_z_a_8_a", 453.85)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_9_a")
def test_pin_isc3_pg_sigma_z_a_9_a() -> None:
    _check("isc3_pg_sigma_z_a_9_a", 5000)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_1_b")
def test_pin_isc3_pg_sigma_z_a_1_b() -> None:
    _check("isc3_pg_sigma_z_a_1_b", 0.9447)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_2_b")
def test_pin_isc3_pg_sigma_z_a_2_b() -> None:
    _check("isc3_pg_sigma_z_a_2_b", 1.0542)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_3_b")
def test_pin_isc3_pg_sigma_z_a_3_b() -> None:
    _check("isc3_pg_sigma_z_a_3_b", 1.0932)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_4_b")
def test_pin_isc3_pg_sigma_z_a_4_b() -> None:
    _check("isc3_pg_sigma_z_a_4_b", 1.1262)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_5_b")
def test_pin_isc3_pg_sigma_z_a_5_b() -> None:
    _check("isc3_pg_sigma_z_a_5_b", 1.2644)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_6_b")
def test_pin_isc3_pg_sigma_z_a_6_b() -> None:
    _check("isc3_pg_sigma_z_a_6_b", 1.4094)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_7_b")
def test_pin_isc3_pg_sigma_z_a_7_b() -> None:
    _check("isc3_pg_sigma_z_a_7_b", 1.7283)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_8_b")
def test_pin_isc3_pg_sigma_z_a_8_b() -> None:
    _check("isc3_pg_sigma_z_a_8_b", 2.1166)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_a_9_b")
def test_pin_isc3_pg_sigma_z_a_9_b() -> None:
    _check("isc3_pg_sigma_z_a_9_b", 0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_b_1_xmax")
def test_pin_isc3_pg_sigma_z_b_1_xmax() -> None:
    _check("isc3_pg_sigma_z_b_1_xmax", 0.2)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_b_2_xmax")
def test_pin_isc3_pg_sigma_z_b_2_xmax() -> None:
    _check("isc3_pg_sigma_z_b_2_xmax", 0.4)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_b_1_a")
def test_pin_isc3_pg_sigma_z_b_1_a() -> None:
    _check("isc3_pg_sigma_z_b_1_a", 90.673)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_b_2_a")
def test_pin_isc3_pg_sigma_z_b_2_a() -> None:
    _check("isc3_pg_sigma_z_b_2_a", 98.483)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_b_3_a")
def test_pin_isc3_pg_sigma_z_b_3_a() -> None:
    _check("isc3_pg_sigma_z_b_3_a", 109.3)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_b_1_b")
def test_pin_isc3_pg_sigma_z_b_1_b() -> None:
    _check("isc3_pg_sigma_z_b_1_b", 0.93198)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_b_2_b")
def test_pin_isc3_pg_sigma_z_b_2_b() -> None:
    _check("isc3_pg_sigma_z_b_2_b", 0.98332)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_b_3_b")
def test_pin_isc3_pg_sigma_z_b_3_b() -> None:
    _check("isc3_pg_sigma_z_b_3_b", 1.0971)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_c_1_a")
def test_pin_isc3_pg_sigma_z_c_1_a() -> None:
    _check("isc3_pg_sigma_z_c_1_a", 61.141)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_c_1_b")
def test_pin_isc3_pg_sigma_z_c_1_b() -> None:
    _check("isc3_pg_sigma_z_c_1_b", 0.91465)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_1_xmax")
def test_pin_isc3_pg_sigma_z_d_1_xmax() -> None:
    _check("isc3_pg_sigma_z_d_1_xmax", 0.3)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_2_xmax")
def test_pin_isc3_pg_sigma_z_d_2_xmax() -> None:
    _check("isc3_pg_sigma_z_d_2_xmax", 1.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_3_xmax")
def test_pin_isc3_pg_sigma_z_d_3_xmax() -> None:
    _check("isc3_pg_sigma_z_d_3_xmax", 3.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_4_xmax")
def test_pin_isc3_pg_sigma_z_d_4_xmax() -> None:
    _check("isc3_pg_sigma_z_d_4_xmax", 10.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_5_xmax")
def test_pin_isc3_pg_sigma_z_d_5_xmax() -> None:
    _check("isc3_pg_sigma_z_d_5_xmax", 30.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_1_a")
def test_pin_isc3_pg_sigma_z_d_1_a() -> None:
    _check("isc3_pg_sigma_z_d_1_a", 34.459)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_2_a")
def test_pin_isc3_pg_sigma_z_d_2_a() -> None:
    _check("isc3_pg_sigma_z_d_2_a", 32.093)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_3_a")
def test_pin_isc3_pg_sigma_z_d_3_a() -> None:
    _check("isc3_pg_sigma_z_d_3_a", 32.093)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_4_a")
def test_pin_isc3_pg_sigma_z_d_4_a() -> None:
    _check("isc3_pg_sigma_z_d_4_a", 33.504)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_5_a")
def test_pin_isc3_pg_sigma_z_d_5_a() -> None:
    _check("isc3_pg_sigma_z_d_5_a", 36.65)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_6_a")
def test_pin_isc3_pg_sigma_z_d_6_a() -> None:
    _check("isc3_pg_sigma_z_d_6_a", 44.053)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_1_b")
def test_pin_isc3_pg_sigma_z_d_1_b() -> None:
    _check("isc3_pg_sigma_z_d_1_b", 0.86974)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_2_b")
def test_pin_isc3_pg_sigma_z_d_2_b() -> None:
    _check("isc3_pg_sigma_z_d_2_b", 0.81066)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_3_b")
def test_pin_isc3_pg_sigma_z_d_3_b() -> None:
    _check("isc3_pg_sigma_z_d_3_b", 0.64403)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_4_b")
def test_pin_isc3_pg_sigma_z_d_4_b() -> None:
    _check("isc3_pg_sigma_z_d_4_b", 0.60486)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_5_b")
def test_pin_isc3_pg_sigma_z_d_5_b() -> None:
    _check("isc3_pg_sigma_z_d_5_b", 0.56589)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_d_6_b")
def test_pin_isc3_pg_sigma_z_d_6_b() -> None:
    _check("isc3_pg_sigma_z_d_6_b", 0.51179)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_1_xmax")
def test_pin_isc3_pg_sigma_z_e_1_xmax() -> None:
    _check("isc3_pg_sigma_z_e_1_xmax", 0.1)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_2_xmax")
def test_pin_isc3_pg_sigma_z_e_2_xmax() -> None:
    _check("isc3_pg_sigma_z_e_2_xmax", 0.3)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_3_xmax")
def test_pin_isc3_pg_sigma_z_e_3_xmax() -> None:
    _check("isc3_pg_sigma_z_e_3_xmax", 1.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_4_xmax")
def test_pin_isc3_pg_sigma_z_e_4_xmax() -> None:
    _check("isc3_pg_sigma_z_e_4_xmax", 2.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_5_xmax")
def test_pin_isc3_pg_sigma_z_e_5_xmax() -> None:
    _check("isc3_pg_sigma_z_e_5_xmax", 4.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_6_xmax")
def test_pin_isc3_pg_sigma_z_e_6_xmax() -> None:
    _check("isc3_pg_sigma_z_e_6_xmax", 10.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_7_xmax")
def test_pin_isc3_pg_sigma_z_e_7_xmax() -> None:
    _check("isc3_pg_sigma_z_e_7_xmax", 20.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_8_xmax")
def test_pin_isc3_pg_sigma_z_e_8_xmax() -> None:
    _check("isc3_pg_sigma_z_e_8_xmax", 40.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_1_a")
def test_pin_isc3_pg_sigma_z_e_1_a() -> None:
    _check("isc3_pg_sigma_z_e_1_a", 24.26)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_2_a")
def test_pin_isc3_pg_sigma_z_e_2_a() -> None:
    _check("isc3_pg_sigma_z_e_2_a", 23.331)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_3_a")
def test_pin_isc3_pg_sigma_z_e_3_a() -> None:
    _check("isc3_pg_sigma_z_e_3_a", 21.628)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_4_a")
def test_pin_isc3_pg_sigma_z_e_4_a() -> None:
    _check("isc3_pg_sigma_z_e_4_a", 21.628)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_5_a")
def test_pin_isc3_pg_sigma_z_e_5_a() -> None:
    _check("isc3_pg_sigma_z_e_5_a", 22.534)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_6_a")
def test_pin_isc3_pg_sigma_z_e_6_a() -> None:
    _check("isc3_pg_sigma_z_e_6_a", 24.703)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_7_a")
def test_pin_isc3_pg_sigma_z_e_7_a() -> None:
    _check("isc3_pg_sigma_z_e_7_a", 26.97)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_8_a")
def test_pin_isc3_pg_sigma_z_e_8_a() -> None:
    _check("isc3_pg_sigma_z_e_8_a", 35.42)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_9_a")
def test_pin_isc3_pg_sigma_z_e_9_a() -> None:
    _check("isc3_pg_sigma_z_e_9_a", 47.618)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_1_b")
def test_pin_isc3_pg_sigma_z_e_1_b() -> None:
    _check("isc3_pg_sigma_z_e_1_b", 0.8366)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_2_b")
def test_pin_isc3_pg_sigma_z_e_2_b() -> None:
    _check("isc3_pg_sigma_z_e_2_b", 0.81956)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_3_b")
def test_pin_isc3_pg_sigma_z_e_3_b() -> None:
    _check("isc3_pg_sigma_z_e_3_b", 0.7566)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_4_b")
def test_pin_isc3_pg_sigma_z_e_4_b() -> None:
    _check("isc3_pg_sigma_z_e_4_b", 0.63077)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_5_b")
def test_pin_isc3_pg_sigma_z_e_5_b() -> None:
    _check("isc3_pg_sigma_z_e_5_b", 0.57154)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_6_b")
def test_pin_isc3_pg_sigma_z_e_6_b() -> None:
    _check("isc3_pg_sigma_z_e_6_b", 0.50527)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_7_b")
def test_pin_isc3_pg_sigma_z_e_7_b() -> None:
    _check("isc3_pg_sigma_z_e_7_b", 0.46713)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_8_b")
def test_pin_isc3_pg_sigma_z_e_8_b() -> None:
    _check("isc3_pg_sigma_z_e_8_b", 0.37615)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_e_9_b")
def test_pin_isc3_pg_sigma_z_e_9_b() -> None:
    _check("isc3_pg_sigma_z_e_9_b", 0.29592)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_1_xmax")
def test_pin_isc3_pg_sigma_z_f_1_xmax() -> None:
    _check("isc3_pg_sigma_z_f_1_xmax", 0.2)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_2_xmax")
def test_pin_isc3_pg_sigma_z_f_2_xmax() -> None:
    _check("isc3_pg_sigma_z_f_2_xmax", 0.7)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_3_xmax")
def test_pin_isc3_pg_sigma_z_f_3_xmax() -> None:
    _check("isc3_pg_sigma_z_f_3_xmax", 1.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_4_xmax")
def test_pin_isc3_pg_sigma_z_f_4_xmax() -> None:
    _check("isc3_pg_sigma_z_f_4_xmax", 2.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_5_xmax")
def test_pin_isc3_pg_sigma_z_f_5_xmax() -> None:
    _check("isc3_pg_sigma_z_f_5_xmax", 3.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_6_xmax")
def test_pin_isc3_pg_sigma_z_f_6_xmax() -> None:
    _check("isc3_pg_sigma_z_f_6_xmax", 7.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_7_xmax")
def test_pin_isc3_pg_sigma_z_f_7_xmax() -> None:
    _check("isc3_pg_sigma_z_f_7_xmax", 15.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_8_xmax")
def test_pin_isc3_pg_sigma_z_f_8_xmax() -> None:
    _check("isc3_pg_sigma_z_f_8_xmax", 30.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_9_xmax")
def test_pin_isc3_pg_sigma_z_f_9_xmax() -> None:
    _check("isc3_pg_sigma_z_f_9_xmax", 60.0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_1_a")
def test_pin_isc3_pg_sigma_z_f_1_a() -> None:
    _check("isc3_pg_sigma_z_f_1_a", 15.209)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_2_a")
def test_pin_isc3_pg_sigma_z_f_2_a() -> None:
    _check("isc3_pg_sigma_z_f_2_a", 14.457)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_3_a")
def test_pin_isc3_pg_sigma_z_f_3_a() -> None:
    _check("isc3_pg_sigma_z_f_3_a", 13.953)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_4_a")
def test_pin_isc3_pg_sigma_z_f_4_a() -> None:
    _check("isc3_pg_sigma_z_f_4_a", 13.953)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_5_a")
def test_pin_isc3_pg_sigma_z_f_5_a() -> None:
    _check("isc3_pg_sigma_z_f_5_a", 14.823)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_6_a")
def test_pin_isc3_pg_sigma_z_f_6_a() -> None:
    _check("isc3_pg_sigma_z_f_6_a", 16.187)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_7_a")
def test_pin_isc3_pg_sigma_z_f_7_a() -> None:
    _check("isc3_pg_sigma_z_f_7_a", 17.836)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_8_a")
def test_pin_isc3_pg_sigma_z_f_8_a() -> None:
    _check("isc3_pg_sigma_z_f_8_a", 22.651)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_9_a")
def test_pin_isc3_pg_sigma_z_f_9_a() -> None:
    _check("isc3_pg_sigma_z_f_9_a", 27.074)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_10_a")
def test_pin_isc3_pg_sigma_z_f_10_a() -> None:
    _check("isc3_pg_sigma_z_f_10_a", 34.219)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_1_b")
def test_pin_isc3_pg_sigma_z_f_1_b() -> None:
    _check("isc3_pg_sigma_z_f_1_b", 0.81558)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_2_b")
def test_pin_isc3_pg_sigma_z_f_2_b() -> None:
    _check("isc3_pg_sigma_z_f_2_b", 0.78407)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_3_b")
def test_pin_isc3_pg_sigma_z_f_3_b() -> None:
    _check("isc3_pg_sigma_z_f_3_b", 0.68465)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_4_b")
def test_pin_isc3_pg_sigma_z_f_4_b() -> None:
    _check("isc3_pg_sigma_z_f_4_b", 0.63227)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_5_b")
def test_pin_isc3_pg_sigma_z_f_5_b() -> None:
    _check("isc3_pg_sigma_z_f_5_b", 0.54503)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_6_b")
def test_pin_isc3_pg_sigma_z_f_6_b() -> None:
    _check("isc3_pg_sigma_z_f_6_b", 0.4649)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_7_b")
def test_pin_isc3_pg_sigma_z_f_7_b() -> None:
    _check("isc3_pg_sigma_z_f_7_b", 0.41507)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_8_b")
def test_pin_isc3_pg_sigma_z_f_8_b() -> None:
    _check("isc3_pg_sigma_z_f_8_b", 0.32681)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_9_b")
def test_pin_isc3_pg_sigma_z_f_9_b() -> None:
    _check("isc3_pg_sigma_z_f_9_b", 0.27436)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_pg_sigma_z_f_10_b")
def test_pin_isc3_pg_sigma_z_f_10_b() -> None:
    _check("isc3_pg_sigma_z_f_10_b", 0.21716)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_a_coef")
def test_pin_isc3_briggs_urban_y_a_coef() -> None:
    _check("isc3_briggs_urban_y_a_coef", 0.32)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_a_slope")
def test_pin_isc3_briggs_urban_y_a_slope() -> None:
    _check("isc3_briggs_urban_y_a_slope", 0.0004)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_a_exponent")
def test_pin_isc3_briggs_urban_y_a_exponent() -> None:
    _check("isc3_briggs_urban_y_a_exponent", -0.5)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_b_coef")
def test_pin_isc3_briggs_urban_y_b_coef() -> None:
    _check("isc3_briggs_urban_y_b_coef", 0.32)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_b_slope")
def test_pin_isc3_briggs_urban_y_b_slope() -> None:
    _check("isc3_briggs_urban_y_b_slope", 0.0004)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_b_exponent")
def test_pin_isc3_briggs_urban_y_b_exponent() -> None:
    _check("isc3_briggs_urban_y_b_exponent", -0.5)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_c_coef")
def test_pin_isc3_briggs_urban_y_c_coef() -> None:
    _check("isc3_briggs_urban_y_c_coef", 0.22)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_c_slope")
def test_pin_isc3_briggs_urban_y_c_slope() -> None:
    _check("isc3_briggs_urban_y_c_slope", 0.0004)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_c_exponent")
def test_pin_isc3_briggs_urban_y_c_exponent() -> None:
    _check("isc3_briggs_urban_y_c_exponent", -0.5)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_e_coef")
def test_pin_isc3_briggs_urban_y_e_coef() -> None:
    _check("isc3_briggs_urban_y_e_coef", 0.11)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_e_slope")
def test_pin_isc3_briggs_urban_y_e_slope() -> None:
    _check("isc3_briggs_urban_y_e_slope", 0.0004)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_e_exponent")
def test_pin_isc3_briggs_urban_y_e_exponent() -> None:
    _check("isc3_briggs_urban_y_e_exponent", -0.5)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_f_coef")
def test_pin_isc3_briggs_urban_y_f_coef() -> None:
    _check("isc3_briggs_urban_y_f_coef", 0.11)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_f_slope")
def test_pin_isc3_briggs_urban_y_f_slope() -> None:
    _check("isc3_briggs_urban_y_f_slope", 0.0004)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_y_f_exponent")
def test_pin_isc3_briggs_urban_y_f_exponent() -> None:
    _check("isc3_briggs_urban_y_f_exponent", -0.5)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_a_coef")
def test_pin_isc3_briggs_urban_z_a_coef() -> None:
    _check("isc3_briggs_urban_z_a_coef", 0.24)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_a_slope")
def test_pin_isc3_briggs_urban_z_a_slope() -> None:
    _check("isc3_briggs_urban_z_a_slope", 0.001)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_a_exponent")
def test_pin_isc3_briggs_urban_z_a_exponent() -> None:
    _check("isc3_briggs_urban_z_a_exponent", 0.5)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_b_coef")
def test_pin_isc3_briggs_urban_z_b_coef() -> None:
    _check("isc3_briggs_urban_z_b_coef", 0.24)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_b_slope")
def test_pin_isc3_briggs_urban_z_b_slope() -> None:
    _check("isc3_briggs_urban_z_b_slope", 0.001)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_b_exponent")
def test_pin_isc3_briggs_urban_z_b_exponent() -> None:
    _check("isc3_briggs_urban_z_b_exponent", 0.5)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_c_coef")
def test_pin_isc3_briggs_urban_z_c_coef() -> None:
    _check("isc3_briggs_urban_z_c_coef", 0.2)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_c_slope")
def test_pin_isc3_briggs_urban_z_c_slope() -> None:
    _check("isc3_briggs_urban_z_c_slope", 0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_c_exponent")
def test_pin_isc3_briggs_urban_z_c_exponent() -> None:
    _check("isc3_briggs_urban_z_c_exponent", 0)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_e_coef")
def test_pin_isc3_briggs_urban_z_e_coef() -> None:
    _check("isc3_briggs_urban_z_e_coef", 0.08)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_e_slope")
def test_pin_isc3_briggs_urban_z_e_slope() -> None:
    _check("isc3_briggs_urban_z_e_slope", 0.0015)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_e_exponent")
def test_pin_isc3_briggs_urban_z_e_exponent() -> None:
    _check("isc3_briggs_urban_z_e_exponent", -0.5)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_f_coef")
def test_pin_isc3_briggs_urban_z_f_coef() -> None:
    _check("isc3_briggs_urban_z_f_coef", 0.08)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_f_slope")
def test_pin_isc3_briggs_urban_z_f_slope() -> None:
    _check("isc3_briggs_urban_z_f_slope", 0.0015)


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "value printed in the ISC3 volume II table, transcribed by hand")
@pytest.mark.knowledge("isc3_briggs_urban_z_f_exponent")
def test_pin_isc3_briggs_urban_z_f_exponent() -> None:
    _check("isc3_briggs_urban_z_f_exponent", -0.5)

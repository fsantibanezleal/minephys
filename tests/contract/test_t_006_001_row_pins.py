"""T-006-001 (DC-006-01): literal `@pytest.mark.knowledge("<row id>")` pins for the verified environment rows that no other test pins literally.

`tests/contract/test_t_006_001_environment_knowledge.py` pins every verified row through a marker built at import time
(`pytest.mark.knowledge(row_id)`); tools that look for the pins by source text (`tools/check_knowledge.py`, the SC-008-01 and FR-008-14
checks of spec 008, `tools/trace.py`) read only string literals, so each such row also needs a literal marker somewhere. The verified
rows of the section 7 list that the unit tests of spec 006 do not pin literally are listed here, each with its published value or range
(AP-42 Table 13.2.2-2 and Table 13.2.2-3, ISC3 volume II Table 1-1 and the Briggs urban formulae of Table 1-3; hand transcription, the YAML
parsed with `yaml.safe_load` independently of the loader).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

TABLE = Path(__file__).resolve().parents[2] / "src" / "minephys" / "knowledge" / "environment.yaml"


def _row(row_id: str) -> dict[str, Any]:
    assert TABLE.is_file(), "missing src/minephys/knowledge/environment.yaml"
    rows = {r["id"]: r for r in yaml.safe_load(TABLE.read_text(encoding="utf-8"))["rows"]}
    assert row_id in rows, f"{row_id} is not in the environment table"
    return rows[row_id]


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("ap42_industrial_k_pm25")
def test_pin_ap42_industrial_k_pm25() -> None:
    row = _row("ap42_industrial_k_pm25")
    assert row["value"] == 0.15
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("ap42_industrial_k_pm30")
def test_pin_ap42_industrial_k_pm30() -> None:
    row = _row("ap42_industrial_k_pm30")
    assert row["value"] == 4.9
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("ap42_industrial_a_pm25")
def test_pin_ap42_industrial_a_pm25() -> None:
    row = _row("ap42_industrial_a_pm25")
    assert row["value"] == 0.9
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("ap42_industrial_a_pm30")
def test_pin_ap42_industrial_a_pm30() -> None:
    row = _row("ap42_industrial_a_pm30")
    assert row["value"] == 0.7
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("ap42_industrial_b_pm25")
def test_pin_ap42_industrial_b_pm25() -> None:
    row = _row("ap42_industrial_b_pm25")
    assert row["value"] == 0.45
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("ap42_industrial_b_pm30")
def test_pin_ap42_industrial_b_pm30() -> None:
    row = _row("ap42_industrial_b_pm30")
    assert row["value"] == 0.45
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("ap42_watering_m_2")
def test_pin_ap42_watering_m_2() -> None:
    row = _row("ap42_watering_m_2")
    assert row["value"] == 1
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("ap42_watering_m_3")
def test_pin_ap42_watering_m_3() -> None:
    row = _row("ap42_watering_m_3")
    assert row["value"] == 2
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("ap42_watering_ce_1")
def test_pin_ap42_watering_ce_1() -> None:
    row = _row("ap42_watering_ce_1")
    assert row["value"] == 0
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("ap42_watering_ce_2")
def test_pin_ap42_watering_ce_2() -> None:
    row = _row("ap42_watering_ce_2")
    assert row["value"] == 0
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_pg_sigma_y_c_a")
def test_pin_isc3_pg_sigma_y_c_a() -> None:
    row = _row("isc3_pg_sigma_y_c_a")
    assert row["value"] == 24.167
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_pg_sigma_y_d_a")
def test_pin_isc3_pg_sigma_y_d_a() -> None:
    row = _row("isc3_pg_sigma_y_d_a")
    assert row["value"] == 2.5334
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_pg_sigma_y_c_c")
def test_pin_isc3_pg_sigma_y_c_c() -> None:
    row = _row("isc3_pg_sigma_y_c_c")
    assert row["value"] == 12.5
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_pg_sigma_y_d_c")
def test_pin_isc3_pg_sigma_y_d_c() -> None:
    row = _row("isc3_pg_sigma_y_d_c")
    assert row["value"] == 1.0857
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_pg_sigma_y_c_d")
def test_pin_isc3_pg_sigma_y_c_d() -> None:
    row = _row("isc3_pg_sigma_y_c_d")
    assert row["value"] == 8.333
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_pg_sigma_y_d_d")
def test_pin_isc3_pg_sigma_y_d_d() -> None:
    row = _row("isc3_pg_sigma_y_d_d")
    assert row["value"] == 0.72382
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_pg_sigma_y_c_f")
def test_pin_isc3_pg_sigma_y_c_f() -> None:
    row = _row("isc3_pg_sigma_y_c_f")
    assert row["value"] == 4.1667
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_pg_sigma_y_d_f")
def test_pin_isc3_pg_sigma_y_d_f() -> None:
    row = _row("isc3_pg_sigma_y_d_f")
    assert row["value"] == 0.36191
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_briggs_urban_y_d_slope")
def test_pin_isc3_briggs_urban_y_d_slope() -> None:
    row = _row("isc3_briggs_urban_y_d_slope")
    assert row["value"] == 0.0004
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_briggs_urban_y_d_exponent")
def test_pin_isc3_briggs_urban_y_d_exponent() -> None:
    row = _row("isc3_briggs_urban_y_d_exponent")
    assert row["value"] == -0.5
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_briggs_urban_z_d_slope")
def test_pin_isc3_briggs_urban_z_d_slope() -> None:
    row = _row("isc3_briggs_urban_z_d_slope")
    assert row["value"] == 0.0003
    assert row["verification"] == "verified"


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("isc3_briggs_urban_z_d_exponent")
def test_pin_isc3_briggs_urban_z_d_exponent() -> None:
    row = _row("isc3_briggs_urban_z_d_exponent")
    assert row["value"] == -0.5
    assert row["verification"] == "verified"

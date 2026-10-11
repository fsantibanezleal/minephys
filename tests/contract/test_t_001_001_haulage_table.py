# ruff: noqa: E501
"""T-001-001 (DC-001-01): `src/minephys/knowledge/haulage.yaml` (rows of spec 001 section 7.5) and its BibTeX entries.

Expected deliverables: the table `haulage.yaml` (schema DC-000-02, licence CC-BY-4.0) and, in `references.bib`, the
entries `epa2025ghghub` (US EPA GHG Emission Factors Hub 2025, a US Government work, year 2025),
`oem2016rollingresistance` (OEM rolling-resistance article, year 2016) and `minephys:spec-001-haulage` (this
specification, the citation of the tripwire rows). Every value is a YAML NUMBER (PyYAML reads `1e9` and `3.6e6` as strings; write `1.0e+9`).

Oracle: the rows and values printed in spec 001 section 7.5 and section 7.3 (hand transcription, TC-0 exact), and the
JSON Schemas of the foundation as the reference implementation of DC-000-02 and DC-000-03.
"""

from __future__ import annotations

import pytest
from _table_helpers_a import (
    all_row_ids,
    bib_entry_as_object,
    load_bib,
    load_table,
    rows_by_id,
    schema_errors,
)

TABLE = "haulage"
FUNCTIONS = {
    "grade_resistance",
    "total_resistance",
    "required_force",
    "rimpull_limited_speed",
    "retarder_limited_speed",
    "loose_density",
    "loading_passes",
    "segment_travel_time",
    "cycle_time",
    "segment_energy",
    "cycle_energy",
    "bev_cycle_energy",
    "trolley_cycle_energy",
    "fuel_use",
    "co2_from_diesel",
    "co2_from_electricity",
    "match_factor",
    "mmc_queue",
    "finite_source_queue",
    "mean_value_analysis",
}

# id -> (value, units token, role, verification, citation)
RESISTANCE_ROWS = {
    "rolling_resistance_hard_smooth": 0.015,
    "rolling_resistance_firm_maintained": 0.03,
    "rolling_resistance_rutted_soft": 0.08,
    "rolling_resistance_loose_gravel": 0.10,
    "rolling_resistance_per_cm_penetration": 0.006,
}
TRIPWIRES = {
    "tripwire_grade_abs_max": (0.30, "1"),
    "tripwire_rolling_resistance_max": (0.20, "1"),
    "tripwire_truck_mass_min": (1000.0, "kg"),
    "tripwire_truck_mass_max": (2_000_000.0, "kg"),
    "tripwire_swell_max": (1.0, "1"),
    "tripwire_bank_density_min": (500.0, "kg/m"),
    "tripwire_fuel_energy_density_min": (1.0e9, "J/m"),
    "tripwire_grid_intensity_max": (1.0e-6, "kg/J"),
}


def symbols(row: dict) -> list[str]:
    s = row["symbol"]
    return [s] if isinstance(s, str) else list(s)


@pytest.mark.req("DC-001-01")
@pytest.mark.oracle("reference-implementation", "jsonschema Draft 2020-12 validation against contracts/ (DC-000-02)")
def test_table_header_and_schema() -> None:
    doc = load_table(TABLE)
    assert doc["table"] == TABLE
    assert doc["schema_version"] == 1
    assert doc["licence"] == "CC-BY-4.0"
    assert schema_errors("knowledge-table.schema.json", doc) == []
    ids = [r["id"] for r in doc["rows"]]
    assert len(ids) == len(set(ids))
    assert not set(ids) & all_row_ids(TABLE), "row ids are unique across all tables"


@pytest.mark.req("DC-001-01")
@pytest.mark.oracle("hand-calculation", "spec 001 7.5: diesel_co2_kg_per_us_gal = 10.21 kg CO2 / US gal, verified")
def test_diesel_co2_row() -> None:
    r = rows_by_id(TABLE)["diesel_co2_kg_per_us_gal"]
    assert isinstance(r["value"], int | float)
    assert r["value"] == 10.21
    assert r["units"] == "kg CO₂ / US gal"
    assert r["role"] == "parameter"
    assert r["verification"] == "verified"
    assert r["verified_on"] == "2026-10-06"
    assert r["citation"] == "epa2025ghghub"
    assert "Table 2" in r["page"]
    assert "p. 2" in r["page"]
    assert "minephys.haulage.co2_from_diesel" in symbols(r)


@pytest.mark.req("DC-001-01")
@pytest.mark.oracle(
    "hand-calculation", "spec 001 7.5: rolling-resistance rows are UNVERIFIED parameters, never defaults"
)
@pytest.mark.parametrize(("row_id", "value"), sorted(RESISTANCE_ROWS.items()))
def test_rolling_resistance_rows(row_id: str, value: float) -> None:
    r = rows_by_id(TABLE)[row_id]
    assert isinstance(r["value"], int | float)
    assert r["value"] == value
    assert r["role"] == "parameter"
    assert r["verification"] == "UNVERIFIED"
    assert "verified_on" not in r
    assert r["citation"] == "oem2016rollingresistance"
    assert r["page"].strip()
    assert r["units"] == ("1 per cm" if row_id.endswith("per_cm_penetration") else "1")
    assert set(symbols(r)) <= {f"minephys.haulage.{n}" for n in FUNCTIONS}


@pytest.mark.req("DC-001-01")
@pytest.mark.oracle("hand-calculation", "spec 001 7.3: the eight tripwire thresholds are UNVERIFIED limits")
@pytest.mark.parametrize(("row_id", "expected"), sorted(TRIPWIRES.items()))
def test_tripwire_rows(row_id: str, expected: tuple[float, str]) -> None:
    value, units = expected
    r = rows_by_id(TABLE)[row_id]
    assert isinstance(r["value"], int | float)
    assert r["value"] == value
    assert units in r["units"]
    assert r["role"] == "limit"
    assert r["verification"] == "UNVERIFIED"
    assert r["citation"] == "minephys:spec-001-haulage"
    assert "7.3" in r["page"]
    assert symbols(r), "a tripwire row names the functions that read it"
    assert set(symbols(r)) <= {f"minephys.haulage.{n}" for n in FUNCTIONS}


@pytest.mark.req("DC-001-01")
@pytest.mark.oracle("hand-calculation", "spec 001 7.5: no UNVERIFIED value is presented as verified, and vice versa")
def test_only_the_epa_row_is_verified() -> None:
    verified = {i for i, r in rows_by_id(TABLE).items() if r["verification"] == "verified"}
    assert verified == {"diesel_co2_kg_per_us_gal"}


@pytest.mark.req("DC-001-01")
@pytest.mark.oracle("reference-implementation", "jsonschema validation of the parsed BibTeX entries (DC-000-03)")
def test_cited_bibliography_entries() -> None:
    bib = load_bib()
    cited = {r["citation"] for r in load_table(TABLE)["rows"]}
    assert cited == {"epa2025ghghub", "oem2016rollingresistance", "minephys:spec-001-haulage"}
    for key in cited:
        assert key in bib, f"references.bib has no entry {key}"
        assert schema_errors("bibliography-entry.schema.json", bib_entry_as_object(key, bib[key])) == [], key
    assert bib["epa2025ghghub"]["year"] == "2025"
    assert bib["oem2016rollingresistance"]["year"] == "2016"
    assert bib["epa2025ghghub"]["access"] in {"open", "regulation"}, "a US Government work"


@pytest.mark.req("DC-001-01")
@pytest.mark.oracle("hand-calculation", "FR-000-31: a CC-BY-4.0 table cites no share-alike source")
def test_table_cites_no_share_alike_source() -> None:
    bib = load_bib()
    for r in load_table(TABLE)["rows"]:
        assert not bib[r["citation"]].get("licence", "").startswith("CC-BY-SA"), r["id"]

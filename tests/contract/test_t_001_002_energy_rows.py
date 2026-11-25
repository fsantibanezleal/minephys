# ruff: noqa: E501
"""T-001-002 (DC-001-02): the five route-energy rows of `src/minephys/knowledge/haulage.yaml` and their BibTeX entries.

Expected deliverables: five `verified` rows of role `parameter` in `haulage.yaml` (spec 001 section 7.5, second table)
and, in `references.bib`, the new entry `afdc2026fuelproperties` (US DOE Alternative Fuels Data Center, Fuel Properties
Comparison, a US Government work, read 2026-11-25) next to the existing entry `lindgren2022`. Every value is a YAML
NUMBER.

Oracles (all hand calculations on numbers printed in the two sources, none produced by the code under test):
  - Lindgren et al. 2022 (Energies 15(13), 4871), Table 2, p. 7: "Loss from DC-bus to wheel, same in reverse at
    regeneration" 11.5 %; "Marginal diesel consumption, ca 40% efficiency, fuel to DC-power" 0.253 l/kWh; "Resistive
    loss in battery and DC/DC converter at 1C charge/discharge rate" 3 %.
  - US DOE AFDC Fuel Properties Comparison, row "Low Sulfur Diesel": lower heating value 128,488 Btu/gal.
  - Unit definitions: 1 Btu (International Table) = 1055.05585262 J (exact by the IT calorie definition), 1 US gal = 231 in^3
    = 3.785411784e-3 m^3 (NIST Handbook 44, the foundation `units` table).
"""

from __future__ import annotations

import math

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
VERIFIED_ON = "2026-11-25"

BTU_IT_J = 1055.05585262
US_GAL_M3 = 231 * 0.0254**3
LHV_J_PER_M3 = 128488 * BTU_IT_J / US_GAL_M3  # 3.58117e10 J/m^3 (35.81 MJ/L)
DC_TO_WHEEL = 1.0 - 0.115
BATTERY_PASS = 1.0 - 0.03

# id -> (value, units, symbol, citation, page locator tokens)
ROWS = {
    "diesel_electric_fuel_to_wheel_efficiency": (0.40 * DC_TO_WHEEL, "1", "minephys.haulage.trolley_cycle_energy"),
    "electric_dc_bus_to_wheel_efficiency": (DC_TO_WHEEL, "1", "minephys.haulage.trolley_cycle_energy"),
    "battery_electric_battery_to_wheel_efficiency": (
        DC_TO_WHEEL * BATTERY_PASS,
        "1",
        "minephys.haulage.bev_cycle_energy",
    ),
    "battery_electric_regeneration_efficiency": (DC_TO_WHEEL * BATTERY_PASS, "1", "minephys.haulage.bev_cycle_energy"),
    "diesel_lower_heating_value_j_per_m3": (LHV_J_PER_M3, "J/m³", "minephys.haulage.fuel_use"),
}
LINDGREN = {
    "diesel_electric_fuel_to_wheel_efficiency",
    "electric_dc_bus_to_wheel_efficiency",
    "battery_electric_battery_to_wheel_efficiency",
    "battery_electric_regeneration_efficiency",
}


@pytest.mark.req("DC-001-02")
@pytest.mark.oracle(
    "hand-calculation", "the five new ids exist, are unique across every table and keep the table schema"
)
def test_the_five_rows_exist_and_the_table_keeps_its_schema() -> None:
    doc = load_table(TABLE)
    assert schema_errors("knowledge-table.schema.json", doc) == []
    ids = [r["id"] for r in doc["rows"]]
    assert len(ids) == len(set(ids))
    assert set(ROWS) <= set(ids)
    assert not set(ids) & all_row_ids(TABLE)


@pytest.mark.req("DC-001-02")
@pytest.mark.parametrize("row_id", sorted(ROWS))
@pytest.mark.knowledge("diesel_electric_fuel_to_wheel_efficiency")
@pytest.mark.knowledge("electric_dc_bus_to_wheel_efficiency")
@pytest.mark.knowledge("battery_electric_battery_to_wheel_efficiency")
@pytest.mark.knowledge("battery_electric_regeneration_efficiency")
@pytest.mark.knowledge("diesel_lower_heating_value_j_per_m3")
@pytest.mark.oracle(
    "hand-calculation",
    "0.40 x (1-0.115) = 0.354; 1-0.115 = 0.885; 0.885 x (1-0.03) = 0.85845; 128488 Btu/gal x 1055.05585262 J / 3.785411784e-3 m^3",
)
def test_row_values_units_role_and_status(row_id: str) -> None:
    value, units, symbol = ROWS[row_id]
    r = rows_by_id(TABLE)[row_id]
    assert isinstance(r["value"], int | float)
    assert r["value"] == pytest.approx(value, rel=1e-9)
    assert r["units"] == units
    assert r["role"] == "parameter"
    assert r["verification"] == "verified"
    assert r["verified_on"] == VERIFIED_ON
    assert symbol in ([r["symbol"]] if isinstance(r["symbol"], str) else r["symbol"])


@pytest.mark.req("DC-001-02")
@pytest.mark.oracle(
    "hand-calculation", "every row names its source, a page or table locator, the derivation and an uncertainty note"
)
@pytest.mark.parametrize("row_id", sorted(ROWS))
def test_row_citations_pages_and_notes(row_id: str) -> None:
    r = rows_by_id(TABLE)[row_id]
    if row_id in LINDGREN:
        assert r["citation"] == "lindgren2022"
        assert "Table 2" in r["page"] and "p. 7" in r["page"]
    else:
        assert r["citation"] == "afdc2026fuelproperties"
        assert "Low Sulfur Diesel" in r["page"] and "lower heating value" in r["page"].lower()
    notes = r.get("notes", "")
    assert "Uncertainty" in notes, "the row states what is known about its uncertainty"
    assert len(notes) >= 80


@pytest.mark.req("DC-001-02")
@pytest.mark.oracle("hand-calculation", "the rows state the system boundary and what the value excludes")
def test_notes_state_the_boundary() -> None:
    rows = rows_by_id(TABLE)
    assert "friction" in rows["battery_electric_regeneration_efficiency"]["notes"]
    assert "load-independent" in rows["diesel_electric_fuel_to_wheel_efficiency"]["notes"]
    assert "pantograph" in rows["electric_dc_bus_to_wheel_efficiency"]["notes"]
    assert "Btu" in rows["diesel_lower_heating_value_j_per_m3"]["notes"]
    assert "lower heating value" in rows["diesel_lower_heating_value_j_per_m3"]["quantity"].lower()


@pytest.mark.req("DC-001-02")
@pytest.mark.oracle(
    "worked-example",
    "lindgren2022 Table 2, p. 7: 0.253 l/kWh at ca 40 % gives 3.6 MJ / (0.40 x 0.253 l) = 35.57 MJ/l, within 1 % of the AFDC value",
)
def test_the_two_sources_agree_on_the_diesel_energy_content() -> None:
    implied = 3.6e6 / (0.40 * 0.253e-3)  # J/m^3 from the marginal consumption and the efficiency
    got = rows_by_id(TABLE)["diesel_lower_heating_value_j_per_m3"]["value"]
    assert math.isclose(implied, got, rel_tol=0.01)
    assert got > 1.0e9, "above the tripwire tripwire_fuel_energy_density_min"


@pytest.mark.req("DC-001-02")
@pytest.mark.oracle("reference-implementation", "jsonschema validation of the parsed BibTeX entries (DC-000-03)")
def test_bibliography_entries() -> None:
    bib = load_bib()
    for key in ("lindgren2022", "afdc2026fuelproperties"):
        assert key in bib, f"references.bib has no entry {key}"
        assert schema_errors("bibliography-entry.schema.json", bib_entry_as_object(key, bib[key])) == [], key
    assert bib["lindgren2022"]["doi"] == "10.3390/en15134871"
    assert bib["lindgren2022"]["access"] == "open"
    assert bib["lindgren2022"]["licence"] == "CC-BY-4.0"
    afdc = bib["afdc2026fuelproperties"]
    assert afdc["year"] == "2026"
    assert afdc["url"] == "https://afdc.energy.gov/fuels/properties"
    assert afdc["access"] in {"open", "regulation"}, "a US Government work"
    assert "GREET" in afdc["note"], "the note names the source of the page's heating values"


@pytest.mark.req("DC-001-02")
@pytest.mark.oracle("hand-calculation", "FR-000-31: a CC-BY-4.0 table cites no share-alike source")
def test_the_new_rows_cite_no_share_alike_source() -> None:
    bib = load_bib()
    for row_id in ROWS:
        key = rows_by_id(TABLE)[row_id]["citation"]
        assert not bib[key].get("licence", "").startswith("CC-BY-SA"), row_id

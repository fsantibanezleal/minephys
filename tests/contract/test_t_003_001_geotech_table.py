"""T-003-001 (DC-003-01): `src/minephys/knowledge/geotech.yaml` (rows of spec 003 section 7.5) and its BibTeX entries.

Expected deliverables: the table `geotech.yaml` (schema DC-000-02, licence CC-BY-4.0) and, in
`references.bib`, the entries `hoek2002` (Hoek, Carranza-Torres and Corkum 2002, year 2002), `hoek2019` (Hoek
and Brown 2019, year 2019; the 2018/2019 in-press edition cited with the 2002 rows), `wolff2023` (Wolff et al.
2023, preprint, year 2023) and `minephys:spec-003-geotech` (this specification, the citation of the tripwire
rows); and the entries the oracle markers of the geotech tests cite: `fredlund1977` (Fredlund and Krahn 1977,
year 1977, the slope-stability benchmark of Slide verification problem 21), `rocscience2020slide` (the
Rocscience Slide hand-calculation note) and `monserrat2014` (Monserrat, Crosetto and Luzi 2014, year 2014, the
phase relation). Every value is a YAML NUMBER or an exact `"p/q"` string where section 7.5 prints a quoted
rational (`"20/3"`); `tripwire_wavelength_range` is a range row.

Oracle: the rows, values, units, roles, citations, pages and verification statuses printed in spec 003 section
7.5 and the tripwire values of section 7.3 (hand transcription, exact), and the JSON Schemas of the foundation
as the reference implementation of DC-000-02 and DC-000-03.
"""

from __future__ import annotations

import pytest
from _table_helpers_a import all_row_ids, bib_entry_as_object, load_bib, load_table, rows_by_id, schema_errors

TABLE = "geotech"
FUNCTIONS = {
    "hoek_brown_parameters",
    "hoek_brown_sigma1",
    "hoek_brown_uniaxial_strength",
    "hoek_brown_tensile_strength",
    "hoek_brown_rock_mass_strength",
    "equivalent_mohr_coulomb",
    "sigma3_max",
    "circular_slices",
    "bishop_simplified_fos",
    "spencer_fos",
    "monte_carlo_fos",
    "probability_of_failure",
    "required_samples",
    "voight_creep_series",
    "inverse_velocity_ttf",
    "bayesian_ttf",
    "slope_radar_los",
    "los_phase",
    "wrap_phase",
    "los_from_phase",
    "max_unambiguous_los_step",
}

# id -> (value, role, verification, citation, page token)
ROWS = {
    "hb_mb_gsi_denominator_constant": (28, "model_constant", "verified", "hoek2002", "eq. 3"),
    "hb_mb_disturbance_coefficient": (14, "model_constant", "verified", "hoek2002", "eq. 3"),
    "hb_s_gsi_denominator_constant": (9, "model_constant", "verified", "hoek2002", "eq. 4"),
    "hb_s_disturbance_coefficient": (3, "model_constant", "verified", "hoek2002", "eq. 4"),
    "hb_a_gsi_scale": (15, "model_constant", "verified", "hoek2002", "eq. 5"),
    "hb_a_offset_exponent": ("20/3", "model_constant", "verified", "hoek2002", "eq. 5"),
    "hb_sigma3max_slope_coefficient": (0.72, "model_constant", "verified", "hoek2002", "eq. 19"),
    "hb_sigma3max_slope_exponent": (-0.91, "model_constant", "verified", "hoek2002", "eq. 19"),
    "hb_sigma3max_tunnel_coefficient": (0.47, "model_constant", "verified", "hoek2002", "eq. 18"),
    "hb_sigma3max_tunnel_exponent": (-0.94, "model_constant", "verified", "hoek2002", "eq. 18"),
    "hb_disturbance_open_pit_production_blasting": (1.0, "parameter", "verified", "hoek2002", "Table 1"),
    "hb_disturbance_open_pit_mechanical_excavation": (0.7, "parameter", "verified", "hoek2002", "Table 1"),
    "gbsar_ku_band_wavelength": (0.0175, "parameter", "verified", "wolff2023", "p. 8"),
}
TRIPWIRES = {
    "tripwire_sigma_ci_min": (1.0e5, "Pa"),
    "tripwire_sigma_ci_max": (1.0e9, "Pa"),
    "tripwire_cohesion_min": (100.0, "Pa"),
    "tripwire_unit_weight_min": (1000.0, "N/m"),
    "tripwire_friction_angle_max": (1.2, "rad"),
    "tripwire_slope_velocity_max": (1.0e-2, "m/s"),
}


def symbols(row: dict) -> list[str]:
    s = row["symbol"]
    return [s] if isinstance(s, str) else list(s)


@pytest.mark.req("DC-003-01")
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


@pytest.mark.req("DC-003-01")
@pytest.mark.oracle(
    "hand-calculation", "spec 003 7.5: value, role, verification, citation and page of every printed row"
)
@pytest.mark.parametrize("row_id", sorted(ROWS))
def test_row_matches_section_7_5(row_id: str) -> None:
    value, role, verification, citation, page = ROWS[row_id]
    r = rows_by_id(TABLE)[row_id]
    assert r["value"] == value
    if isinstance(value, str):
        assert isinstance(r["value"], str), "an exact rational stays a p/q string"
    else:
        assert isinstance(r["value"], int | float)
        assert not isinstance(r["value"], bool)
    assert r["role"] == role
    assert r["verification"] == verification
    assert r["verified_on"] == "2026-10-06"
    assert r["citation"] == citation
    assert page in r["page"]
    assert set(symbols(r)) <= {f"minephys.geotech.{n}" for n in FUNCTIONS}


@pytest.mark.req("DC-003-01")
@pytest.mark.oracle("hand-calculation", "spec 003 7.5: units of the printed rows")
def test_units() -> None:
    rows = rows_by_id(TABLE)
    assert rows["gbsar_ku_band_wavelength"]["units"] == "m"
    for r in (
        "hb_mb_gsi_denominator_constant",
        "hb_s_gsi_denominator_constant",
        "hb_a_gsi_scale",
        "hb_a_offset_exponent",
    ):
        assert rows[r]["units"] == "1"
    assert rows["hb_disturbance_open_pit_production_blasting"]["units"] == "1"


@pytest.mark.req("DC-003-01")
@pytest.mark.oracle(
    "hand-calculation", "spec 003 7.3: the tripwire thresholds are UNVERIFIED limits cited to this specification"
)
@pytest.mark.parametrize(("row_id", "expected"), sorted(TRIPWIRES.items()))
def test_tripwire_rows(row_id: str, expected: tuple[float, str]) -> None:
    value, units = expected
    r = rows_by_id(TABLE)[row_id]
    assert isinstance(r["value"], int | float)
    assert r["value"] == value
    assert units in r["units"]
    assert r["role"] == "limit"
    assert r["verification"] == "UNVERIFIED"
    assert r["citation"] == "minephys:spec-003-geotech"
    assert "7.3" in r["page"]
    assert symbols(r)


@pytest.mark.req("DC-003-01")
@pytest.mark.oracle("hand-calculation", "spec 003 7.3: the wavelength tripwire is a range row, 1e-4 m to 1 m")
def test_wavelength_tripwire_is_a_range_row() -> None:
    r = rows_by_id(TABLE)["tripwire_wavelength_range"]
    assert r["range"] == {"min": 1.0e-4, "max": 1.0}
    assert r["units"] == "m"
    assert r["role"] == "limit"
    assert r["verification"] == "UNVERIFIED"
    assert r["citation"] == "minephys:spec-003-geotech"
    assert symbols(r)


@pytest.mark.req("DC-003-01")
@pytest.mark.oracle("hand-calculation", "spec 003 7.5: the verified rows are exactly the thirteen printed ones")
def test_verified_rows_are_exactly_those_of_section_7_5() -> None:
    verified = {i for i, r in rows_by_id(TABLE).items() if r["verification"] == "verified"}
    assert verified == set(ROWS)


@pytest.mark.req("DC-003-01")
@pytest.mark.oracle("reference-implementation", "jsonschema validation of the parsed BibTeX entries (DC-000-03)")
def test_cited_bibliography_entries() -> None:
    bib = load_bib()
    cited = {r["citation"] for r in load_table(TABLE)["rows"]}
    assert {"hoek2002", "wolff2023", "minephys:spec-003-geotech"} <= cited
    for key in cited:
        assert key in bib, f"references.bib has no entry {key}"
        assert schema_errors("bibliography-entry.schema.json", bib_entry_as_object(key, bib[key])) == [], key
        assert not bib[key].get("licence", "").startswith("CC-BY-SA"), key
    assert bib["hoek2002"]["year"] == "2002"
    assert bib["wolff2023"]["year"] == "2023"
    assert "hoek2019" in bib
    assert bib["hoek2019"]["year"] == "2019"


@pytest.mark.req("DC-003-01")
@pytest.mark.oracle(
    "reference-implementation",
    "jsonschema validation of the BibTeX entries cited by the oracle markers (DC-000-03, FR-000-33)",
)
def test_entries_cited_by_the_oracle_markers() -> None:
    bib = load_bib()
    for key in ("fredlund1977", "rocscience2020slide", "monserrat2014"):
        assert key in bib, f"references.bib has no entry {key}"
        assert schema_errors("bibliography-entry.schema.json", bib_entry_as_object(key, bib[key])) == [], key
        assert not bib[key].get("licence", "").startswith("CC-BY-SA"), key
    assert bib["fredlund1977"]["year"] == "1977"
    assert bib["monserrat2014"]["year"] == "2014"

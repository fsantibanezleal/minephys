"""T-002-001 (DC-002-01): `src/minephys/knowledge/blasting.yaml` (rows of spec 002 section 7.5), BibTeX entries.

Expected deliverables: the table `blasting.yaml` (schema DC-000-02, licence CC-BY-4.0) and, in `references.bib`, the
entries `cunningham2005` (Cunningham 2005, year 2005), `mutinda2021` (Mutinda et al. 2021, year 2021), `szendrei2022`
(Szendrei and Tose, J. S. Afr. Inst. Min. Metall. 122(12), year 2022), `cfr30_816_67` (30 CFR 816.67, a regulation, US
Government work) and `minephys:spec-002-blasting` (this specification, the citation of the tripwire rows). Every value
is a YAML NUMBER or an exact `"p/q"` string where section 7.5 prints a quoted rational (`"1/6"`, `"19/20"`, `"19/30"`,
`"2/3"`); the 0.693 row stays 0.693 (the library uses ln 2, section 8).

Oracle: the rows, values, units, roles, citations, pages and verification statuses printed in spec 002 section
7.5 and the tripwire values of section 7.3 (hand transcription, exact), and the JSON Schemas of the foundation
as the reference implementation of DC-000-02 and DC-000-03.
"""

from __future__ import annotations

import pytest
from _table_helpers_a import all_row_ids, bib_entry_as_object, load_bib, load_table, rows_by_id, schema_errors

TABLE = "blasting"
FUNCTIONS = {
    "charge_per_hole",
    "powder_factor",
    "kuznetsov_x50",
    "rock_factor",
    "hardness_factor",
    "rock_density_influence",
    "uniformity_index",
    "rosin_rammler_passing",
    "rosin_rammler_size",
    "swebrec_passing",
    "swebrec_size",
    "kco_undulation",
    "kco_distribution",
    "scaled_distance",
    "ppv_scaled_distance",
    "ppv_limit",
    "max_charge_per_delay",
    "flyrock_range_no_drag",
    "flyrock_range_lundborg",
    "flyrock_trajectory",
}

# id -> (value, role, verification, citation, page token)
ROWS = {
    "kuznetsov_powder_factor_exponent": (-0.8, "model_constant", "verified", "cunningham2005", "p. 201"),
    "kuznetsov_charge_exponent": ("1/6", "model_constant", "verified", "cunningham2005", "p. 201"),
    "kuznetsov_tnt_relative_weight_strength": (115, "model_constant", "verified", "cunningham2005", "p. 201"),
    "kuzram_rws_exponent_2005": ("19/20", "model_constant", "verified", "cunningham2005", "p. 201"),
    "kuzram_rws_exponent_1983": ("19/30", "model_constant", "UNVERIFIED", "mutinda2021", "p. 109"),
    "kuzram_rock_factor_coefficient": (0.06, "model_constant", "verified", "cunningham2005", "p. 204"),
    "kuzram_hardness_modulus_divisor": (3, "model_constant", "verified", "cunningham2005", "p. 205"),
    "kuzram_hardness_ucs_divisor": (5, "model_constant", "verified", "cunningham2005", "p. 205"),
    "kuzram_hardness_modulus_switch": (50, "model_constant", "verified", "cunningham2005", "p. 205"),
    "kuzram_rdi_density_coefficient": (0.025, "model_constant", "UNVERIFIED", "mutinda2021", "p. 109"),
    "kuzram_rdi_offset": (50, "model_constant", "UNVERIFIED", "mutinda2021", "p. 109"),
    "cunningham_n_constant": (2.2, "model_constant", "verified", "cunningham2005", "p. 202"),
    "cunningham_n_burden_coefficient": (14, "model_constant", "verified", "cunningham2005", "p. 202"),
    "cunningham_n_charge_offset": (0.1, "model_constant", "verified", "cunningham2005", "p. 202"),
    "cunningham_n_charge_exponent": (0.1, "model_constant", "verified", "cunningham2005", "p. 202"),
    "rosin_rammler_median_constant": (0.693, "model_constant", "verified", "cunningham2005", "p. 202"),
    "kuzram_rock_factor_min": (0.8, "limit", "verified", "cunningham2005", "p. 201"),
    "kuzram_rock_factor_max": (22, "limit", "verified", "cunningham2005", "p. 201"),
    "kuzram_uniformity_typical_min": (0.8, "limit", "UNVERIFIED", None, None),
    "kuzram_uniformity_typical_max": (1.5, "limit", "UNVERIFIED", None, None),
    "cfr_816_67_ppv_limit_near": (1.25, "limit", "verified", "cfr30_816_67", "816.67"),
    "cfr_816_67_ppv_limit_mid": (1.00, "limit", "verified", "cfr30_816_67", "816.67"),
    "cfr_816_67_ppv_limit_far": (0.75, "limit", "verified", "cfr30_816_67", "816.67"),
    "cfr_816_67_distance_band_near_max": (300, "limit", "verified", "cfr30_816_67", "816.67"),
    "cfr_816_67_distance_band_mid_max": (5000, "limit", "verified", "cfr30_816_67", "816.67"),
    "cfr_816_67_scaled_distance_factor_near": (50, "limit", "verified", "cfr30_816_67", "816.67"),
    "cfr_816_67_scaled_distance_factor_mid": (55, "limit", "verified", "cfr30_816_67", "816.67"),
    "cfr_816_67_scaled_distance_factor_far": (65, "limit", "verified", "cfr30_816_67", "816.67"),
    "lundborg_max_range_coefficient": (260, "model_constant", "UNVERIFIED", "szendrei2022", "p. 726"),
    "lundborg_max_range_exponent": ("2/3", "model_constant", "UNVERIFIED", "szendrei2022", "p. 726"),
    "flyrock_air_density_reference": (1.24, "parameter", "verified", "szendrei2022", "p. 728"),
}
TRIPWIRES = {
    "tripwire_powder_factor_max": 5.0,
    "tripwire_rws_min": 20.0,
    "tripwire_hole_diameter_max": 1.0,
    "tripwire_k_site_max": 100.0,
    "tripwire_launch_speed_max": 500.0,
    "tripwire_air_density_max": 2.0,
}


def symbols(row: dict) -> list[str]:
    s = row["symbol"]
    return [s] if isinstance(s, str) else list(s)


@pytest.mark.req("DC-002-01")
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


@pytest.mark.req("DC-002-01")
@pytest.mark.oracle(
    "hand-calculation", "spec 002 7.5: value, role, verification, citation and page of every printed row"
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
    if verification == "verified":
        assert r["verified_on"] == "2026-10-06"
    else:
        assert "verified_on" not in r
    if citation is not None:
        assert r["citation"] == citation
        assert page in r["page"]
    assert r["page"].strip()
    assert set(symbols(r)) <= {f"minephys.blasting.{n}" for n in FUNCTIONS}


@pytest.mark.req("DC-002-01")
@pytest.mark.oracle("hand-calculation", "spec 002 7.5: ranges and units of the remaining rows")
def test_ranges_and_units() -> None:
    rows = rows_by_id(TABLE)
    drag = rows["flyrock_drag_coefficient_range"]
    assert drag["range"] == {"min": 0.6, "max": 1.8}
    assert drag["role"] == "parameter"
    assert drag["verification"] == "verified"
    assert drag["citation"] == "szendrei2022"
    assert "p. 728" in drag["page"]
    assert rows["flyrock_air_density_reference"]["units"] == "kg/m³"
    assert rows["kuzram_hardness_modulus_switch"]["units"] == "GPa"
    for r in (rows[f"cfr_816_67_ppv_limit_{k}"] for k in ("near", "mid", "far")):
        assert r["units"] == "in/s"
    for k in ("near_max", "mid_max"):
        assert rows[f"cfr_816_67_distance_band_{k}"]["units"] == "ft"
    assert "ft" in rows["cfr_816_67_scaled_distance_factor_near"]["units"]
    assert "in" in rows["lundborg_max_range_coefficient"]["units"]
    assert rows["kuznetsov_tnt_relative_weight_strength"]["units"].startswith("1")
    assert rows["kuzram_rdi_density_coefficient"]["units"].startswith("1/")


@pytest.mark.req("DC-002-01")
@pytest.mark.oracle("hand-calculation", "spec 002 7.3: the six tripwire thresholds are UNVERIFIED limits")
@pytest.mark.parametrize(("row_id", "value"), sorted(TRIPWIRES.items()))
def test_tripwire_rows(row_id: str, value: float) -> None:
    r = rows_by_id(TABLE)[row_id]
    assert isinstance(r["value"], int | float)
    assert r["value"] == value
    assert r["role"] == "limit"
    assert r["verification"] == "UNVERIFIED"
    assert r["citation"] == "minephys:spec-002-blasting"
    assert "7.3" in r["page"]
    assert symbols(r)


@pytest.mark.req("DC-002-01")
@pytest.mark.oracle("hand-calculation", "spec 002 7.5: the verified rows are exactly the ones read on a primary page")
def test_verified_rows_are_exactly_those_of_section_7_5() -> None:
    verified = {i for i, r in rows_by_id(TABLE).items() if r["verification"] == "verified"}
    expected = {i for i, (_, _, v, *_rest) in ROWS.items() if v == "verified"} | {"flyrock_drag_coefficient_range"}
    assert verified == expected


@pytest.mark.req("DC-002-01")
@pytest.mark.oracle("reference-implementation", "jsonschema validation of the parsed BibTeX entries (DC-000-03)")
def test_cited_bibliography_entries() -> None:
    bib = load_bib()
    cited = {r["citation"] for r in load_table(TABLE)["rows"]}
    assert {"cunningham2005", "mutinda2021", "szendrei2022", "cfr30_816_67", "minephys:spec-002-blasting"} <= cited
    for key in cited:
        assert key in bib, f"references.bib has no entry {key}"
        assert schema_errors("bibliography-entry.schema.json", bib_entry_as_object(key, bib[key])) == [], key
    assert bib["cunningham2005"]["year"] == "2005"
    assert bib["mutinda2021"]["year"] == "2021"
    assert bib["szendrei2022"]["year"] == "2022"
    assert bib["cfr30_816_67"]["access"] == "regulation"
    for key in cited:
        assert not bib[key].get("licence", "").startswith("CC-BY-SA"), key

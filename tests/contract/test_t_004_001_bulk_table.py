# ruff: noqa: E501
"""T-004-001 (DC-004-01): `src/minephys/knowledge/bulk.yaml` (rows of spec 004 section 7.5) and its BibTeX entries.

Expected deliverables: the table `bulk.yaml` (schema DC-000-02, licence CC-BY-4.0) and, in `references.bib`,
the entries `beverloo1961flow` (Beverloo, Leniger and van de Velde 1961, year 1961, paywalled; the key of spec
008's export example), `mankoc2007beverloo` (Mankoc et al. 2007, year 2007; the key of spec 008's export
example), `darias2020` (Darias, Madrid and Pugnaloni 2020, year 2020), `dasilva2025` (da Silva et al. 2025,
arXiv 2512.03698, year 2025), `cema_belt_conveyors_7th` (CEMA, Belt Conveyors for Bulk Materials, 7th ed.,
paywalled), `pdhonline_m344` (PDHonline course M344), `minkkinen2008` (Minkkinen 2008, Eurachem workshop, year
2008), `geelhoed2011` (Geelhoed 2011, year 2011) and `minephys:spec-004-bulk` (this specification, the
citation of the tripwire rows). The spec names its sources without keys; these keys are the test author's
choice, aligned with spec 008's example where one exists. Every value is a YAML NUMBER or an exact `"p/q"`
string where section 7.5 prints a quoted rational (`"5/2"`); the ranges of section 7.5 (0.55-0.65, 1-2,
0.016-0.035) are range rows (`range: {min, max}`, no `value`). Exactly one row is verified
(`beverloo_discharge_coefficient_dem`).

Oracle: the rows, values, units, roles, citations, pages and verification statuses printed in spec 004
sections 7.5 and 7.3 (hand transcription, exact), and the JSON Schemas of the foundation as the reference
implementation of DC-000-02 and DC-000-03.
"""

from __future__ import annotations

import re

import pytest
from _table_helpers_a import all_row_ids, bib_entry_as_object, load_bib, load_table, rows_by_id, schema_errors

TABLE = "bulk"
FUNCTIONS = {
    "beverloo_discharge",
    "repose_cone_height",
    "repose_cone_volume",
    "repose_ridge_volume",
    "conveyor_capacity",
    "cema_effective_tension",
    "conveyor_power",
    "gy_fundamental_sampling_error",
    "gy_blending_variance",
    "variance_reduction_ratio",
}

# id -> (value, role, verification, citation, page token, function that must be among the symbols)
VALUE_ROWS = {
    "beverloo_exponent": ("5/2", "model_constant", "UNVERIFIED", "beverloo1961flow", "", "beverloo_discharge"),
    "beverloo_discharge_coefficient_dem": (0.56, "parameter", "verified", "dasilva2025", "p. 9", "beverloo_discharge"),
    "cema_return_belt_coefficient": (
        0.015,
        "model_constant",
        "UNVERIFIED",
        "cema_belt_conveyors_7th",
        "",
        "cema_effective_tension",
    ),
    "gy_fse_shape_factor_default": (
        0.5,
        "parameter",
        "UNVERIFIED",
        "minkkinen2008",
        "p. 6",
        "gy_fundamental_sampling_error",
    ),
    "gy_fse_granulometric_factor_wide": (
        0.25,
        "parameter",
        "UNVERIFIED",
        "minkkinen2008",
        "p. 7",
        "gy_fundamental_sampling_error",
    ),
}
# id -> (min, max, citation keys that must appear among citation, page and notes, function)
RANGE_ROWS = {
    "beverloo_discharge_coefficient_range": (0.55, 0.65, ("mankoc2007beverloo",), "beverloo_discharge"),
    "beverloo_annulus_coefficient_range": (1, 2, ("mankoc2007beverloo", "darias2020"), "beverloo_discharge"),
    "cema_ky_typical_range": (0.016, 0.035, ("pdhonline_m344",), "cema_effective_tension"),
}
TRIPWIRES = {
    "tripwire_orifice_diameter_max": (10.0, "m", {"beverloo_discharge"}),
    "tripwire_particle_diameter_max": (1.0, "m", {"beverloo_discharge"}),
    "tripwire_bulk_density_min": (100.0, "kg/m", {"beverloo_discharge", "conveyor_capacity"}),
    "tripwire_repose_angle_max": (1.05, "rad", {"repose_cone_height", "repose_cone_volume", "repose_ridge_volume"}),
    "tripwire_belt_speed_max": (15.0, "m/s", {"conveyor_capacity", "conveyor_power"}),
    "tripwire_mineralogical_factor_min": (100.0, "kg/m", {"gy_fundamental_sampling_error"}),
    "tripwire_top_size_max": (0.5, "m", {"gy_fundamental_sampling_error"}),
}


def symbols(row: dict) -> list[str]:
    s = row["symbol"]
    return [s] if isinstance(s, str) else list(s)


def functions_of(row: dict) -> set[str]:
    return {s.removeprefix("minephys.bulk.") for s in symbols(row)}


@pytest.mark.req("DC-004-01")
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


@pytest.mark.req("DC-004-01")
@pytest.mark.oracle("hand-calculation", "spec 004 7.5: the table holds exactly the printed rows plus the tripwire rows")
def test_row_set() -> None:
    assert set(rows_by_id(TABLE)) == set(VALUE_ROWS) | set(RANGE_ROWS) | set(TRIPWIRES)


@pytest.mark.req("DC-004-01")
@pytest.mark.oracle(
    "hand-calculation", "spec 004 7.5: value, role, verification, citation and page of every printed value row"
)
@pytest.mark.parametrize("row_id", sorted(VALUE_ROWS))
def test_value_row_matches_section_7_5(row_id: str) -> None:
    value, role, verification, citation, page, function = VALUE_ROWS[row_id]
    r = rows_by_id(TABLE)[row_id]
    assert r["value"] == value
    if isinstance(value, str):
        assert isinstance(r["value"], str), "an exact rational stays a p/q string"
    else:
        assert isinstance(r["value"], int | float)
        assert not isinstance(r["value"], bool)
    assert "range" not in r
    assert r["role"] == role
    assert r["verification"] == verification
    if verification == "verified":
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(r["verified_on"]))
    else:
        assert "verified_on" not in r
    assert r["citation"] == citation
    assert page in r["page"]
    assert r["page"].strip()
    assert function in functions_of(r)
    assert functions_of(r) <= FUNCTIONS


@pytest.mark.req("DC-004-01")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 7.5: the exponent is read on Mankoc et al. 2007 eq. 1 p. 1 (secondary) from Beverloo 1961 (primary, not read)",
)
def test_beverloo_exponent_provenance() -> None:
    r = rows_by_id(TABLE)["beverloo_exponent"]
    assert r["units"] == "1"
    text = " ".join([r["citation"], r["page"], r.get("notes", "")])
    assert "mankoc2007beverloo" in text
    assert "eq. 1" in text
    assert "p. 1" in text
    assert r["verification"] == "UNVERIFIED"


@pytest.mark.req("DC-004-01")
@pytest.mark.oracle(
    "hand-calculation", "spec 004 7.5: the three ranges are range rows, UNVERIFIED parameters, never defaults"
)
@pytest.mark.parametrize("row_id", sorted(RANGE_ROWS))
def test_range_rows(row_id: str) -> None:
    low, high, keys, function = RANGE_ROWS[row_id]
    r = rows_by_id(TABLE)[row_id]
    assert r["range"] == {"min": low, "max": high}
    assert r["role"] == "parameter"
    assert r["verification"] == "UNVERIFIED"
    assert "verified_on" not in r
    assert r["units"] == "1"
    text = " ".join([r["citation"], r["page"], r.get("notes", "")])
    for key in keys:
        assert key in text, f"{row_id}: {key} is not cited"
    assert re.search(r"p\. (1|13)", text)
    assert function in functions_of(r)
    assert functions_of(r) <= FUNCTIONS


@pytest.mark.req("DC-004-01")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 7.5: the DEM coefficient 0.56 is fitted with the particle density 3,000 kg/m3 (da Silva 2025 p. 9)",
)
def test_dem_coefficient_row() -> None:
    r = rows_by_id(TABLE)["beverloo_discharge_coefficient_dem"]
    assert r["units"] == "1"
    text = (r["page"] + " " + r.get("notes", "") + " " + r.get("quantity", "")).lower()
    assert "particle" in text, "the row records the density basis it was fitted with"
    assert "3000" in text.replace(",", "").replace(" ", "") or "3,000" in text


@pytest.mark.req("DC-004-01")
@pytest.mark.oracle(
    "hand-calculation", "spec 004 7.3: the seven tripwire thresholds are UNVERIFIED limits cited to this specification"
)
@pytest.mark.parametrize("row_id", sorted(TRIPWIRES))
def test_tripwire_rows(row_id: str) -> None:
    value, units, funcs = TRIPWIRES[row_id]
    r = rows_by_id(TABLE)[row_id]
    assert isinstance(r["value"], int | float)
    assert not isinstance(r["value"], bool)
    assert r["value"] == value
    assert units in r["units"]
    assert r["role"] == "limit"
    assert r["verification"] == "UNVERIFIED"
    assert "verified_on" not in r
    assert r["citation"] == "minephys:spec-004-bulk"
    assert "7.3" in r["page"]
    assert funcs <= functions_of(r)
    assert functions_of(r) <= FUNCTIONS


@pytest.mark.req("DC-004-01")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 7.5: the only verified row is the DEM coefficient (everything else is secondary-only or a design choice)",
)
def test_verified_rows_are_exactly_those_of_section_7_5() -> None:
    verified = {i for i, r in rows_by_id(TABLE).items() if r["verification"] == "verified"}
    assert verified == {"beverloo_discharge_coefficient_dem"}


@pytest.mark.req("DC-004-01")
@pytest.mark.oracle("reference-implementation", "jsonschema validation of the parsed BibTeX entries (DC-000-03)")
def test_cited_bibliography_entries() -> None:
    bib = load_bib()
    cited = {r["citation"] for r in load_table(TABLE)["rows"]}
    assert {
        "beverloo1961flow",
        "dasilva2025",
        "cema_belt_conveyors_7th",
        "minkkinen2008",
        "minephys:spec-004-bulk",
    } <= cited
    secondary = {
        "mankoc2007beverloo",
        "darias2020",
        "pdhonline_m344",
        "geelhoed2011",
    }  # cited in pages and notes, or by the equations
    for key in cited | secondary:
        assert key in bib, f"references.bib has no entry {key}"
        assert schema_errors("bibliography-entry.schema.json", bib_entry_as_object(key, bib[key])) == [], key
        assert not bib[key].get("licence", "").startswith("CC-BY-SA"), key
    assert bib["beverloo1961flow"]["year"] == "1961"
    assert bib["mankoc2007beverloo"]["year"] == "2007"
    assert bib["darias2020"]["year"] == "2020"
    assert bib["dasilva2025"]["year"] == "2025"
    assert bib["minkkinen2008"]["year"] == "2008"
    assert bib["geelhoed2011"]["year"] == "2011"
    assert bib["beverloo1961flow"]["access"] == "paywalled"
    assert bib["cema_belt_conveyors_7th"]["access"] == "paywalled"

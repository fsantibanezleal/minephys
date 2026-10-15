"""T-006-001 (DC-006-01, DC-006-02): the environment knowledge table, its equation entries and its bibliography keys.

Expected deliverables (spec 006 section 7 and section 6):
- `src/minephys/knowledge/environment.yaml`: a DC-000-02 table `environment` (licence CC-BY-4.0) with every row of section 7
  (ids as in the "Row id (pattern)" column: `ap42_industrial_{k,a,b}_{pm25,pm10,pm30}`, `ap42_range_*`, `ap42_watering_{m,ce}_{1..4}`,
  `isc3_pg_sigma_y_{c,d}_{a..f}`, `isc3_pg_sigma_z_{a..f}_{k}_{xmax,a,b}`, `isc3_briggs_urban_{y,z}_{a..f}_{coef,slope,exponent}`,
  the lidar thresholds, ...), values as published (percent, short tons, mph, lb/VMT, km, ...), role, citation key, verification;
- the environment entries of `src/minephys/knowledge/catalogue/equations.yaml` (DC-008-01);
- the section 7 bibliography keys in `src/minephys/knowledge/references.bib`.

Oracle: the values printed in the primary documents, transcribed from spec 006 section 7 (AP-42 Tables 13.2.2-2 and 13.2.2-3,
Figure 13.2.2-2; ISC3 volume II Tables 1-1 to 1-4; the lidar-study abstract). The ISC3 coefficients pinned here are those that
the plan's hand values (spec 006 plan, FR-006-09) exercise: sigma_y of classes A, C, D, F; sigma_z bands of A (0.16-0.20 km),
C, D (0.31-1.00 km) and F (1.01-2.00 km); Briggs urban class D. Every other coefficient is pinned by structure (row counts per
class: 9, 3, 1, 6, 9, 10 bands). The YAML is parsed with `yaml.safe_load`, independently of the `minephys.knowledge` loader.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
KDIR = ROOT / "src" / "minephys" / "knowledge"
TABLE = KDIR / "environment.yaml"
EQUATIONS = KDIR / "catalogue" / "equations.yaml"
BIB = KDIR / "references.bib"
AP42 = "epa2006ap42s1322"
ISC3 = "epa1995isc3v2"
LIDAR = "phillips2017dust"

# (row id, value, role, citation key, verified?)
EXPECTED_VALUES: list[tuple[str, float, str, str, bool]] = [
    ("ap42_industrial_k_pm25", 0.15, "model_constant", AP42, True),
    ("ap42_industrial_k_pm10", 1.5, "model_constant", AP42, True),
    ("ap42_industrial_k_pm30", 4.9, "model_constant", AP42, True),
    ("ap42_industrial_a_pm25", 0.9, "model_constant", AP42, True),
    ("ap42_industrial_a_pm10", 0.9, "model_constant", AP42, True),
    ("ap42_industrial_a_pm30", 0.7, "model_constant", AP42, True),
    ("ap42_industrial_b_pm25", 0.45, "model_constant", AP42, True),
    ("ap42_industrial_b_pm10", 0.45, "model_constant", AP42, True),
    ("ap42_industrial_b_pm30", 0.45, "model_constant", AP42, True),
    ("ap42_silt_reference", 12, "model_constant", AP42, True),
    ("ap42_weight_reference", 3, "model_constant", AP42, True),
    ("ap42_lb_per_vmt_in_g_per_vkt", 281.9, "conversion", AP42, True),
    ("ap42_wet_day_threshold", 0.254, "model_constant", AP42, True),
    ("ap42_days_per_year", 365, "model_constant", AP42, True),
    ("ap42_watering_m_1", 0, "model_constant", AP42, True),
    ("ap42_watering_m_2", 1, "model_constant", AP42, True),
    ("ap42_watering_m_3", 2, "model_constant", AP42, True),
    ("ap42_watering_m_4", 5, "model_constant", AP42, True),
    ("ap42_watering_ce_1", 0, "model_constant", AP42, True),
    ("ap42_watering_ce_2", 0, "model_constant", AP42, True),
    ("ap42_watering_ce_3", 75, "model_constant", AP42, True),
    ("ap42_watering_ce_4", 95, "model_constant", AP42, True),
    ("isc3_sigma_y_scale", 465.11628, "model_constant", ISC3, True),
    ("isc3_deg_to_rad", 0.017453293, "model_constant", ISC3, True),
    ("isc3_pg_sigma_y_c_a", 24.1670, "model_constant", ISC3, True),
    ("isc3_pg_sigma_y_d_a", 2.5334, "model_constant", ISC3, True),
    ("isc3_pg_sigma_y_c_c", 12.5000, "model_constant", ISC3, True),
    ("isc3_pg_sigma_y_d_c", 1.0857, "model_constant", ISC3, True),
    ("isc3_pg_sigma_y_c_d", 8.3330, "model_constant", ISC3, True),
    ("isc3_pg_sigma_y_d_d", 0.72382, "model_constant", ISC3, True),
    ("isc3_pg_sigma_y_c_f", 4.1667, "model_constant", ISC3, True),
    ("isc3_pg_sigma_y_d_f", 0.36191, "model_constant", ISC3, True),
    ("isc3_sigma_z_cap", 5000, "limit", ISC3, True),
    ("isc3_briggs_urban_y_d_coef", 0.16, "model_constant", ISC3, True),
    ("isc3_briggs_urban_y_d_slope", 0.0004, "model_constant", ISC3, True),
    ("isc3_briggs_urban_y_d_exponent", -0.5, "model_constant", ISC3, True),
    ("isc3_briggs_urban_z_d_coef", 0.14, "model_constant", ISC3, True),
    ("isc3_briggs_urban_z_d_slope", 0.0003, "model_constant", ISC3, True),
    ("isc3_briggs_urban_z_d_exponent", -0.5, "model_constant", ISC3, True),
    ("isc3_urban_min_distance", 100, "limit", ISC3, True),
    ("isc3_lid_uniform_ratio", 1.6, "model_constant", ISC3, True),
    ("lidar_dust_min_transmittance_retroreflective", 0.02, "limit", LIDAR, True),
    ("lidar_dust_min_transmittance_low_reflectivity", 0.06, "limit", LIDAR, True),
    ("extinction_efficiency_large_particle", 2, "model_constant", "bohren1983absorption", False),
]
# range rows: id -> (min, max)
EXPECTED_RANGES: dict[str, tuple[float, float]] = {
    "ap42_range_silt": (1.8, 25.2),
    "ap42_range_weight": (2.0, 290.0),
    "ap42_range_speed": (5.0, 43.0),
    "ap42_range_wheels": (4.0, 17.0),
    "ap42_range_moisture": (0.03, 13.0),
    "lidar_dust_onset_transmittance": (0.71, 0.74),
}
# (class letter, band ordinal, xmax km, a, b) pinned through the plan's hand values
SIGMA_Z_PINS = [
    ("a", 3, 0.20, 170.22, 1.0932),
    ("c", 1, None, 61.141, 0.91465),
    ("d", 2, 1.00, 32.093, 0.81066),
    ("f", 4, 2.00, 13.953, 0.63227),
]
BAND_COUNTS = {"a": 9, "b": 3, "c": 1, "d": 6, "e": 9, "f": 10}

MODEL_FUNCTIONS = [
    "ap42_unpaved_emission_factor",
    "precipitation_correction",
    "watering_control_efficiency",
    "pasquill_sigmas",
    "gaussian_plume",
    "line_source_plume",
    "finite_line_source_plume",
    "mass_extinction_coefficient",
    "beer_lambert_transmittance",
    "lidar_dust_return",
]
EXPECTED_BIB: dict[str, tuple[str, str | None]] = {
    "epa2006ap42s1322": ("regulation", None),
    "epa1995isc3v2": ("open", None),
    "turner1970workbook": ("bibliographic-only", None),
    "phillips2017dust": ("paywalled", "10.1002/rob.21701"),
    "bohren1983absorption": ("paywalled", "10.1002/9783527618156"),
    "niosh2012dust": ("open", "10.26616/nioshpub2012112"),
}


def _table() -> dict[str, Any]:
    assert TABLE.is_file(), "missing src/minephys/knowledge/environment.yaml (DC-006-01)"
    doc = yaml.safe_load(TABLE.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def _rows() -> dict[str, dict[str, Any]]:
    return {r["id"]: r for r in _table()["rows"]}


def _bib() -> dict[str, dict[str, str]]:
    assert BIB.is_file(), "missing src/minephys/knowledge/references.bib"
    out: dict[str, dict[str, str]] = {}
    for chunk in re.split(r"(?m)^@", BIB.read_text(encoding="utf-8"))[1:]:
        m = re.match(r"(\w+)\{([^,\s]+),", chunk)
        if m:
            fields = {k.lower(): v.strip() for k, v in re.findall(r"(?m)^\s*(\w+)\s*=\s*\{(.*?)\}\s*,?\s*$", chunk)}
            out[m.group(2)] = fields
    return out


@pytest.mark.req("DC-006-01")
@pytest.mark.oracle("hand-calculation", "spec 006 section 7 transcribed")
def test_table_header_is_a_dc_000_02_table() -> None:
    doc = _table()
    assert set(doc) == {"schema_version", "table", "title", "licence", "rows"}
    assert doc["schema_version"] == 1 and doc["table"] == "environment" and doc["licence"] == "CC-BY-4.0"
    ids = [r["id"] for r in doc["rows"]]
    assert len(ids) == len(set(ids)), "duplicate row ids"


@pytest.mark.req("DC-006-01")
@pytest.mark.parametrize(("row_id", "value", "role", "citation", "verified"), EXPECTED_VALUES, ids=[r[0] for r in EXPECTED_VALUES])
def test_value_rows_match_the_printed_values(row_id: str, value: float, role: str, citation: str, verified: bool) -> None:
    row = _rows()[row_id]
    assert row["value"] == value, f"{row_id}: printed value {value}"
    assert row["role"] == role and row["citation"] == citation
    assert isinstance(row["page"], str) and re.search(r"\d", row["page"])
    assert isinstance(row["units"], str) and row["units"].strip() and isinstance(row["quantity"], str)
    if verified:
        assert row["verification"] == "verified" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(row["verified_on"]))
    else:
        assert row["verification"] == "UNVERIFIED" and "verified_on" not in row


@pytest.mark.req("DC-006-01")
@pytest.mark.parametrize("row_id", sorted(EXPECTED_RANGES))
def test_range_rows(row_id: str) -> None:
    row = _rows()[row_id]
    assert "value" not in row and set(row["range"]) == {"min", "max"}
    assert (row["range"]["min"], row["range"]["max"]) == EXPECTED_RANGES[row_id]
    assert row["role"] == "limit"
    assert row["verification"] == "verified"


for _r in EXPECTED_VALUES:
    if _r[4]:

        def _make(rid: str = _r[0]) -> Any:
            def test() -> None:
                assert _rows()[rid]["verification"] == "verified"

            test.__name__ = f"test_verified_row_pin_{rid}"
            return pytest.mark.knowledge(rid)(pytest.mark.req("DC-006-01")(test))

        globals()[f"test_verified_row_pin_{_r[0]}"] = _make()
for _rid in EXPECTED_RANGES:

    def _make_range(rid: str = _rid) -> Any:
        def test() -> None:
            assert _rows()[rid]["verification"] == "verified"

        test.__name__ = f"test_verified_row_pin_{rid}"
        return pytest.mark.knowledge(rid)(pytest.mark.req("DC-006-01")(test))

    globals()[f"test_verified_row_pin_{_rid}"] = _make_range()


@pytest.mark.req("DC-006-01")
def test_the_isc3_sigma_y_table_has_twelve_rows() -> None:
    rows = _rows()
    for coefficient in ("c", "d"):
        for cls in "abcdef":
            assert f"isc3_pg_sigma_y_{coefficient}_{cls}" in rows


@pytest.mark.req("DC-006-01")
def test_the_isc3_sigma_z_table_has_the_published_band_counts() -> None:
    bands: dict[str, dict[int, dict[str, float]]] = {c: {} for c in "abcdef"}
    for rid, row in _rows().items():
        m = re.fullmatch(r"isc3_pg_sigma_z_([a-f])_(\d+)_(xmax|a|b)", rid)
        if m:
            bands[m.group(1)].setdefault(int(m.group(2)), {})[m.group(3)] = row["value"]
    for cls, expected in BAND_COUNTS.items():
        assert len(bands[cls]) == expected, f"class {cls.upper()}: {len(bands[cls])} bands, Table 1-2 has {expected}"
        for k, parts in bands[cls].items():
            assert "a" in parts and "b" in parts, f"class {cls.upper()} band {k} lacks a coefficient"
    for cls, ordinal, xmax, a, b in SIGMA_Z_PINS:
        parts = bands[cls][sorted(bands[cls])[ordinal - 1]]
        assert parts["a"] == a and parts["b"] == b, f"Table 1-2 class {cls.upper()} band {ordinal}"
        if xmax is not None:
            assert parts["xmax"] == xmax


@pytest.mark.req("DC-006-01")
def test_rows_name_functions_of_the_module_as_symbols() -> None:
    for row in _table()["rows"]:
        sym = row["symbol"]
        for s in [sym] if isinstance(sym, str) else sym:
            assert s.startswith("minephys.environment."), f"{row['id']}: symbol outside the module: {s}"


@pytest.mark.req("DC-006-01")
def test_extinction_efficiency_row_is_unverified_and_flagged() -> None:
    row = _rows()["extinction_efficiency_large_particle"]
    assert row["verification"] == "UNVERIFIED" and row["value"] == 2 and row["role"] == "model_constant"
    assert "minephys.environment.mass_extinction_coefficient" in ([row["symbol"]] if isinstance(row["symbol"], str) else row["symbol"])


@pytest.mark.req("DC-006-02")
def test_every_model_has_an_environment_equation_entry() -> None:
    assert EQUATIONS.is_file(), "missing knowledge/catalogue/equations.yaml"
    doc = yaml.safe_load(EQUATIONS.read_text(encoding="utf-8"))
    entries = [e for e in doc["equations"] if e.get("domain") == "environment"]
    functions = {e["function"] for e in entries}
    wanted = {f"minephys.environment.{n}" for n in MODEL_FUNCTIONS}
    assert wanted <= functions, f"missing equation entries for {sorted(wanted - functions)}"
    ids = set(_rows())
    for e in entries:
        assert e["latex"].strip() and e["symbols"]
        assert set(e.get("rows", [])) <= ids


@pytest.mark.req("DC-006-02")
def test_unverified_interpretations_are_flagged_in_the_catalogue() -> None:
    """Spec 006 section 7: the one-way transmittance reading of the lidar thresholds and Q_ext = 2 are UNVERIFIED."""
    assert EQUATIONS.is_file(), "missing knowledge/catalogue/equations.yaml"
    doc = yaml.safe_load(EQUATIONS.read_text(encoding="utf-8"))
    by_fn = {e["function"]: e for e in doc["equations"] if e.get("domain") == "environment"}
    for name in ("lidar_dust_return", "mass_extinction_coefficient"):
        assert by_fn[f"minephys.environment.{name}"]["verification"] == "UNVERIFIED", name


@pytest.mark.req("DC-006-01")
def test_section7_bibliography_keys_and_access_classes() -> None:
    bib = _bib()
    for key, (access, doi) in EXPECTED_BIB.items():
        assert key in bib, f"missing bibliography entry {key}"
        assert bib[key].get("access") == access, key
        assert bib[key].get("doi") or bib[key].get("url"), f"{key}: DOI or URL required (DC-000-03)"
        if doi:
            assert bib[key]["doi"] == doi
    assert "13.2.2_unpaved_roads.pdf" in bib["epa2006ap42s1322"]["url"]
    assert "isc3v2.pdf" in bib["epa1995isc3v2"]["url"]


@pytest.mark.req("DC-006-01")
def test_every_row_citation_resolves_in_the_bibliography() -> None:
    bib = _bib()
    for row in _table()["rows"]:
        assert row["citation"] in bib, f"{row['id']}: citation {row['citation']} not in references.bib"

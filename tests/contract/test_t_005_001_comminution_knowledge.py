"""T-005-001 (DC-005-01, DC-005-02): the comminution knowledge table, its equation entries and its bibliography keys.

Expected deliverables (spec 005 section 7 and section 6):
- `src/minephys/knowledge/comminution.yaml`: a DC-000-02 table `comminution` (licence CC-BY-4.0) holding every row of
  the section 7 list, with the published value, role, citation key, verification status and `verified_on` date;
- the comminution entries of `src/minephys/knowledge/catalogue/equations.yaml` (DC-008-01): one entry per model
  function of FR-005-01 to FR-005-28 whose `function` is `minephys.comminution.<name>`, domain `comminution`;
- the section 7 bibliography keys in `src/minephys/knowledge/references.bib` with the `access` classes of section 7.

Oracle: the values printed in the two readable guidelines, transcribed from spec 005 section 7 into this file
(hand transcription; the YAML is parsed here with `yaml.safe_load`, independently of the `minephys.knowledge` loader).
`@pytest.mark.knowledge(id)` pins each verified row (FR-000-21).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
KDIR = ROOT / "src" / "minephys" / "knowledge"
TABLE = KDIR / "comminution.yaml"
EQUATIONS = KDIR / "catalogue" / "equations.yaml"
BIB = KDIR / "references.bib"

GMSG = "gmsg2016morrell"
BOND = "mcivor2016bondgmsg"

# (row id, value, role, citation key, verified?)  -- spec 005 section 7, "Knowledge rows"
EXPECTED_ROWS: list[tuple[str, float, str, str, bool]] = [
    ("bond_law_coefficient", 10, "model_constant", BOND, True),
    ("bond_min_product_size", 70, "limit", BOND, True),
    ("bond_bm_constant", 44.5, "model_constant", BOND, True),
    ("bond_bm_exponent_screen", 0.23, "model_constant", BOND, True),
    ("bond_bm_exponent_grindability", 0.82, "model_constant", BOND, True),
    ("bond_short_ton_to_metric", 1.1025, "conversion", BOND, True),
    ("morrell_coefficient", 4, "model_constant", GMSG, True),
    ("morrell_f_constant", 0.295, "model_constant", GMSG, True),
    ("morrell_f_scale", 1000000, "model_constant", GMSG, True),
    ("morrell_coarse_fine_boundary", 750, "model_constant", GMSG, True),
    ("morrell_fine_grind_limit", 45, "limit", GMSG, True),
    ("morrell_k1_pebble_crusher", 0.95, "model_constant", GMSG, True),
    ("morrell_k2_open_circuit", 1.19, "model_constant", GMSG, True),
    ("morrell_k3_open_circuit", 1.19, "model_constant", GMSG, True),
    ("morrell_ks_crusher", 55, "model_constant", GMSG, True),
    ("morrell_ks_hpgr", 35, "model_constant", GMSG, True),
    ("morrell_s_exponent", -0.2, "model_constant", GMSG, True),
    ("morrell_ws_factor", 0.19, "model_constant", GMSG, True),
    ("morrell_mib_constant", 18.18, "model_constant", GMSG, True),
    ("morrell_mib_screen_exponent", 0.295, "model_constant", GMSG, True),
    ("morrell_relative_error_sd", 0.065, "limit", GMSG, True),
    ("austin_reference_size", 0.001, "model_constant", "austin1984ballmilling", False),
]

# symbols that the section 7 "Symbol" column names explicitly
EXPECTED_SYMBOLS: dict[str, set[str]] = {
    "bond_law_coefficient": {"bond_energy", "bond_operating_work_index"},
    "bond_min_product_size": {"bond_energy", "bond_operating_work_index"},
    "bond_bm_constant": {"bond_ball_mill_work_index"},
    "bond_bm_exponent_screen": {"bond_ball_mill_work_index"},
    "bond_bm_exponent_grindability": {"bond_ball_mill_work_index"},
    "bond_short_ton_to_metric": {"bond_ball_mill_work_index"},
    "morrell_coarse_fine_boundary": {"morrell_tumbling_coarse", "morrell_tumbling_fine"},
    "morrell_fine_grind_limit": {"morrell_tumbling_fine"},
    "morrell_k1_pebble_crusher": {"morrell_tumbling_coarse"},
    "morrell_k2_open_circuit": {"morrell_crusher"},
    "morrell_k3_open_circuit": {"morrell_hpgr"},
    "morrell_ks_crusher": {"morrell_crusher"},
    "morrell_ks_hpgr": {"morrell_hpgr"},
    "morrell_s_exponent": {"morrell_crusher", "morrell_hpgr"},
    "morrell_ws_factor": {"morrell_size_distribution_correction"},
    "morrell_mib_constant": {"morrell_mib"},
    "morrell_mib_screen_exponent": {"morrell_mib"},
    "austin_reference_size": {"austin_selection"},
}

# model functions of FR-005-01 .. FR-005-28 (DC-005-02: one equation entry per model)
MODEL_FUNCTIONS = [
    "bond_energy",
    "bond_operating_work_index",
    "bond_ball_mill_work_index",
    "morrell_energy",
    "morrell_tumbling_coarse",
    "morrell_tumbling_fine",
    "morrell_crusher",
    "morrell_hpgr",
    "morrell_size_distribution_correction",
    "morrell_mib",
    "pbm_batch_grinding",
    "pbm_continuous_mill",
    "austin_selection",
    "austin_breakage",
    "flotation_first_order",
    "klimpel_recovery",
    "flotation_cell_recovery",
    "two_product_recovery",
    "passing_size",
    "class_masses",
    "crusher_matrix_model",
    "whiten_classification",
]

# section 7 "Bibliography keys used" with their `access` class and DOI where one is printed
EXPECTED_BIB: dict[str, tuple[str, str | None]] = {
    "mcivor2016bondgmsg": ("open", None),
    "gmsg2016morrell": ("open", None),
    "bond1952third": ("bibliographic-only", None),
    "bond1961crushing": ("bibliographic-only", None),
    "morrell2004alternative": ("paywalled", "10.1016/j.minpro.2003.10.002"),
    "morrell2008method": ("paywalled", "10.1016/j.mineng.2007.10.001"),
    "morrell2009predicting": ("paywalled", "10.1016/j.mineng.2009.01.005"),
    "austin1971rate": ("paywalled", "10.1016/0032-5910(71)80064-5"),
    "reid1965batch": ("paywalled", "10.1016/0009-2509(65)80093-8"),
    "austin1984ballmilling": ("bibliographic-only", None),
    "whiten1972crushing": ("bibliographic-only", None),
    "gharai2016flotation": ("paywalled", "10.1080/08827508.2015.1115991"),
    "wills2016": ("paywalled", "10.1016/C2010-0-65478-2"),
    "ouchterlony2005swebrec": ("paywalled", "10.1179/037178405X44539"),
}


def _table() -> dict[str, Any]:
    assert TABLE.is_file(), "missing src/minephys/knowledge/comminution.yaml (DC-005-01)"
    doc = yaml.safe_load(TABLE.read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def _rows() -> dict[str, dict[str, Any]]:
    return {r["id"]: r for r in _table()["rows"]}


def _bib_entries() -> dict[str, dict[str, str]]:
    assert BIB.is_file(), "missing src/minephys/knowledge/references.bib"
    text = BIB.read_text(encoding="utf-8")
    out: dict[str, dict[str, str]] = {}
    for chunk in re.split(r"(?m)^@", text)[1:]:
        m = re.match(r"(\w+)\{([^,\s]+),", chunk)
        if not m:
            continue
        fields = {k.lower(): v.strip() for k, v in re.findall(r"(?m)^\s*(\w+)\s*=\s*\{(.*?)\}\s*,?\s*$", chunk)}
        fields["_type"] = m.group(1).lower()
        out[m.group(2)] = fields
    return out


@pytest.mark.req("DC-005-01")
@pytest.mark.oracle("hand-calculation", "spec 005 section 7 transcribed")
def test_table_header_is_a_dc_000_02_table() -> None:
    doc = _table()
    assert set(doc) == {"schema_version", "table", "title", "licence", "rows"}
    assert doc["schema_version"] == 1
    assert doc["table"] == "comminution"  # equals the file stem
    assert doc["licence"] == "CC-BY-4.0"
    assert isinstance(doc["title"], str) and doc["title"].strip()


@pytest.mark.req("DC-005-01")
def test_every_section7_row_is_present_exactly_once() -> None:
    ids = [r["id"] for r in _table()["rows"]]
    assert len(ids) == len(set(ids)), "duplicate row ids"
    missing = {row[0] for row in EXPECTED_ROWS} - set(ids)
    assert not missing, f"rows of spec 005 section 7 missing from the table: {sorted(missing)}"


@pytest.mark.req("DC-005-01")
@pytest.mark.parametrize(("row_id", "value", "role", "citation", "verified"), EXPECTED_ROWS, ids=[r[0] for r in EXPECTED_ROWS])
def test_row_matches_the_printed_value(row_id: str, value: float, role: str, citation: str, verified: bool) -> None:
    row = _rows()[row_id]
    assert row["value"] == pytest.approx(value, rel=0, abs=0)  # exact transcription, no rounding allowed
    assert row["role"] == role
    assert row["citation"] == citation
    assert isinstance(row["page"], str) and re.search(r"\d", row["page"]), "page locator required"
    assert isinstance(row["units"], str) and row["units"].strip()
    assert isinstance(row["quantity"], str) and row["quantity"].strip()
    if verified:
        assert row["verification"] == "verified"
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(row["verified_on"]))
    else:
        assert row["verification"] == "UNVERIFIED"
        assert "verified_on" not in row  # forbidden on an UNVERIFIED row (data model)


# one knowledge pin per verified row (FR-000-21); the transcription check is the test above
def _pin(row_id: str) -> Any:
    def test(row_id: str = row_id) -> None:
        row = _rows()[row_id]
        expected = next(r for r in EXPECTED_ROWS if r[0] == row_id)
        assert row["value"] == expected[1]
        assert row["verification"] == "verified"

    test.__name__ = f"test_verified_row_pin_{row_id}"
    return pytest.mark.knowledge(row_id)(pytest.mark.req("DC-005-01")(test))


for _r in EXPECTED_ROWS:
    if _r[4]:
        globals()[f"test_verified_row_pin_{_r[0]}"] = _pin(_r[0])


@pytest.mark.req("DC-005-01")
def test_rows_name_the_functions_that_read_them() -> None:
    rows = _rows()
    for row_id, names in EXPECTED_SYMBOLS.items():
        sym = rows[row_id]["symbol"]
        symbols = {sym} if isinstance(sym, str) else set(sym)
        for name in names:
            assert f"minephys.comminution.{name}" in symbols, f"{row_id} must list {name}"
    for row in _table()["rows"]:
        sym = row["symbol"]
        for s in [sym] if isinstance(sym, str) else sym:
            assert s.startswith("minephys.comminution."), f"{row['id']}: symbol outside the module: {s}"


@pytest.mark.req("DC-005-01")
def test_unverified_austin_row_is_flagged_not_hidden() -> None:
    row = _rows()["austin_reference_size"]
    assert row["verification"] == "UNVERIFIED"
    assert row["value"] == 0.001
    assert row["units"].strip() == "m"


@pytest.mark.req("DC-005-02")
def test_every_model_has_a_comminution_equation_entry() -> None:
    assert EQUATIONS.is_file(), "missing knowledge/catalogue/equations.yaml (first catalogue entry, FR-008-22)"
    doc = yaml.safe_load(EQUATIONS.read_text(encoding="utf-8"))
    entries = [e for e in doc["equations"] if e.get("domain") == "comminution"]
    functions = {e["function"] for e in entries}
    wanted = {f"minephys.comminution.{n}" for n in MODEL_FUNCTIONS}
    assert wanted <= functions, f"missing equation entries for {sorted(wanted - functions)}"
    for e in entries:
        assert e["latex"].strip()
        assert e["symbols"], "symbols with units are required"
        assert e["verification"] in {"verified", "UNVERIFIED"}


@pytest.mark.req("DC-005-02")
def test_unverified_models_are_flagged_in_the_catalogue() -> None:
    """Spec 005 section 7: the Austin forms, the Whiten crusher model and Klimpel/cell forms are UNVERIFIED."""
    assert EQUATIONS.is_file(), "missing knowledge/catalogue/equations.yaml"
    doc = yaml.safe_load(EQUATIONS.read_text(encoding="utf-8"))
    by_fn = {e["function"]: e for e in doc["equations"] if e.get("domain") == "comminution"}
    for name in ("austin_selection", "austin_breakage", "crusher_matrix_model", "whiten_classification", "klimpel_recovery"):
        entry = by_fn[f"minephys.comminution.{name}"]
        assert entry["verification"] == "UNVERIFIED", name
        assert "verified_on" not in entry


@pytest.mark.req("DC-005-02")
def test_equation_rows_resolve_to_table_rows() -> None:
    ids = set(_rows())
    assert EQUATIONS.is_file(), "missing knowledge/catalogue/equations.yaml"
    doc = yaml.safe_load(EQUATIONS.read_text(encoding="utf-8"))
    for e in doc["equations"]:
        if e.get("domain") == "comminution":
            assert set(e.get("rows", [])) <= ids


@pytest.mark.req("DC-005-01")
def test_section7_bibliography_keys_and_access_classes() -> None:
    bib = _bib_entries()
    for key, (access, doi) in EXPECTED_BIB.items():
        assert key in bib, f"missing bibliography entry {key}"
        assert bib[key].get("access") == access, key
        if doi is not None:
            assert bib[key].get("doi") == doi, key
        assert bib[key].get("doi") or bib[key].get("url"), f"{key}: DOI or URL required (DC-000-03)"
    assert "ceecthefuture.org" in bib["mcivor2016bondgmsg"]["url"]
    assert "smctesting.com" in bib["gmsg2016morrell"]["url"]


@pytest.mark.req("DC-005-01")
def test_every_row_citation_resolves_in_the_bibliography() -> None:
    bib = _bib_entries()
    for row in _table()["rows"]:
        assert row["citation"] in bib, f"{row['id']}: citation {row['citation']} not in references.bib"

"""T-000-012 (FR-000-08, FR-000-09): docstring and model-card audit over every exported function.

The audit runs on every function exported (`__all__`) by `minephys.units` and by each model subpackage found on disk,
and, so that it cannot pass vacuously, on the functions that specs 001 to 004 list in their section 7.1 signature
tables (haulage, blasting, geotech, bulk). Rules (hand-written here, spec 000 FR-000-08 and FR-000-09):

* numpydoc sections `Parameters` and `Returns`, and the model-card sections `Equation`, `Source`, `Validity` and
  `Knowledge rows` (a numpydoc heading: a title line followed by a line of at least three dashes). Conversion helpers
  of `minephys.units` need only `Parameters` and `Returns` (they are not models).
* every parameter of the signature is documented, in signature order, as `name : type [unit]`; the bracketed unit
  may be absent only when the type text names a bool, str, option set `{...}` or a random generator;
  `Returns` carries at least one bracketed unit unless it returns a bool or str;
* `Source` holds a BibTeX key present in `src/minephys/knowledge/references.bib` followed by a page locator
  (`p. 12`, `pp. 12-14`, `Table 2`, `Eq. 5`, `Appendix B.8`, `Fig. 3` or `section 7`);
* `Knowledge rows` is `none` or a list of row ids that exist in a table under `src/minephys/knowledge/`;
* no parameter name ends with a unit suffix outside the closed list of spec 000 A2.

Oracle: hand-written rules (plan 000 test strategy: "hand-written rules, numpydoc section parse").
"""

# ruff: noqa: PERF401
from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "src" / "minephys"
KNOWLEDGE = PKG / "knowledge"

EXPECTED = {
    "haulage": [
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
    ],
    "blasting": [
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
    ],
    "geotech": [
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
    ],
    "bulk": [
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
    ],
}
UNIT_FUNCTIONS = [
    "deg_to_rad",
    "rad_to_deg",
    "pct_to_fraction",
    "fraction_to_pct",
    "in_per_s_to_m_per_s",
    "m_per_s_to_in_per_s",
    "ft_to_m",
    "m_to_ft",
    "lb_to_kg",
    "kg_to_lb",
    "us_gal_to_m3",
    "m3_to_us_gal",
    "kwh_to_j",
    "j_to_kwh",
]
MODEL_CARD = ("Equation", "Source", "Validity", "Knowledge rows")
UNBRACKETED_OK = re.compile(r"\bbool\b|\bstr\b|\{|\bGenerator\b|\brng\b|callable|\bnone\b", re.I)
BRACKET = re.compile(r"\[[^\]\s][^\]]*\]")
PAGE = re.compile(
    r"\b(pp?\.\s*\d|Table\s*\d|Eq\.?\s*\d|Equation\s*\d|Appendix\s*[A-Z0-9]|Fig(?:ure|\.)?\s*\d|section\s*\d|§\s*\d)",
    re.I,
)
BANNED_SUFFIX = re.compile(r"_(km|kpa|psi|gal|mph|kmh|yd|oz|hr|day|kw|mw|gpa)$")


def parse_sections(doc: str) -> dict[str, list[str]]:
    """numpydoc split: a title line followed by a dashes line (>= 3) starts a section."""
    lines = inspect.cleandoc(doc).splitlines()
    sections: dict[str, list[str]] = {}
    current: str | None = None
    i = 0
    while i < len(lines):
        if i + 1 < len(lines) and lines[i].strip() and re.fullmatch(r"-{3,}", lines[i + 1].strip()):
            current = lines[i].strip()
            sections[current] = []
            i += 2
            continue
        if current is not None:
            sections[current].append(lines[i])
        i += 1
    return sections


def parameter_entries(body: list[str]) -> list[tuple[str, str]]:
    out = []
    for line in body:
        m = re.match(r"^(\*{0,2}[A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)\s*:\s*(.*)$", line)
        if m:
            for name in (n.strip() for n in m.group(1).split(",")):
                out.append((name.lstrip("*"), m.group(2)))
    return out


def bib_keys() -> set[str]:
    bib = KNOWLEDGE / "references.bib"
    assert bib.is_file(), "missing src/minephys/knowledge/references.bib"
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib.read_text(encoding="utf-8")))


def row_ids() -> set[str]:
    ids: set[str] = set()
    for f in list(KNOWLEDGE.glob("*.yaml")) + list(KNOWLEDGE.glob("share-alike/*.yaml")):
        ids |= {r["id"] for r in yaml.safe_load(f.read_text(encoding="utf-8"))["rows"]}
    return ids


def audit(fn, *, model: bool, keys: set[str] | None = None, rows: set[str] | None = None) -> list[str]:
    """Return the list of violations for one function (empty = clean)."""
    problems: list[str] = []
    doc = inspect.getdoc(fn) or ""
    if not doc:
        return ["no docstring"]
    sec = parse_sections(doc)
    for need in ("Parameters", "Returns", *(MODEL_CARD if model else ())):
        if need not in sec:
            problems.append(f"missing section {need}")
    sig = inspect.signature(fn)
    names = [p.name for p in sig.parameters.values() if p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)]
    for n in names:
        if BANNED_SUFFIX.search(n):
            problems.append(f"parameter {n} carries a unit suffix outside the closed list A2")
    if "Parameters" in sec:
        entries = parameter_entries(sec["Parameters"])
        documented = [n for n, _ in entries]
        if [n for n in documented if n in names] != names:
            problems.append(f"parameters {names} not documented in signature order (found {documented})")
        for n, text in entries:
            if n in names and not BRACKET.search(text) and not UNBRACKETED_OK.search(text):
                problems.append(f"parameter {n} has no bracketed unit")
    if "Returns" in sec:
        body = "\n".join(sec["Returns"])
        if not BRACKET.search(body) and not re.search(r"\b(bool|str)\b", body):
            problems.append("Returns has no bracketed unit")
    if model:
        for title in MODEL_CARD:
            if title in sec and not "".join(sec[title]).strip():
                problems.append(f"empty section {title}")
        if "Source" in sec:
            text = "\n".join(sec["Source"])
            found = [
                k for k in (keys or set()) if re.search(rf"(?<![A-Za-z0-9_:-]){re.escape(k)}(?![A-Za-z0-9_:-])", text)
            ]
            if not found:
                problems.append("Source names no BibTeX key present in references.bib")
            if not PAGE.search(text):
                problems.append("Source gives no page locator")
        if "Knowledge rows" in sec:
            text = " ".join(sec["Knowledge rows"]).strip()
            if text and text.lower().rstrip(".") != "none":
                listed = re.findall(r"[a-z][a-z0-9_]*", text.replace("`", " "))
                unknown = [r for r in listed if rows is not None and r not in rows]
                if unknown:
                    problems.append(f"Knowledge rows names unknown row ids {unknown}")
    return problems


def _exported_functions(module_name: str) -> dict[str, object]:
    mod = importlib.import_module(module_name)
    out: dict[str, object] = {}
    for name in getattr(mod, "__all__", ()):
        obj = getattr(mod, name)
        if inspect.isfunction(obj):
            out[name] = obj
    return out


# ------------------------------------------------------------ the auditor itself, on hand-written docstrings

GOOD = """
Cycle time of one haul.

Parameters
----------
haul : float [s]
    Loaded travel time.
variant : {"a", "b"}
    Option.

Returns
-------
float [s]
    Total time.

Equation
--------
t = haul

Source
------
doe2020, p. 12

Validity
--------
haul >= 0.

Knowledge rows
--------------
none
"""


def _good(haul, variant="a"):
    return haul


_good.__doc__ = GOOD


@pytest.mark.req("FR-000-09")
@pytest.mark.oracle("hand-calculation", "a docstring that follows every rule has no violations")
def test_auditor_accepts_a_good_docstring() -> None:
    assert audit(_good, model=True, keys={"doe2020"}, rows=set()) == []


@pytest.mark.req("FR-000-09")
@pytest.mark.req("FR-000-08")
@pytest.mark.oracle("hand-calculation", "each rule has a hand-written violation that the auditor must report")
@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda d: d.replace("Equation\n--------\nt = haul\n\n", ""), "missing section Equation"),
        (lambda d: d.replace("Validity\n--------\nhaul >= 0.\n\n", ""), "missing section Validity"),
        (lambda d: d.replace("Knowledge rows\n--------------\nnone", ""), "missing section Knowledge rows"),
        (lambda d: d.replace("haul : float [s]", "haul : float"), "no bracketed unit"),
        (lambda d: d.replace("float [s]\n    Total", "float\n    Total"), "Returns has no bracketed unit"),
        (lambda d: d.replace("doe2020, p. 12", "doe2020"), "no page locator"),
        (lambda d: d.replace("doe2020, p. 12", "nobody1999, p. 12"), "no BibTeX key"),
        (lambda d: d.replace("none", "made_up_row"), "unknown row ids"),
        (lambda d: d.replace("haul : float [s]", "speed : float [s]"), "signature order"),
    ],
)
def test_auditor_reports_each_rule(mutation, expected: str) -> None:
    def f(haul, variant="a"):
        return haul

    f.__doc__ = mutation(GOOD)
    problems = audit(f, model=True, keys={"doe2020"}, rows=set())
    assert any(expected in p for p in problems), problems


@pytest.mark.req("FR-000-08")
@pytest.mark.oracle("hand-calculation", "a unit suffix outside the closed list of A2 is reported")
def test_auditor_reports_a_non_closed_list_suffix() -> None:
    def f(length_km):
        """T.

        Parameters
        ----------
        length_km : float [km]

        Returns
        -------
        float [m]
        """
        return length_km

    assert any("closed list" in p for p in audit(f, model=False))


# ------------------------------------------------------------ the real package


@pytest.mark.req("FR-000-08")
@pytest.mark.oracle("hand-calculation", "units helpers: Parameters and Returns with bracketed units")
@pytest.mark.parametrize("name", UNIT_FUNCTIONS)
def test_units_helpers_are_documented(name: str) -> None:
    fns = _exported_functions("minephys.units")
    assert name in fns, f"minephys.units does not export {name}"
    assert audit(fns[name], model=False) == []


def _model_cases() -> list[tuple[str, str]]:
    cases = [(mod, fn) for mod, names in EXPECTED.items() for fn in names]
    for p in sorted(PKG.iterdir()):
        if (
            p.is_dir()
            and (p / "__init__.py").is_file()
            and not p.name.startswith("_")
            and p.name not in {*EXPECTED, "knowledge"}
        ):
            mod = importlib.import_module(f"minephys.{p.name}")
            cases += [(p.name, n) for n in getattr(mod, "__all__", ()) if inspect.isfunction(getattr(mod, n))]
    return cases


@pytest.mark.req("FR-000-08")
@pytest.mark.req("FR-000-09")
@pytest.mark.oracle("hand-calculation", "numpydoc plus model-card sections on every exported model function")
@pytest.mark.parametrize(("module", "name"), _model_cases(), ids=lambda v: str(v))
def test_model_function_card(module: str, name: str) -> None:
    fns = _exported_functions(f"minephys.{module}")
    assert name in fns, f"minephys.{module} does not export the function {name}"
    problems = audit(fns[name], model=True, keys=bib_keys(), rows=row_ids())
    assert problems == [], problems


@pytest.mark.req("FR-000-09")
@pytest.mark.oracle(
    "hand-calculation", "an exported name that is not a function must be a class or constant, not a stub"
)
@pytest.mark.parametrize("module", sorted(EXPECTED))
def test_every_exported_function_of_a_model_subpackage_is_audited(module: str) -> None:
    mod = importlib.import_module(f"minephys.{module}")
    exported = {n for n in mod.__all__ if inspect.isfunction(getattr(mod, n))}
    assert set(EXPECTED[module]) <= exported
    extra = exported - set(EXPECTED[module])
    for name in sorted(extra):  # helper functions added by the implementation get the same audit
        assert audit(getattr(mod, name), model=True, keys=bib_keys(), rows=row_ids()) == [], name

"""T-000-006 (P-000-05, FR-000-08): the `units` table (spec 000 section 8, A7) and the conversion helpers.

Expected API, module `minephys.units` (all elementwise, SI at the other end, FR-000-07 return types):

    deg_to_rad(x) / rad_to_deg(x)                     [deg] <-> [rad]
    pct_to_fraction(x) / fraction_to_pct(x)           [%] <-> [1]
    in_per_s_to_m_per_s(x) / m_per_s_to_in_per_s(x)   [in/s] <-> [m/s]
    ft_to_m(x) / m_to_ft(x)                           [ft] <-> [m]
    lb_to_kg(x) / kg_to_lb(x)                         [lb] <-> [kg]
    us_gal_to_m3(x) / m3_to_us_gal(x)                 [US gal] <-> [m^3]
    kwh_to_j(x) / j_to_kwh(x)                         [kWh] <-> [J]
and the table `src/minephys/knowledge/units.yaml` with the six rows of spec 000 A7 (role `conversion`, verified,
`verified_on` set). Conversion factors are read from the rows (FR-000-19); the US gallon is 231 in^3 with
1 in = 0.0254 m, i.e. 3.785411784e-3 m^3, derived exactly in code.

Oracles: exact unit definitions of NIST SP 811 Appendix B.8 and NIST Handbook 44 (2026) Appendix C, read in spec 000
A7 (hand calculation); the identity pairs are analytical. Tolerances: round trip rtol 1e-15 (P-000-05), exact
definitions TC-1 (rtol 1e-12).
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

import minephys
from minephys import units as U

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "src" / "minephys" / "knowledge" / "units.yaml"

PAIRS = [
    ("deg_to_rad", "rad_to_deg"),
    ("pct_to_fraction", "fraction_to_pct"),
    ("in_per_s_to_m_per_s", "m_per_s_to_in_per_s"),
    ("ft_to_m", "m_to_ft"),
    ("lb_to_kg", "kg_to_lb"),
    ("us_gal_to_m3", "m3_to_us_gal"),
    ("kwh_to_j", "j_to_kwh"),
]
ALL_FUNCS = [name for pair in PAIRS for name in pair]

# exact definitions: (function, input, expected SI output)
EXACT = [
    ("deg_to_rad", 180.0, math.pi),
    ("deg_to_rad", 90.0, math.pi / 2.0),
    ("rad_to_deg", math.pi, 180.0),
    ("pct_to_fraction", 25.0, 0.25),
    ("fraction_to_pct", 0.05, 5.0),
    ("in_per_s_to_m_per_s", 100.0, 2.54),  # 1 in = 0.0254 m exactly
    ("ft_to_m", 10.0, 3.048),  # 1 ft = 0.3048 m exactly
    ("m_to_ft", 0.3048, 1.0),
    ("lb_to_kg", 1.0, 0.45359237),  # avoirdupois pound, exact
    ("kg_to_lb", 0.45359237, 1.0),
    ("us_gal_to_m3", 1.0, 3.785411784e-3),  # 231 in^3 x 0.0254^3
    ("m3_to_us_gal", 3.785411784e-3, 1.0),
    ("kwh_to_j", 1.0, 3.6e6),
    ("j_to_kwh", 3.6e6, 1.0),
]


def _table() -> dict:
    assert TABLE.is_file(), "missing knowledge table src/minephys/knowledge/units.yaml"
    return yaml.safe_load(TABLE.read_text(encoding="utf-8"))


def _row(row_id: str) -> dict:
    rows = {r["id"]: r for r in _table()["rows"]}
    assert row_id in rows, f"units.yaml has no row {row_id!r}"
    return rows[row_id]


def _pin(row_id: str, value: float, units: str) -> None:
    r = _row(row_id)
    # PyYAML (YAML 1.1) reads `3.6e6` as a STRING; a table value must be a YAML number (DC-000-02: type number).
    assert isinstance(r["value"], int | float)
    assert not isinstance(r["value"], bool)
    assert r["value"] == value
    assert r["units"] == units
    assert r["role"] == "conversion"
    assert r["verification"] == "verified"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["verified_on"])
    assert r["page"].strip()
    assert r["citation"].strip()


@pytest.mark.req("P-000-05")
@pytest.mark.oracle("hand-calculation", "spec 000 A7: table header and licence")
def test_units_table_header() -> None:
    t = _table()
    assert t["schema_version"] == 1
    assert t["table"] == "units"
    assert t["licence"] == "CC-BY-4.0"
    assert {r["id"] for r in t["rows"]} >= {
        "standard_gravity",
        "inch",
        "foot",
        "pound",
        "us_gallon_cubic_inches",
        "kilowatt_hour",
    }


@pytest.mark.req("P-000-05")
@pytest.mark.knowledge("standard_gravity")
@pytest.mark.oracle("worked-example", "nistsp811 Appendix B.8: standard acceleration of free fall, exact")
def test_row_standard_gravity() -> None:
    _pin("standard_gravity", 9.80665, "m/s²")


@pytest.mark.req("P-000-05")
@pytest.mark.knowledge("inch")
@pytest.mark.oracle("worked-example", "nistsp811 Appendix B.8; nisthb44 p. 21: 2.54 centimeters (exactly)")
def test_row_inch() -> None:
    _pin("inch", 0.0254, "m")


@pytest.mark.req("P-000-05")
@pytest.mark.knowledge("foot")
@pytest.mark.oracle("worked-example", "nistsp811 Appendix B.8: 1 ft = 0.3048 m, exact")
def test_row_foot() -> None:
    _pin("foot", 0.3048, "m")


@pytest.mark.req("P-000-05")
@pytest.mark.knowledge("pound")
@pytest.mark.oracle("worked-example", "nisthb44 p. 17: avoirdupois pound = 0.45359237 kg")
def test_row_pound() -> None:
    _pin("pound", 0.45359237, "kg")


@pytest.mark.req("P-000-05")
@pytest.mark.knowledge("us_gallon_cubic_inches")
@pytest.mark.oracle("worked-example", "nisthb44 p. 25: 231 cubic inches (exactly)")
def test_row_us_gallon_cubic_inches() -> None:
    _pin("us_gallon_cubic_inches", 231, "in³")


@pytest.mark.req("P-000-05")
@pytest.mark.knowledge("kilowatt_hour")
@pytest.mark.oracle("worked-example", "nistsp811 Appendix B.8: 1 kWh = 3.6e6 J, exact")
def test_row_kilowatt_hour() -> None:
    _pin("kilowatt_hour", 3.6e6, "J")


@pytest.mark.req("P-000-05")
@pytest.mark.oracle("hand-calculation", "exact definitions of spec 000 A7")
@pytest.mark.parametrize(("name", "x", "expected"), EXACT, ids=lambda v: str(v))
def test_exact_definitions(name: str, x: float, expected: float) -> None:
    got = getattr(U, name)(x)
    assert type(got) is np.float64
    assert got == pytest.approx(expected, rel=1e-12)


@pytest.mark.req("P-000-05")
@pytest.mark.oracle("analytical", "round trip of every pair returns the input (P-000-05)")
@pytest.mark.parametrize(("fwd", "back"), PAIRS)
@settings(max_examples=200, deadline=None)
@given(
    x=st.one_of(
        st.floats(1e-6, 1e6),
        st.floats(-1e6, -1e-6),
    )
)
def test_property_round_trip(fwd: str, back: str, x: float) -> None:
    f, b = getattr(U, fwd), getattr(U, back)
    assert b(f(x)) == pytest.approx(x, rel=1e-15, abs=0.0)
    assert f(b(x)) == pytest.approx(x, rel=1e-15, abs=0.0)


@pytest.mark.req("P-000-05")
@pytest.mark.oracle("analytical", "metamorphic: a linear unit conversion is homogeneous, additive and odd")
@pytest.mark.parametrize("name", ALL_FUNCS)
@settings(max_examples=100, deadline=None)
@given(a=st.floats(-1e6, 1e6), b=st.floats(-1e6, 1e6), k=st.floats(1e-3, 1e3))
def test_property_conversions_are_linear(name: str, a: float, b: float, k: float) -> None:
    f = getattr(U, name)
    scale = max(abs(float(f(a))), abs(float(f(b))), abs(float(f(a + b))), 1e-300)
    assert f(k * a) == pytest.approx(k * f(a), rel=1e-12, abs=1e-12 * scale)
    assert f(a + b) == pytest.approx(f(a) + f(b), rel=1e-12, abs=1e-12 * scale)
    assert f(-a) == -f(a)
    assert f(0.0) == 0.0


@pytest.mark.req("P-000-05")
@pytest.mark.oracle("hand-calculation", "metamorphic: composition of definitions, 1 US gal in in^3 via the rows")
def test_us_gallon_is_231_cubic_inches_of_the_inch_row() -> None:
    inch = _row("inch")["value"]
    cubic = _row("us_gallon_cubic_inches")["value"]
    assert U.us_gal_to_m3(1.0) == pytest.approx(cubic * inch**3, rel=1e-14)
    assert U.us_gal_to_m3(1.0) == pytest.approx(3.785411784e-3, rel=1e-14)
    assert U.in_per_s_to_m_per_s(1.0) == pytest.approx(inch, rel=1e-15)
    assert U.ft_to_m(1.0) == pytest.approx(12 * inch, rel=1e-15)  # 1 ft = 12 in exactly


@pytest.mark.req("P-000-05")
@pytest.mark.req("FR-000-07")
@pytest.mark.oracle("hand-calculation", "arrays broadcast elementwise; the scalar rule returns numpy.float64")
@pytest.mark.parametrize("name", ALL_FUNCS)
def test_vectorised_matches_scalar_and_returns_float64(name: str) -> None:
    f = getattr(U, name)
    xs = np.array([[-2.5, 0.0], [1.0, 1e5]])
    out = f(xs)
    assert out.dtype == np.float64
    assert out.shape == (2, 2)
    expected = np.array([[f(float(v)) for v in row] for row in xs])
    np.testing.assert_allclose(out, expected, rtol=1e-14, atol=1e-14 * float(np.max(np.abs(expected))))
    assert f(np.empty(0)).shape == (0,)
    assert f(np.float32(2.0)) == f(2.0)
    assert f(3) == f(3.0)


@pytest.mark.req("P-000-05")
@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("hand-calculation", "hostile inputs of FR-000-10 and FR-000-11")
@pytest.mark.parametrize("name", ALL_FUNCS)
def test_hostile_inputs(name: str) -> None:
    f = getattr(U, name)
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(minephys.InputError):
            f(bad)
    for bad in ("1.0", None, True, 1 + 1j, b"1"):
        with pytest.raises(minephys.InputTypeError):
            f(bad)
    with pytest.raises(minephys.InputError):
        f(np.array([1.0, np.nan]))


@pytest.mark.req("FR-000-08")
@pytest.mark.oracle("hand-calculation", "FR-000-08: every docstring states the units in square brackets")
@pytest.mark.parametrize("name", ALL_FUNCS)
def test_docstrings_state_units_in_square_brackets(name: str) -> None:
    doc = getattr(U, name).__doc__ or ""
    assert "Parameters" in doc
    assert "Returns" in doc
    assert len(re.findall(r"\[[^\]\s][^\]]*\]", doc)) >= 2, "one bracketed unit per parameter and per return value"


@pytest.mark.req("FR-000-08")
@pytest.mark.oracle("hand-calculation", "spec 000 A2: unit suffixes are a closed list; helper names carry their unit")
def test_public_names_are_the_documented_helpers() -> None:
    public = {n for n in dir(U) if not n.startswith("_") and callable(getattr(U, n))}
    assert set(ALL_FUNCS) <= public
    exported = set(getattr(U, "__all__", ()))
    assert set(ALL_FUNCS) <= exported

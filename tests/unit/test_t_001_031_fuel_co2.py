"""T-001-031 (FR-001-13, FR-001-14, FR-001-15): fuel use, diesel CO2 and grid CO2.

Expected API:
    `H.fuel_use(source_energy, fuel_energy_density)` -> `E / density` in m^3 (J and J/m^3 in);
    `H.co2_from_diesel(fuel_volume, emission_factor=None)` -> kg; with `emission_factor=None` the factor is the verified
        row `diesel_co2_kg_per_us_gal` = 10.21 kg CO2 / US gal divided by the exact US gallon 3.785411784e-3 m^3, i.e.
        2,697.1967 kg/m^3; otherwise the given factor in kg/m^3;
    `H.co2_from_electricity(energy, grid_intensity)` -> `energy * grid_intensity` in kg (J and kg/J in), no default.

Oracles: the printed values of spec 001 section 7.4 (TC-2), the published EPA factor (US EPA GHG Emission Factors Hub
2025, Table 2, p. 2: 10.21 kg CO2 per gallon of diesel, a combustion factor) and the exact definition of the US gallon
(231 in^3, NIST Handbook 44, 1 in = 0.0254 m).
"""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pytest
import yaml

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

US_GALLON_M3 = 231 * 0.0254**3  # exact: 3.785411784e-3 m^3
ROW_FILE = Path(__file__).resolve().parents[2] / "src" / "minephys" / "knowledge" / "haulage.yaml"


@pytest.mark.req("FR-001-13")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: 4,034,736,000 J / 36e9 J/m^3 = 0.112076 m^3 of diesel")
def test_fuel_use_printed_value() -> None:
    got = H.fuel_use(4034736000.0, 36e9)
    assert type(got) is np.float64
    assert got == pytest.approx(0.112076, abs=5e-7)
    assert got == pytest.approx(4034736000.0 / 36e9, rel=1e-12)


@pytest.mark.req("FR-001-13")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: the three-segment cycle, 4.35427764e9 J -> 0.120952 m^3")
def test_fuel_use_of_the_cycle() -> None:
    assert H.fuel_use(4.35427764e9, 36e9) == pytest.approx(0.120952, abs=5e-7)


@pytest.mark.req("FR-001-13")
@pytest.mark.oracle("analytical", "zero energy burns no fuel; arrays divide elementwise; no defaults")
def test_fuel_use_zero_arrays_and_signature() -> None:
    assert H.fuel_use(0.0, 36e9) == 0.0
    e = np.array([0.0, 3.6e10, 7.2e10])
    np.testing.assert_allclose(H.fuel_use(e, 36e9), [0.0, 1.0, 2.0], rtol=1e-14, atol=0.0)
    for p in inspect.signature(H.fuel_use).parameters.values():
        assert p.default is inspect.Parameter.empty


@pytest.mark.req("FR-001-14")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: co2_from_diesel(0.112076 m^3) = 302.291 kg")
def test_diesel_co2_printed_values() -> None:
    got = H.co2_from_diesel(0.112076)
    assert type(got) is np.float64
    assert got == pytest.approx(302.291, abs=5e-4)
    # the cycle's CO2 is printed from the unrounded fuel volume 4.35427764e9 / 36e9 = 0.12095215...
    assert H.co2_from_diesel(4.35427764e9 / 36e9) == pytest.approx(326.232, abs=5e-4)


@pytest.mark.req("FR-001-14")
@pytest.mark.oracle("hand-calculation", "10.21 / 3.785411784e-3 = 2,697.1967 kg per m^3 (spec 001 FR-001-14)")
def test_default_factor_in_si() -> None:
    assert H.co2_from_diesel(1.0) == pytest.approx(2697.1967, abs=5e-5)
    assert H.co2_from_diesel(1.0) == pytest.approx(10.21 / 3.785411784e-3, rel=1e-12)


@pytest.mark.req("FR-001-14")
@pytest.mark.knowledge("diesel_co2_kg_per_us_gal")
@pytest.mark.oracle("worked-example", "epa2025ghghub Table 2, p. 2: diesel combustion, 10.21 kg CO2 per US gallon")
def test_one_us_gallon_emits_the_published_10_21_kg() -> None:
    assert H.co2_from_diesel(US_GALLON_M3) == pytest.approx(10.21, rel=1e-12)
    assert H.co2_from_diesel(10.0 * US_GALLON_M3) == pytest.approx(102.1, rel=1e-12)


@pytest.mark.req("FR-001-14")
@pytest.mark.knowledge("diesel_co2_kg_per_us_gal")
@pytest.mark.oracle("worked-example", "epa2025ghghub Table 2, p. 2: the knowledge row holds the published value")
def test_the_default_comes_from_the_knowledge_row() -> None:
    assert ROW_FILE.is_file(), "missing src/minephys/knowledge/haulage.yaml"
    rows = {r["id"]: r for r in yaml.safe_load(ROW_FILE.read_text(encoding="utf-8"))["rows"]}
    row = rows["diesel_co2_kg_per_us_gal"]
    assert row["value"] == 10.21
    assert H.co2_from_diesel(1.0) == pytest.approx(row["value"] / US_GALLON_M3, rel=1e-12)


@pytest.mark.req("FR-001-14")
@pytest.mark.oracle("hand-calculation", "an explicit factor replaces the default: 2.0 m^3 * 2500 kg/m^3 = 5000 kg")
def test_explicit_emission_factor() -> None:
    assert H.co2_from_diesel(2.0, emission_factor=2500.0) == 5000.0
    assert H.co2_from_diesel(0.0) == 0.0
    out = H.co2_from_diesel(np.array([0.0, 1.0, 2.0]), emission_factor=2000.0)
    np.testing.assert_allclose(out, [0.0, 2000.0, 4000.0], rtol=0.0, atol=0.0)


@pytest.mark.req("FR-001-15")
@pytest.mark.oracle("hand-calculation", "3.6e6 J (1 kWh) at 0.4 kg/kWh = 0.4 / 3.6e6 kg/J gives 0.4 kg")
def test_grid_co2_is_the_product() -> None:
    got = H.co2_from_electricity(3.6e6, 0.4 / 3.6e6)
    assert type(got) is np.float64
    assert got == pytest.approx(0.4, rel=1e-12)


@pytest.mark.req("FR-001-15")
@pytest.mark.oracle("hand-calculation", "1.54032635e9 J * 1e-7 kg/J = 154.032635 kg (the BEV cycle of spec 7.4)")
def test_grid_co2_of_the_bev_cycle() -> None:
    assert H.co2_from_electricity(1.54032635e9, 1.0e-7) == pytest.approx(154.032635, rel=1e-12)


@pytest.mark.req("FR-001-15")
@pytest.mark.oracle(
    "analytical", "no default for the grid intensity; arrays multiply elementwise; zero energy gives zero"
)
def test_grid_co2_has_no_default_and_broadcasts() -> None:
    for p in inspect.signature(H.co2_from_electricity).parameters.values():
        assert p.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        H.co2_from_electricity(1.0e9)  # type: ignore[call-arg]
    e = np.array([[1.0e6], [2.0e6]])
    gi = np.array([1.0e-8, 2.0e-8, 3.0e-8])
    np.testing.assert_allclose(H.co2_from_electricity(e, gi), e * gi, rtol=1e-14, atol=0.0)
    assert H.co2_from_electricity(0.0, 1e-7) == 0.0

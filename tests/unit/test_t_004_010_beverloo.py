# ruff: noqa: E501
"""T-004-010 (FR-004-01, FR-004-02): Beverloo's discharge law.

Expected API, module `minephys.bulk` (elementwise, float64; a scalar call gives a NumPy float64):

    beverloo_discharge(orifice_diameter, particle_diameter, bulk_density, discharge_coefficient, annulus_coefficient,
                       g=9.80665) -> C rho_b sqrt(g) (D - k d)^(5/2)  [kg/s]
        D orifice diameter [m], d particle diameter [m], rho_b bulk density [kg/m^3], C discharge coefficient [1], k
        annulus coefficient [1], g [m/s^2] with the default g0 = 9.80665 exactly. `discharge_coefficient` and
        `annulus_coefficient` have NO default (the literature ranges are documented rows, never defaults). The
        exponent 5/2 is read from the row `beverloo_exponent`, which is UNVERIFIED (secondary source only): every call
        emits `minephys.knowledge.UnverifiedParameterWarning` (spec 004 section 7.6). If D <= k d (no free-flowing
        opening) the call raises `InputError` naming `orifice_diameter` (FR-004-02).

Oracles: spec 004 section 7.4 hand calculations (C = 0.56 and k = 1.5 are passed explicitly as illustrative
inputs: 106.28641 kg/s at D = 0.3 m, 13.996565 kg/s at D = 0.15 m, 688.26469 kg/s at D = 0.6 m; TC-2),
dimensional analysis of the exponent (the only combination of rho_b, g and a length that has the units kg/s is
rho_b g^(1/2) L^(5/2); verified by scaling), and an independent float64 recomputation (TC-1).
"""

from __future__ import annotations

import inspect
import math
import warnings

import numpy as np
import pytest
from minephys.knowledge import UnverifiedParameterWarning

import minephys
from minephys import bulk as B

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

G0 = 9.80665


def beverloo(d_orifice, d_particle, rho, c, k, g=G0):
    return B.beverloo_discharge(d_orifice, d_particle, rho, c, k, g)


@pytest.mark.req("FR-004-01")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 7.4: beverloo_discharge(0.3, 0.02, 1600, 0.56, 1.5) = 106.28641 kg/s (382.6 t/h); 0.15 m: 13.996565; 0.6 m: 688.26469",
)
@pytest.mark.parametrize(
    ("orifice", "expected", "tolerance"),
    [(0.3, 106.28641, 5e-6), (0.15, 13.996565, 5e-7), (0.6, 688.26469, 5e-6)],
)
def test_spec_worked_values(orifice: float, expected: float, tolerance: float) -> None:
    q = beverloo(orifice, 0.02, 1600.0, 0.56, 1.5)
    assert type(q) is np.float64
    assert q == pytest.approx(expected, abs=tolerance)  # TC-2: half a unit of the last printed digit


@pytest.mark.req("FR-004-01")
@pytest.mark.oracle("hand-calculation", "spec 004 7.4: 106.28641 kg/s is 382.6 t/h")
def test_spec_tonnes_per_hour() -> None:
    assert float(beverloo(0.3, 0.02, 1600.0, 0.56, 1.5)) * 3.6 == pytest.approx(382.6, abs=0.05)


GRID = [
    (orifice, particle, k)
    for orifice in (0.05, 0.3, 1.0, 2.0)
    for particle in (1e-4, 0.01, 0.04)
    for k in (0.0, 1.0, 1.5, 3.0)
    if orifice > 1.05 * k * particle  # an open grid only; the closed cases are in test_no_free_opening
]


@pytest.mark.req("FR-004-01")
@pytest.mark.oracle("analytical", "independent float64 recomputation of C rho sqrt(g) (D - k d)^(5/2) on a grid (TC-1)")
@pytest.mark.parametrize(("orifice", "particle", "k"), GRID)
def test_closed_form_grid(orifice: float, particle: float, k: float) -> None:
    c, rho, g = 0.6, 1450.0, 9.81
    ref = c * rho * math.sqrt(g) * (orifice - k * particle) ** 2.5
    assert beverloo(orifice, particle, rho, c, k, g) == pytest.approx(ref, rel=1e-12)


@pytest.mark.req("FR-004-01")
@pytest.mark.oracle(
    "analytical",
    "dimensional analysis: the exponent of the free opening is 5/2, found by scaling D and d together by lambda",
)
@pytest.mark.parametrize("lam", [2.0, 10.0, 0.1, 1000.0])
def test_length_exponent_is_five_halves(lam: float) -> None:
    base = float(beverloo(0.4, 0.02, 1500.0, 0.6, 1.4))
    scaled = float(beverloo(0.4 * lam, 0.02 * lam, 1500.0, 0.6, 1.4))
    assert math.log(scaled / base) / math.log(lam) == pytest.approx(2.5, rel=1e-10)
    assert scaled == pytest.approx(base * lam**2.5, rel=1e-12)


@pytest.mark.req("FR-004-01")
@pytest.mark.oracle(
    "analytical",
    "dimensional analysis: the discharge is linear in bulk density and in C and goes as the square root of g",
)
def test_density_coefficient_and_gravity_exponents() -> None:
    base = float(beverloo(0.3, 0.02, 1600.0, 0.56, 1.5))
    assert float(beverloo(0.3, 0.02, 3200.0, 0.56, 1.5)) == pytest.approx(2.0 * base, rel=1e-13)
    assert float(beverloo(0.3, 0.02, 1600.0, 1.12, 1.5)) == pytest.approx(2.0 * base, rel=1e-13)
    assert float(beverloo(0.3, 0.02, 1600.0, 0.56, 1.5, 4.0 * G0)) == pytest.approx(2.0 * base, rel=1e-13)
    assert float(beverloo(0.3, 0.02, 1600.0, 0.56, 1.5, G0 / 4.0)) == pytest.approx(0.5 * base, rel=1e-13)


@pytest.mark.req("FR-004-01")
@pytest.mark.oracle("analytical", "dimensional analysis: units m, kg -> mm, g leave the physical discharge unchanged")
def test_unit_change_m_to_mm() -> None:
    q_si = float(beverloo(0.3, 0.02, 1600.0, 0.56, 1.5))  # kg/s
    # lengths in mm, mass in g: rho in g/mm^3 = 1e-6 kg/m^3 (1 kg/m^3 = 1e3 g / 1e9 mm^3), g in mm/s^2
    q_mm = float(beverloo(300.0, 20.0, 1600.0e-6, 0.56, 1.5, G0 * 1e3))  # g/s
    assert q_mm == pytest.approx(q_si * 1e3, rel=1e-12)


@pytest.mark.req("FR-004-01")
@pytest.mark.oracle("analytical", "g defaults to g0 = 9.80665 exactly; C and k have no default")
def test_defaults() -> None:
    params = inspect.signature(B.beverloo_discharge).parameters
    assert list(params) == [
        "orifice_diameter",
        "particle_diameter",
        "bulk_density",
        "discharge_coefficient",
        "annulus_coefficient",
        "g",
    ]
    assert params["g"].default == 9.80665
    for name in (
        "orifice_diameter",
        "particle_diameter",
        "bulk_density",
        "discharge_coefficient",
        "annulus_coefficient",
    ):
        assert params[name].default is inspect.Parameter.empty, f"{name} must not have a default"
    with pytest.raises(TypeError):
        B.beverloo_discharge(0.3, 0.02, 1600.0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        B.beverloo_discharge(0.3, 0.02, 1600.0, 0.56)  # type: ignore[call-arg]
    assert beverloo(0.3, 0.02, 1600.0, 0.56, 1.5, G0) == B.beverloo_discharge(0.3, 0.02, 1600.0, 0.56, 1.5)
    assert B.beverloo_discharge(0.3, 0.02, 1600.0, 0.56, 1.5, g=9.81) == pytest.approx(
        float(beverloo(0.3, 0.02, 1600.0, 0.56, 1.5)) * math.sqrt(9.81 / G0), rel=1e-13
    )


@pytest.mark.req("FR-004-01")
@pytest.mark.oracle(
    "analytical", "spec 004 7.6: the UNVERIFIED exponent row makes every call emit UnverifiedParameterWarning"
)
def test_unverified_exponent_warns() -> None:
    with pytest.warns(UnverifiedParameterWarning):
        B.beverloo_discharge(0.3, 0.02, 1600.0, 0.56, 1.5)
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        out = B.beverloo_discharge(0.3, 0.02, 1600.0, 0.56, 1.5)
    assert any(issubclass(w.category, UnverifiedParameterWarning) for w in rec)
    assert math.isfinite(float(out)), "the warning never replaces the result"
    assert not any(issubclass(w.category, minephys.ValidityWarning) for w in rec), "the worked case trips no tripwire"


@pytest.mark.req("FR-004-01")
@pytest.mark.oracle(
    "analytical", "k = 0 (annulus coefficient >= 0) gives C rho sqrt(g) D^(5/2); the result is elementwise over arrays"
)
def test_zero_annulus_and_arrays() -> None:
    q0 = beverloo(0.5, 0.02, 1600.0, 0.6, 0.0)
    assert q0 == pytest.approx(0.6 * 1600.0 * math.sqrt(G0) * 0.5**2.5, rel=1e-13)
    d = np.array([[0.2], [0.4]])
    rho = np.array([1400.0, 1600.0, 1800.0])
    q = beverloo(d, 0.02, rho, 0.58, 1.4)
    assert q.shape == (2, 3)
    assert q.dtype == np.float64
    ref = 0.58 * rho[None, :] * math.sqrt(G0) * (d - 1.4 * 0.02) ** 2.5
    np.testing.assert_allclose(q, ref, rtol=1e-13)
    assert np.all(np.diff(q, axis=0) > 0), "wider opening, more flow"


@pytest.mark.req("FR-004-02")
@pytest.mark.oracle(
    "hand-calculation", "spec 004 7.4: beverloo_discharge(0.03, 0.02, 1600, 0.56, 1.5) raises InputError (D = k d)"
)
def test_spec_closed_opening() -> None:
    with pytest.raises(minephys.InputError) as ei:
        beverloo(0.03, 0.02, 1600.0, 0.56, 1.5)
    assert ei.value.argument == "orifice_diameter"
    assert "orifice_diameter" in str(ei.value)


@pytest.mark.req("FR-004-02")
@pytest.mark.oracle(
    "analytical", "D <= k d is no free-flowing opening: InputError naming orifice_diameter, whichever side"
)
@pytest.mark.parametrize(
    ("orifice", "particle", "k"),
    [
        (0.02, 0.02, 1.5),  # D < k d
        (0.01, 0.02, 1.5),
        (0.03, 0.02, 1.5),  # D = k d (to rounding)
        (0.04, 0.02, 2.0),  # D = k d exactly
        (0.05, 0.05, 1.0),  # D = d, k = 1
        (0.0499999, 0.05, 1.0),
        (1e-3, 0.5, 3.0),
        (0.3, 0.2, 1.5),  # 1.5 * 0.2 rounds to 0.30000000000000004 >= 0.3
        (0.3, 0.3, 2.0),
    ],
)
def test_no_free_opening(orifice: float, particle: float, k: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        beverloo(orifice, particle, 1600.0, 0.56, k)
    assert ei.value.argument == "orifice_diameter"


@pytest.mark.req("FR-004-02")
@pytest.mark.oracle(
    "analytical", "the check is strict: just above k d is accepted and gives a small positive discharge"
)
@pytest.mark.parametrize("excess", [1e-9, 1e-6, 1e-3])
def test_just_open(excess: float) -> None:
    d, k = 0.02, 1.5
    q = float(beverloo(k * d * (1.0 + excess), d, 1600.0, 0.56, k))
    assert q > 0.0
    assert q == pytest.approx(0.56 * 1600.0 * math.sqrt(G0) * (k * d * excess) ** 2.5, rel=1e-5)


@pytest.mark.req("FR-004-02")
@pytest.mark.oracle(
    "analytical", "one closed opening inside an array raises, naming orifice_diameter (never NaN or a silent value)"
)
def test_closed_element_in_an_array() -> None:
    d = np.array([0.3, 0.02, 0.6])
    with pytest.raises(minephys.InputError) as ei:
        beverloo(d, 0.02, 1600.0, 0.56, 1.5)
    assert ei.value.argument == "orifice_diameter"
    with pytest.raises(minephys.InputError) as ei2:
        beverloo(
            0.3, np.array([0.01, 0.2]), 1600.0, 0.56, 1.5
        )  # the 0.2 m particle closes the 0.3 m orifice (1.5 * 0.2)
    assert ei2.value.argument == "orifice_diameter"
    with pytest.raises(minephys.InputError) as ei3:
        beverloo(0.3, 0.02, 1600.0, 0.56, np.array([1.0, 15.0]))  # k = 15: k d = 0.3
    assert ei3.value.argument == "orifice_diameter"

"""T-001-011 (FR-001-03): required tractive force.

Expected API: `H.required_force(mass, total_resistance, acceleration=0, effective_mass=None, drag_area=0,
air_density=None, speed=0, g=9.80665)` -> N (float64 / ndarray). Optional parameters are passed by keyword here.

    F = mass * g * total_resistance + m_eff * acceleration + 0.5 * air_density * drag_area * speed**2

with m_eff = mass when `effective_mass` is None. Oracles: the printed value 470,719.2 N of spec 001 section 7.4 and
hand calculations written out in the comments below (g = 9.80665 m/s^2 unless a case says g = 9.81). Tolerance TC-1.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import minephys
from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

G0 = 9.80665


@pytest.mark.req("FR-001-03")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: required_force(400000, 0.12) = 470,719.2 N")
def test_printed_value() -> None:
    got = H.required_force(400000, 0.12)
    assert type(got) is np.float64
    assert got == pytest.approx(470719.2, rel=1e-12)


@pytest.mark.req("FR-001-03")
@pytest.mark.oracle("hand-calculation", "400000 * 0.12 = 48000; 48000 * 9.81 = 470,880 N (the docs' 470.9 kN)")
def test_gravity_override() -> None:
    assert H.required_force(400000, 0.12, g=9.81) == pytest.approx(470880.0, rel=1e-12)


@pytest.mark.req("FR-001-03")
@pytest.mark.oracle("hand-calculation", "1000 * 9.80665 * 0.1 = 980.665; inertia 1000 * 0.5 = 500; total 1480.665 N")
def test_inertia_term_defaults_to_the_mass() -> None:
    assert H.required_force(1000.0, 0.1, acceleration=0.5) == pytest.approx(1480.665, rel=1e-12)


@pytest.mark.req("FR-001-03")
@pytest.mark.oracle("hand-calculation", "980.665 + 1100 * 0.5 = 1530.665 N (rotating-mass allowance)")
def test_effective_mass_replaces_the_mass_in_the_inertia_term_only() -> None:
    assert H.required_force(1000.0, 0.1, acceleration=0.5, effective_mass=1100.0) == pytest.approx(1530.665, rel=1e-12)
    assert H.required_force(1000.0, 0.1, effective_mass=1100.0) == pytest.approx(980.665, rel=1e-12)


@pytest.mark.req("FR-001-03")
@pytest.mark.oracle("hand-calculation", "0.5 * 1.2 * 45 * 10^2 = 2700 N of drag; 980.665 + 2700 = 3680.665 N")
def test_drag_term() -> None:
    got = H.required_force(1000.0, 0.1, drag_area=45.0, air_density=1.2, speed=10.0)
    assert got == pytest.approx(3680.665, rel=1e-12)


@pytest.mark.req("FR-001-03")
@pytest.mark.oracle(
    "hand-calculation", "all terms: 981 + 2200 * (-1.5) + 0.5 * 1.0 * 30 * 400 = 981 - 3300 + 6000 = 3681 N"
)
def test_all_terms_together() -> None:
    got = H.required_force(
        2000.0,
        0.05,
        acceleration=-1.5,
        effective_mass=2200.0,
        drag_area=30.0,
        air_density=1.0,
        speed=20.0,
        g=9.81,
    )
    assert got == pytest.approx(3681.0, rel=1e-12)


@pytest.mark.req("FR-001-03")
@pytest.mark.oracle(
    "hand-calculation", "a downhill resistance gives a negative force: 1000 * 9.80665 * (-0.05) = -490.3325 N"
)
def test_negative_resistance_and_deceleration_give_negative_force() -> None:
    assert H.required_force(1000.0, -0.05) == pytest.approx(-490.3325, rel=1e-12)
    assert H.required_force(1000.0, 0.0, acceleration=-2.0) == pytest.approx(-2000.0, rel=1e-12)
    assert H.required_force(1000.0, 0.0) == 0.0


@pytest.mark.req("FR-001-03")
@pytest.mark.oracle("hand-calculation", "without drag area the speed and the air density are irrelevant")
def test_no_drag_without_drag_area() -> None:
    base = H.required_force(1000.0, 0.1)
    assert H.required_force(1000.0, 0.1, speed=30.0) == base
    assert H.required_force(1000.0, 0.1, speed=30.0, air_density=1.2) == base


@pytest.mark.req("FR-001-03")
@pytest.mark.req("FR-001-22")
@pytest.mark.oracle("hand-calculation", "FR-001-22: the air density is required when the drag area is positive")
def test_air_density_is_required_with_a_drag_area() -> None:
    with pytest.raises(minephys.InputError) as ei:
        H.required_force(1000.0, 0.1, drag_area=10.0, speed=5.0)
    assert ei.value.argument == "air_density"
    with pytest.raises(minephys.InputError) as ei2:
        H.required_force(1000.0, 0.1, drag_area=10.0, air_density=None, speed=5.0)
    assert ei2.value.argument == "air_density"


@pytest.mark.req("FR-001-03")
@pytest.mark.oracle("hand-calculation", "broadcast: masses (column) with resistances (row)")
def test_broadcasting() -> None:
    m = np.array([[1000.0], [2000.0]])
    tr = np.array([0.0, 0.1, 0.2])
    out = H.required_force(m, tr)
    assert out.shape == (2, 3)
    np.testing.assert_allclose(out, m * G0 * tr, rtol=1e-12, atol=0.0)


@pytest.mark.req("FR-001-03")
@pytest.mark.oracle("analytical", "each term is linear in its own factor and the terms add (independent recomputation)")
@settings(deadline=None)
@given(
    m=st.floats(1e3, 7e5),
    tr=st.floats(-0.1, 0.3),
    a=st.floats(-3.0, 3.0),
    cda=st.floats(0.0, 100.0),
    rho=st.floats(0.1, 2.0),
    v=st.floats(0.0, 30.0),
    meff_ratio=st.floats(1.0, 1.2),
)
def test_decomposition_into_rolling_inertia_and_drag(
    m: float, tr: float, a: float, cda: float, rho: float, v: float, meff_ratio: float
) -> None:
    meff = m * meff_ratio
    expected = m * G0 * tr + meff * a + 0.5 * rho * cda * v * v
    got = H.required_force(m, tr, acceleration=a, effective_mass=meff, drag_area=cda, air_density=rho, speed=v)
    assert got == pytest.approx(expected, rel=1e-11, abs=1e-9 * (abs(m * G0 * tr) + abs(meff * a) + 1.0))
    # linearity in the mass for fixed acceleration, drag and speed excluded
    scaled = H.required_force(3.0 * m, tr, acceleration=a, effective_mass=3.0 * meff)
    plain = H.required_force(m, tr, acceleration=a, effective_mass=meff)
    assert scaled == pytest.approx(3.0 * plain, rel=1e-11, abs=1e-9)

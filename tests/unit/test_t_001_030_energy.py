"""T-001-030 (FR-001-11, FR-001-12): segment and cycle energy.

Expected API (SI, per spec 001 section 7.1; optional parameters by keyword):

    H.segment_energy(mass, length, rolling_resistance, grade, efficiency=1, regen_efficiency=0,
                     small_angle=False, g=9.80665)                                   -> J, elementwise
    H.cycle_energy(mass, length, rolling_resistance, grade, efficiency=1, regen_efficiency=0,
                   small_angle=False, g=9.80665)                                     -> J, a scalar (sum over segments)

With the wheel energy E_w = mass * g * total_resistance * length of a segment, the energy drawn from the source is
E_w / efficiency when E_w >= 0, and regen_efficiency * E_w (<= 0, energy returned) when E_w < 0. `cycle_energy` takes
1-D per-segment arrays (scalars broadcast) and sums `segment_energy`.

Oracles: the printed values of spec 001 section 7.4 (TC-2) and hand calculations with g = 9.80665 written below.
"""

from __future__ import annotations

import numpy as np
import pytest

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

G0 = 9.80665
# the cycle example of spec 001 section 7.4 (exact grade resistance), per segment
MASS = np.array([400000.0, 180000.0, 400000.0])
LENGTH = np.array([3000.0, 3000.0, 1000.0])
RR = np.array([0.02, 0.02, 0.03])
GRADE = np.array([0.10, -0.10, 0.0])


@pytest.mark.req("FR-001-11")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: 400000 * 9.80665 * 0.12 * 3000 = 1,412,157,600 J = 392.266 kWh")
def test_segment_energy_printed_value() -> None:
    got = H.segment_energy(400000, 3000, 0.02, 0.10, small_angle=True)
    assert type(got) is np.float64
    assert got == pytest.approx(1412157600.0, rel=1e-12)
    assert got == pytest.approx(1.4121576e9, abs=50.0)  # TC-2: 8 significant figures, half unit = 50 J
    assert got / 3.6e6 == pytest.approx(392.266, abs=5e-4)  # kWh


@pytest.mark.req("FR-001-11")
@pytest.mark.oracle("hand-calculation", "efficiency 0.35: 1,412,157,600 / 0.35 = 4,034,736,000 J")
def test_efficiency_divides_the_wheel_energy() -> None:
    got = H.segment_energy(400000, 3000, 0.02, 0.10, efficiency=0.35, small_angle=True)
    assert got == pytest.approx(4034736000.0, rel=1e-12)


@pytest.mark.req("FR-001-11")
@pytest.mark.oracle(
    "hand-calculation", "spec 001 7.4 wheel energies of the three-segment cycle (exact grade resistance)"
)
@pytest.mark.parametrize(
    ("i", "printed", "half_unit"),
    [(0, 1.40631738e9, 5.0), (1, -4.21019179e8, 0.5), (2, 1.17679800e8, 0.5)],
)
def test_wheel_energies_of_the_cycle_example(i: int, printed: float, half_unit: float) -> None:
    got = H.segment_energy(MASS[i], LENGTH[i], RR[i], GRADE[i], regen_efficiency=1.0)
    assert got == pytest.approx(printed, abs=half_unit)  # TC-2: half a unit of the 9th significant figure


@pytest.mark.req("FR-001-11")
@pytest.mark.oracle(
    "hand-calculation", "downhill: E_w = -421,019,178.9 J; regen 0.6 returns 60 %; no regeneration returns none"
)
def test_downhill_segment_returns_energy_only_with_regeneration() -> None:
    wheel = H.segment_energy(180000.0, 3000.0, 0.02, -0.10, regen_efficiency=1.0)
    assert wheel == pytest.approx(-421019178.9141307, rel=1e-9)
    assert H.segment_energy(180000.0, 3000.0, 0.02, -0.10, regen_efficiency=0.6) == pytest.approx(
        0.6 * wheel, rel=1e-12
    )
    assert H.segment_energy(180000.0, 3000.0, 0.02, -0.10) == 0.0
    # the drive efficiency does not touch the regenerated branch
    assert H.segment_energy(180000.0, 3000.0, 0.02, -0.10, efficiency=0.5, regen_efficiency=0.6) == pytest.approx(
        0.6 * wheel, rel=1e-12
    )


@pytest.mark.req("FR-001-11")
@pytest.mark.oracle(
    "hand-calculation", "E_w = 0 (level, no rolling resistance) costs nothing; E_w exactly 0 is on the drive branch"
)
def test_zero_wheel_energy() -> None:
    assert H.segment_energy(400000.0, 1000.0, 0.0, 0.0, efficiency=0.5, regen_efficiency=0.6) == 0.0


@pytest.mark.req("FR-001-11")
@pytest.mark.oracle("hand-calculation", "g override and zero length")
def test_gravity_override_and_zero_length() -> None:
    assert H.segment_energy(1000.0, 100.0, 0.1, 0.0, g=10.0) == pytest.approx(1000.0 * 10.0 * 0.1 * 100.0, rel=1e-12)
    assert H.segment_energy(1000.0, 0.0, 0.1, 0.1) == 0.0


@pytest.mark.req("FR-001-11")
@pytest.mark.oracle("hand-calculation", "elementwise over arrays, with the sign branch chosen per element")
def test_segment_energy_array() -> None:
    out = H.segment_energy(MASS, LENGTH, RR, GRADE, efficiency=0.35, regen_efficiency=0.6)
    assert out.shape == (3,)
    wheel = MASS * G0 * (RR + GRADE / np.hypot(1.0, GRADE)) * LENGTH
    expected = np.where(wheel >= 0, wheel / 0.35, 0.6 * wheel)
    np.testing.assert_allclose(out, expected, rtol=1e-12, atol=0.0)


@pytest.mark.req("FR-001-12")
@pytest.mark.oracle(
    "hand-calculation", "spec 001 7.4: cycle_energy at efficiency 0.35, no regeneration = 4.35427764e9 J"
)
def test_cycle_energy_diesel_printed_value() -> None:
    got = H.cycle_energy(MASS, LENGTH, RR, GRADE, efficiency=0.35)
    assert np.ndim(got) == 0
    assert type(got) is np.float64
    assert got == pytest.approx(4.35427764e9, abs=5.0)  # TC-2: 9 significant figures, half unit = 5 J
    assert got == pytest.approx((1406317375.364735 + 117679800.0) / 0.35, rel=1e-9)


@pytest.mark.req("FR-001-12")
@pytest.mark.oracle(
    "hand-calculation", "spec 001 7.4: at efficiency 0.85 with regeneration 0.6 the cycle needs 1.54032635e9 J"
)
def test_cycle_energy_with_regeneration() -> None:
    got = H.cycle_energy(MASS, LENGTH, RR, GRADE, efficiency=0.85, regen_efficiency=0.6)
    assert got == pytest.approx(1.54032635e9, abs=5.0)
    assert got / 3.6e6 == pytest.approx(427.868, abs=5e-4)  # kWh, printed 427.868


@pytest.mark.req("FR-001-12")
@pytest.mark.oracle("analytical", "the cycle energy is the sum of the segment energies")
def test_cycle_energy_is_the_sum_of_segment_energies() -> None:
    kw = {"efficiency": 0.8, "regen_efficiency": 0.5}
    segs = [H.segment_energy(MASS[i], LENGTH[i], RR[i], GRADE[i], **kw) for i in range(3)]
    assert H.cycle_energy(MASS, LENGTH, RR, GRADE, **kw) == pytest.approx(sum(segs), rel=1e-12)


@pytest.mark.req("FR-001-12")
@pytest.mark.oracle("hand-calculation", "scalars broadcast against the arrays: a constant mass and rolling resistance")
def test_scalars_broadcast_in_cycle_energy() -> None:
    length = np.array([1000.0, 2000.0])
    grade = np.array([0.05, -0.05])
    full = H.cycle_energy(np.array([100000.0, 100000.0]), length, np.array([0.03, 0.03]), grade, efficiency=0.9)
    broadcast = H.cycle_energy(100000.0, length, 0.03, grade, efficiency=0.9)
    assert broadcast == pytest.approx(full, rel=1e-14)


@pytest.mark.req("FR-001-12")
@pytest.mark.oracle(
    "hand-calculation", "one segment equals segment_energy; a downhill-only profile with regeneration is negative"
)
def test_single_segment_and_net_regeneration() -> None:
    one = H.cycle_energy(np.array([400000.0]), np.array([3000.0]), np.array([0.02]), np.array([0.10]), small_angle=True)
    assert one == pytest.approx(1412157600.0, rel=1e-12)
    net = H.cycle_energy(
        np.array([180000.0, 180000.0]),
        np.array([3000.0, 3000.0]),
        np.array([0.0, 0.0]),
        np.array([-0.10, -0.10]),
        regen_efficiency=0.5,
    )
    assert net < 0.0
    assert net == pytest.approx(2.0 * 0.5 * 180000.0 * G0 * (-0.0995037190209989) * 3000.0, rel=1e-12)

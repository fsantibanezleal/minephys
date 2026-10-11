"""T-001-030 (P-001-05, P-001-06, P-001-07): metamorphic properties of the energy functions.

P-001-05: splitting a segment in two consecutive segments of the same mass, grade and rolling resistance with
L1 + L2 = L leaves `cycle_energy` unchanged; permuting the segments leaves it unchanged. Tolerance: rtol 1e-12 relative
to the sum of |E|, 1-200 segments.
P-001-06: with zero rolling resistance, unit efficiency and full regeneration the cycle energy of a constant mass equals
mass * g * (the elevation change of the profile), and is 0 for a profile that returns to its start elevation
(|grade| <= 0.3, 2-200 segments). Tolerance: atol 1e-12 * sum of |E_w|.
P-001-07: energy is linear in the mass and in the length (k*m or k*L gives k*E), k in [1e-3, 1e3]; and
`co2_from_diesel(V)` equals 10.21 * V / 3.785411784e-3 (unit-change invariance m^3 <-> US gal).

Oracles: analytical (the elevation change of a segment is length * sin(arctan(grade)); g = 9.80665 m/s^2) and the exact
unit definition US gallon = 231 in^3 = 3.785411784e-3 m^3 with the verified EPA factor 10.21 kg CO2 / US gal.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

G0 = 9.80665
US_GALLON_M3 = 3.785411784e-3
CFG = settings(deadline=None)


@st.composite
def segments(draw, min_size=1, max_size=40):
    n = draw(st.integers(min_size, max_size))
    mass = draw(st.floats(2e4, 7e5))
    length = np.array(draw(st.lists(st.floats(10.0, 5000.0), min_size=n, max_size=n)))
    rr = np.array(draw(st.lists(st.floats(0.0, 0.1), min_size=n, max_size=n)))
    grade = np.array(draw(st.lists(st.floats(-0.3, 0.3), min_size=n, max_size=n)))
    return mass, length, rr, grade


def wheel_energies(mass, length, rr, grade):
    return mass * G0 * (rr + grade / np.hypot(1.0, grade)) * length


def energy(mass, length, rr, grade, **kw):
    return float(H.cycle_energy(mass, length, rr, grade, **kw))


@pytest.mark.req("P-001-05")
@pytest.mark.oracle("analytical", "additivity: splitting one segment into two consecutive ones changes nothing")
@CFG
@given(
    seg=segments(min_size=1),
    at=st.integers(0, 39),
    frac=st.floats(0.05, 0.95),
    eff=st.floats(0.3, 1.0),
    reg=st.floats(0.0, 1.0),
)
def test_splitting_a_segment_is_neutral(seg, at: int, frac: float, eff: float, reg: float) -> None:
    mass, length, rr, grade = seg
    i = at % len(length)
    kw = {"efficiency": eff, "regen_efficiency": reg}
    base = energy(mass, length, rr, grade, **kw)
    new_len = np.concatenate([length[:i], [frac * length[i], (1 - frac) * length[i]], length[i + 1 :]])
    new_rr = np.insert(rr, i, rr[i])
    new_grade = np.insert(grade, i, grade[i])
    split = energy(mass, new_len, new_rr, new_grade, **kw)
    scale = float(np.sum(np.abs(wheel_energies(mass, length, rr, grade)))) / min(eff, 1.0)
    assert split == pytest.approx(base, abs=1e-12 * scale, rel=0.0)


@pytest.mark.req("P-001-05")
@pytest.mark.oracle("analytical", "permutation invariance of the sum over segments")
@CFG
@given(seg=segments(min_size=2), seed=st.integers(0, 2**32 - 1), eff=st.floats(0.3, 1.0), reg=st.floats(0.0, 1.0))
def test_permuting_segments_is_neutral(seg, seed: int, eff: float, reg: float) -> None:
    mass, length, rr, grade = seg
    perm = np.random.default_rng(seed).permutation(len(length))
    kw = {"efficiency": eff, "regen_efficiency": reg}
    scale = float(np.sum(np.abs(wheel_energies(mass, length, rr, grade)))) / min(eff, 1.0)
    assert energy(mass, length[perm], rr[perm], grade[perm], **kw) == pytest.approx(
        energy(mass, length, rr, grade, **kw), abs=1e-12 * scale, rel=0.0
    )


@pytest.mark.req("P-001-06")
@pytest.mark.oracle("analytical", "no losses, full regeneration: the cycle energy is m g (elevation gained)")
@CFG
@given(seg=segments(min_size=2, max_size=60))
def test_lossless_energy_is_the_potential_energy_change(seg) -> None:
    mass, length, _, grade = seg
    zeros = np.zeros_like(length)
    rise = float(np.sum(length * grade / np.hypot(1.0, grade)))
    got = energy(mass, length, zeros, grade, efficiency=1.0, regen_efficiency=1.0)
    scale = float(np.sum(np.abs(wheel_energies(mass, length, zeros, grade))))
    assert got == pytest.approx(mass * G0 * rise, abs=1e-12 * scale, rel=0.0)


@pytest.mark.req("P-001-06")
@pytest.mark.oracle(
    "analytical", "a closed profile (returns to its start elevation) costs no net energy without losses"
)
@CFG
@given(seg=segments(min_size=1, max_size=60), last_len=st.floats(1500.0, 6000.0))
def test_closed_profile_has_zero_net_energy(seg, last_len: float) -> None:
    mass, length, _, grade = seg
    rise = float(np.sum(length * grade / np.hypot(1.0, grade)))
    last_len = max(last_len, abs(rise) / 0.25 + 1.0)  # long enough for |grade| <= 0.26
    sin_last = -rise / last_len  # the closing segment brings the elevation back to zero
    last_grade = sin_last / math.sqrt(1.0 - sin_last * sin_last)
    all_len = np.append(length, last_len)
    all_grade = np.append(grade, last_grade)
    zeros = np.zeros_like(all_len)
    got = energy(mass, all_len, zeros, all_grade, efficiency=1.0, regen_efficiency=1.0)
    scale = float(np.sum(np.abs(wheel_energies(mass, all_len, zeros, all_grade))))
    assert abs(got) <= 1e-12 * scale + 1e-9


@pytest.mark.req("P-001-07")
@pytest.mark.oracle("analytical", "energy is linear in the mass and in the length")
@CFG
@given(seg=segments(min_size=1, max_size=30), k=st.floats(1e-3, 1e3), eff=st.floats(0.3, 1.0), reg=st.floats(0.0, 1.0))
def test_energy_is_linear_in_mass_and_length(seg, k: float, eff: float, reg: float) -> None:
    mass, length, rr, grade = seg
    kw = {"efficiency": eff, "regen_efficiency": reg}
    base = energy(mass, length, rr, grade, **kw)
    assert energy(k * mass, length, rr, grade, **kw) == pytest.approx(k * base, rel=1e-11, abs=1e-9)
    assert energy(mass, k * length, rr, grade, **kw) == pytest.approx(k * base, rel=1e-11, abs=1e-9)
    one = float(H.segment_energy(mass, length[0], rr[0], grade[0], **kw))
    assert float(H.segment_energy(k * mass, length[0], rr[0], grade[0], **kw)) == pytest.approx(
        k * one, rel=1e-12, abs=1e-9
    )


@pytest.mark.req("P-001-07")
@pytest.mark.req("FR-001-14")
@pytest.mark.oracle("analytical", "co2_from_diesel(V) = 10.21 * V / 3.785411784e-3: the same in m^3 and in US gallons")
@CFG
@given(gallons=st.floats(1e-3, 1e5), k=st.floats(1e-3, 1e3))
def test_diesel_co2_unit_change_invariance(gallons: float, k: float) -> None:
    v_m3 = gallons * US_GALLON_M3
    assert float(H.co2_from_diesel(v_m3)) == pytest.approx(10.21 * gallons, rel=1e-12)
    assert float(H.co2_from_diesel(v_m3)) == pytest.approx(10.21 * v_m3 / US_GALLON_M3, rel=1e-12)
    assert float(H.co2_from_diesel(k * v_m3)) == pytest.approx(k * float(H.co2_from_diesel(v_m3)), rel=1e-12)

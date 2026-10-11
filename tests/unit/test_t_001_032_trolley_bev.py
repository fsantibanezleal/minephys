"""T-001-032 (FR-001-16, FR-001-17, FR-001-25): trolley-assist and battery-electric cycle energy, segment-array guards.

Expected API (optional parameters by keyword):
    H.trolley_cycle_energy(mass, length, rolling_resistance, grade, on_trolley, diesel_efficiency, electric_efficiency,
                           small_angle=False, g=9.80665)       -> (diesel_energy, electric_energy), J, a pair
        segments with wheel energy E_w > 0 draw E_w / electric_efficiency from the line where `on_trolley` is true and
        E_w / diesel_efficiency from the tank otherwise; segments with E_w <= 0 draw nothing (no regeneration into the
        line, spec 001 section 7.6).
    H.bev_cycle_energy(mass, length, rolling_resistance, grade, drive_efficiency, regen_efficiency,
                       small_angle=False, g=9.80665)           -> net battery energy in J,
        equal to `cycle_energy(..., efficiency=drive_efficiency, regen_efficiency=regen_efficiency)`.

FR-001-25 (the three cycle functions): per-segment arrays must be 1-D, of equal length after broadcasting scalars,
non-empty and at most 100,000 long, else `InputError` naming the argument; a non-boolean `on_trolley` raises
`InputTypeError` naming `on_trolley`.

Oracles: the printed values of spec 001 section 7.4 (TC-2) for the three-segment cycle (exact grade resistance), and
hand calculations.
"""

from __future__ import annotations

import numpy as np
import pytest

import minephys
from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

MASS = np.array([400000.0, 180000.0, 400000.0])
LENGTH = np.array([3000.0, 3000.0, 1000.0])
RR = np.array([0.02, 0.02, 0.03])
GRADE = np.array([0.10, -0.10, 0.0])
ON_TROLLEY = np.array([True, False, False])
G0 = 9.80665


def wheel() -> np.ndarray:
    return MASS * G0 * (RR + GRADE / np.hypot(1.0, GRADE)) * LENGTH


@pytest.mark.req("FR-001-16")
@pytest.mark.oracle(
    "hand-calculation", "spec 001 7.4: trolley cycle = (3.36228000e8 J diesel, 1.56257486e9 J electric)"
)
def test_trolley_printed_values() -> None:
    diesel, electric = H.trolley_cycle_energy(
        MASS, LENGTH, RR, GRADE, ON_TROLLEY, diesel_efficiency=0.35, electric_efficiency=0.9
    )
    assert type(diesel) is np.float64
    assert type(electric) is np.float64
    assert diesel == pytest.approx(3.36228000e8, abs=0.5)  # TC-2: 9 significant figures
    assert electric == pytest.approx(1.56257486e9, abs=5.0)
    w = wheel()
    assert diesel == pytest.approx(w[2] / 0.35, rel=1e-12)
    assert electric == pytest.approx(w[0] / 0.9, rel=1e-12)


@pytest.mark.req("FR-001-16")
@pytest.mark.oracle("hand-calculation", "the downhill segment (E_w < 0) draws nothing, on the line or off it")
def test_downhill_draws_nothing_from_either_source() -> None:
    for flag in (True, False):
        d, e = H.trolley_cycle_energy(
            np.array([180000.0]),
            np.array([3000.0]),
            np.array([0.02]),
            np.array([-0.10]),
            np.array([flag]),
            diesel_efficiency=0.35,
            electric_efficiency=0.9,
        )
        assert d == 0.0
        assert e == 0.0


@pytest.mark.req("FR-001-16")
@pytest.mark.oracle("hand-calculation", "all segments on the line: only electricity; none on the line: only diesel")
def test_all_on_or_all_off_the_trolley() -> None:
    w = wheel()
    positive = float(np.sum(np.where(w > 0, w, 0.0)))
    d_on, e_on = H.trolley_cycle_energy(MASS, LENGTH, RR, GRADE, np.array([True] * 3), 0.35, 0.9)
    assert d_on == 0.0
    assert e_on == pytest.approx(positive / 0.9, rel=1e-12)
    d_off, e_off = H.trolley_cycle_energy(MASS, LENGTH, RR, GRADE, np.array([False] * 3), 0.35, 0.9)
    assert e_off == 0.0
    assert d_off == pytest.approx(positive / 0.35, rel=1e-12)


@pytest.mark.req("FR-001-16")
@pytest.mark.oracle("analytical", "conservation: with unit efficiencies diesel + electric = the positive wheel energy")
def test_unit_efficiencies_conserve_the_positive_wheel_energy() -> None:
    w = wheel()
    d, e = H.trolley_cycle_energy(MASS, LENGTH, RR, GRADE, ON_TROLLEY, 1.0, 1.0)
    assert d + e == pytest.approx(float(np.sum(np.where(w > 0, w, 0.0))), rel=1e-12)
    # and it equals the lossless cycle energy without regeneration
    assert d + e == pytest.approx(float(H.cycle_energy(MASS, LENGTH, RR, GRADE)), rel=1e-12)


@pytest.mark.req("FR-001-16")
@pytest.mark.oracle(
    "hand-calculation", "small_angle and g are honoured: 100 t, 1000 m, RR 0.03, grade 0.05 small angle, g = 10"
)
def test_small_angle_and_gravity() -> None:
    d, e = H.trolley_cycle_energy(
        np.array([100000.0]),
        np.array([1000.0]),
        np.array([0.03]),
        np.array([0.05]),
        np.array([False]),
        0.5,
        0.9,
        small_angle=True,
        g=10.0,
    )
    assert d == pytest.approx(100000.0 * 10.0 * 0.08 * 1000.0 / 0.5, rel=1e-12)  # 1.6e8 J
    assert e == 0.0


@pytest.mark.req("FR-001-17")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: bev_cycle_energy(0.85, 0.6) = 1.54032635e9 J (427.868 kWh)")
def test_bev_printed_value() -> None:
    got = H.bev_cycle_energy(MASS, LENGTH, RR, GRADE, drive_efficiency=0.85, regen_efficiency=0.6)
    assert type(got) is np.float64
    assert got == pytest.approx(1.54032635e9, abs=5.0)
    assert got / 3.6e6 == pytest.approx(427.868, abs=5e-4)
    w = wheel()
    expected = float(np.sum(np.where(w >= 0, w / 0.85, 0.6 * w)))
    assert got == pytest.approx(expected, rel=1e-12)


@pytest.mark.req("FR-001-17")
@pytest.mark.oracle("analytical", "FR-001-17: bev_cycle_energy equals cycle_energy with efficiency = drive_efficiency")
@pytest.mark.parametrize(("drive", "regen"), [(0.85, 0.6), (1.0, 1.0), (0.5, 0.0), (0.9, 0.3)])
def test_bev_equals_cycle_energy(drive: float, regen: float) -> None:
    bev = H.bev_cycle_energy(MASS, LENGTH, RR, GRADE, drive, regen)
    cyc = H.cycle_energy(MASS, LENGTH, RR, GRADE, efficiency=drive, regen_efficiency=regen)
    assert bev == pytest.approx(float(cyc), rel=1e-14)


@pytest.mark.req("FR-001-17")
@pytest.mark.oracle("analytical", "regeneration can only lower the net battery energy")
def test_regeneration_lowers_the_net_energy() -> None:
    none = H.bev_cycle_energy(MASS, LENGTH, RR, GRADE, 0.85, 0.0)
    some = H.bev_cycle_energy(MASS, LENGTH, RR, GRADE, 0.85, 0.5)
    full = H.bev_cycle_energy(MASS, LENGTH, RR, GRADE, 0.85, 1.0)
    assert full < some < none


# ---------------------------------------------------------------- FR-001-25: segment-array guards


def trolley(**over):
    kw = {
        "mass": MASS,
        "length": LENGTH,
        "rolling_resistance": RR,
        "grade": GRADE,
        "on_trolley": ON_TROLLEY,
        "diesel_efficiency": 0.35,
        "electric_efficiency": 0.9,
    }
    kw.update(over)
    return H.trolley_cycle_energy(**kw)


def cycle(**over):
    kw = {"mass": MASS, "length": LENGTH, "rolling_resistance": RR, "grade": GRADE}
    kw.update(over)
    return H.cycle_energy(**kw)


def bev(**over):
    kw = {
        "mass": MASS,
        "length": LENGTH,
        "rolling_resistance": RR,
        "grade": GRADE,
        "drive_efficiency": 0.85,
        "regen_efficiency": 0.6,
    }
    kw.update(over)
    return H.bev_cycle_energy(**kw)


FUNCTIONS = {"cycle_energy": cycle, "trolley_cycle_energy": trolley, "bev_cycle_energy": bev}
ARRAY_ARGS = ["mass", "length", "rolling_resistance", "grade"]


@pytest.mark.req("FR-001-25")
@pytest.mark.oracle("hand-calculation", "a 2-D per-segment array is rejected, naming the argument")
@pytest.mark.parametrize("name", sorted(FUNCTIONS))
@pytest.mark.parametrize("arg", ARRAY_ARGS)
def test_two_dimensional_arrays_are_rejected(name: str, arg: str) -> None:
    base = {"mass": MASS, "length": LENGTH, "rolling_resistance": RR, "grade": GRADE}[arg]
    with pytest.raises(minephys.InputError) as ei:
        FUNCTIONS[name](**{arg: np.stack([base, base])})
    assert ei.value.argument == arg


@pytest.mark.req("FR-001-25")
@pytest.mark.oracle("hand-calculation", "lengths 3 and 4 do not match after broadcasting scalars")
@pytest.mark.parametrize("name", sorted(FUNCTIONS))
def test_mismatched_lengths_are_rejected(name: str) -> None:
    with pytest.raises(minephys.InputError) as ei:
        FUNCTIONS[name](length=np.array([1000.0, 2000.0, 3000.0, 4000.0]))
    msg = str(ei.value)
    assert "length" in msg
    assert ei.value.argument in {"mass", "length", "rolling_resistance", "grade", "on_trolley"} or "length" in msg


@pytest.mark.req("FR-001-25")
@pytest.mark.oracle("hand-calculation", "an empty profile has no segments")
@pytest.mark.parametrize("name", sorted(FUNCTIONS))
def test_empty_arrays_are_rejected(name: str) -> None:
    empty = np.empty(0)
    kw = {"mass": empty, "length": empty, "rolling_resistance": empty, "grade": empty}
    if name == "trolley_cycle_energy":
        kw["on_trolley"] = np.empty(0, dtype=bool)
    with pytest.raises(minephys.InputError) as ei:
        FUNCTIONS[name](**kw)
    assert ei.value.argument in set(ARRAY_ARGS) | {"on_trolley"}


@pytest.mark.req("FR-001-25")
@pytest.mark.oracle("hand-calculation", "100,000 segments are allowed, 100,001 are not")
@pytest.mark.parametrize("name", sorted(FUNCTIONS))
def test_segment_cap(name: str) -> None:
    def make(n: int) -> dict:
        kw = {
            "mass": np.full(n, 1e5),
            "length": np.full(n, 10.0),
            "rolling_resistance": np.full(n, 0.03),
            "grade": np.full(n, 0.02),
        }
        if name == "trolley_cycle_energy":
            kw["on_trolley"] = np.zeros(n, dtype=bool)
        return kw

    result = FUNCTIONS[name](**make(100_000))
    assert np.all(np.isfinite(result))
    with pytest.raises(minephys.InputError) as ei:
        FUNCTIONS[name](**make(100_001))
    assert ei.value.argument in set(ARRAY_ARGS) | {"on_trolley"}
    assert "100001" in str(ei.value).replace(",", "").replace("_", "")


@pytest.mark.req("FR-001-25")
@pytest.mark.oracle("hand-calculation", "on_trolley must be boolean: integers, floats and strings are type errors")
@pytest.mark.parametrize(
    "bad",
    [np.array([1, 0, 1]), np.array([1.0, 0.0, 1.0]), np.array(["a", "b", "c"]), [1, 0, 1], 1, "yes", None],
    ids=repr,
)
def test_on_trolley_must_be_boolean(bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        trolley(on_trolley=bad)
    assert ei.value.argument == "on_trolley"


@pytest.mark.req("FR-001-25")
@pytest.mark.oracle("hand-calculation", "on_trolley of the wrong length is a size error naming it")
def test_on_trolley_length_mismatch() -> None:
    with pytest.raises(minephys.InputError) as ei:
        trolley(on_trolley=np.array([True, False]))
    assert "on_trolley" in str(ei.value)


@pytest.mark.req("FR-001-25")
@pytest.mark.oracle("hand-calculation", "scalars broadcast against the arrays without error")
def test_scalars_broadcast() -> None:
    d, e = trolley(mass=400000.0, rolling_resistance=0.02)
    assert np.isfinite(d)
    assert np.isfinite(e)
    assert np.isfinite(cycle(mass=400000.0, rolling_resistance=0.02))
    assert np.isfinite(bev(mass=400000.0, rolling_resistance=0.02))

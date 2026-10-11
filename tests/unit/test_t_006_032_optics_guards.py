"""T-006-032 (FR-006-18): optics and lidar guards.

Public API under test (`minephys.environment`): `mass_extinction_coefficient(diameter, particle_density,
extinction_efficiency=None)`, `extinction_coefficient(mass_concentration, mass_extinction)`,
`beer_lambert_transmittance(extinction, path_length)`, `path_transmittance(positions, extinction_profile)`,
`lidar_dust_return(distance, extinction, positions=None, target="retroreflective", onset_transmittance=None,
min_transmittance=None)` (signatures as in tests/unit/test_t_006_030_beer_lambert.py and test_t_006_031_lidar_dust.py).
Expected: `minephys.InputError` naming the argument for NaN or +-inf, a negative extinction, concentration or length, a
non-positive distance, diameter, density or extinction efficiency, positions that are not strictly increasing, not starting at 0
or not ending at `distance`, a profile of a different length, more than 10^6 profile points, an unknown `target`, thresholds
outside (0, 1) or with a minimum >= the onset; `minephys.InputTypeError` for non-numeric arguments.

Oracle: the hostile classes written in FR-006-18.
"""

from __future__ import annotations

import datetime as dt
import importlib
from typing import Any

import numpy as np
import pytest

NAN, INF = float("nan"), float("inf")


def _e():
    return importlib.import_module("minephys.environment")


def _errors():
    importlib.import_module("minephys.environment")
    import minephys

    return minephys.InputError, minephys.InputTypeError


POS = [0.0, -1.0, NAN, INF, -INF]
NONNEG = [-1e-9, -1.0, NAN, INF, -INF]
POSITIONS = np.array([0.0, 10.0, 25.0, 50.0])
PROFILE = np.array([0.0, 0.01, 0.02, 0.01])

CASES: dict[str, tuple[dict[str, Any], dict[str, list[Any]]]] = {
    "mass_extinction_coefficient": (
        {"diameter": 10e-6, "particle_density": 2650.0, "extinction_efficiency": 2.0},
        {"diameter": POS, "particle_density": POS, "extinction_efficiency": POS},
    ),
    "extinction_coefficient": (
        {"mass_concentration": 1e-6, "mass_extinction": 113.2},
        {"mass_concentration": NONNEG, "mass_extinction": NONNEG},
    ),
    "beer_lambert_transmittance": (
        {"extinction": 1e-3, "path_length": 50.0},
        {"extinction": NONNEG, "path_length": NONNEG},
    ),
    "lidar_dust_return": (
        {"distance": 100.0, "extinction": 0.002},
        {
            "distance": POS,
            "extinction": NONNEG,
            "onset_transmittance": [0.0, 1.0, -0.1, 1.5, NAN, INF],
            "min_transmittance": [0.0, 1.0, -0.1, 1.5, NAN, INF],
        },
    ),
}
OPTIONAL = {("mass_extinction_coefficient", "extinction_efficiency"), ("lidar_dust_return", "onset_transmittance"), ("lidar_dust_return", "min_transmittance")}
NON_NUMERIC: list[Any] = ["abc", "１.０", None, 1 + 2j, True, b"1", object(), dt.datetime(2020, 1, 1), np.array(["a"])]


def _call(fn: str, kwargs: dict[str, Any]) -> Any:
    return getattr(_e(), fn)(**kwargs)


def _bad() -> list[Any]:
    return [
        pytest.param(fn, arg, v, id=f"{fn}-{arg}-{v!r}") for fn, (_, bads) in CASES.items() for arg, vals in bads.items() for v in vals
    ]


def _non_numeric() -> list[Any]:
    return [
        pytest.param(fn, arg, v, id=f"{fn}-{arg}-{type(v).__name__}")
        for fn, (base, _) in CASES.items()
        for arg in base
        for v in NON_NUMERIC
        if not (v is None and (fn, arg) in OPTIONAL)
    ]


@pytest.mark.req("FR-006-18")
def test_fr_006_18_reference_calls_are_valid() -> None:
    for fn, (base, _) in CASES.items():
        assert _call(fn, base) is not None
    e = _e()
    assert e.path_transmittance(POSITIONS, PROFILE) > 0.0
    assert e.lidar_dust_return(50.0, PROFILE, positions=POSITIONS) is not None


@pytest.mark.req("FR-006-18")
@pytest.mark.oracle("hand-calculation", "FR-006-18 hostile classes")
@pytest.mark.parametrize(("fn", "arg", "bad"), _bad())
def test_fr_006_18_hostile_values(fn: str, arg: str, bad: Any) -> None:
    _e()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _call(fn, {**CASES[fn][0], arg: bad})
    assert exc.value.argument == arg


@pytest.mark.req("FR-006-18")
@pytest.mark.parametrize(("fn", "arg", "bad"), _non_numeric())
def test_fr_006_18_non_numeric_arguments(fn: str, arg: str, bad: Any) -> None:
    _e()
    _, input_type_error = _errors()
    with pytest.raises(input_type_error) as exc:
        _call(fn, {**CASES[fn][0], arg: bad})
    assert exc.value.argument == arg


@pytest.mark.req("FR-006-18")
@pytest.mark.parametrize("target", ["Retroreflective", "retro", "", "low reflectivity", "LOW_REFLECTIVITY", "mirror", " retroreflective"])
def test_fr_006_18_unknown_target(target: str) -> None:
    _e()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _call("lidar_dust_return", {**CASES["lidar_dust_return"][0], "target": target})
    assert exc.value.argument == "target"
    assert "retroreflective" in str(exc.value)  # the allowed values are listed (FR-000-15)


@pytest.mark.req("FR-006-18")
def test_fr_006_18_thresholds_must_leave_room_between_minimum_and_onset() -> None:
    _e()
    input_error, _ = _errors()
    for onset, minimum in ((0.5, 0.5), (0.5, 0.6), (0.1, 0.9)):
        with pytest.raises(input_error) as exc:
            _call("lidar_dust_return", {**CASES["lidar_dust_return"][0], "onset_transmittance": onset, "min_transmittance": minimum})
        assert exc.value.argument in {"onset_transmittance", "min_transmittance"}
    # a valid pair, and a single override that stays consistent with the other default
    assert _call("lidar_dust_return", {**CASES["lidar_dust_return"][0], "onset_transmittance": 0.9, "min_transmittance": 0.1}) is not None
    assert _call("lidar_dust_return", {**CASES["lidar_dust_return"][0], "onset_transmittance": 0.5}) is not None
    with pytest.raises(input_error):  # an onset below the default minimum (0.02)
        _call("lidar_dust_return", {**CASES["lidar_dust_return"][0], "onset_transmittance": 0.01})


@pytest.mark.req("FR-006-18")
def test_fr_006_18_positions_must_run_from_zero_to_distance_strictly_increasing() -> None:
    e = _e()
    input_error, _ = _errors()
    beta = np.array([0.0, 0.01, 0.02, 0.01])
    for positions, arg in (
        (np.array([0.0, 10.0, 10.0, 50.0]), "positions"),  # tie
        (np.array([0.0, 30.0, 20.0, 50.0]), "positions"),  # decreasing step
        (np.array([1.0, 10.0, 25.0, 50.0]), "positions"),  # does not start at 0
        (np.array([0.0, 10.0, 25.0, 49.0]), "positions"),  # does not end at the distance
        (np.array([0.0, 10.0, 25.0, 51.0]), "positions"),
        (np.array([0.0, NAN, 25.0, 50.0]), "positions"),
        (np.array([0.0, 10.0, 25.0, INF]), "positions"),
        (np.array([-5.0, 10.0, 25.0, 50.0]), "positions"),
    ):
        with pytest.raises(input_error) as exc:
            e.lidar_dust_return(50.0, beta, positions=positions)
        assert exc.value.argument == arg


@pytest.mark.req("FR-006-18")
def test_fr_006_18_profile_length_and_values() -> None:
    e = _e()
    input_error, _ = _errors()
    for beta in (np.array([0.0, 0.01, 0.02]), np.array([0.0, 0.01, 0.02, 0.01, 0.0]), np.array([[0.0, 0.01], [0.02, 0.01]])):
        with pytest.raises(input_error) as exc:
            e.lidar_dust_return(50.0, beta, positions=POSITIONS)
        assert exc.value.argument in {"extinction", "positions"}
    for bad in (-1e-9, NAN, INF):
        beta = PROFILE.copy()
        beta[2] = bad
        with pytest.raises(input_error) as exc:
            e.lidar_dust_return(50.0, beta, positions=POSITIONS)
        assert exc.value.argument == "extinction"
        with pytest.raises(input_error) as exc:
            e.path_transmittance(POSITIONS, beta)
        assert exc.value.argument == "extinction_profile"


@pytest.mark.req("FR-006-18")
def test_fr_006_18_path_transmittance_positions_and_lengths() -> None:
    e = _e()
    input_error, _ = _errors()
    for positions in (np.array([0.0, 10.0, 10.0, 50.0]), np.array([0.0, 30.0, 20.0, 50.0]), np.array([0.0, NAN, 25.0, 50.0])):
        with pytest.raises(input_error) as exc:
            e.path_transmittance(positions, PROFILE)
        assert exc.value.argument == "positions"
    with pytest.raises(input_error) as exc:
        e.path_transmittance(POSITIONS, PROFILE[:3])
    assert exc.value.argument in {"positions", "extinction_profile"}
    with pytest.raises(input_error):
        e.path_transmittance(np.array([5.0]), np.array([0.01]))  # a path needs at least two points


@pytest.mark.req("FR-006-18")
def test_fr_006_18_the_profile_size_cap_is_one_million_points() -> None:
    e = _e()
    input_error, _ = _errors()
    n = 1_000_000
    ok_positions = np.linspace(0.0, 100.0, n)
    assert 0.0 < e.path_transmittance(ok_positions, np.full(n, 1e-4)) < 1.0  # the cap itself is accepted
    too_many = np.linspace(0.0, 100.0, n + 1)
    with pytest.raises(input_error) as exc:
        e.path_transmittance(too_many, np.full(n + 1, 1e-4))
    assert exc.value.argument in {"positions", "extinction_profile"}
    with pytest.raises(input_error) as exc:
        e.lidar_dust_return(100.0, np.full(n + 1, 1e-4), positions=too_many)
    assert exc.value.argument in {"positions", "extinction"}

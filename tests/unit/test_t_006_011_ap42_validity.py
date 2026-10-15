"""T-006-011 (FR-006-02, FR-006-03): validity flags, `ValidityWarning` and strict mode at the Table 13.2.2-3 bounds.

Expected public API (`minephys.environment`):
    ap42_unpaved_validity(silt_fraction, mean_weight, mean_speed=None, mean_wheels=None, moisture_fraction=None)
        -> named tuple of boolean arrays, one field per argument that was given (field names = the argument names) plus `all`;
        True where the value lies inside the AP-42 Table 13.2.2-3 industrial-road range, bounds inclusive: silt 1.8-25.2 %
        (fractions 0.018-0.252), weight 2-290 short tons (1,814.36948-263,083.5746 kg), speed 5-43 mph (2.2352-19.22272 m/s),
        wheels 4-17, moisture 0.03-13 % (fractions 0.0003-0.13).
    ap42_unpaved_emission_factor(..., strict=False): outside a range it emits `minephys.ValidityWarning` (attributes `argument`,
        `bounds`, `row` = `ap42_range_{silt,weight,speed,wheels,moisture}`) and returns the extrapolated value; with `strict=True`
        it raises `minephys.InputError` naming every failed argument.

Oracle: the Table 13.2.2-3 bounds (`epa2006ap42s1322`, p. 13.2.2-5, transcribed in spec 006 section 7) converted with the exact
unit definitions 1 short ton = 907.18474 kg and 1 mph = 0.44704 m/s; the exact-bound cases use a relative nudge of 1e-12 so
that the result does not depend on how the implementation orders its unit conversion.
"""

from __future__ import annotations

import importlib
import math
import warnings

import numpy as np
import pytest

ST = 907.18474
MPH = 0.44704
BOUNDS = {
    # argument: (lo, hi, row id, a value comfortably inside)
    "silt_fraction": (0.018, 0.252, "ap42_range_silt", 0.10),
    "mean_weight": (2.0 * ST, 290.0 * ST, "ap42_range_weight", 100.0 * ST),
    "mean_speed": (5.0 * MPH, 43.0 * MPH, "ap42_range_speed", 20.0 * MPH),
    "mean_wheels": (4.0, 17.0, "ap42_range_wheels", 6.0),
    "moisture_fraction": (0.0003, 0.13, "ap42_range_moisture", 0.02),
}
INSIDE = {k: v[3] for k, v in BOUNDS.items()}


def _e():
    return importlib.import_module("minephys.environment")


def _validity_warning():
    importlib.import_module("minephys.environment")
    import minephys

    return minephys.ValidityWarning


def _errors():
    importlib.import_module("minephys.environment")
    import minephys

    return minephys.InputError


def _flags(**kw):
    return _e().ap42_unpaved_validity(**{**INSIDE, **kw})


@pytest.mark.req("FR-006-02")
@pytest.mark.oracle("hand-calculation", "Table 13.2.2-3 bounds, inclusive, converted to SI")
@pytest.mark.knowledge("ap42_range_silt")
@pytest.mark.knowledge("ap42_range_weight")
@pytest.mark.knowledge("ap42_range_speed")
@pytest.mark.knowledge("ap42_range_wheels")
@pytest.mark.knowledge("ap42_range_moisture")
@pytest.mark.parametrize("arg", list(BOUNDS))
def test_fr_006_02_flags_at_just_inside_and_just_outside_each_bound(arg: str) -> None:
    lo, hi, _, mid = BOUNDS[arg]
    if arg == "mean_wheels":  # integer bounds are exact: the bound itself is inside
        values = np.array([3.0, 3.999999, 4.0, 10.0, 17.0, 17.000001, 18.0])
    else:
        values = np.array(
            [lo * (1 - 1e-6), lo * (1 - 1e-12), lo * (1 + 1e-12), mid, hi * (1 - 1e-12), hi * (1 + 1e-12), hi * (1 + 1e-6)]
        )
    expected = np.array([False, False, True, True, True, False, False])
    required = {"silt_fraction": 0.10, "mean_weight": 100.0 * ST}
    call = {**required, arg: values}  # the argument under test replaces its inside value (optional ones are added)
    flags = getattr(_e().ap42_unpaved_validity(**call), arg)
    assert np.asarray(flags).dtype == np.bool_
    np.testing.assert_array_equal(np.asarray(flags), expected)

@pytest.mark.req("FR-006-02")
def test_fr_006_02_all_is_the_conjunction_and_fields_follow_the_given_arguments() -> None:
    e = _e()
    res = e.ap42_unpaved_validity(
        silt_fraction=np.array([0.10, 0.30, 0.10]),
        mean_weight=np.array([50_000.0, 50_000.0, 400_000.0]),
    )
    assert np.array_equal(res.silt_fraction, [True, False, True])
    assert np.array_equal(res.mean_weight, [True, True, False])
    assert np.array_equal(res.all, [True, False, False])
    assert "all" in res._fields and "silt_fraction" in res._fields and "mean_weight" in res._fields
    full = e.ap42_unpaved_validity(0.10, 50_000.0, mean_speed=10.0, mean_wheels=6, moisture_fraction=0.01)
    for name in ("silt_fraction", "mean_weight", "mean_speed", "mean_wheels", "moisture_fraction", "all"):
        assert bool(getattr(full, name)) is True
    bad_speed = e.ap42_unpaved_validity(0.10, 50_000.0, mean_speed=25.0)
    assert bool(bad_speed.mean_speed) is False and bool(bad_speed.all) is False
    assert bool(bad_speed.silt_fraction) is True  # the other flags are unaffected


@pytest.mark.req("FR-006-02")
def test_fr_006_02_broadcast_shapes_and_scalars() -> None:
    e = _e()
    res = e.ap42_unpaved_validity(np.array([[0.05], [0.4]]), np.array([5_000.0, 500_000.0, 100_000.0]))
    assert np.asarray(res.all).shape == (2, 3)
    assert np.array_equal(np.asarray(res.all), [[True, False, True], [False, False, False]])
    assert np.asarray(e.ap42_unpaved_validity(0.1, 1e5).all).dtype == np.bool_


@pytest.mark.req("FR-006-03")
@pytest.mark.oracle("hand-calculation", "320 short tons (290,299.12 kg) exceeds the 290 short-ton bound")
@pytest.mark.knowledge("ap42_range_weight")
def test_fr_006_03_heavy_trucks_warn_and_return_the_extrapolated_value() -> None:
    e = _e()
    warning = _validity_warning()
    weight = 320.0 * ST
    with pytest.warns(warning) as rec:
        got = e.ap42_unpaved_emission_factor(0.10, weight, "PM10")
    expected = 1.5 * (10.0 / 12.0) ** 0.9 * (320.0 / 3.0) ** 0.45 * 0.45359237 / 1609.344
    np.testing.assert_allclose(got, expected, rtol=1e-12, atol=0)
    msg = next(r.message for r in rec if isinstance(r.message, warning))
    assert msg.argument == "mean_weight" and msg.row == "ap42_range_weight"
    assert any(math.isclose(b, 290.0 * ST, rel_tol=1e-9) or math.isclose(b, 290.0, rel_tol=1e-9) for b in msg.bounds)
    text = str(msg)
    assert "mean_weight" in text and "ap42_range_weight" in text


@pytest.mark.req("FR-006-03")
@pytest.mark.parametrize(
    ("arg", "bad"),
    [
        ("silt_fraction", 0.30),
        ("silt_fraction", 0.01),
        ("mean_weight", 1000.0),
        ("mean_weight", 320.0 * ST),
        ("mean_speed", 25.0),
        ("mean_speed", 1.0),
        ("mean_wheels", 20),
        ("mean_wheels", 2),
        ("moisture_fraction", 0.2),
        ("moisture_fraction", 0.0001),
    ],
)
def test_fr_006_03_each_argument_warns_with_its_own_row(arg: str, bad: float) -> None:
    e = _e()
    warning = _validity_warning()
    kw = {k: v for k, v in INSIDE.items() if k in ("mean_speed", "mean_wheels", "moisture_fraction")}
    kw.update(silt_fraction=INSIDE["silt_fraction"], mean_weight=INSIDE["mean_weight"])
    kw[arg] = bad
    with pytest.warns(warning) as rec:
        e.ap42_unpaved_emission_factor(kw.pop("silt_fraction"), kw.pop("mean_weight"), "PM10", **kw)
    hits = [r.message for r in rec if isinstance(r.message, warning)]
    assert any(h.argument == arg and h.row == BOUNDS[arg][2] for h in hits), [(h.argument, h.row) for h in hits]


@pytest.mark.req("FR-006-03")
def test_fr_006_03_no_warning_inside_the_ranges() -> None:
    e = _e()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        e.ap42_unpaved_emission_factor(0.10, 100.0 * ST, "PM10", mean_speed=10.0, mean_wheels=6, moisture_fraction=0.02)
        e.ap42_unpaved_emission_factor(0.10, 100.0 * ST, "PM30", strict=True)


@pytest.mark.req("FR-006-03")
@pytest.mark.oracle("hand-calculation", "strict=True turns the warning into InputError naming each failed argument")
def test_fr_006_03_strict_mode_raises_and_names_every_failed_argument() -> None:
    e = _e()
    input_error = _errors()
    with pytest.raises(input_error) as exc:
        e.ap42_unpaved_emission_factor(0.10, 320.0 * ST, "PM10", strict=True)
    assert exc.value.argument == "mean_weight"
    with pytest.raises(input_error) as exc:
        e.ap42_unpaved_emission_factor(0.30, 320.0 * ST, "PM10", mean_speed=25.0, strict=True)
    msg = str(exc.value)
    assert "silt_fraction" in msg and "mean_weight" in msg and "mean_speed" in msg
    # inside the range strict mode returns the same value as the default mode
    a = e.ap42_unpaved_emission_factor(0.10, 100.0 * ST, "PM10", strict=True)
    b = e.ap42_unpaved_emission_factor(0.10, 100.0 * ST, "PM10")
    assert a == b


@pytest.mark.req("FR-006-03")
def test_fr_006_03_arrays_warn_when_any_element_is_out_of_range() -> None:
    e = _e()
    warning = _validity_warning()
    with pytest.warns(warning):
        out = e.ap42_unpaved_emission_factor(0.10, np.array([50_000.0, 300_000.0]), "PM10")
    assert out.shape == (2,) and np.all(np.isfinite(out))

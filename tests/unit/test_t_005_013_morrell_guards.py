"""T-005-013 (FR-005-12): the Morrell functions reject hostile inputs, sizes on the wrong side of 750 um, unknown stages.

Public API under test (`minephys.comminution`; signatures as in tests/unit/test_t_005_012_morrell.py). Expected
errors: `minephys.InputError` naming the argument for NaN, +-inf, zero or negative values, a product size not finer
than the feed, `morrell_tumbling_coarse` with x1 <= 750 um, `morrell_tumbling_fine` with P80 >= 750 um and a `stage` that
is not one of "primary", "secondary", "tertiary", "pebble" (case-sensitive); `minephys.InputTypeError` for non-numeric
arguments and for flags (`pebble_crusher`, `closed_circuit`) that are not booleans.

Oracle: the hostile classes written in FR-005-12 itself.
"""

from __future__ import annotations

import datetime as dt
import importlib
from typing import Any

import numpy as np
import pytest


def _c():
    return importlib.import_module("minephys.comminution")


def _errors():
    importlib.import_module("minephys.comminution")
    import minephys

    return minephys.InputError, minephys.InputTypeError


# (function, valid keyword arguments, names of the numeric arguments, names of the boolean flags)
CASES: list[tuple[str, dict[str, Any], list[str], list[str]]] = [
    ("morrell_energy", {"m_index": 7.2e4, "x1": 2e-3, "x2": 1.5e-4}, ["m_index", "x1", "x2"], []),
    ("morrell_tumbling_coarse", {"mia": 7.0e4, "x1": 0.1, "pebble_crusher": True}, ["mia", "x1"], ["pebble_crusher"]),
    ("morrell_tumbling_fine", {"mib": 6.8e4, "p80": 1.06e-4}, ["mib", "p80"], []),
    (
        "morrell_crusher",
        {"mic": 2.6e4, "x1": 0.1, "x2": 0.035, "closed_circuit": True, "stage": "secondary"},
        ["mic", "x1", "x2"],
        ["closed_circuit"],
    ),
    (
        "morrell_hpgr",
        {"mih": 5.0e4, "x1": 0.035, "x2": 0.004, "closed_circuit": True},
        ["mih", "x1", "x2"],
        ["closed_circuit"],
    ),
    ("morrell_size_distribution_correction", {"mia": 7.0e4, "x1": 0.1, "x2": 6.5e-3}, ["mia", "x1", "x2"], []),
    (
        "morrell_mib",
        {"closing_screen": 1.06e-4, "grindability": 1.825e-3, "f80": 2.7461e-3, "p80": 7.97e-5},
        ["closing_screen", "grindability", "f80", "p80"],
        [],
    ),
]
BAD_NUMBERS = [float("nan"), float("inf"), float("-inf"), 0.0, -1.0]
NON_NUMERIC: list[Any] = [
    "1.0",
    "１.０",
    None,
    1 + 2j,
    True,
    b"1",
    object(),
    dt.datetime(2020, 1, 1),
    np.datetime64("2020-01-01"),
    np.array(["x"]),
    np.array([2j]),
]
NON_BOOLEAN: list[Any] = [1, 0, 1.0, "True", "yes", None, np.float64(1.0), [True], np.int64(1)]


def _numeric_sweep() -> list[tuple[str, dict[str, Any], str]]:
    return [(fn, kw, a) for fn, kw, nums, _ in CASES for a in nums]


def _flag_sweep() -> list[tuple[str, dict[str, Any], str]]:
    return [(fn, kw, a) for fn, kw, _, flags in CASES for a in flags]


@pytest.mark.req("FR-005-12")
@pytest.mark.oracle("hand-calculation", "FR-005-12 hostile classes")
@pytest.mark.parametrize(("fn", "kw", "arg"), _numeric_sweep())
@pytest.mark.parametrize("bad", BAD_NUMBERS)
def test_fr_005_12_bad_numbers_raise_input_error(fn: str, kw: dict[str, Any], arg: str, bad: float) -> None:
    c = _c()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        getattr(c, fn)(**dict(kw, **{arg: bad}))
    assert exc.value.argument == arg


@pytest.mark.req("FR-005-12")
@pytest.mark.parametrize(("fn", "kw", "arg"), _numeric_sweep())
def test_fr_005_12_array_with_a_bad_element_raises(fn: str, kw: dict[str, Any], arg: str) -> None:
    c = _c()
    input_error, _ = _errors()
    for bad in (float("nan"), float("-inf"), -2.0):
        with pytest.raises(input_error) as exc:
            getattr(c, fn)(**dict(kw, **{arg: np.array([kw[arg], bad])}))
        assert exc.value.argument == arg


@pytest.mark.req("FR-005-12")
@pytest.mark.parametrize(("fn", "kw", "arg"), _numeric_sweep())
@pytest.mark.parametrize("bad", NON_NUMERIC, ids=lambda v: type(v).__name__)
def test_fr_005_12_non_numeric_raises_input_type_error(fn: str, kw: dict[str, Any], arg: str, bad: Any) -> None:
    c = _c()
    _, input_type_error = _errors()
    with pytest.raises(input_type_error) as exc:
        getattr(c, fn)(**dict(kw, **{arg: bad}))
    assert exc.value.argument == arg


@pytest.mark.req("FR-005-12")
@pytest.mark.parametrize(("fn", "kw", "arg"), _flag_sweep())
@pytest.mark.parametrize("bad", NON_BOOLEAN, ids=lambda v: f"{type(v).__name__}-{v!r}")
def test_fr_005_12_non_boolean_flag_raises_input_type_error(fn: str, kw: dict[str, Any], arg: str, bad: Any) -> None:
    c = _c()
    _, input_type_error = _errors()
    with pytest.raises(input_type_error) as exc:
        getattr(c, fn)(**dict(kw, **{arg: bad}))
    assert exc.value.argument == arg


@pytest.mark.req("FR-005-12")
@pytest.mark.parametrize(
    ("fn", "kw", "product", "feed"),
    [
        ("morrell_energy", {"m_index": 7.2e4}, "x2", "x1"),
        ("morrell_crusher", {"mic": 2.6e4, "closed_circuit": True, "stage": "primary"}, "x2", "x1"),
        ("morrell_hpgr", {"mih": 5.0e4, "closed_circuit": False}, "x2", "x1"),
        ("morrell_size_distribution_correction", {"mia": 7.0e4}, "x2", "x1"),
        ("morrell_mib", {"closing_screen": 1.06e-4, "grindability": 1.8e-3}, "p80", "f80"),
    ],
)
def test_fr_005_12_product_not_finer_than_feed_raises(fn: str, kw: dict[str, Any], product: str, feed: str) -> None:
    c = _c()
    input_error, _ = _errors()
    for feed_size, product_size in ((0.01, 0.01), (0.01, 0.02), (1e-4, 1.0)):
        with pytest.raises(input_error) as exc:
            getattr(c, fn)(**kw, **{feed: feed_size, product: product_size})
        assert exc.value.argument in {product, feed}
    # an array in which one element is unordered
    with pytest.raises(input_error):
        getattr(c, fn)(**kw, **{feed: np.array([0.1, 0.001]), product: 0.01})


@pytest.mark.req("FR-005-12")
@pytest.mark.knowledge("morrell_coarse_fine_boundary")
def test_fr_005_12_coarse_tumbling_needs_a_feed_coarser_than_750_um() -> None:
    c = _c()
    input_error, _ = _errors()
    for x1 in (750e-6, 749e-6, 1e-4, 1e-6):
        with pytest.raises(input_error) as exc:
            c.morrell_tumbling_coarse(7.0e4, x1, False)
        assert exc.value.argument == "x1"
    assert c.morrell_tumbling_coarse(7.0e4, 751e-6, False) > 0.0  # just coarser than the boundary is fine
    with pytest.raises(input_error):
        c.morrell_tumbling_coarse(7.0e4, np.array([0.1, 5e-4]), False)


@pytest.mark.req("FR-005-12")
@pytest.mark.knowledge("morrell_coarse_fine_boundary")
def test_fr_005_12_fine_tumbling_needs_a_grind_finer_than_750_um() -> None:
    c = _c()
    input_error, _ = _errors()
    for p80 in (750e-6, 751e-6, 1e-3, 0.1):
        with pytest.raises(input_error) as exc:
            c.morrell_tumbling_fine(6.8e4, p80)
        assert exc.value.argument == "p80"
    assert c.morrell_tumbling_fine(6.8e4, 749e-6) > 0.0
    with pytest.raises(input_error):
        c.morrell_tumbling_fine(6.8e4, np.array([1e-4, 8e-4]))


@pytest.mark.req("FR-005-12")
@pytest.mark.parametrize("stage", ["Primary", "SECONDARY", "quaternary", "", " primary", "primary ", "tertiary\n", "µ"])
def test_fr_005_12_unknown_stage_raises_input_error(stage: str) -> None:
    c = _c()
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        c.morrell_crusher(2.6e4, 0.1, 0.035, True, stage)
    assert exc.value.argument == "stage"
    assert "primary" in str(exc.value)  # FR-000-15: the message lists the allowed values


@pytest.mark.req("FR-005-12")
def test_fr_005_12_all_four_stages_are_accepted() -> None:
    c = _c()
    for stage in ("primary", "secondary", "tertiary", "pebble"):
        assert c.morrell_crusher(2.6e4, 0.1, 0.035, True, stage) > 0.0

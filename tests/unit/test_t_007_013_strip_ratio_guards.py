"""T-007-013 (FR-007-10): strip-ratio guards (zero ore raises, never inf or NaN).

Public API under test (`minephys.planning`): `strip_ratio(pit, tonnage, is_ore)`.
Expected: `minephys.InputError` for mismatched lengths, a negative or non-finite tonnage and a selection with zero ore tonnage
(including an empty pit and a pit of waste only; the function never returns inf or NaN); `minephys.InputTypeError` for a
non-boolean mask (`pit` or `is_ore`: integers, floats, strings) or a non-numeric tonnage.

Oracle: the hostile classes written in FR-007-10.
"""

from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pytest

NAN, INF = float("nan"), float("inf")
PIT = np.array([True, True, False, True])
TONNAGE = np.array([1.0, 2.0, 3.0, 4.0]) * 1e5
ORE = np.array([False, True, False, True])


def _f():
    return importlib.import_module("minephys.planning").strip_ratio


def _errors():
    importlib.import_module("minephys.planning")
    import minephys

    return minephys.InputError, minephys.InputTypeError


@pytest.mark.req("FR-007-10")
def test_fr_007_10_reference_call_is_valid() -> None:
    assert _f()(PIT, TONNAGE, ORE) == pytest.approx(1.0e5 / 6.0e5, rel=1e-12)


@pytest.mark.req("FR-007-10")
@pytest.mark.oracle("hand-calculation", "FR-007-10 hostile classes")
@pytest.mark.parametrize(
    "pit",
    [np.zeros(4, dtype=bool), np.array([True, False, True, False]), np.array([True, False, False, False])],
    ids=["empty", "waste-only-block-0-and-2", "waste-only-block-0"],
)
def test_fr_007_10_zero_ore_tonnage_raises(pit: np.ndarray) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error):
        _f()(pit, TONNAGE, ORE)


@pytest.mark.req("FR-007-10")
def test_fr_007_10_ore_blocks_with_zero_tonnage_count_as_zero_ore() -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error):
        _f()(PIT, np.array([1.0, 0.0, 3.0, 0.0]), ORE)  # the selected ore blocks have no tonnage


@pytest.mark.req("FR-007-10")
@pytest.mark.parametrize("bad", [-1e-9, -1.0, NAN, INF, -INF])
def test_fr_007_10_bad_tonnage(bad: float) -> None:
    input_error, _ = _errors()
    tonnage = TONNAGE.copy()
    tonnage[0] = bad
    with pytest.raises(input_error) as exc:
        _f()(PIT, tonnage, ORE)
    assert exc.value.argument == "tonnage"


@pytest.mark.req("FR-007-10")
@pytest.mark.parametrize(
    ("pit", "tonnage", "is_ore", "involved"),
    [
        (PIT[:3], TONNAGE, ORE, {"pit", "tonnage"}),
        (PIT, TONNAGE[:3], ORE, {"pit", "tonnage"}),
        (PIT, TONNAGE, ORE[:3], {"is_ore", "tonnage", "pit"}),
        (PIT, TONNAGE.reshape(2, 2), ORE, {"tonnage"}),
        (PIT.reshape(2, 2), TONNAGE, ORE, {"pit"}),
    ],
    ids=["pit-short", "tonnage-short", "ore-short", "tonnage-2d", "pit-2d"],
)
def test_fr_007_10_mismatched_lengths_and_ranks(pit: Any, tonnage: Any, is_ore: Any, involved: set[str]) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _f()(pit, tonnage, is_ore)
    assert exc.value.argument in involved


@pytest.mark.req("FR-007-10")
@pytest.mark.parametrize(
    "bad",
    [np.array([1, 1, 0, 1]), np.array([1.0, 1.0, 0.0, 1.0]), np.array(["a", "b", "c", "d"]), np.array([None, True, False, True], dtype=object)],
    ids=["int", "float", "str", "object"],
)
def test_fr_007_10_masks_must_be_boolean_arrays(bad: Any) -> None:
    _, input_type_error = _errors()
    f = _f()
    with pytest.raises(input_type_error) as exc:
        f(bad, TONNAGE, ORE)
    assert exc.value.argument == "pit"
    with pytest.raises(input_type_error) as exc:
        f(PIT, TONNAGE, bad)
    assert exc.value.argument == "is_ore"


@pytest.mark.req("FR-007-10")
@pytest.mark.parametrize("bad", ["abc", None, 1 + 2j, b"1", object(), np.array(["a", "b", "c", "d"])], ids=lambda v: type(v).__name__)
def test_fr_007_10_non_numeric_tonnage(bad: Any) -> None:
    _, input_type_error = _errors()
    with pytest.raises(input_type_error) as exc:
        _f()(PIT, bad, ORE)
    assert exc.value.argument == "tonnage"

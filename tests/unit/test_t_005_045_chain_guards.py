"""T-005-045 (FR-005-31): the mine-to-mill chain rejects hostile inputs and returns no partial result.

Public API under test (`minephys.comminution`): `mine_to_mill_chain(sizes, blast_passing, classification, breakage,
target_p80, installed_power, energy_model, *, work_index=None, mia=None, mib=None, fines_size)` (see
tests/unit/test_t_005_044_chain.py).
Expected: `minephys.InputError` whose `argument` names the offending argument for an unknown `energy_model`, a `target_p80`
that is not finer than the crusher product F80, a non-positive installed power, the indices its energy model needs being
missing or invalid, and inputs that the component functions reject (a Morrell chain whose F80 is not coarser than 750 um is
rejected through `morrell_tumbling_coarse`); `minephys.InputTypeError` for non-numeric arguments.

Oracle: the hostile classes written in FR-005-31.
"""

from __future__ import annotations

import datetime as dt
import importlib
from typing import Any

import numpy as np
import pytest

KWH = 3600.0


def _errors():
    importlib.import_module("minephys.comminution")
    import minephys

    return minephys.InputError, minephys.InputTypeError


SIZES = np.array([0.4, 0.2, 0.1, 0.05, 0.025])
BLAST = np.array([1.0, 0.85, 0.55, 0.3, 0.12])
CLASSIFICATION = np.array([0.9, 0.6, 0.2, 0.0, 0.0])
BREAKAGE = np.array(
    [
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [0.4, 0.0, 0.0, 0.0, 0.0],
        [0.3, 0.5, 0.0, 0.0, 0.0],
        [0.2, 0.3, 0.6, 0.0, 0.0],
        [0.1, 0.2, 0.4, 0.0, 0.0],
    ]
)
NAN, INF = float("nan"), float("inf")


def _chain(**over: Any) -> Any:
    kw: dict[str, Any] = dict(
        sizes=SIZES,
        blast_passing=BLAST,
        classification=CLASSIFICATION,
        breakage=BREAKAGE,
        target_p80=1.5e-4,
        installed_power=5.0e6,
        energy_model="bond",
        work_index=14.0 * KWH,
        fines_size=0.05,
    )
    kw.update(over)
    for k in [k for k, v in kw.items() if v is _DROP]:
        del kw[k]
    return importlib.import_module("minephys.comminution").mine_to_mill_chain(**kw)


_DROP = object()


def _morrell(**over: Any) -> Any:
    kw: dict[str, Any] = {"energy_model": "morrell", "work_index": _DROP, "mia": 19.4 * KWH, "mib": 18.8 * KWH}
    kw.update(over)
    return _chain(**kw)


@pytest.mark.req("FR-005-31")
def test_fr_005_31_reference_calls_are_valid() -> None:
    assert _chain().throughput > 0.0
    assert _morrell(target_p80=106e-6).throughput > 0.0


@pytest.mark.req("FR-005-31")
@pytest.mark.oracle("hand-calculation", "FR-005-31 hostile classes")
@pytest.mark.parametrize("name", ["unknown", "Bond", "BOND", "", "morrell ", "bond-energy"])
def test_fr_005_31_unknown_energy_model(name: str) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _chain(energy_model=name)
    assert exc.value.argument == "energy_model"
    assert "bond" in str(exc.value) and "morrell" in str(exc.value)  # the allowed values are listed


@pytest.mark.req("FR-005-31")
def test_fr_005_31_target_must_be_finer_than_the_crusher_product() -> None:
    input_error, _ = _errors()
    for target in (0.1, 0.5, 1.0, 10.0):  # the product F80 of this crusher is about 0.0925 m (hand calculation)
        with pytest.raises(input_error) as exc:
            _chain(target_p80=target)
        assert exc.value.argument == "target_p80"


@pytest.mark.req("FR-005-31")
@pytest.mark.parametrize("power", [0.0, -1.0, -1e6, NAN, INF, -INF])
def test_fr_005_31_installed_power(power: float) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _chain(installed_power=power)
    assert exc.value.argument == "installed_power"


@pytest.mark.req("FR-005-31")
@pytest.mark.parametrize("target", [0.0, -1e-4, NAN, INF])
def test_fr_005_31_target_p80_domain(target: float) -> None:
    input_error, _ = _errors()
    with pytest.raises(input_error) as exc:
        _chain(target_p80=target)
    assert exc.value.argument == "target_p80"


@pytest.mark.req("FR-005-31")
def test_fr_005_31_bond_model_needs_a_valid_work_index() -> None:
    input_error, _ = _errors()
    for bad in (_DROP, None, 0.0, -1.0, NAN, INF):
        with pytest.raises(input_error) as exc:
            _chain(work_index=bad)
        assert exc.value.argument == "work_index"


@pytest.mark.req("FR-005-31")
def test_fr_005_31_morrell_model_needs_valid_mia_and_mib() -> None:
    input_error, _ = _errors()
    for name in ("mia", "mib"):
        for bad in (_DROP, None, 0.0, -1.0, NAN, INF):
            with pytest.raises(input_error) as exc:
                _morrell(target_p80=106e-6, **{name: bad})
            assert exc.value.argument == name


@pytest.mark.req("FR-005-31")
def test_fr_005_31_morrell_needs_a_feed_coarser_than_750_um() -> None:
    input_error, _ = _errors()
    fine_sizes = np.array([4e-4, 2e-4, 1e-4, 5e-5, 2.5e-5])  # crusher product F80 below 750 um
    with pytest.raises(input_error):
        _morrell(sizes=fine_sizes, target_p80=1e-5)


@pytest.mark.req("FR-005-31")
def test_fr_005_31_component_inputs_are_rejected() -> None:
    input_error, _ = _errors()
    for over in (
        {"blast_passing": np.array([1.0, 0.85, 0.9, 0.3, 0.12])},  # not monotone
        {"blast_passing": np.array([1.2, 0.85, 0.55, 0.3, 0.12])},  # above 1
        {"blast_passing": np.array([1.0, 0.85, NAN, 0.3, 0.12])},
        {"sizes": np.array([0.4, 0.2, 0.2, 0.05, 0.025])},  # tie
        {"classification": np.array([0.9, 0.6, 0.2, 0.0, 1.5])},
        {"classification": np.array([0.9, 0.6, 0.2, 0.0, 0.1])},  # the finest class cannot be broken
        {"breakage": BREAKAGE.T.copy()},  # not lower triangular
        {"breakage": BREAKAGE[:4, :4]},  # shape mismatch
        {"fines_size": -0.05},
        {"fines_size": NAN},
    ):
        with pytest.raises(input_error):
            _chain(**over)


@pytest.mark.req("FR-005-31")
def test_fr_005_31_breakage_column_sums_are_checked() -> None:
    input_error, _ = _errors()
    bad = BREAKAGE.copy()
    bad[:, 0] *= 0.9  # column 0 belongs to a class with c > 0
    with pytest.raises(input_error) as exc:
        _chain(breakage=bad)
    assert exc.value.argument == "breakage"


@pytest.mark.req("FR-005-31")
@pytest.mark.parametrize("bad", ["abc", None, 1 + 2j, True, b"1", object(), dt.datetime(2020, 1, 1)], ids=lambda v: type(v).__name__)
def test_fr_005_31_non_numeric_arguments(bad: Any) -> None:
    _, input_type_error = _errors()
    for name in ("sizes", "blast_passing", "classification", "breakage", "target_p80", "installed_power"):
        with pytest.raises(input_type_error) as exc:
            _chain(**{name: bad})
        assert exc.value.argument == name

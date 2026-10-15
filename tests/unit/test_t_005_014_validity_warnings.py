"""T-005-014 (FR-005-32, FR-005-33): validity warnings below 70 um (Bond) and 45 um (Morrell fine term).

Public API under test (`minephys.comminution`): `bond_energy(work_index, f80, p80)`,
`bond_operating_work_index(specific_energy, f80, p80)`, `morrell_tumbling_fine(mib, p80)`.
Expected behaviour (FR-000-16): when P80 lies inside the physical domain but below the published limit, the function
emits `minephys.ValidityWarning` whose `argument` is "p80", whose `row` is the knowledge-row id
(`bond_min_product_size` = 70 um; `morrell_fine_grind_limit` = 45 um), whose `bounds` hold the limit and whose message
names the argument, the bound and the row id, and it still returns the closed-form result. At or above the limit no
warning is emitted. (The chain's warnings are tested with the chain, T-005-044.)

Oracle: hand calculation of the closed forms written below, plus the published limits (`mcivor2016bondgmsg` p. 1:
"applies down to approximately 70 um"; `gmsg2016morrell` section B.1, p. 6: "approximately 45 um").
"""

from __future__ import annotations

import importlib
import math
import warnings

import numpy as np
import pytest

KWH = 3600.0


def _c():
    return importlib.import_module("minephys.comminution")


def _warning_class():
    importlib.import_module("minephys.comminution")
    import minephys

    return minephys.ValidityWarning


def _g(x_um: float) -> float:
    return x_um ** (-(0.295 + x_um / 1e6))


def _bound_in(w: Warning, limit_m: float, limit_um: float) -> bool:
    bounds = getattr(w, "bounds", ())
    return any(math.isclose(b, limit_m, rel_tol=1e-12) or math.isclose(b, limit_um, rel_tol=1e-12) for b in bounds)


@pytest.mark.req("FR-005-32")
@pytest.mark.knowledge("bond_min_product_size")
@pytest.mark.oracle("worked-example", "mcivor2016bondgmsg p. 1: Bond's law applies down to approximately 70 um")
def test_fr_005_32_bond_energy_warns_below_70_um_and_still_returns() -> None:
    c = _c()
    warning = _warning_class()
    wi = 15.0 * KWH
    with pytest.warns(warning) as rec:
        w = c.bond_energy(wi, 2e-3, 50e-6)
    expected = 10.0 * wi * (1.0 / math.sqrt(50.0) - 1.0 / math.sqrt(2000.0))
    np.testing.assert_allclose(w, expected, rtol=1e-12, atol=0)
    hits = [r.message for r in rec if isinstance(r.message, warning)]
    assert hits, "no ValidityWarning recorded"
    msg = hits[0]
    assert msg.argument == "p80"
    assert msg.row == "bond_min_product_size"
    assert _bound_in(msg, 70e-6, 70.0)
    text = str(msg)
    assert "p80" in text and "bond_min_product_size" in text


@pytest.mark.req("FR-005-32")
@pytest.mark.knowledge("bond_min_product_size")
def test_fr_005_32_bond_operating_work_index_warns_below_70_um() -> None:
    c = _c()
    warning = _warning_class()
    with pytest.warns(warning) as rec:
        wio = c.bond_operating_work_index(2.0e4, 1e-3, 40e-6)
    np.testing.assert_allclose(
        wio, 2.0e4 / (10.0 / math.sqrt(40.0) - 10.0 / math.sqrt(1000.0)), rtol=1e-12, atol=0
    )
    msg = next(r.message for r in rec if isinstance(r.message, warning))
    assert msg.argument == "p80" and msg.row == "bond_min_product_size"


@pytest.mark.req("FR-005-32")
@pytest.mark.parametrize("p80", [70e-6, 70.0000001e-6, 100e-6, 1e-3])
def test_fr_005_32_no_bond_warning_at_or_above_70_um(p80: float) -> None:
    c = _c()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        c.bond_energy(5.4e4, 5e-3, p80)
        c.bond_operating_work_index(3.0e4, 5e-3, p80)


@pytest.mark.req("FR-005-32")
@pytest.mark.parametrize("p80", [69.9999e-6, 30e-6, 10e-6])
def test_fr_005_32_bond_warns_on_either_side_of_the_limit(p80: float) -> None:
    c = _c()
    warning = _warning_class()
    with pytest.warns(warning):
        c.bond_energy(5.4e4, 5e-3, p80)


@pytest.mark.req("FR-005-32")
def test_fr_005_32_one_warning_when_any_array_element_is_out_of_range() -> None:
    c = _c()
    warning = _warning_class()
    p80 = np.array([150e-6, 60e-6, 200e-6])
    with pytest.warns(warning):
        out = c.bond_energy(5.4e4, 5e-3, p80)
    assert out.shape == (3,) and np.all(np.isfinite(out))


@pytest.mark.req("FR-005-33")
@pytest.mark.knowledge("morrell_fine_grind_limit")
@pytest.mark.oracle("worked-example", "gmsg2016morrell section B.1, p. 6: the fine term applies down to approximately 45 um")
def test_fr_005_33_morrell_fine_warns_below_45_um_and_still_returns() -> None:
    c = _c()
    warning = _warning_class()
    mib = 18.8 * KWH
    with pytest.warns(warning) as rec:
        w = c.morrell_tumbling_fine(mib, 40e-6)
    np.testing.assert_allclose(w, mib * 4.0 * (_g(40.0) - _g(750.0)), rtol=1e-12, atol=0)
    msg = next(r.message for r in rec if isinstance(r.message, warning))
    assert msg.argument == "p80"
    assert msg.row == "morrell_fine_grind_limit"
    assert _bound_in(msg, 45e-6, 45.0)
    assert "p80" in str(msg) and "morrell_fine_grind_limit" in str(msg)


@pytest.mark.req("FR-005-33")
@pytest.mark.parametrize("p80", [45e-6, 45.0000001e-6, 106e-6, 700e-6])
def test_fr_005_33_no_morrell_warning_at_or_above_45_um(p80: float) -> None:
    c = _c()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        c.morrell_tumbling_fine(6.8e4, p80)


@pytest.mark.req("FR-005-33")
@pytest.mark.parametrize("p80", [44.999e-6, 20e-6, 10e-6])
def test_fr_005_33_morrell_fine_warns_just_below_and_far_below(p80: float) -> None:
    c = _c()
    warning = _warning_class()
    with pytest.warns(warning):
        c.morrell_tumbling_fine(6.8e4, p80)


@pytest.mark.req("FR-005-33")
@pytest.mark.req("FR-005-32")
def test_validity_warning_is_a_user_warning_with_the_documented_attributes() -> None:
    c = _c()
    warning = _warning_class()
    assert issubclass(warning, UserWarning)
    with pytest.warns(warning) as rec:
        c.morrell_tumbling_fine(6.8e4, 30e-6)
    msg = next(r.message for r in rec if isinstance(r.message, warning))
    assert isinstance(msg.bounds, tuple)

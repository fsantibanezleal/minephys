"""T-005-012 (FR-005-05 to FR-005-11, SC-005-01): the Morrell energy-size relation and circuit terms.

Expected public API (`minephys.comminution`; sizes in m, energies and indices in J/kg, grindability in kg/rev;
the 80 % passing sizes are converted to um once inside, f(x) = -(0.295 + x_um / 1e6)):
    morrell_energy(m_index, x1, x2)                              W  = Mi * 4 * (x2^f(x2) - x1^f(x1))
    morrell_tumbling_coarse(mia, x1, pebble_crusher)             Wa = K1 Mia 4 (750^f(750) - x1^f(x1)), K1 = 0.95 if pebble_crusher else 1
    morrell_tumbling_fine(mib, p80)                              Wb = Mib 4 (P80^f(P80) - 750^f(750))
    morrell_crusher(mic, x1, x2, closed_circuit, stage)          Wc = Sc K2 Mic 4 (x2^f(x2) - x1^f(x1)); K2 = 1 closed / 1.19 open;
                                                                 Sc = min(55 (x1 x2)^-0.2, 1) for "primary"/"secondary", 1 for "tertiary"/"pebble"
    morrell_hpgr(mih, x1, x2, closed_circuit)                    Wh = Sh K3 Mih 4 (...), Sh = min(35 (x1 x2)^-0.2, 1), K3 = 1 / 1.19
    morrell_size_distribution_correction(mia, x1, x2)            Ws = 0.19 Mia 4 (...)
    morrell_mib(closing_screen, grindability, f80, p80)          Mib = 18.18 / (P100^0.295 Gbp (P80^f(P80) - F80^f(F80)))  [kWh/t -> J/kg]

Oracles
- hand calculation of every equation, written below with `math` (TC-1, rtol 1e-12);
- worked examples of the Morrell-method guideline Annex C (`gmsg2016morrell`, pp. 11-12; spec 005 section 7):
  Mia = 19.4, Mib = 18.8, Mic = 7.2, Mih = 13.9 kWh/t, circuit feed 100 mm, final P80 = 106 um; stage values 9.6, 8.4,
  1.13, 0.4, 0.5, 1.1, 2.4, 4.5, 5.5, 0.9 kWh/t and circuit totals 18.3, 15.7, 16.4 kWh/t (TC-2: half a unit of the last
  published digit for stages, +-0.1 kWh/t for totals because the guideline adds rounded stage values).
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest

KWH = 3600.0  # J/kg per kWh/t (exact unit definition)
MIA, MIB, MIC, MIH = 19.4 * KWH, 18.8 * KWH, 7.2 * KWH, 13.9 * KWH


def _c():
    return importlib.import_module("minephys.comminution")


def _f(x_um: float) -> float:
    return -(0.295 + x_um / 1e6)


def _g(x_um: float) -> float:
    return x_um ** _f(x_um)


def _hand(mi_kwh: float, x1_um: float, x2_um: float) -> float:
    """Mi * 4 * (x2^f(x2) - x1^f(x1)) in kWh/t, sizes in um."""
    return mi_kwh * 4.0 * (_g(x2_um) - _g(x1_um))


def _close(got: float, expected_kwh: float, rtol: float = 1e-12) -> None:
    np.testing.assert_allclose(got, expected_kwh * KWH, rtol=rtol, atol=0)


@pytest.mark.req("FR-005-05")
@pytest.mark.oracle("hand-calculation", "Mi = 20 kWh/t, 2,000 -> 150 um: exponents -0.297 and -0.29515 -> 9.862056 kWh/t")
@pytest.mark.knowledge("morrell_coefficient")
@pytest.mark.knowledge("morrell_f_constant")
@pytest.mark.knowledge("morrell_f_scale")
def test_fr_005_05_morrell_energy_hand_calculation() -> None:
    c = _c()
    w = c.morrell_energy(20.0 * KWH, 2.0e-3, 1.5e-4)
    assert _f(2000.0) == pytest.approx(-0.297, abs=1e-15) and _f(150.0) == pytest.approx(-0.29515, abs=1e-15)
    _close(w, 20.0 * 4.0 * (150.0 ** (-0.29515) - 2000.0 ** (-0.297)))
    np.testing.assert_allclose(w / KWH, 9.862056, rtol=0, atol=6e-7)  # plan 005 hand value
    assert isinstance(w, np.float64)


@pytest.mark.req("FR-005-05")
def test_fr_005_05_array_broadcast_returns_float64_array() -> None:
    c = _c()
    x1 = np.array([[1e-3], [2e-3]])
    x2 = np.array([5e-5, 1e-4, 2e-4])
    w = c.morrell_energy(3.6e4, x1, x2)
    assert w.shape == (2, 3) and w.dtype == np.float64
    ref = [[3.6e4 * 4 * (_g(b * 1e6) - _g(a * 1e6)) for b in (5e-5, 1e-4, 2e-4)] for a in (1e-3, 2e-3)]
    np.testing.assert_allclose(w, ref, rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-06")
@pytest.mark.req("SC-005-01")
@pytest.mark.oracle("worked-example", "gmsg2016morrell Annex C pp. 11-12: Wa = 9.6 (100 mm, pebble crusher), 4.5 (4 mm), 5.5 (6.5 mm)")
@pytest.mark.knowledge("morrell_k1_pebble_crusher")
@pytest.mark.knowledge("morrell_coarse_fine_boundary")
@pytest.mark.parametrize(
    ("x1_mm", "pebble", "hand_kwh", "printed"),
    [(100.0, True, 9.625169, 9.6), (4.0, False, 4.454749, 4.5), (6.5, False, 5.454933, 5.5)],
)
def test_fr_005_06_coarse_tumbling_energy(x1_mm: float, pebble: bool, hand_kwh: float, printed: float) -> None:
    c = _c()
    k1 = 0.95 if pebble else 1.0
    w = c.morrell_tumbling_coarse(MIA, x1_mm * 1e-3, pebble)
    _close(w, k1 * 19.4 * 4.0 * (_g(750.0) - _g(x1_mm * 1e3)))
    np.testing.assert_allclose(w / KWH, hand_kwh, rtol=0, atol=6e-7)  # plan 005 hand values
    assert abs(w / KWH - printed) <= 0.05  # TC-2
    # the keyword form is part of the API
    assert c.morrell_tumbling_coarse(mia=MIA, x1=x1_mm * 1e-3, pebble_crusher=pebble) == w


@pytest.mark.req("FR-005-06")
def test_fr_005_06_pebble_crusher_factor_is_exactly_k1() -> None:
    c = _c()
    with_pc = c.morrell_tumbling_coarse(MIA, 0.1, True)
    without = c.morrell_tumbling_coarse(MIA, 0.1, False)
    np.testing.assert_allclose(with_pc, 0.95 * without, rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-07")
@pytest.mark.req("SC-005-01")
@pytest.mark.oracle("worked-example", "gmsg2016morrell Annex C: Wb = 8.4 kWh/t at P80 = 106 um")
def test_fr_005_07_fine_tumbling_energy() -> None:
    c = _c()
    w = c.morrell_tumbling_fine(MIB, 106e-6)
    _close(w, 18.8 * 4.0 * (_g(106.0) - _g(750.0)))
    np.testing.assert_allclose(w / KWH, 8.375604, rtol=0, atol=6e-7)
    assert abs(w / KWH - 8.4) <= 0.05


@pytest.mark.req("FR-005-08")
@pytest.mark.req("SC-005-01")
@pytest.mark.oracle("worked-example", "gmsg2016morrell Annex C: pebble crusher 1.13, secondary 0.4 closed / 0.5 open, tertiary 1.1 kWh/t")
@pytest.mark.knowledge("morrell_k2_open_circuit")
@pytest.mark.knowledge("morrell_ks_crusher")
@pytest.mark.knowledge("morrell_s_exponent")
def test_fr_005_08_crusher_energy_worked_examples() -> None:
    c = _c()
    # pebble crusher 52.5 -> 12 mm, open circuit, Sc not applied to pebble crushers (hand 1.132374, printed 1.13)
    w = c.morrell_crusher(MIC, 52.5e-3, 12e-3, False, "pebble")
    _close(w, 1.19 * _hand(7.2, 52500.0, 12000.0))
    np.testing.assert_allclose(w / KWH, 1.132374, rtol=0, atol=6e-7)
    assert abs(w / KWH - 1.13) <= 0.005
    # secondary crusher 100 -> 35 mm: Sc = 0.678499 (hand), closed 0.411598 (printed 0.4), open 0.489802 (printed 0.5)
    sc = min(55.0 * (100000.0 * 35000.0) ** -0.2, 1.0)
    assert sc == pytest.approx(0.678499, abs=1e-6)
    closed = c.morrell_crusher(MIC, 0.1, 0.035, True, "secondary")
    opened = c.morrell_crusher(MIC, 0.1, 0.035, False, "secondary")
    _close(closed, sc * _hand(7.2, 100000.0, 35000.0))
    _close(opened, sc * 1.19 * _hand(7.2, 100000.0, 35000.0))
    np.testing.assert_allclose(closed / KWH, 0.411598, rtol=0, atol=6e-7)
    np.testing.assert_allclose(opened / KWH, 0.489802, rtol=0, atol=6e-7)
    assert abs(closed / KWH - 0.4) <= 0.05 and abs(opened / KWH - 0.5) <= 0.05
    # tertiary crusher 35 -> 6.5 mm closed: Sc would be 1.172 and is replaced by 1 (hand 1.129098, printed 1.1)
    w3 = c.morrell_crusher(MIC, 35e-3, 6.5e-3, True, "tertiary")
    _close(w3, _hand(7.2, 35000.0, 6500.0))
    np.testing.assert_allclose(w3 / KWH, 1.129098, rtol=0, atol=6e-7)
    assert abs(w3 / KWH - 1.1) <= 0.05


@pytest.mark.req("FR-005-08")
@pytest.mark.oracle("hand-calculation", "Sc = min(55 (x1 x2)^-0.2, 1) applies to primary and secondary only")
def test_fr_005_08_stage_dependent_size_factor() -> None:
    c = _c()
    base = _hand(7.2, 52500.0, 12000.0)  # closed circuit, no size factor
    sc = 55.0 * (52500.0 * 12000.0) ** -0.2
    assert sc == pytest.approx(0.956, abs=5e-4) and sc < 1.0  # the pebble example where Sc would bite
    for stage in ("primary", "secondary"):
        _close(c.morrell_crusher(MIC, 52.5e-3, 12e-3, True, stage), sc * base)
    for stage in ("tertiary", "pebble"):
        _close(c.morrell_crusher(MIC, 52.5e-3, 12e-3, True, stage), base)
    # Sc is clamped at 1 for primary/secondary stages too (35 -> 6.5 mm gives 1.172)
    for stage in ("primary", "secondary"):
        _close(c.morrell_crusher(MIC, 35e-3, 6.5e-3, True, stage), _hand(7.2, 35000.0, 6500.0))
    # open circuit is exactly K2 = 1.19 times the closed circuit
    for stage in ("primary", "secondary", "tertiary", "pebble"):
        closed = c.morrell_crusher(MIC, 0.1, 0.035, True, stage)
        opened = c.morrell_crusher(MIC, 0.1, 0.035, False, stage)
        np.testing.assert_allclose(opened, 1.19 * closed, rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-09")
@pytest.mark.req("SC-005-01")
@pytest.mark.oracle("worked-example", "gmsg2016morrell Annex C: HPGR 35 -> 4 mm closed, Sh = 0.82, 2.4 kWh/t")
@pytest.mark.knowledge("morrell_ks_hpgr")
@pytest.mark.knowledge("morrell_k3_open_circuit")
def test_fr_005_09_hpgr_energy() -> None:
    c = _c()
    sh = min(35.0 * (35000.0 * 4000.0) ** -0.2, 1.0)
    assert sh == pytest.approx(0.821944, abs=1e-6)
    closed = c.morrell_hpgr(MIH, 35e-3, 4e-3, True)
    _close(closed, sh * _hand(13.9, 35000.0, 4000.0))
    np.testing.assert_allclose(closed / KWH, 2.380690, rtol=0, atol=6e-7)
    assert abs(closed / KWH - 2.4) <= 0.05
    opened = c.morrell_hpgr(MIH, 35e-3, 4e-3, False)
    np.testing.assert_allclose(opened, 1.19 * closed, rtol=1e-12, atol=0)
    # Sh is clamped at 1: coarse-to-slightly-finer reduction where 35 (x1 x2)^-0.2 > 1 (x1 x2 < 35^5 um^2)
    small = c.morrell_hpgr(MIH, 4e-3, 2e-3, True)
    _close(small, _hand(13.9, 4000.0, 2000.0))


@pytest.mark.req("FR-005-10")
@pytest.mark.req("SC-005-01")
@pytest.mark.oracle("worked-example", "gmsg2016morrell Annex C: Ws = 0.9 kWh/t (6.5 mm vs 100 mm)")
@pytest.mark.knowledge("morrell_ws_factor")
def test_fr_005_10_size_distribution_correction() -> None:
    c = _c()
    w = c.morrell_size_distribution_correction(MIA, 0.1, 6.5e-3)
    _close(w, 0.19 * _hand(19.4, 100000.0, 6500.0))
    np.testing.assert_allclose(w / KWH, 0.888597, rtol=0, atol=6e-7)
    assert abs(w / KWH - 0.9) <= 0.05


@pytest.mark.req("FR-005-11")
@pytest.mark.oracle("hand-calculation", "Mib = 18.18 / (P100^0.295 Gbp (P80^f(P80) - F80^f(F80))) = 13.976217 kWh/t on the Bond test sheet data")
@pytest.mark.knowledge("morrell_mib_constant")
@pytest.mark.knowledge("morrell_mib_screen_exponent")
def test_fr_005_11_mib_from_the_bond_test() -> None:
    c = _c()
    mib = c.morrell_mib(106e-6, 1.825e-3, 2746.1e-6, 79.7e-6)
    expected = 18.18 / (106.0**0.295 * 1.825 * (_g(79.7) - _g(2746.1)))
    _close(mib, expected)
    np.testing.assert_allclose(mib / KWH, 13.976217, rtol=0, atol=6e-7)


@pytest.mark.req("FR-005-11")
@pytest.mark.oracle("analytical", "Mib is inversely proportional to Gbp and to P100^0.295")
def test_fr_005_11_mib_scaling_in_grindability_and_screen() -> None:
    c = _c()
    base = c.morrell_mib(106e-6, 1.825e-3, 2746.1e-6, 79.7e-6)
    np.testing.assert_allclose(c.morrell_mib(106e-6, 3.65e-3, 2746.1e-6, 79.7e-6), base / 2.0, rtol=1e-12, atol=0)
    np.testing.assert_allclose(
        c.morrell_mib(212e-6, 1.825e-3, 2746.1e-6, 79.7e-6), base / 2.0**0.295, rtol=1e-12, atol=0
    )


@pytest.mark.req("SC-005-01")
@pytest.mark.oracle("worked-example", "gmsg2016morrell Annex C circuit totals: SABC 18.3, HPGR/ball 15.7, crushing/ball 16.4 kWh/t")
def test_sc_005_01_circuit_totals_of_the_three_published_circuits() -> None:
    c = _c()
    kwh = lambda j: j / KWH  # noqa: E731
    # SABC: Wa (100 mm, pebble crusher) + Wb (106 um) + pebble crusher 25 % recycle on new feed
    wa = kwh(c.morrell_tumbling_coarse(MIA, 0.1, True))
    wb = kwh(c.morrell_tumbling_fine(MIB, 106e-6))
    wc = kwh(c.morrell_crusher(MIC, 52.5e-3, 12e-3, False, "pebble"))
    assert abs(wa + wb + 0.25 * wc - 18.3) <= 0.1
    # HPGR / ball mill: secondary crusher (closed) + HPGR (closed) + Wa (4 mm) + Wb
    total = (
        kwh(c.morrell_crusher(MIC, 0.1, 0.035, True, "secondary"))
        + kwh(c.morrell_hpgr(MIH, 0.035, 0.004, True))
        + kwh(c.morrell_tumbling_coarse(MIA, 0.004, False))
        + wb
    )
    assert abs(total - 15.7) <= 0.1
    # Crushing / ball mill: secondary (open) + tertiary (closed) + Wa (6.5 mm) + Wb + Ws
    total = (
        kwh(c.morrell_crusher(MIC, 0.1, 0.035, False, "secondary"))
        + kwh(c.morrell_crusher(MIC, 0.035, 6.5e-3, True, "tertiary"))
        + kwh(c.morrell_tumbling_coarse(MIA, 6.5e-3, False))
        + wb
        + kwh(c.morrell_size_distribution_correction(MIA, 0.1, 6.5e-3))
    )
    assert abs(total - 16.4) <= 0.1

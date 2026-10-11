"""T-005-010 (FR-005-01, FR-005-02, FR-005-03, SC-005-01): Bond's law, operating work index and ball-mill test index.

Expected public API (`minephys.comminution`, SI at the boundary: sizes in m, energies in J/kg, grindability in kg/rev):
    bond_energy(work_index, f80, p80)                                  -> W  = 10 Wi (1/sqrt(P80) - 1/sqrt(F80)), sizes in um inside
    bond_operating_work_index(specific_energy, f80, p80)               -> Wio = W / (10/sqrt(P80) - 10/sqrt(F80))
    bond_ball_mill_work_index(closing_screen, grindability, f80, p80)  -> 1.1025 * 44.5 / (P1^0.23 Gbp^0.82 (10/sqrt(P80) - 10/sqrt(F80)))
Scalars in give `numpy.float64`; arrays give a float64 array of the broadcast shape (FR-000-07).

Oracles
- hand calculation: the equations written out below with `math` (TC-1, rtol 1e-12);
- worked examples of the Bond-efficiency guideline (`mcivor2016bondgmsg`, pp. 1-2 and the test sheet on p. 11, as
  transcribed in spec 005 section 7): 9.5 x (10/sqrt(1,000) - 10/sqrt(19,300)) = 2.32, 9.8 x (10/sqrt(155) -
  10/sqrt(1,000)) = 4.77, total 7.09, standard work index 9.70, operating work index 8.56 / (...) = 11.7,
  7.0 / (10/sqrt(212) - 10/sqrt(2,500)) = 14.4, ball-mill test 10.0 kWh/short ton = 11.0 kWh/t (TC-2);
- analytical limit: W -> Wi as F80 -> infinity at P80 = 100 um, with |W - Wi| = 10 Wi / sqrt(F80_um).
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest

KWH_PER_T = 3600.0  # J/kg per kWh/t (1 kWh = 3.6e6 J, 1 t = 1000 kg): exact unit definition


def _c():  # first-party import happens inside each test: the module under test is looked up first
    return importlib.import_module("minephys.comminution")


def _d(f_um: float, p_um: float) -> float:
    """The bracket 10/sqrt(P80) - 10/sqrt(F80) of Bond's law, sizes in um."""
    return 10.0 / math.sqrt(p_um) - 10.0 / math.sqrt(f_um)


@pytest.mark.req("FR-005-01")
@pytest.mark.oracle("hand-calculation", "Bond's law, Wi = 15 kWh/t, F80 = 2,000 um, P80 = 150 um -> 8.893347 kWh/t")
def test_fr_005_01_bond_energy_hand_calculation() -> None:
    c = _c()
    wi = 15.0 * KWH_PER_T
    w = c.bond_energy(wi, 2.0e-3, 1.5e-4)
    expected = wi * _d(2000.0, 150.0)
    np.testing.assert_allclose(w, expected, rtol=1e-12, atol=0)
    np.testing.assert_allclose(w, 32016.05, rtol=1e-7)  # printed to 7 significant figures in plan 005
    assert isinstance(w, np.float64)


@pytest.mark.req("FR-005-01")
@pytest.mark.req("SC-005-01")
@pytest.mark.oracle("worked-example", "mcivor2016bondgmsg p. 2: rod-ball standard circuit stage energies")
@pytest.mark.knowledge("bond_law_coefficient")
@pytest.mark.parametrize(
    ("wi_kwh", "f_um", "p_um", "printed"),
    [(9.5, 19300.0, 1000.0, 2.32), (9.8, 1000.0, 155.0, 4.77)],
)
def test_fr_005_01_published_rod_ball_stage_energies(wi_kwh: float, f_um: float, p_um: float, printed: float) -> None:
    c = _c()
    w = c.bond_energy(wi_kwh * KWH_PER_T, f_um * 1e-6, p_um * 1e-6) / KWH_PER_T
    assert abs(w - printed) <= 0.005  # two decimals published: half a unit of the last digit
    total = (
        c.bond_energy(9.5 * KWH_PER_T, 19300e-6, 1000e-6) + c.bond_energy(9.8 * KWH_PER_T, 1000e-6, 155e-6)
    ) / KWH_PER_T
    assert abs(total - 7.09) <= 0.005 + 1e-9  # 2.32 + 4.77 = 7.09 as printed


@pytest.mark.req("FR-005-01")
@pytest.mark.oracle("analytical", "W -> Wi as F80 -> infinity at P80 = 100 um; |W - Wi| = 10 Wi / sqrt(F80_um)")
def test_fr_005_01_limit_large_feed_tends_to_work_index() -> None:
    c = _c()
    wi = 7.5 * KWH_PER_T
    for f_m in (1.0, 10.0, 1000.0):
        w = c.bond_energy(wi, f_m, 1.0e-4)
        bound = 10.0 * wi / math.sqrt(f_m * 1e6)
        assert abs(w - wi) <= bound * (1 + 1e-9)
        assert w < wi
    assert abs(c.bond_energy(wi, 1000.0, 1.0e-4) - wi) < 1e-3 * wi


@pytest.mark.req("FR-005-01")
@pytest.mark.req("FR-005-02")
def test_fr_005_01_broadcasting_and_types() -> None:
    c = _c()
    f = np.array([[2e-3], [3e-3]])  # (2, 1)
    p = np.array([1e-4, 1.5e-4, 2e-4])  # (3,)
    w = c.bond_energy(54000.0, f, p)
    assert isinstance(w, np.ndarray) and w.dtype == np.float64 and w.shape == (2, 3)
    ref = np.array([[54000.0 * _d(fu, pu) for pu in (100.0, 150.0, 200.0)] for fu in (2000.0, 3000.0)])
    np.testing.assert_allclose(w, ref, rtol=1e-12, atol=0)
    wio = c.bond_operating_work_index(30000.0, f, p)
    assert wio.shape == (2, 3) and wio.dtype == np.float64
    # Python int and numpy float32 scalars are accepted and upcast (FR-000-07)
    assert isinstance(c.bond_energy(54000, np.float32(0.5), 1e-3), np.float64)


@pytest.mark.req("FR-005-02")
@pytest.mark.oracle("hand-calculation", "Wio = W / (10/sqrt(P80) - 10/sqrt(F80)), sizes in um")
def test_fr_005_02_operating_work_index_hand_calculation() -> None:
    c = _c()
    w = 4.2 * KWH_PER_T
    wio = c.bond_operating_work_index(w, 1.2e-3, 90e-6)
    np.testing.assert_allclose(wio, w / _d(1200.0, 90.0), rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-02")
@pytest.mark.req("SC-005-01")
@pytest.mark.oracle("worked-example", "mcivor2016bondgmsg pp. 1-2: black-box and rod-ball operating/standard work indices")
@pytest.mark.parametrize(
    ("energy_kwh", "f_um", "p_um", "printed"),
    [
        (7.0, 2500.0, 212.0, 14.4),  # black-box circuit: Wio = 14.4 kWh/t
        (7.09, 19300.0, 155.0, 9.70),  # rod-ball standard circuit: standard work index 9.70
        (8.56, 19300.0, 155.0, 11.7),  # rod-ball operating work index 11.7
    ],
)
def test_fr_005_02_published_operating_work_indices(energy_kwh: float, f_um: float, p_um: float, printed: float) -> None:
    c = _c()
    wio = c.bond_operating_work_index(energy_kwh * KWH_PER_T, f_um * 1e-6, p_um * 1e-6) / KWH_PER_T
    assert abs(wio - printed) <= 0.05  # one decimal published (two for 9.70: still inside 0.05)


@pytest.mark.req("FR-005-03")
@pytest.mark.oracle("hand-calculation", "1.1025 * 44.5 / (P1^0.23 Gbp^0.82 (10/sqrt(P80) - 10/sqrt(F80))) = 11.028663 kWh/t")
@pytest.mark.knowledge("bond_bm_constant")
@pytest.mark.knowledge("bond_bm_exponent_screen")
@pytest.mark.knowledge("bond_bm_exponent_grindability")
@pytest.mark.knowledge("bond_short_ton_to_metric")
def test_fr_005_03_ball_mill_test_hand_calculation() -> None:
    c = _c()
    wi = c.bond_ball_mill_work_index(106e-6, 1.825e-3, 2746.1e-6, 79.7e-6)
    expected_kwh_t = 1.1025 * 44.5 / (106.0**0.23 * 1.825**0.82 * _d(2746.1, 79.7))
    np.testing.assert_allclose(wi, expected_kwh_t * KWH_PER_T, rtol=1e-12, atol=0)
    np.testing.assert_allclose(expected_kwh_t, 11.028663, rtol=1e-7)  # plan 005 hand value
    assert isinstance(wi, np.float64)


@pytest.mark.req("FR-005-03")
@pytest.mark.req("SC-005-01")
@pytest.mark.oracle("worked-example", "mcivor2016bondgmsg p. 11 test sheet: 10.0 kWh/short ton = 11.0 kWh/t")
def test_fr_005_03_published_ball_mill_test_result() -> None:
    c = _c()
    wi = c.bond_ball_mill_work_index(106e-6, 1.825e-3, 2746.1e-6, 79.7e-6) / KWH_PER_T
    assert abs(wi - 11.0) <= 0.05  # TC-2, spec FR-005-03
    assert abs(wi / 1.1025 - 10.0) <= 0.05  # the short-ton value, 10.0 kWh/st


@pytest.mark.req("FR-005-03")
@pytest.mark.oracle("analytical", "Wi is proportional to 1/G^0.82 and to 1/P1^-0.23: closed-form exponent checks")
def test_fr_005_03_exponent_scaling() -> None:
    c = _c()
    base = c.bond_ball_mill_work_index(106e-6, 1.825e-3, 2746.1e-6, 79.7e-6)
    # doubling the grindability divides the index by 2^0.82
    np.testing.assert_allclose(
        c.bond_ball_mill_work_index(106e-6, 2 * 1.825e-3, 2746.1e-6, 79.7e-6), base / 2**0.82, rtol=1e-12, atol=0
    )
    # doubling the closing screen divides the index by 2^0.23
    np.testing.assert_allclose(
        c.bond_ball_mill_work_index(2 * 106e-6, 1.825e-3, 2746.1e-6, 79.7e-6), base / 2**0.23, rtol=1e-12, atol=0
    )

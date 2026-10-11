"""T-005-062 (NFR-005-03, FR-000-25): one worked-example oracle per function family in the Pyodide smoke subset.

These tests carry the `pyodide` marker: the CI Pyodide job runs them inside Pyodide, and they are excluded from the
CPython wheel run by `-m "not gpu and not pyodide and not kit"` (FR-000-24). They also run unchanged on CPython
(`pytest -m pyodide`), which is how this red phase proves them. Each family is pinned by one published or hand-derived value
with a tolerance of its kind (TC-2 for printed values, TC-1 for closed forms):

- Bond: the ball-mill test sheet, 10.0 kWh/short ton = 11.0 kWh/t (`mcivor2016bondgmsg` p. 11);
- Morrell: Wb = 8.4 kWh/t at P80 = 106 um (`gmsg2016morrell` Annex C) and the 100 mm pebble-crusher Wa = 9.6 kWh/t;
- population balance: the three-class batch solution at 120 s (analytical, Reid 1965) and one tank (0.5, 0.1875, 0.3125);
- flotation: first order 0.893936 and the two-product recovery 0.903614 (hand calculation of plan 005);
- size distribution and crusher: the plan's crusher product (0.12, 0.3816, 0.4984) and the Swebrec x80 = 0.70711 m;
- chain: the three-class chain of the unit tests (crusher product passing 1.0, 0.88, 0.4984).
API as in the unit tests of T-005-010 to T-005-044.
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest

KWH = 3600.0

pytestmark = [pytest.mark.pyodide, pytest.mark.req("NFR-005-03")]


def _c():
    return importlib.import_module("minephys.comminution")


@pytest.mark.oracle("worked-example", "mcivor2016bondgmsg p. 11: 10.0 kWh/st = 11.0 kWh/t")
def test_nfr_005_03_bond_family() -> None:
    c = _c()
    wi = c.bond_ball_mill_work_index(106e-6, 1.825e-3, 2746.1e-6, 79.7e-6) / KWH
    assert abs(wi - 11.0) <= 0.05
    w = c.bond_energy(15.0 * KWH, 2.0e-3, 1.5e-4) / KWH
    np.testing.assert_allclose(w, 8.893347, rtol=0, atol=6e-7)


@pytest.mark.oracle("worked-example", "gmsg2016morrell Annex C: Wb = 8.4 kWh/t, Wa (100 mm, pebble crusher) = 9.6 kWh/t")
def test_nfr_005_03_morrell_family() -> None:
    c = _c()
    assert abs(c.morrell_tumbling_fine(18.8 * KWH, 106e-6) / KWH - 8.4) <= 0.05
    assert abs(c.morrell_tumbling_coarse(19.4 * KWH, 0.1, True) / KWH - 9.6) <= 0.05


@pytest.mark.oracle("analytical", "three-class batch grinding equation and one perfectly mixed tank")
def test_nfr_005_03_population_balance_family() -> None:
    c = _c()
    s = np.array([0.5, 0.3, 0.0]) / 60.0
    b = np.array([[0.0, 0.0, 0.0], [0.6, 0.0, 0.0], [0.4, 1.0, 0.0]])
    out = c.pbm_batch_grinding(np.array([1.0, 0.0, 0.0]), s, b, [120.0])[0]
    m1 = math.exp(-s[0] * 120.0)
    m2 = 0.6 * s[0] / (s[1] - s[0]) * (math.exp(-s[0] * 120.0) - math.exp(-s[1] * 120.0))
    np.testing.assert_allclose(out, [m1, m2, 1.0 - m1 - m2], rtol=1e-10, atol=1e-13)
    tank = c.pbm_continuous_mill(np.array([1.0, 0.0, 0.0]), s, b, 120.0)
    np.testing.assert_allclose(tank, [0.5, 0.1875, 0.3125], rtol=1e-12, atol=1e-15)


@pytest.mark.oracle("hand-calculation", "plan 005: 0.893936 first order, 0.903614 two-product recovery")
def test_nfr_005_03_flotation_family() -> None:
    c = _c()
    np.testing.assert_allclose(c.flotation_first_order(0.9, 1.0 / 60.0, 300.0), 0.893936, rtol=0, atol=6e-7)
    np.testing.assert_allclose(c.klimpel_recovery(0.9, 1.0 / 60.0, 300.0), 0.721213, rtol=0, atol=6e-7)
    _, recovery = c.two_product_recovery(0.01, 0.25, 0.001)
    np.testing.assert_allclose(recovery, 0.903614, rtol=0, atol=6e-7)


@pytest.mark.oracle("analytical", "crusher balance (0.12, 0.3816, 0.4984) and the Swebrec closed-form x80 = 0.70711 m")
def test_nfr_005_03_size_distribution_and_crusher_family() -> None:
    c = _c()
    p = c.crusher_matrix_model(
        np.array([0.6, 0.3, 0.1]),
        np.array([0.8, 0.4, 0.0]),
        np.array([[0.0, 0.0, 0.0], [0.7, 0.0, 0.0], [0.3, 1.0, 0.0]]),
    )
    np.testing.assert_allclose(p, [0.12, 0.3816, 0.4984], rtol=1e-12, atol=1e-15)
    sizes = np.geomspace(2.0, 10e-6, 400)
    passing = 1.0 / (1.0 + (np.log(2.0 / sizes) / math.log(2.0 / 0.25)) ** 2.0)
    np.testing.assert_allclose(c.passing_size(sizes, passing), 0.70711, rtol=2e-3)


@pytest.mark.oracle("hand-calculation", "three-class chain with the plan's crusher")
def test_nfr_005_03_chain_family() -> None:
    c = _c()
    res = c.mine_to_mill_chain(
        sizes=np.array([0.3, 0.1, 0.03]),
        blast_passing=np.array([1.0, 0.4, 0.1]),
        classification=np.array([0.8, 0.4, 0.0]),
        breakage=np.array([[0.0, 0.0, 0.0], [0.7, 0.0, 0.0], [0.3, 1.0, 0.0]]),
        target_p80=2e-4,
        installed_power=2.0e6,
        energy_model="bond",
        work_index=12.0 * KWH,
        fines_size=0.03,
    )
    np.testing.assert_allclose(res.product_passing, [1.0, 0.88, 0.4984], rtol=1e-12, atol=1e-15)
    assert res.throughput > 0.0

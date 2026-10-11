"""T-005-044 (FR-005-30, FR-005-32, FR-005-33): the mine-to-mill chain, composed by hand from the component relations.

Expected public API (`minephys.comminution`):
    mine_to_mill_chain(sizes, blast_passing, classification, breakage, target_p80, installed_power, energy_model, *,
                       work_index=None, mia=None, mib=None, fines_size)  -> ChainResult
with sizes the coarse-to-fine upper class sizes [m] and blast_passing the cumulative passing of the blast at those sizes;
`classification` and `breakage` as in `crusher_matrix_model`; `target_p80` the final grind [m]; `installed_power` [W];
`energy_model` "bond" (needs `work_index` [J/kg]) or "morrell" (needs `mia` and `mib` [J/kg]; no pebble crusher, K1 = 1);
`fines_size` [m] is a grid size here. The names of the index keywords are those of the component functions (the plan lists only the
result fields) and are recorded as an assumption in the red-phase report. `ChainResult` has the attributes
    product_passing (cumulative passing of the crusher product at `sizes`), f80 [m], fines_fraction, specific_energy [J/kg],
    throughput [kg/s] = installed_power / specific_energy.
The chain composes: class_masses -> crusher_matrix_model -> cumulative_passing -> passing_size -> (bond_energy | morrell_tumbling_coarse
+ morrell_tumbling_fine) -> power / energy.

Oracles
- the composition written out in this file with plain NumPy/`math` (steady-state balance by forward substitution, log-log
  interpolation, the closed forms of Bond and Morrell), compared at rtol 1e-12 (FR-005-30);
- analytical: with an identity crusher (C = 0) and the Bond model the chain equals bond_energy(Wi, x80, P80) with the Swebrec
  closed form x80 = xmax (x50/xmax)^(0.25^(1/b)) on a 400-point grid (rtol 2e-3, interpolation error <= 4.3e-4, plan 005);
- validity warnings of FR-005-32/33 (`ValidityWarning` named `p80` with the row id) are raised through the composed functions.
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


def _hand_crusher_product(feed: np.ndarray, cl: np.ndarray, b: np.ndarray) -> np.ndarray:
    n = len(feed)
    x = np.zeros(n)
    for i in range(n):  # x = f + B C x, strictly lower triangular B
        x[i] = feed[i] + sum(b[i, j] * cl[j] * x[j] for j in range(i))
    return (1.0 - cl) * x


def _hand_loglog_size(sizes: np.ndarray, passing: np.ndarray, fraction: float) -> float:
    for i in range(len(sizes) - 1):
        if passing[i] >= fraction >= passing[i + 1]:
            lx0, lx1 = math.log(sizes[i]), math.log(sizes[i + 1])
            lp0, lp1 = math.log(passing[i]), math.log(passing[i + 1])
            return math.exp(lx0 + (math.log(fraction) - lp0) * (lx1 - lx0) / (lp1 - lp0))
    raise AssertionError("fraction outside the curve")


def _hand_chain(sizes: np.ndarray, blast: np.ndarray, cl: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, float]:
    masses = np.r_[blast[:-1] - blast[1:], blast[-1]]  # class_masses
    product = _hand_crusher_product(masses, cl, b)
    passing = np.cumsum(product[::-1])[::-1]  # cumulative_passing
    return passing, _hand_loglog_size(sizes, passing, 0.8)


def _bond_hand(wi: float, f80_m: float, p80_m: float) -> float:
    return 10.0 * wi * (1.0 / math.sqrt(p80_m * 1e6) - 1.0 / math.sqrt(f80_m * 1e6))


def _morrell_hand(mia: float, mib: float, f80_m: float, p80_m: float) -> float:
    f = lambda x: -(0.295 + x / 1e6)  # noqa: E731
    g = lambda x: x ** f(x)  # noqa: E731
    x1, p = f80_m * 1e6, p80_m * 1e6
    return mia * 4.0 * (g(750.0) - g(x1)) + mib * 4.0 * (g(p) - g(750.0))


@pytest.mark.req("FR-005-30")
@pytest.mark.oracle("hand-calculation", "the composition class_masses -> crusher -> cumulative_passing -> passing_size -> Bond -> power/energy")
def test_fr_005_30_bond_chain_equals_the_hand_composition() -> None:
    c = _c()
    wi, p80, power = 14.0 * KWH, 1.5e-4, 5.0e6
    res = c.mine_to_mill_chain(
        sizes=SIZES,
        blast_passing=BLAST,
        classification=CLASSIFICATION,
        breakage=BREAKAGE,
        target_p80=p80,
        installed_power=power,
        energy_model="bond",
        work_index=wi,
        fines_size=0.05,
    )
    passing, f80 = _hand_chain(SIZES, BLAST, CLASSIFICATION, BREAKAGE)
    energy = _bond_hand(wi, f80, p80)
    np.testing.assert_allclose(res.product_passing, passing, rtol=1e-12, atol=1e-15)
    np.testing.assert_allclose(res.f80, f80, rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.fines_fraction, passing[3], rtol=1e-12, atol=0)  # P(0.05 m)
    np.testing.assert_allclose(res.specific_energy, energy, rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.throughput, power / energy, rtol=1e-12, atol=0)
    assert np.isfinite(res.throughput) and res.throughput > 0.0
    # mass is conserved by the crusher: the product curve starts at the blast curve's top value
    np.testing.assert_allclose(res.product_passing[0], BLAST[0], rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-30")
@pytest.mark.oracle("hand-calculation", "Morrell model: Wa(F80) + Wb(P80) from the crusher product")
def test_fr_005_30_morrell_chain_equals_the_hand_composition() -> None:
    c = _c()
    mia, mib, p80, power = 19.4 * KWH, 18.8 * KWH, 106e-6, 8.0e6
    res = c.mine_to_mill_chain(
        sizes=SIZES,
        blast_passing=BLAST,
        classification=CLASSIFICATION,
        breakage=BREAKAGE,
        target_p80=p80,
        installed_power=power,
        energy_model="morrell",
        mia=mia,
        mib=mib,
        fines_size=0.025,
    )
    passing, f80 = _hand_chain(SIZES, BLAST, CLASSIFICATION, BREAKAGE)
    energy = _morrell_hand(mia, mib, f80, p80)
    np.testing.assert_allclose(res.f80, f80, rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.specific_energy, energy, rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.throughput, power / energy, rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.fines_fraction, passing[4], rtol=1e-12, atol=0)
    assert res.f80 > 750e-6  # the Morrell coarse term needs a feed coarser than 750 um


@pytest.mark.req("FR-005-30")
@pytest.mark.oracle("hand-calculation", "three-class case with the plan's crusher: f = (0.6, 0.3, 0.1) as a blast curve")
def test_fr_005_30_three_class_case() -> None:
    c = _c()
    sizes = np.array([0.3, 0.1, 0.03])
    blast = np.array([1.0, 0.4, 0.1])  # class masses (0.6, 0.3, 0.1)
    res = c.mine_to_mill_chain(
        sizes=sizes,
        blast_passing=blast,
        classification=np.array([0.8, 0.4, 0.0]),
        breakage=np.array([[0.0, 0.0, 0.0], [0.7, 0.0, 0.0], [0.3, 1.0, 0.0]]),
        target_p80=2e-4,
        installed_power=2.0e6,
        energy_model="bond",
        work_index=12.0 * KWH,
        fines_size=0.03,
    )
    # crusher product (plan 005 hand values) 0.12, 0.3816, 0.4984 -> cumulative passing 1.0, 0.88, 0.4984
    np.testing.assert_allclose(res.product_passing, [1.0, 0.88, 0.4984], rtol=1e-12, atol=1e-15)
    f80 = _hand_loglog_size(sizes, np.array([1.0, 0.88, 0.4984]), 0.8)
    np.testing.assert_allclose(res.f80, f80, rtol=1e-12, atol=0)
    np.testing.assert_allclose(res.fines_fraction, 0.4984, rtol=1e-12, atol=0)


@pytest.mark.req("FR-005-30")
@pytest.mark.oracle("analytical", "identity crusher + Bond = Bond's law at the closed-form Swebrec x80 (x50 = 0.25, xmax = 2, b = 2)")
def test_fr_005_30_identity_crusher_matches_bond_at_the_swebrec_x80() -> None:
    c = _c()
    x50, xmax, b = 0.25, 2.0, 2.0
    sizes = np.geomspace(xmax, 10e-6, 400)
    passing = 1.0 / (1.0 + (np.log(xmax / sizes) / math.log(xmax / x50)) ** b)
    wi, p80, power = 15.0 * KWH, 1.0e-4, 1.0e7
    res = c.mine_to_mill_chain(
        sizes=sizes,
        blast_passing=passing,
        classification=np.zeros(400),
        breakage=np.zeros((400, 400)),
        target_p80=p80,
        installed_power=power,
        energy_model="bond",
        work_index=wi,
        fines_size=float(sizes[200]),
    )
    x80 = xmax * (x50 / xmax) ** (0.25 ** (1.0 / b))  # 0.70711 m
    np.testing.assert_allclose(res.f80, x80, rtol=2e-3, atol=0)
    np.testing.assert_allclose(res.specific_energy, _bond_hand(wi, x80, p80), rtol=2e-3, atol=0)
    np.testing.assert_allclose(res.throughput, power / _bond_hand(wi, x80, p80), rtol=2e-3, atol=0)
    np.testing.assert_allclose(res.product_passing, passing, rtol=1e-12, atol=1e-15)  # C = 0 returns the feed exactly


@pytest.mark.req("FR-005-30")
def test_fr_005_30_result_is_deterministic_and_inputs_are_not_modified() -> None:
    c = _c()
    args = dict(
        sizes=SIZES.copy(),
        blast_passing=BLAST.copy(),
        classification=CLASSIFICATION.copy(),
        breakage=BREAKAGE.copy(),
        target_p80=1.5e-4,
        installed_power=5.0e6,
        energy_model="bond",
        work_index=14.0 * KWH,
        fines_size=0.05,
    )
    before = {k: v.copy() for k, v in args.items() if isinstance(v, np.ndarray)}
    a, b = c.mine_to_mill_chain(**args), c.mine_to_mill_chain(**args)
    assert np.array_equal(a.product_passing, b.product_passing) and a.throughput == b.throughput
    for k, v in before.items():
        assert np.array_equal(args[k], v)


def _bond_call(c, p80: float) -> object:
    return c.mine_to_mill_chain(
        sizes=SIZES,
        blast_passing=BLAST,
        classification=CLASSIFICATION,
        breakage=BREAKAGE,
        target_p80=p80,
        installed_power=5.0e6,
        energy_model="bond",
        work_index=14.0 * KWH,
        fines_size=0.05,
    )


def _morrell_call(c, p80: float) -> object:
    return c.mine_to_mill_chain(
        sizes=SIZES,
        blast_passing=BLAST,
        classification=CLASSIFICATION,
        breakage=BREAKAGE,
        target_p80=p80,
        installed_power=5.0e6,
        energy_model="morrell",
        mia=19.4 * KWH,
        mib=18.8 * KWH,
        fines_size=0.05,
    )


@pytest.mark.req("FR-005-32")
@pytest.mark.knowledge("bond_min_product_size")
def test_fr_005_32_bond_chain_warns_below_70_um_and_still_returns() -> None:
    c = _c()
    warning = _warning_class()
    with pytest.warns(warning) as rec:
        res = _bond_call(c, 50e-6)
    msg = next(r.message for r in rec if isinstance(r.message, warning) and getattr(r.message, "row", None) == "bond_min_product_size")
    assert msg.argument == "p80"
    _, f80 = _hand_chain(SIZES, BLAST, CLASSIFICATION, BREAKAGE)
    np.testing.assert_allclose(res.specific_energy, _bond_hand(14.0 * KWH, f80, 50e-6), rtol=1e-12, atol=0)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _bond_call(c, 70e-6)  # the limit itself and anything coarser do not warn


@pytest.mark.req("FR-005-33")
@pytest.mark.knowledge("morrell_fine_grind_limit")
def test_fr_005_33_morrell_chain_warns_below_45_um_and_still_returns() -> None:
    c = _c()
    warning = _warning_class()
    with pytest.warns(warning) as rec:
        res = _morrell_call(c, 40e-6)
    msg = next(r.message for r in rec if isinstance(r.message, warning) and getattr(r.message, "row", None) == "morrell_fine_grind_limit")
    assert msg.argument == "p80"
    _, f80 = _hand_chain(SIZES, BLAST, CLASSIFICATION, BREAKAGE)
    np.testing.assert_allclose(res.specific_energy, _morrell_hand(19.4 * KWH, 18.8 * KWH, f80, 40e-6), rtol=1e-12, atol=0)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _morrell_call(c, 45e-6)

"""T-005-044 (P-005-15, FR-005-30): metamorphic relations of `mine_to_mill_chain`.

Public API under test (`minephys.comminution`): `mine_to_mill_chain(...)` returning `ChainResult(product_passing, f80,
fines_fraction, specific_energy, throughput)`; signature and assumptions as in tests/unit/test_t_005_044_chain.py.

Relations
- power scaling: installed_power x lambda scales the throughput by lambda and leaves F80, the specific energy and the product
  curve unchanged (TC-1);
- identity crusher + Bond = Bond's law at the Swebrec closed-form x80 = xmax (x50/xmax)^(0.25^(1/b)) (Swebrec x50 in
  [0.05, 1] m, xmax in [2 x50, 5] m, b in [1, 4], 400 log-spaced sizes from 10 um to xmax; rtol 2e-3 because of the log-log
  interpolation error <= 4.3e-4, hand-checked in plan 005);
- mass conservation: the crusher conserves mass, so the product curve starts at the feed curve's top value;
- a finer crusher (every classification probability raised) can only move mass to finer classes: the product curve does not
  decrease anywhere, F80 does not increase, the specific energy does not increase and the throughput does not decrease.
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

KWH = 3600.0
CI = settings(max_examples=200, deadline=None)
SEEDS = st.integers(0, 2**32 - 1)


def _c():
    return importlib.import_module("minephys.comminution")


def swebrec(x50: float, xmax: float, b: float, n: int = 400) -> tuple[np.ndarray, np.ndarray]:
    sizes = np.geomspace(xmax, 10e-6, n)
    return sizes, 1.0 / (1.0 + (np.log(xmax / sizes) / math.log(xmax / x50)) ** b)


def _call(c, sizes, passing, cl, br, **over):
    kw = dict(
        sizes=sizes,
        blast_passing=passing,
        classification=cl,
        breakage=br,
        target_p80=1.2e-4,
        installed_power=6.0e6,
        energy_model="bond",
        work_index=13.0 * KWH,
        fines_size=float(sizes[len(sizes) // 2]),
    )
    kw.update(over)
    return c.mine_to_mill_chain(**kw)


def crusher(n: int, seed: int, max_c: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    cl = rng.random(n) * max_c
    cl[-1] = 0.0
    b = np.zeros((n, n))
    for j in range(n - 1):
        w = rng.random(n - 1 - j) + 1e-3
        b[j + 1 :, j] = w / w.sum()
    return cl, b


def hand_f80(sizes: np.ndarray, passing: np.ndarray) -> float:
    for i in range(len(sizes) - 1):
        if passing[i] >= 0.8 >= passing[i + 1]:
            lx0, lx1 = math.log(sizes[i]), math.log(sizes[i + 1])
            lp0, lp1 = math.log(passing[i]), math.log(passing[i + 1])
            return math.exp(lx0 + (math.log(0.8) - lp0) * (lx1 - lx0) / (lp1 - lp0))
    raise AssertionError("no 80 % passing size on the grid")


def hand_product_passing(passing: np.ndarray, cl: np.ndarray, b: np.ndarray) -> np.ndarray:
    m = np.r_[passing[:-1] - passing[1:], passing[-1]]
    x = np.zeros(len(m))
    for i in range(len(m)):
        x[i] = m[i] + sum(b[i, j] * cl[j] * x[j] for j in range(i))
    return np.cumsum(((1.0 - cl) * x)[::-1])[::-1]


@pytest.mark.req("P-005-15")
@pytest.mark.oracle("analytical", "throughput = installed_power / specific_energy is linear in the power")
@CI
@given(
    x50=st.floats(0.05, 1.0),
    ratio=st.floats(2.0, 5.0),
    b=st.floats(1.0, 4.0),
    lam=st.floats(math.log(1e-3), math.log(1e3)).map(math.exp),
)
def test_p_005_15_power_scaling(x50: float, ratio: float, b: float, lam: float) -> None:
    c = _c()
    xmax = min(x50 * ratio, 5.0)
    assume(xmax >= 2.0 * x50)
    sizes, passing = swebrec(x50, xmax, b)
    z = np.zeros(400)
    base = _call(c, sizes, passing, z, np.zeros((400, 400)))
    scaled = _call(c, sizes, passing, z, np.zeros((400, 400)), installed_power=6.0e6 * lam)
    np.testing.assert_allclose(scaled.throughput, lam * base.throughput, rtol=1e-12, atol=0)
    assert scaled.f80 == base.f80 and scaled.specific_energy == base.specific_energy
    assert np.array_equal(scaled.product_passing, base.product_passing)


@pytest.mark.req("P-005-15")
@pytest.mark.oracle("analytical", "Swebrec closed form x80 = xmax (x50/xmax)^(0.25^(1/b)); Bond's law at that size")
@CI
@given(x50=st.floats(0.05, 1.0), ratio=st.floats(2.0, 5.0), b=st.floats(1.0, 4.0))
def test_p_005_15_identity_crusher_equals_bond_at_the_swebrec_x80(x50: float, ratio: float, b: float) -> None:
    c = _c()
    xmax = min(x50 * ratio, 5.0)
    assume(xmax >= 2.0 * x50)
    sizes, passing = swebrec(x50, xmax, b)
    wi, p80 = 13.0 * KWH, 1.2e-4
    res = _call(c, sizes, passing, np.zeros(400), np.zeros((400, 400)), work_index=wi, target_p80=p80)
    x80 = xmax * (x50 / xmax) ** (0.25 ** (1.0 / b))
    w = 10.0 * wi * (1.0 / math.sqrt(p80 * 1e6) - 1.0 / math.sqrt(x80 * 1e6))
    np.testing.assert_allclose(res.f80, x80, rtol=2e-3, atol=0)
    np.testing.assert_allclose(res.specific_energy, w, rtol=2e-3, atol=0)


@pytest.mark.req("P-005-15")
@CI
@given(n=st.integers(8, 40), seed=SEEDS)
def test_p_005_15_chain_equals_the_hand_composition_on_random_crushers(n: int, seed: int) -> None:
    c = _c()
    sizes = np.geomspace(1.0, 1e-5, n)
    passing = 1.0 / (1.0 + (np.log(1.0 / sizes) / math.log(1.0 / 0.2)) ** 1.5)
    cl, b = crusher(n, seed)
    product = hand_product_passing(passing, cl, b)
    assume(product[-1] < 0.79)  # the 80 % passing size must exist on the grid
    assume(hand_f80(sizes, product) > 3e-4)  # and stay coarser than the 120 um target
    res = _call(c, sizes, passing, cl, b)
    np.testing.assert_allclose(res.product_passing, product, rtol=1e-11, atol=1e-14)
    np.testing.assert_allclose(res.product_passing[0], passing[0], rtol=1e-12, atol=0)  # mass conservation


@pytest.mark.req("P-005-15")
@pytest.mark.oracle("analytical", "raising the breakage probabilities moves mass to finer classes only")
@CI
@given(n=st.integers(8, 40), seed=SEEDS, bump=st.floats(0.0, 0.4))
def test_p_005_15_a_finer_crusher_gives_a_finer_product_and_a_higher_throughput(n: int, seed: int, bump: float) -> None:
    c = _c()
    sizes = np.geomspace(1.0, 1e-5, n)
    passing = 1.0 / (1.0 + (np.log(1.0 / sizes) / math.log(1.0 / 0.2)) ** 1.5)
    cl, b = crusher(n, seed, max_c=0.5)
    cl_more = cl.copy()
    cl_more[:-1] = np.minimum(1.0, cl[:-1] + bump)
    prod_more = hand_product_passing(passing, cl_more, b)
    assume(prod_more[-1] < 0.79)
    assume(hand_f80(sizes, prod_more) > 3e-4)
    low = _call(c, sizes, passing, cl, b)
    high = _call(c, sizes, passing, cl_more, b)
    assert np.all(high.product_passing >= low.product_passing - 1e-12)
    assert high.f80 <= low.f80 * (1.0 + 1e-12)
    assert high.specific_energy <= low.specific_energy * (1.0 + 1e-12)
    assert high.throughput >= low.throughput * (1.0 - 1e-12)

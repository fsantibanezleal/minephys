"""T-005-012 (P-005-03, P-005-04, P-005-05): property and metamorphic tests of the Morrell relation.

Public API under test (`minephys.comminution`): `morrell_energy`, `morrell_tumbling_coarse`, `morrell_tumbling_fine`,
`morrell_crusher` (signatures as in tests/unit/test_t_005_012_morrell.py).

Metamorphic relations: path additivity (P-005-03), Morrell consistency Wa + Wb = W and Wc(Sc = K2 = 1) = W (P-005-04),
linearity in the index and strict monotonicity in the product size (P-005-05).

Generators (spec 005 section 4): indices log-uniform in [3,600, 3.6e5] J/kg, 200 examples. Where a relation sums terms
that cancel at the 750 um boundary (P-005-04) the sizes keep a factor 2 away from it, so that the summation error stays
within the stated rtol 1e-11 (the cancelling term g(750) is about 0.14 while the sum is at least 0.06). Validity
warnings (FR-005-33) are not under test here and are silenced.
"""

from __future__ import annotations

import importlib
import math
import warnings

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)


def _c():
    return importlib.import_module("minephys.comminution")


def sizes(lo: float, hi: float) -> st.SearchStrategy[float]:
    return st.floats(math.log(lo), math.log(hi)).map(math.exp)


INDICES = st.floats(math.log(3.6e3), math.log(3.6e5)).map(math.exp)


@pytest.mark.req("P-005-03")
@pytest.mark.oracle("analytical", "the Morrell relation telescopes: W(F->P) = W(F->M) + W(M->P)")
@CI
@given(mi=INDICES, p=sizes(1e-5, 1e-3), r1=st.floats(1.2, 30.0), r2=st.floats(1.2, 30.0))
def test_p_005_03_path_additivity(mi: float, p: float, r1: float, r2: float) -> None:
    c = _c()
    m, f = p * r1, p * r1 * r2
    whole = c.morrell_energy(mi, f, p)
    parts = c.morrell_energy(mi, f, m) + c.morrell_energy(mi, m, p)
    np.testing.assert_allclose(parts, whole, rtol=1e-11, atol=0)


@pytest.mark.req("P-005-04")
@pytest.mark.oracle("analytical", "Wa + Wb = W for Mia = Mib and K1 = 1; Wc with Sc = K2 = 1 equals W")
@CI
@given(mi=INDICES, x1=sizes(1.5e-3, 1.0), p80=sizes(1e-5, 3.75e-4))
def test_p_005_04_tumbling_terms_sum_to_the_single_relation(mi: float, x1: float, p80: float) -> None:
    c = _c()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wa = c.morrell_tumbling_coarse(mi, x1, False)
        wb = c.morrell_tumbling_fine(mi, p80)
    np.testing.assert_allclose(wa + wb, c.morrell_energy(mi, x1, p80), rtol=1e-11, atol=0)


@pytest.mark.req("P-005-04")
@CI
@given(mi=INDICES, p=sizes(1e-5, 1e-2), r=st.floats(1.2, 100.0))
def test_p_005_04_crusher_with_unit_factors_equals_the_single_relation(mi: float, p: float, r: float) -> None:
    c = _c()
    x1 = p * r
    # tertiary stage: Sc = 1; closed circuit: K2 = 1
    got = c.morrell_crusher(mi, x1, p, True, "tertiary")
    np.testing.assert_allclose(got, c.morrell_energy(mi, x1, p), rtol=1e-12, atol=0)
    pebble = c.morrell_crusher(mi, x1, p, True, "pebble")
    np.testing.assert_allclose(pebble, got, rtol=1e-12, atol=0)


@pytest.mark.req("P-005-05")
@pytest.mark.oracle("analytical", "W is linear in Mi and increases strictly as the product size decreases")
@CI
@given(
    mi=INDICES,
    lam=st.floats(math.log(1e-3), math.log(1e3)).map(math.exp),
    p=sizes(1e-5, 0.02),
    r=st.floats(1.2, 50.0),
)
def test_p_005_05_linearity_in_the_index(mi: float, lam: float, p: float, r: float) -> None:
    c = _c()
    f = p * r
    w = c.morrell_energy(mi, f, p)
    np.testing.assert_allclose(c.morrell_energy(lam * mi, f, p), lam * w, rtol=1e-12, atol=0)


@pytest.mark.req("P-005-05")
@CI
@given(mi=INDICES, f=sizes(1e-3, 1.0), r1=st.floats(1.05, 20.0), r2=st.floats(1.05, 20.0))
def test_p_005_05_energy_increases_as_the_product_gets_finer(mi: float, f: float, r1: float, r2: float) -> None:
    c = _c()
    p_coarse = f / (r1 * 1.5)
    p_fine = p_coarse / r2
    assert c.morrell_energy(mi, f, p_fine) > c.morrell_energy(mi, f, p_coarse) > 0.0


@pytest.mark.req("P-005-05")
@CI
@given(mi=INDICES, p=sizes(1e-5, 2e-3), r1=st.floats(1.05, 20.0), r2=st.floats(1.05, 20.0))
def test_p_005_05_energy_decreases_as_the_feed_approaches_the_product(mi: float, p: float, r1: float, r2: float) -> None:
    c = _c()
    mid = p * r1
    feed = mid * r2
    assert c.morrell_energy(mi, feed, p) > c.morrell_energy(mi, mid, p)

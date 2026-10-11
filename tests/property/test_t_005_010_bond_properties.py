"""T-005-010 (P-005-01, P-005-02, P-005-03): property and metamorphic tests of Bond's law.

Public API under test (`minephys.comminution`): `bond_energy(work_index, f80, p80)` and
`bond_operating_work_index(specific_energy, f80, p80)` (sizes in m, energies in J/kg).

Generators follow spec 005 section 4: sizes log-uniform in [10 um, 1 m] (restricted below where a relation needs it),
indices log-uniform in [3,600, 3.6e5] J/kg, 200 examples (`thresholds.yaml` `property_tests.ci_examples_per_test`).
Validity warnings below 70 um (FR-005-32) are not under test here and are silenced.

Metamorphic relations: strict monotonicity in F80 and P80 (P-005-01), homogeneity in Wi and the inverse
relation (P-005-02), path additivity W(F->P) = W(F->M) + W(M->P) (P-005-03), and the closed form itself.
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


def sizes(lo: float = 1e-5, hi: float = 1.0) -> st.SearchStrategy[float]:
    return st.floats(math.log(lo), math.log(hi)).map(math.exp)


INDICES = st.floats(math.log(3.6e3), math.log(3.6e5)).map(math.exp)


@pytest.mark.req("P-005-01")
@pytest.mark.oracle("analytical", "strict monotonicity of W = 10 Wi (1/sqrt(P80) - 1/sqrt(F80))")
@CI
@given(wi=INDICES, p=sizes(1e-5, 0.1), r1=st.floats(1.01, 50.0), r2=st.floats(1.01, 50.0))
def test_p_005_01_energy_decreases_as_feed_approaches_product(wi: float, p: float, r1: float, r2: float) -> None:
    c = _c()
    mid, feed = p * r1, p * r1 * r2
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert c.bond_energy(wi, feed, p) > c.bond_energy(wi, mid, p)  # coarser feed needs more energy
        assert c.bond_energy(wi, mid, p) > 0.0


@pytest.mark.req("P-005-01")
@CI
@given(wi=INDICES, f=sizes(1e-3, 1.0), r=st.floats(1.01, 50.0))
def test_p_005_01_energy_increases_as_product_gets_finer(wi: float, f: float, r: float) -> None:
    c = _c()
    p_coarse = f / 2.0
    p_fine = p_coarse / r
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert c.bond_energy(wi, f, p_fine) > c.bond_energy(wi, f, p_coarse)


@pytest.mark.req("P-005-02")
@pytest.mark.oracle("analytical", "W is homogeneous of degree 1 in Wi; Wio inverts W")
@CI
@given(
    wi=INDICES,
    lam=st.floats(math.log(1e-3), math.log(1e3)).map(math.exp),
    p=sizes(1e-5, 0.1),
    ratio=st.floats(1.5, 1e3),
)
def test_p_005_02_scaling_and_inverse(wi: float, lam: float, p: float, ratio: float) -> None:
    c = _c()
    f = p * ratio
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        w = c.bond_energy(wi, f, p)
        np.testing.assert_allclose(c.bond_energy(lam * wi, f, p), lam * w, rtol=1e-12, atol=0)
        np.testing.assert_allclose(c.bond_operating_work_index(w, f, p), wi, rtol=1e-12, atol=0)
        np.testing.assert_allclose(
            c.bond_operating_work_index(lam * w, f, p), lam * wi, rtol=1e-12, atol=0
        )


@pytest.mark.req("P-005-03")
@pytest.mark.oracle("analytical", "Bond's law telescopes: W(F->P) = W(F->M) + W(M->P)")
@CI
@given(wi=INDICES, p=sizes(1e-5, 0.05), r1=st.floats(1.2, 30.0), r2=st.floats(1.2, 30.0))
def test_p_005_03_path_additivity(wi: float, p: float, r1: float, r2: float) -> None:
    c = _c()
    m = p * r1
    f = m * r2
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        whole = c.bond_energy(wi, f, p)
        parts = c.bond_energy(wi, f, m) + c.bond_energy(wi, m, p)
    np.testing.assert_allclose(parts, whole, rtol=1e-11, atol=0)  # three evaluations summed (spec: TC-1 x 10)


@pytest.mark.req("P-005-01")
@pytest.mark.req("P-005-02")
@CI
@given(wi=INDICES, f=sizes(1e-3, 1.0), p=sizes(1e-5, 5e-4))
def test_closed_form_agreement_over_the_generator_domain(wi: float, f: float, p: float) -> None:
    c = _c()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        got = c.bond_energy(wi, f, p)
    expected = 10.0 * wi * (1.0 / math.sqrt(p * 1e6) - 1.0 / math.sqrt(f * 1e6))
    np.testing.assert_allclose(got, expected, rtol=1e-12, atol=0)

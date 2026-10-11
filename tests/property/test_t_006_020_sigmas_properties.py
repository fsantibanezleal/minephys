"""T-006-020 (P-006-09): properties of the ISC3 dispersion coefficients.

Public API under test (`minephys.environment`): `pasquill_sigmas(x, stability_class, terrain="rural")` -> (sigma_y, sigma_z) [m]
(see tests/unit/test_t_006_020_sigmas.py). x log-uniform in [10 m, 100 km], both terrains, 200 examples; urban near-field
warnings (FR-006-10) are not under test here and are silenced.

Relations (P-006-09)
- sigma_y is strictly increasing in x for every class and terrain;
- sigma_z is non-decreasing in x except at the band edges of ISC3 Table 1-2, where a drop is at most 1e-4 relative
  (the spec states the largest drop is 9e-5, hand-checked);
- at any fixed x both are ordered A >= B >= C >= D >= E >= F.
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
X = st.floats(math.log(10.0), math.log(100_000.0)).map(math.exp)
TERRAIN = st.sampled_from(["rural", "urban"])
CLASSES = "ABCDEF"


def _f():
    return importlib.import_module("minephys.environment").pasquill_sigmas


def _quiet(x, cls, terrain):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return _f()(x, cls, terrain)


@pytest.mark.req("P-006-09")
@pytest.mark.oracle("analytical", "sigma_y grows with distance for every stability class and both terrains")
@CI
@given(x=X, r=st.floats(1.001, 5.0), cls=st.sampled_from(list(CLASSES)), terrain=TERRAIN)
def test_p_006_09_sigma_y_strictly_increasing(x: float, r: float, cls: str, terrain: str) -> None:
    x2 = min(x * r, 100_000.0)
    if x2 <= x:
        return
    assert _quiet(x2, cls, terrain)[0] > _quiet(x, cls, terrain)[0]


@pytest.mark.req("P-006-09")
@CI
@given(x=X, r=st.floats(1.0005, 5.0), cls=st.sampled_from(list(CLASSES)), terrain=TERRAIN)
def test_p_006_09_sigma_z_non_decreasing_up_to_the_band_edge_drop(x: float, r: float, cls: str, terrain: str) -> None:
    x2 = min(x * r, 100_000.0)
    if x2 <= x:
        return
    z1, z2 = _quiet(x, cls, terrain)[1], _quiet(x2, cls, terrain)[1]
    assert z2 >= z1 * (1.0 - 1e-4)  # a drop is possible only across a Table 1-2 band edge and stays below 1e-4


@pytest.mark.req("P-006-09")
@pytest.mark.oracle("analytical", "stability ordering A >= B >= C >= D >= E >= F at every distance")
@CI
@given(x=X, terrain=TERRAIN)
def test_p_006_09_stability_classes_are_ordered(x: float, terrain: str) -> None:
    ys, zs = zip(*(_quiet(x, c, terrain) for c in CLASSES), strict=True)
    for a, b in zip(ys, ys[1:], strict=False):
        assert a >= b * (1.0 - 1e-12)
    for a, b in zip(zs, zs[1:], strict=False):
        assert a >= b * (1.0 - 1e-12)


@pytest.mark.req("P-006-09")
@CI
@given(x=X, cls=st.sampled_from(list(CLASSES)), terrain=TERRAIN)
def test_sigmas_are_positive_finite_float64_scalars(x: float, cls: str, terrain: str) -> None:
    sy, sz = _quiet(x, cls, terrain)
    assert isinstance(sy, np.float64) and isinstance(sz, np.float64)
    assert 0.0 < sy < 1e8 and 0.0 < sz < 1e8  # finite and positive (the cap applies to the rural classes A, B and C only)

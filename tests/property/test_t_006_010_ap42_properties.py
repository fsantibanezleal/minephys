"""T-006-010 (P-006-01, P-006-02, P-006-03): properties of the AP-42 emission factor.

Public API under test (`minephys.environment`): `ap42_unpaved_emission_factor(silt_fraction, mean_weight, size_class, ...)`
(see tests/unit/test_t_006_010_ap42.py).
Generators (spec 006 section 4): silt fraction in [0.018, 0.252]; weight in [1,814, 263,083] kg and, for the extrapolation
checks, up to 400,000 kg; 200 examples. Validity warnings (FR-006-03) are not under test here and are silenced.

Relations
- P-006-01 power-law scaling: E(lambda s, W) = lambda^a E(s, W), E(s, lambda W) = lambda^b E(s, W) (lambda in [0.5, 2]); E is
  strictly increasing in silt and in weight (TC-1 and strict inequality);
- P-006-02 unit invariance: the SI result equals the published-unit expression times 0.45359237 / 1609.344, evaluated here;
- P-006-03 size classes: E(PM2.5) = 0.1 E(PM10) (TC-1) and E(PM10) < E(PM30) for every silt fraction <= 1 and weight > 0 (strict).
"""

from __future__ import annotations

import importlib
import warnings

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
SHORT_TON = 907.18474
LB = 0.45359237 / 1609.344
SILT = st.floats(0.018, 0.252)
WEIGHT = st.floats(1814.0, 263_083.0)
WEIGHT_EXT = st.floats(1814.0, 400_000.0)
LAM = st.floats(0.5, 2.0)
A = {"PM2.5": 0.9, "PM10": 0.9, "PM30": 0.7}
K = {"PM2.5": 0.15, "PM10": 1.5, "PM30": 4.9}


def _f():
    return importlib.import_module("minephys.environment").ap42_unpaved_emission_factor


def _quiet(*args):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return _f()(*args)


@pytest.mark.req("P-006-01")
@pytest.mark.oracle("analytical", "E is a power law in s (exponent a) and in W (exponent 0.45)")
@CI
@given(s=st.floats(0.018, 0.126), w=WEIGHT_EXT, lam=LAM, cls=st.sampled_from(["PM2.5", "PM10", "PM30"]))
def test_p_006_01_scaling_in_silt(s: float, w: float, lam: float, cls: str) -> None:
    base = _quiet(s, w, cls)
    scaled = _quiet(lam * s, w, cls)
    np.testing.assert_allclose(scaled, lam ** A[cls] * base, rtol=1e-12, atol=0)


@pytest.mark.req("P-006-01")
@CI
@given(s=SILT, w=st.floats(1814.0, 200_000.0), lam=LAM, cls=st.sampled_from(["PM2.5", "PM10", "PM30"]))
def test_p_006_01_scaling_in_weight(s: float, w: float, lam: float, cls: str) -> None:
    base = _quiet(s, w, cls)
    np.testing.assert_allclose(_quiet(s, lam * w, cls), lam**0.45 * base, rtol=1e-12, atol=0)


@pytest.mark.req("P-006-01")
@CI
@given(s=SILT, w=WEIGHT_EXT, d1=st.floats(1.01, 3.0), d2=st.floats(1.01, 3.0), cls=st.sampled_from(["PM2.5", "PM10", "PM30"]))
def test_p_006_01_strictly_increasing_in_silt_and_weight(s: float, w: float, d1: float, d2: float, cls: str) -> None:
    base = _quiet(s, w, cls)
    assert _quiet(s * d1, w, cls) > base
    assert _quiet(s, w * d2, cls) > base


@pytest.mark.req("P-006-02")
@pytest.mark.oracle("analytical", "SI result = published-unit expression x (0.45359237 kg/lb) / (1609.344 m/mile)")
@CI
@given(s=SILT, w=WEIGHT_EXT, cls=st.sampled_from(["PM2.5", "PM10", "PM30"]))
def test_p_006_02_unit_invariance(s: float, w: float, cls: str) -> None:
    published = K[cls] * (100.0 * s / 12.0) ** A[cls] * (w / SHORT_TON / 3.0) ** 0.45  # lb/VMT, s in %, W in short tons
    np.testing.assert_allclose(_quiet(s, w, cls), published * LB, rtol=1e-12, atol=0)


@pytest.mark.req("P-006-02")
def test_p_006_02_the_unit_factor_equals_the_printed_281_9_g_per_vkt() -> None:
    # k at the reference point (s = 12 %, W = 3 short tons) is 1.5 lb/VMT for PM10: its SI value gives the factor of the function
    one_lb_per_vmt = _quiet(0.12, 3.0 * SHORT_TON, "PM10") / 1.5  # kg/m for 1 lb/VMT
    np.testing.assert_allclose(one_lb_per_vmt * 1e6, 281.9, rtol=2e-4)  # kg/m -> g/km
    np.testing.assert_allclose(one_lb_per_vmt, LB, rtol=1e-12, atol=0)


@pytest.mark.req("P-006-03")
@pytest.mark.oracle("analytical", "k(PM2.5) = 0.1 k(PM10) with identical exponents; k(PM10) a^0.9 < k(PM30) a^0.7 for s <= 100 %")
@CI
@given(s=st.floats(0.001, 1.0), w=st.floats(100.0, 500_000.0))
def test_p_006_03_size_class_relations_over_the_full_domain(s: float, w: float) -> None:
    pm25, pm10, pm30 = _quiet(s, w, "PM2.5"), _quiet(s, w, "PM10"), _quiet(s, w, "PM30")
    np.testing.assert_allclose(pm25, 0.1 * pm10, rtol=1e-12, atol=0)
    assert pm10 < pm30

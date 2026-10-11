"""T-006-012 (P-006-04): precipitation and control are linear and monotone.

Public API under test (`minephys.environment`): `precipitation_correction(emission_factor, wet_days)`,
`watering_control_efficiency(moisture_ratio)`, `controlled_emission_factor(emission_factor, control_efficiency)`
(see tests/unit/test_t_006_012_ap42_corrections.py).
Relations (P in [0, 365], M in [0, 5]; TC-1): E_ext equals E at P = 0, 0 at P = 365 and is non-increasing in P and linear in E;
CE(M) is continuous (its increase over [M1, M2] never exceeds 0.75 (M2 - M1), the slope of the steepest segment of the figure,
between M = 1 and 2) and non-decreasing on [0, 5]; the controlled factor is linear in E.
"""

from __future__ import annotations

import importlib

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
EMISSION = st.floats(1e-9, 1e3)


def _e():
    return importlib.import_module("minephys.environment")


@pytest.mark.req("P-006-04")
@pytest.mark.oracle("analytical", "E_ext = E (365 - P) / 365")
@CI
@given(e=EMISSION, p1=st.floats(0.0, 365.0), p2=st.floats(0.0, 365.0), lam=st.floats(0.1, 10.0))
def test_p_006_04_precipitation_correction_is_linear_and_non_increasing(e: float, p1: float, p2: float, lam: float) -> None:
    env = _e()
    lo, hi = sorted((p1, p2))
    assert env.precipitation_correction(e, hi) <= env.precipitation_correction(e, lo) * (1.0 + 1e-15)
    np.testing.assert_allclose(env.precipitation_correction(lam * e, lo), lam * env.precipitation_correction(e, lo), rtol=1e-12)
    np.testing.assert_allclose(env.precipitation_correction(e, 0.0), e, rtol=1e-13, atol=0)
    assert env.precipitation_correction(e, 365.0) == 0.0


@pytest.mark.req("P-006-04")
@pytest.mark.oracle("analytical", "piecewise-linear and non-decreasing with slopes 0, 0.75 and 0.0667 per unit of M")
@CI
@given(m1=st.floats(0.0, 5.0), m2=st.floats(0.0, 5.0))
def test_p_006_04_efficiency_is_non_decreasing_and_continuous(m1: float, m2: float) -> None:
    env = _e()
    lo, hi = sorted((m1, m2))
    c_lo, c_hi = env.watering_control_efficiency(lo), env.watering_control_efficiency(hi)
    assert 0.0 <= c_lo <= c_hi <= 0.95 + 1e-15
    assert c_hi - c_lo <= 0.75 * (hi - lo) + 1e-12  # the steepest segment of the figure has slope 0.75


@pytest.mark.req("P-006-04")
@CI
@given(e=EMISSION, lam=st.floats(0.1, 10.0), ce=st.floats(0.0, 1.0))
def test_p_006_04_controlled_factor_is_linear_in_the_emission_factor(e: float, lam: float, ce: float) -> None:
    env = _e()
    np.testing.assert_allclose(env.controlled_emission_factor(lam * e, ce), lam * env.controlled_emission_factor(e, ce), rtol=1e-12)
    assert 0.0 <= env.controlled_emission_factor(e, ce) <= e * (1.0 + 1e-15)

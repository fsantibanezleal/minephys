"""T-006-022 (P-006-08): metamorphic relations of the line-source plumes.

Public API under test (`minephys.environment`): `gaussian_plume`, `line_source_plume(q_line, u, z, h, sigma_z)` and
`finite_line_source_plume(q_line, u, y, z, h, y1, y2, sigma_y, sigma_z)` (see tests/unit/test_t_006_021_plume.py and
test_t_006_022_line_source.py). Generators: u log-uniform in [0.5, 20] m/s, heights in [0, 200] m, sigma in [1, 500] m,
200 examples.

Relations
- the infinite line equals the integral over y of the point-source plume with q = q_line dy (trapezoid quadrature out to 12 sigma_y
  on 4,001 points: the Gaussian integrand is negligible at the ends, so the rule converges spectrally; rtol 1e-8);
- the finite line tends to the infinite one when its half-length exceeds 10 sigma_y (<= 1e-12 relative) and is additive over
  adjacent segments (TC-1); reversing the order of the end points changes nothing in the symmetric case; the field is linear in
  q_line and inversely proportional to u.
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)
LOGU = st.floats(math.log(0.5), math.log(20.0)).map(math.exp)
SIGMA = st.floats(1.0, 500.0)
HEIGHT = st.floats(0.0, 200.0)
QL = st.floats(1e-9, 1e-3)


def _e():
    return importlib.import_module("minephys.environment")


@pytest.mark.req("P-006-08")
@pytest.mark.oracle("reference-implementation", "trapezoid quadrature of gaussian_plume over the crosswind coordinate")
@settings(max_examples=60, deadline=None)
@given(ql=QL, u=LOGU, z=HEIGHT, h=HEIGHT, sy=st.floats(1.0, 200.0), sz=SIGMA)
def test_p_006_08_infinite_line_equals_the_crosswind_integral(ql: float, u: float, z: float, h: float, sy: float, sz: float) -> None:
    e = _e()
    y = np.linspace(-12.0 * sy, 12.0 * sy, 4001)
    integral = np.trapezoid(e.gaussian_plume(ql, u, y, z, h, sy, sz), y)
    np.testing.assert_allclose(e.line_source_plume(ql, u, z, h, sz), integral, rtol=1e-8, atol=1e-300)


@pytest.mark.req("P-006-08")
@CI
@given(ql=QL, u=LOGU, y=st.floats(-100.0, 100.0), z=HEIGHT, h=HEIGHT, sy=st.floats(1.0, 80.0), sz=SIGMA, extra=st.floats(0.0, 50.0))
def test_p_006_08_long_segments_tend_to_the_infinite_line(ql: float, u: float, y: float, z: float, h: float, sy: float, sz: float, extra: float) -> None:
    e = _e()
    half = 10.0 * sy + extra
    finite = e.finite_line_source_plume(ql, u, y, z, h, y - half, y + half, sy, sz)
    np.testing.assert_allclose(finite, e.line_source_plume(ql, u, z, h, sz), rtol=1e-12, atol=1e-300)


@pytest.mark.req("P-006-08")
@pytest.mark.oracle("analytical", "the erf difference is additive over adjacent segments")
@CI
@given(
    ql=QL,
    u=LOGU,
    y=st.floats(-100.0, 100.0),
    z=HEIGHT,
    h=HEIGHT,
    sy=st.floats(5.0, 100.0),
    sz=SIGMA,
    a=st.floats(-200.0, 0.0),
    w1=st.floats(10.0, 150.0),
    w2=st.floats(10.0, 150.0),
)
def test_p_006_08_additivity_over_adjacent_segments(ql, u, y, z, h, sy, sz, a, w1, w2) -> None:
    e = _e()
    b, c = a + w1, a + w1 + w2
    whole = e.finite_line_source_plume(ql, u, y, z, h, a, c, sy, sz)
    parts = e.finite_line_source_plume(ql, u, y, z, h, a, b, sy, sz) + e.finite_line_source_plume(ql, u, y, z, h, b, c, sy, sz)
    np.testing.assert_allclose(parts, whole, rtol=1e-10, atol=1e-12 * abs(whole) + 1e-300)


@pytest.mark.req("P-006-08")
@CI
@given(ql=QL, u=LOGU, y=st.floats(-100.0, 100.0), z=HEIGHT, h=HEIGHT, sy=st.floats(5.0, 100.0), sz=SIGMA, lam=st.floats(0.1, 10.0))
def test_p_006_08_linear_in_the_line_strength_and_inverse_in_the_wind(ql, u, y, z, h, sy, sz, lam) -> None:
    e = _e()
    base = e.finite_line_source_plume(ql, u, y, z, h, -50.0, 50.0, sy, sz)
    np.testing.assert_allclose(e.finite_line_source_plume(lam * ql, u, y, z, h, -50.0, 50.0, sy, sz), lam * base, rtol=1e-12, atol=1e-300)
    np.testing.assert_allclose(e.finite_line_source_plume(ql, lam * u, y, z, h, -50.0, 50.0, sy, sz), base / lam, rtol=1e-12, atol=1e-300)
    # a symmetric segment gives a field that is even in y
    np.testing.assert_allclose(
        e.finite_line_source_plume(ql, u, -y, z, h, -50.0, 50.0, sy, sz), base, rtol=1e-12, atol=1e-300
    )

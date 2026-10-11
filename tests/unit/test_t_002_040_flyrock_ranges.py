"""T-002-040 (FR-002-10, FR-002-11): drag-free flyrock range and Lundborg's empirical maximum throw.

Expected API:
    `B.flyrock_range_no_drag(launch_speed, launch_angle, g=9.80665)` -> v0^2 sin(2 theta0) / g in m (launch and
    landing at
        the same level; speed in m/s, angle in rad);
    `B.flyrock_range_lundborg(hole_diameter)` -> 260 * d^(2/3) in m with the diameter converted from m to inches first
        (`lundborg_max_range_*` rows, UNVERIFIED secondary transcription, so every call emits
        `minephys.knowledge.UnverifiedParameterWarning` naming the rows and the key `szendrei2022`).

Oracles: spec 002 section 7.4 (range 163.15459 m for 40 m/s at 45 degrees; Lundborg 760.24461 m for a 5-inch
hole, TC-2), the published value "very close to 760 m" for a 5-inch hole (Szendrei and Tose 2022, p. 729; 3
significant figures) and hand calculations (1 in = 0.0254 m).
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest
from minephys.knowledge import UnverifiedParameterWarning

from minephys import blasting as B

G0 = 9.80665


def lundborg(d_m: float):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return B.flyrock_range_lundborg(d_m)


@pytest.mark.req("FR-002-10")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: 40^2 * sin(pi/2) / 9.80665 = 163.15459 m")
def test_vacuum_range_printed_value() -> None:
    got = B.flyrock_range_no_drag(40.0, math.pi / 4.0)
    assert type(got) is np.float64
    assert got == pytest.approx(163.15459, abs=5e-6)  # TC-2: 8 significant figures
    assert got == pytest.approx(1600.0 / G0, rel=1e-12)


@pytest.mark.req("FR-002-10")
@pytest.mark.oracle(
    "hand-calculation",
    "other angles and gravity: 30 degrees gives 1600 sin(60 deg) / 9.80665; g = 9.81 gives 1600 / 9.81",
)
def test_other_angles_and_gravity() -> None:
    assert B.flyrock_range_no_drag(40.0, math.radians(30.0)) == pytest.approx(
        1600.0 * math.sin(math.radians(60.0)) / G0, rel=1e-12
    )
    assert B.flyrock_range_no_drag(40.0, math.pi / 4.0, g=9.81) == pytest.approx(1600.0 / 9.81, rel=1e-12)
    assert B.flyrock_range_no_drag(40.0, math.pi / 4.0, g=1.62) == pytest.approx(1600.0 / 1.62, rel=1e-12)  # the Moon


@pytest.mark.req("FR-002-10")
@pytest.mark.oracle(
    "analytical", "grazing launches: theta = 0 and theta = pi/2 give no range (sin 0 = 0, sin pi = 0 up to rounding)"
)
def test_range_vanishes_at_the_ends_of_the_angle_interval() -> None:
    assert B.flyrock_range_no_drag(40.0, 0.0) == 0.0
    assert B.flyrock_range_no_drag(40.0, math.pi / 2.0) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.req("FR-002-10")
@pytest.mark.oracle("analytical", "45 degrees is the optimum: v^2 / g is an upper bound for every angle")
@pytest.mark.parametrize("theta", np.linspace(0.0, math.pi / 2.0, 21).tolist())
def test_forty_five_degrees_maximises_the_range(theta: float) -> None:
    assert B.flyrock_range_no_drag(40.0, theta) <= 1600.0 / G0 * (1.0 + 1e-12)


@pytest.mark.req("FR-002-10")
@pytest.mark.oracle("hand-calculation", "arrays broadcast: speeds (column) by angles (row)")
def test_broadcasting() -> None:
    v = np.array([[10.0], [20.0], [40.0]])
    th = np.array([0.3, 0.6, 0.9, 1.2])
    out = B.flyrock_range_no_drag(v, th)
    assert out.shape == (3, 4)
    np.testing.assert_allclose(out, v**2 * np.sin(2.0 * th) / G0, rtol=1e-13)
    assert B.flyrock_range_no_drag(np.empty(0), 0.7).shape == (0,)


@pytest.mark.req("FR-002-11")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: 260 * (0.127 / 0.0254)^(2/3) = 260 * 5^(2/3) = 760.24461 m")
def test_lundborg_printed_value() -> None:
    got = lundborg(0.127)
    assert type(got) is np.float64
    assert got == pytest.approx(760.24461, abs=5e-6)  # TC-2: 8 significant figures
    assert got == pytest.approx(260.0 * 5.0 ** (2.0 / 3.0), rel=1e-12)


@pytest.mark.req("FR-002-11")
@pytest.mark.oracle(
    "worked-example", "szendrei2022 p. 729: for a 5-inch hole Lundborg's maximum throw is very close to 760 m"
)
def test_lundborg_published_value() -> None:
    assert lundborg(0.127) == pytest.approx(760.0, abs=0.5)  # TC-2: 3 significant figures


@pytest.mark.req("FR-002-11")
@pytest.mark.oracle(
    "hand-calculation", "1 inch gives the coefficient itself (260 m); 8 inches give 260 * 8^(2/3) = 1040 m"
)
def test_lundborg_unit_conversion_and_round_numbers() -> None:
    assert lundborg(0.0254) == pytest.approx(260.0, rel=1e-12)
    assert lundborg(8 * 0.0254) == pytest.approx(1040.0, rel=1e-12)
    assert lundborg(0.2032) == pytest.approx(1040.0, rel=1e-12)


@pytest.mark.req("FR-002-11")
@pytest.mark.oracle("analytical", "R scales as d^(2/3): 8 times the diameter gives 4 times the range; arrays broadcast")
def test_lundborg_scaling_and_arrays() -> None:
    d = np.array([0.05, 0.1, 0.2, 0.311])
    r = lundborg(d)
    assert r.shape == (4,)
    np.testing.assert_allclose(lundborg(8.0 * d), 4.0 * r, rtol=1e-12)
    np.testing.assert_allclose(r, 260.0 * (d / 0.0254) ** (2.0 / 3.0), rtol=1e-12)
    assert lundborg(np.empty(0)).shape == (0,)


@pytest.mark.req("FR-002-11")
@pytest.mark.oracle(
    "hand-calculation", "FR-008-12: the UNVERIFIED Lundborg rows are reported on use, naming both rows and the key"
)
def test_lundborg_warns_about_its_unverified_rows() -> None:
    with pytest.warns(UnverifiedParameterWarning) as rec:
        B.flyrock_range_lundborg(0.127)
    text = " ".join(str(w.message) for w in rec)
    assert "lundborg_max_range_coefficient" in text
    assert "lundborg_max_range_exponent" in text
    assert "szendrei2022" in text

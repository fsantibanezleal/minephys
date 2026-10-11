"""T-003-023 (FR-003-09): cross-check of `bishop_simplified_fos` against pySlope on the Fredlund-Krahn geometry.

Reference implementation: pySlope 1.4.0 (MIT, Bishop only; a dev-only dependency locked by T-003-002, never a
runtime dependency). The geometry is Fredlund and Krahn (1977), Slide verification problem #21: ground (0,
60), (60, 60), (140, 20), (180, 20) ft, i.e. a 40 ft high slope with a 2H:1V face (length 80 ft); gamma = 120
pcf, c' = 600 psf, phi' = 20 deg; the circle (centre (120, 90) ft, R = 80 ft) and three more circles that cut
the ground twice. pySlope places the crest of a slope of height H and length L at (160 ft, 200 ft) for H = 40
ft, so its coordinates are ours shifted by (+100, +140) ft. pySlope runs with 100 slices, tolerance 1e-9 and
200 iterations. Tolerance |dF| <= 0.01 (discretisation-limited, spec 003 section 7.4); the two codes use the
same slicing rule and in fact agree far more closely.

pySlope is imported inside the tests, after the first-party function has been called, so that the failure
reason is the missing implementation. Imperial inputs are converted with the exact definitions 1 ft = 0.3048 m
and 1 lbf = 0.45359237 kg * 9.80665 m/s^2.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from minephys import geotech as G

FT = 0.3048
LBF = 0.45359237 * 9.80665
GAMMA = 120.0 * LBF / FT**3  # N/m^3
COHESION = 600.0 * LBF / FT**2  # Pa
GROUND_X = np.array([0.0, 60.0, 140.0, 180.0]) * FT
GROUND_Z = np.array([60.0, 60.0, 20.0, 20.0]) * FT
CIRCLES = [(120.0, 90.0, 80.0), (115.0, 95.0, 75.0), (125.0, 100.0, 90.0), (110.0, 85.0, 70.0)]


def pyslope_fos(cx_ft: float, cz_ft: float, r_ft: float) -> float:
    from pyslope import Material, Slope

    slope = Slope(height=40.0 * FT, length=80.0 * FT)
    slope.set_materials(
        Material(
            unit_weight=GAMMA / 1000.0,
            friction_angle=20.0,
            cohesion=COHESION / 1000.0,
            depth_to_bottom=40.0 * FT + 30.0,
        )
    )
    slope.update_analysis_options(slices=100, tolerance=1e-9, max_iterations=200)
    slope.add_single_circular_plane(c_x=(cx_ft + 100.0) * FT, c_y=(cz_ft + 140.0) * FT, radius=r_ft * FT)
    slope.analyse_slope()
    return float(slope.get_min_FOS())


@pytest.mark.req("FR-003-09")
@pytest.mark.oracle("reference-implementation", "pySlope 1.4.0 Bishop on the same circle and 100 slices (|dF| <= 0.01)")
@pytest.mark.parametrize(("cx", "cz", "r"), CIRCLES)
def test_bishop_matches_pyslope(cx: float, cz: float, r: float) -> None:
    s = G.circular_slices(GROUND_X, GROUND_Z, cx * FT, cz * FT, r * FT, 100, GAMMA)
    ours = float(
        G.bishop_simplified_fos(s.width, s.weight, s.base_angle, s.pore_pressure, COHESION, math.radians(20.0))
    )
    assert ours == pytest.approx(pyslope_fos(cx, cz, r), abs=0.01)


@pytest.mark.req("FR-003-09")
@pytest.mark.oracle(
    "worked-example",
    "fredlund1977 as slide verification problem 21 pp. 91-92: the published Bishop F = 2.080 (|dF| <= 0.01)",
)
def test_pyslope_and_minephys_both_reproduce_the_published_benchmark() -> None:
    s = G.circular_slices(GROUND_X, GROUND_Z, 120.0 * FT, 90.0 * FT, 80.0 * FT, 100, GAMMA)
    ours = float(
        G.bishop_simplified_fos(s.width, s.weight, s.base_angle, s.pore_pressure, COHESION, math.radians(20.0))
    )
    theirs = pyslope_fos(120.0, 90.0, 80.0)
    assert ours == pytest.approx(2.080, abs=0.01)
    assert theirs == pytest.approx(2.080, abs=0.01)
    assert ours == pytest.approx(theirs, abs=0.01)

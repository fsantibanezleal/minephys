"""T-002-030 (FR-002-08): scaled distance and the square-root scaled-distance PPV site law.

Expected API:
    `B.scaled_distance(distance, charge_per_delay)` -> D / sqrt(W) in m / kg^(1/2);
    `B.ppv_scaled_distance(distance, charge_per_delay, k_site, beta)` -> K * (D / sqrt(W))^(-beta) in m/s, with
    `k_site` the
        PPV in m/s at a scaled distance of 1 m/kg^(1/2); `k_site` and `beta` have no default.
Oracles: spec 002 section 7.4 (scaled_distance(300, 150) = 24.494897; ppv_scaled_distance(300, 150, 1.0, 1.6) =
5.9907197e-3 m/s; TC-2) and hand calculations. Tolerance TC-1 otherwise.
"""

from __future__ import annotations

import inspect
import math

import numpy as np
import pytest

from minephys import blasting as B


@pytest.mark.req("FR-002-08")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: 300 / sqrt(150) = 24.494897 m/kg^0.5")
def test_scaled_distance_printed_value() -> None:
    got = B.scaled_distance(300.0, 150.0)
    assert type(got) is np.float64
    assert got == pytest.approx(24.494897, abs=5e-7)  # TC-2
    assert got == pytest.approx(300.0 / math.sqrt(150.0), rel=1e-14)


@pytest.mark.req("FR-002-08")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: 1.0 * 24.494897^-1.6 = 5.9907197e-3 m/s")
def test_ppv_printed_value() -> None:
    got = B.ppv_scaled_distance(300.0, 150.0, 1.0, 1.6)
    assert type(got) is np.float64
    assert got == pytest.approx(5.9907197e-3, abs=5e-11)  # TC-2: 8 significant figures
    assert got == pytest.approx((300.0 / math.sqrt(150.0)) ** -1.6, rel=1e-13)


@pytest.mark.req("FR-002-08")
@pytest.mark.oracle(
    "hand-calculation",
    "K = 0.5 m/s at 1 m/kg^0.5, beta 1.5: D = 100 m, W = 100 kg gives scaled distance 10, PPV 0.5 * 10^-1.5",
)
def test_site_law_round_numbers() -> None:
    assert B.scaled_distance(100.0, 100.0) == pytest.approx(10.0, rel=1e-14)
    assert B.ppv_scaled_distance(100.0, 100.0, 0.5, 1.5) == pytest.approx(0.5 * 10.0**-1.5, rel=1e-13)
    assert B.ppv_scaled_distance(1.0, 1.0, 0.7, 2.0) == pytest.approx(0.7, rel=1e-14)  # SD = 1 gives K itself
    assert B.ppv_scaled_distance(400.0, 25.0, 2.0, 1.0) == pytest.approx(2.0 / 80.0, rel=1e-14)  # SD = 80, beta 1


@pytest.mark.req("FR-002-08")
@pytest.mark.oracle("hand-calculation", "k_site and beta have no default: calling without them is a TypeError")
def test_no_defaults_for_site_constants() -> None:
    params = inspect.signature(B.ppv_scaled_distance).parameters
    assert params["k_site"].default is inspect.Parameter.empty
    assert params["beta"].default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        B.ppv_scaled_distance(300.0, 150.0)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        B.ppv_scaled_distance(300.0, 150.0, 1.0)  # type: ignore[call-arg]


@pytest.mark.req("FR-002-08")
@pytest.mark.oracle(
    "hand-calculation", "arrays broadcast: distances (row) by charges (column); empty arrays give empty results"
)
def test_broadcasting() -> None:
    d = np.array([100.0, 200.0, 400.0])
    w = np.array([[25.0], [100.0]])
    out = B.ppv_scaled_distance(d, w, 0.8, 1.6)
    assert out.shape == (2, 3)
    np.testing.assert_allclose(out, 0.8 * (d / np.sqrt(w)) ** -1.6, rtol=1e-13)
    assert B.scaled_distance(np.empty(0), 10.0).shape == (0,)
    assert B.ppv_scaled_distance(np.empty(0), 10.0, 1.0, 1.5).shape == (0,)

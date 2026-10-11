"""T-001-020 (FR-001-08, FR-001-09): loose density and loader passes.

Expected API:
    `H.loose_density(bank_density, swell)` -> `bank_density / (1 + swell)` in kg/m^3 (float64);
    `H.loading_passes(target_payload, bucket_volume, fill_factor, loose_density)` -> the smallest integer n >= 1 with
    `n * bucket_volume * fill_factor * loose_density >= target_payload`, where a quotient within a relative 1e-12 of an
    integer counts as that integer; returned as `numpy.int64` (scalar) or an int64 array.

Oracles: spec 001 section 7.4 (the exact-multiple case = 3 passes; 220,000 kg gives 4) and hand calculations below.
"""

from __future__ import annotations

import numpy as np
import pytest

from minephys import haulage as H

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


@pytest.mark.req("FR-001-08")
@pytest.mark.oracle("hand-calculation", "2700 / (1 + 0.35) = 2000 kg/m^3")
def test_loose_density_printed_case() -> None:
    got = H.loose_density(2700.0, 0.35)
    assert type(got) is np.float64
    assert got == pytest.approx(2000.0, rel=1e-12)


@pytest.mark.req("FR-001-08")
@pytest.mark.oracle("hand-calculation", "swell 0 leaves the density; swell 1 halves it; swell 0.25 gives 0.8")
@pytest.mark.parametrize(
    ("bank", "swell", "expected"), [(2700.0, 0.0, 2700.0), (2600.0, 1.0, 1300.0), (2500.0, 0.25, 2000.0)]
)
def test_loose_density_values(bank: float, swell: float, expected: float) -> None:
    assert H.loose_density(bank, swell) == pytest.approx(expected, rel=1e-12)


@pytest.mark.req("FR-001-08")
@pytest.mark.oracle("hand-calculation", "arrays: bank densities (column) by swells (row)")
def test_loose_density_broadcasts() -> None:
    bank = np.array([[2000.0], [3000.0]])
    swell = np.array([0.0, 0.5, 1.0])
    out = H.loose_density(bank, swell)
    assert out.shape == (2, 3)
    np.testing.assert_allclose(out, bank / (1.0 + swell), rtol=1e-14, atol=0.0)


@pytest.mark.req("FR-001-09")
@pytest.mark.oracle(
    "hand-calculation", "spec 001 7.4: 216000 / (40 * 0.9 * 2000) = 3 exactly; the float quotient is 3.0000000000000004"
)
def test_exact_multiple_is_three_passes() -> None:
    got = H.loading_passes(216000.0, 40.0, 0.9, H.loose_density(2700.0, 0.35))
    assert type(got) is np.int64
    assert got == 3


@pytest.mark.req("FR-001-09")
@pytest.mark.oracle("hand-calculation", "spec 001 7.4: 220000 / (40 * 0.9 * 2000) = 3.0556 -> 4 passes")
def test_partial_last_pass_rounds_up() -> None:
    assert H.loading_passes(220000.0, 40.0, 0.9, 2000.0) == 4


@pytest.mark.req("FR-001-09")
@pytest.mark.oracle(
    "hand-calculation", "capacity per pass = 72,000 kg; the 1e-12 relative integer rule decides the border"
)
@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (72000.0, 1),
        (72000.0 * (1 + 1e-13), 1),  # inside the integer rule
        (72000.0 * (1 + 1e-11), 2),  # outside: one more pass
        (72000.0 * (1 - 1e-11), 1),
        (144000.0, 2),
        (144000.0 * (1 + 5e-13), 2),
        (144000.0 * (1 + 5e-11), 3),
        (216000.0 * (1 + 1e-13), 3),
        (216000.0 * (1 + 1e-11), 4),
        (1.0, 1),  # at least one pass
        (71999.0, 1),
        (72001.0, 2),
    ],
)
def test_integer_rule_and_borders(payload: float, expected: int) -> None:
    assert H.loading_passes(payload, 40.0, 0.9, 2000.0) == expected


@pytest.mark.req("FR-001-09")
@pytest.mark.oracle("hand-calculation", "arrays: payloads (row) with two buckets (column)")
def test_array_inputs_return_int64() -> None:
    payload = np.array([50000.0, 100000.0, 216000.0, 220000.0])
    volume = np.array([[20.0], [40.0]])
    out = H.loading_passes(payload, volume, 0.9, 2000.0)
    assert out.dtype == np.int64
    assert out.shape == (2, 4)
    # capacity per pass: 20 -> 36,000 kg; 40 -> 72,000 kg
    np.testing.assert_array_equal(out, [[2, 3, 6, 7], [1, 2, 3, 4]])
    assert H.loading_passes(np.empty(0), 40.0, 0.9, 2000.0).shape == (0,)


@pytest.mark.req("FR-001-09")
@pytest.mark.oracle(
    "hand-calculation",
    "fill factors above 1 are allowed up to 2 (heaped buckets): 40 * 1.2 * 2000 = 96,000 kg per pass",
)
def test_heaped_bucket_fill_factor() -> None:
    assert H.loading_passes(200000.0, 40.0, 1.2, 2000.0) == 3
    assert H.loading_passes(192000.0, 40.0, 1.2, 2000.0) == 2

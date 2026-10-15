# ruff: noqa: E501
"""T-004-031 (FR-004-09, FR-004-12): bed-blending variance of a layered stockpile and the variance reduction ratio.

Expected API, module `minephys.bulk` (elementwise, float64; a scalar call gives a NumPy float64):

    gy_blending_variance(input_variance, n_layers, lag1_correlation=0) ->
        sigma_in^2 / N [1 + 2 sum_{k=1}^{N-1} (1 - k / N) rho^k]       (the variance of the mean of N layers whose
        grades follow a stationary first-order autoregressive series), in the unit^2 of `input_variance`, evaluated in
        closed form sum = rho / (1 - rho) - rho (1 - rho^N) / (N (1 - rho)^2) (rho != 0) so that N up to 1e7 costs
        O(1); close to rho = 1 the result stays within TC-1 of the true value (explicit sum for N <= 1,000 or a series
        expansion).
    variance_reduction_ratio(n_layers, lag1_correlation=0) -> sigma_in^2 / sigma_out^2 = N / [1 + 2 sum_k (1 - k /
    N) rho^k]. `n_layers` is an integer in 1..1e7 (an integer-valued float is accepted: elementwise functions take
    float arrays); -1 < rho < 1; input_variance >= 0.

Oracles: spec 004 section 7.4 (variances 0.01, 0.17200048, 0.26003906 and 0.25 for (N, rho) = (100, 0), (100,
0.9), (10, 0.5), (2, -0.5) at unit input variance; variance reduction ratios 100, 5.8139, 3.8456 and 4; TC-2),
the explicit sum evaluated in 80-digit decimal arithmetic in this file (N <= 1,000) and the closed form
evaluated in 80-digit decimal arithmetic (any N, including N = 1e7 and rho within 1e-9 of 1). Tolerance TC-1
(rtol 1e-12); the extreme near-unit correlations are checked at rtol 1e-11.
"""

from __future__ import annotations

import inspect
import math
from decimal import Decimal, getcontext

import numpy as np
import pytest

import minephys
from minephys import bulk as B

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

getcontext().prec = 80


def explicit_sum(n: int, rho: float) -> Decimal:
    r = Decimal(rho)
    big_n = Decimal(n)
    return sum(((1 - Decimal(k) / big_n) * r**k for k in range(1, n)), Decimal(0))


def closed_sum(n: int, rho: float) -> Decimal:
    if rho == 0.0:
        return Decimal(0)
    r = Decimal(rho)
    big_n = Decimal(n)
    return r / (1 - r) - r * (1 - r**n) / (big_n * (1 - r) ** 2)


def blend_exact(var: float, n: int, rho: float, method: str = "closed") -> float:
    s = explicit_sum(n, rho) if method == "explicit" else closed_sum(n, rho)
    return float(Decimal(var) / Decimal(n) * (1 + 2 * s))


@pytest.mark.req("FR-004-09")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 7.4: gy_blending_variance(1, 100, 0) = 0.01, (1, 100, 0.9) = 0.17200048, (1, 10, 0.5) = 0.26003906, (1, 2, -0.5) = 0.25",
)
@pytest.mark.parametrize(
    ("n", "rho", "expected", "tolerance"),
    [(100, 0.0, 0.01, 5e-14), (100, 0.9, 0.17200048, 5e-9), (10, 0.5, 0.26003906, 5e-9), (2, -0.5, 0.25, 5e-9)],
)
def test_spec_variances(n: int, rho: float, expected: float, tolerance: float) -> None:
    v = B.gy_blending_variance(1.0, n, rho)
    assert type(v) is np.float64
    assert v == pytest.approx(expected, abs=tolerance)  # TC-2


@pytest.mark.req("FR-004-09")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 7.4: variance reduction ratios 100, 5.8139, 3.8456 and 4 for the same four cases (and not 100 for correlated layers)",
)
@pytest.mark.parametrize(
    ("n", "rho", "expected", "tolerance"),
    [(100, 0.0, 100.0, 5e-12), (100, 0.9, 5.8139, 5e-5), (10, 0.5, 3.8456, 5e-5), (2, -0.5, 4.0, 5e-12)],
)
def test_spec_ratios(n: int, rho: float, expected: float, tolerance: float) -> None:
    r = B.variance_reduction_ratio(n, rho)
    assert type(r) is np.float64
    assert r == pytest.approx(expected, abs=tolerance)  # TC-2


@pytest.mark.req("FR-004-09")
@pytest.mark.oracle(
    "analytical",
    "the explicit sum of the definition in 80-digit decimal arithmetic, N <= 1,000, rho over (-0.99, 0.99) (rtol 1e-10 per the spec, 1e-12 achieved)",
)
@pytest.mark.parametrize("n", [1, 2, 3, 10, 57, 100, 999, 1000])
@pytest.mark.parametrize("rho", [-0.99, -0.5, -0.1, 0.0, 0.1, 0.5, 0.9, 0.99])
def test_explicit_sum(n: int, rho: float) -> None:
    got = B.gy_blending_variance(2.5, n, rho)
    assert got == pytest.approx(blend_exact(2.5, n, rho, "explicit"), rel=1e-12)
    ratio = B.variance_reduction_ratio(n, rho)
    assert ratio == pytest.approx(2.5 / blend_exact(2.5, n, rho, "explicit"), rel=1e-12)


@pytest.mark.req("FR-004-09")
@pytest.mark.oracle(
    "analytical",
    "closed form in 80-digit decimal arithmetic for large N (up to 1e7), O(1) evaluation: sum = rho / (1 - rho) - rho (1 - rho^N) / (N (1 - rho)^2)",
)
@pytest.mark.parametrize("n", [1001, 5000, 123_456, 10**6, 10**7])
@pytest.mark.parametrize("rho", [-0.99, -0.3, 0.0, 0.2, 0.9, 0.99, 0.999])
def test_large_n_closed_form(n: int, rho: float) -> None:
    got = B.gy_blending_variance(1.0, n, rho)
    assert got == pytest.approx(blend_exact(1.0, n, rho), rel=1e-12)
    assert B.variance_reduction_ratio(n, rho) == pytest.approx(1.0 / blend_exact(1.0, n, rho), rel=1e-12)


@pytest.mark.req("FR-004-09")
@pytest.mark.oracle(
    "analytical",
    "correlations within 1e-4 .. 1e-9 of +-1: the result stays within 1e-11 of the exact value (explicit sum or series expansion near 1)",
)
@pytest.mark.parametrize("n", [2, 50, 1000, 1001, 10**4, 10**7])
@pytest.mark.parametrize("rho", [0.9999, 1.0 - 1e-6, 1.0 - 1e-9, -0.9999, -(1.0 - 1e-9)])
def test_correlations_near_one(n: int, rho: float) -> None:
    exact = blend_exact(1.0, n, rho, "explicit") if n <= 1000 else blend_exact(1.0, n, rho)
    assert B.gy_blending_variance(1.0, n, rho) == pytest.approx(exact, rel=1e-11)
    assert B.variance_reduction_ratio(n, rho) == pytest.approx(1.0 / exact, rel=1e-11)


@pytest.mark.req("FR-004-09")
@pytest.mark.oracle(
    "analytical",
    "uncorrelated layers: sigma^2 / N exactly; one layer: no reduction at all (variance unchanged, ratio 1) for every rho",
)
@pytest.mark.parametrize("n", [1, 2, 100, 10**6, 10**7])
def test_uncorrelated_and_single_layer(n: int) -> None:
    assert B.gy_blending_variance(3.0, n, 0.0) == pytest.approx(3.0 / n, rel=1e-15)
    assert B.variance_reduction_ratio(n, 0.0) == pytest.approx(float(n), rel=1e-15)
    assert B.gy_blending_variance(3.0, n) == B.gy_blending_variance(3.0, n, 0.0)
    for rho in (-0.9, 0.0, 0.7):
        assert B.gy_blending_variance(3.0, 1, rho) == pytest.approx(3.0, rel=1e-14)
        assert B.variance_reduction_ratio(1, rho) == pytest.approx(1.0, rel=1e-14)


@pytest.mark.req("FR-004-09")
@pytest.mark.oracle(
    "analytical", "correlated layers blend far less than 1/N: rho = 0.9 over 100 layers gives 5.81, not 100 (US-004-3)"
)
def test_correlated_layers_do_not_get_the_one_over_n_gain() -> None:
    assert B.variance_reduction_ratio(100, 0.9) == pytest.approx(5.8139, abs=5e-5)
    assert B.variance_reduction_ratio(100, 0.9) < 6.0
    assert B.variance_reduction_ratio(100, -0.5) > 100.0, "anticorrelated layers blend better than independent ones"


@pytest.mark.req("FR-004-09")
@pytest.mark.oracle(
    "analytical", "the variance is linear in the input variance; zero input variance gives zero; defaults and arrays"
)
def test_linearity_defaults_and_arrays() -> None:
    assert B.gy_blending_variance(0.0, 100, 0.9) == 0.0
    assert B.gy_blending_variance(4.0, 100, 0.9) == pytest.approx(
        4.0 * float(B.gy_blending_variance(1.0, 100, 0.9)), rel=1e-14
    )
    assert inspect.signature(B.gy_blending_variance).parameters["lag1_correlation"].default == 0
    assert inspect.signature(B.variance_reduction_ratio).parameters["lag1_correlation"].default == 0
    assert list(inspect.signature(B.gy_blending_variance).parameters) == [
        "input_variance",
        "n_layers",
        "lag1_correlation",
    ]
    n = np.array([[1], [10], [100]])
    rho = np.array([0.0, 0.5, 0.9])
    v = B.gy_blending_variance(1.0, n, rho)
    ratio = B.variance_reduction_ratio(n, rho)
    assert v.shape == ratio.shape == (3, 3)
    assert v.dtype == ratio.dtype == np.float64
    assert v[1, 1] == pytest.approx(0.26003906, abs=5e-9)
    assert v[2, 0] == pytest.approx(0.01, rel=1e-14)
    np.testing.assert_allclose(ratio * v, 1.0, rtol=1e-13)


@pytest.mark.req("FR-004-09")
@pytest.mark.oracle(
    "analytical", "integer-valued floats and NumPy integers are layer counts; the result does not depend on the dtype"
)
def test_layer_count_dtypes() -> None:
    ref = float(B.gy_blending_variance(1.0, 100, 0.9))
    for n in (100.0, np.int64(100), np.int32(100), np.float32(100.0), np.array([100.0])[0]):
        assert float(B.gy_blending_variance(1.0, n, 0.9)) == ref


@pytest.mark.req("FR-004-12")
@pytest.mark.oracle(
    "analytical", "n_layers must be an integer in 1..1e7: InputError naming n_layers (both blending functions)"
)
@pytest.mark.parametrize("bad", [0, -1, -100, 10**7 + 1, 10**9, 2**40, 2.5, 0.5, 99.99, 1e7 + 0.5])
def test_bad_layer_count(bad: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        B.gy_blending_variance(1.0, bad, 0.5)
    assert ei.value.argument == "n_layers"
    with pytest.raises(minephys.InputError) as ei2:
        B.variance_reduction_ratio(bad, 0.5)
    assert ei2.value.argument == "n_layers"


@pytest.mark.req("FR-004-12")
@pytest.mark.oracle("analytical", "the limits 1 and 1e7 are layer counts")
@pytest.mark.parametrize("n", [1, 10**7])
def test_layer_count_limits_are_accepted(n: int) -> None:
    assert math.isfinite(float(B.gy_blending_variance(1.0, n, 0.5)))
    assert math.isfinite(float(B.variance_reduction_ratio(n, 0.5)))


@pytest.mark.req("FR-004-12")
@pytest.mark.oracle(
    "analytical",
    "lag1_correlation must lie strictly inside (-1, 1): InputError naming lag1_correlation (both functions)",
)
@pytest.mark.parametrize("bad", [-1.0, 1.0, 1.0000001, -1.0000001, 1.5, -2.0, 100.0, math.nextafter(1.0, 2.0)])
def test_bad_correlation(bad: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        B.gy_blending_variance(1.0, 100, bad)
    assert ei.value.argument == "lag1_correlation"
    with pytest.raises(minephys.InputError) as ei2:
        B.variance_reduction_ratio(100, bad)
    assert ei2.value.argument == "lag1_correlation"


@pytest.mark.req("FR-004-12")
@pytest.mark.oracle(
    "analytical",
    "an input variance below zero is an InputError naming input_variance; a bad element in an array raises too",
)
def test_bad_input_variance_and_array_elements() -> None:
    for bad in (-1e-12, -1.0, -1e300):
        with pytest.raises(minephys.InputError) as ei:
            B.gy_blending_variance(bad, 100, 0.5)
        assert ei.value.argument == "input_variance"
    with pytest.raises(minephys.InputError) as ei2:
        B.gy_blending_variance(1.0, np.array([10, 100, 0]), 0.5)
    assert ei2.value.argument == "n_layers"
    with pytest.raises(minephys.InputError) as ei3:
        B.variance_reduction_ratio(100, np.array([0.5, 0.2, 1.0]))
    assert ei3.value.argument == "lag1_correlation"

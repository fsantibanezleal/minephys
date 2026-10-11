# ruff: noqa: E501
"""T-004-031 (P-004-08, FR-004-09): metamorphic properties of the blending variance and the variance reduction ratio.

P-004-08: `gy_blending_variance` equals sigma^2 / N for rho = 0, equals its explicit sum for N <= 1,000 (rtol
1e-10), is linear in `input_variance`; the variance reduction ratio is non-decreasing in N for rho >= 0 and
strictly decreasing in rho on (0, 1) for N >= 2. Further: for rho >= 0 the variance never falls below sigma^2
/ N (positive correlation cannot help), for rho <= 0 it never exceeds sigma^2 / N, the product of the ratio
and the variance (unit input variance) is 1, the variance of N layers never exceeds the input variance, and
the sign of rho is monotone: a smaller rho gives a smaller variance for N >= 2.

Generators (spec 004 P-004-08): N in 1..1e7, rho in (-0.99, 0.99), input variance in [1e-6, 1e6]; the explicit
sum is evaluated in 80-digit decimal arithmetic for N <= 1,000. Tolerance TC-1 (rtol 1e-12; the spec's
explicit-sum identity at 1e-10); ordering relations compare arguments at least a relative 1e-6 apart and allow
1e-12 rounding slack.

Oracle: analytical (the definition of the AR(1) variance of the mean as an explicit sum).
"""

from __future__ import annotations

from decimal import Decimal, getcontext

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import bulk as B

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

CFG = settings(deadline=None)
getcontext().prec = 80
RHO = st.floats(-0.99, 0.99)
RHO_POS = st.floats(0.0, 0.99)
N_ANY = st.integers(1, 10**7)
N_SMALL = st.integers(1, 1000)


def explicit(var: float, n: int, rho: float) -> float:
    r = Decimal(rho)
    big_n = Decimal(n)
    s = sum(((1 - Decimal(k) / big_n) * r**k for k in range(1, n)), Decimal(0))
    return float(Decimal(var) / big_n * (1 + 2 * s))


@pytest.mark.req("P-004-08")
@pytest.mark.oracle(
    "analytical", "uncorrelated layers: the variance of the mean is exactly sigma^2 / N, the ratio is N"
)
@CFG
@given(var=st.floats(1e-6, 1e6), n=N_ANY)
def test_independent_layers(var: float, n: int) -> None:
    assert float(B.gy_blending_variance(var, n, 0.0)) == pytest.approx(var / n, rel=1e-14)
    assert float(B.variance_reduction_ratio(n, 0.0)) == pytest.approx(float(n), rel=1e-14)


@pytest.mark.req("P-004-08")
@pytest.mark.oracle(
    "analytical",
    "the closed form equals the explicit sum of the definition for N <= 1,000 (rtol 1e-10 in the spec; 1e-12 here)",
)
@CFG
@given(var=st.floats(1e-6, 1e6), n=N_SMALL, rho=RHO)
def test_closed_form_equals_the_explicit_sum(var: float, n: int, rho: float) -> None:
    assert float(B.gy_blending_variance(var, n, rho)) == pytest.approx(explicit(var, n, rho), rel=1e-12)


@pytest.mark.req("P-004-08")
@pytest.mark.oracle("analytical", "linear in the input variance")
@CFG
@given(var=st.floats(1e-6, 1e6), k=st.floats(1e-3, 1e3), n=N_ANY, rho=RHO)
def test_linear_in_the_input_variance(var: float, k: float, n: int, rho: float) -> None:
    assert float(B.gy_blending_variance(k * var, n, rho)) == pytest.approx(
        k * float(B.gy_blending_variance(var, n, rho)), rel=1e-12
    )
    unit = float(B.gy_blending_variance(1.0, n, rho))
    assert float(B.gy_blending_variance(var, n, rho)) == pytest.approx(var * unit, rel=1e-12)
    assert unit * float(B.variance_reduction_ratio(n, rho)) == pytest.approx(1.0, rel=1e-12)


@pytest.mark.req("P-004-08")
@pytest.mark.oracle("analytical", "for rho >= 0 the variance reduction ratio is non-decreasing in the number of layers")
@CFG
@given(rho=RHO_POS, a=N_ANY, b=N_ANY)
def test_ratio_non_decreasing_in_n(rho: float, a: int, b: int) -> None:
    lo, hi = sorted((a, b))
    assert float(B.variance_reduction_ratio(lo, rho)) <= float(B.variance_reduction_ratio(hi, rho)) * (1.0 + 1e-12)


@pytest.mark.req("P-004-08")
@pytest.mark.oracle("analytical", "for N >= 2 the variance reduction ratio is strictly decreasing in rho on (0, 1)")
@CFG
@given(n=st.integers(2, 10**7), a=st.floats(0.0, 0.99), b=st.floats(0.0, 0.99))
def test_ratio_strictly_decreasing_in_rho(n: int, a: float, b: float) -> None:
    assume(abs(a - b) > 1e-6)
    lo, hi = sorted((a, b))
    assume(lo > 0.0)
    assert float(B.variance_reduction_ratio(n, lo)) > float(B.variance_reduction_ratio(n, hi))


@pytest.mark.req("P-004-08")
@pytest.mark.oracle(
    "analytical",
    "positive correlation cannot help (variance >= sigma^2 / N), anticorrelation cannot hurt (<=); neither exceeds sigma^2",
)
@CFG
@given(var=st.floats(1e-6, 1e6), n=N_ANY, rho=RHO)
def test_bounds_by_the_sign_of_rho(var: float, n: int, rho: float) -> None:
    v = float(B.gy_blending_variance(var, n, rho))
    independent = var / n
    if rho >= 0.0:
        assert v >= independent * (1.0 - 1e-12)
        assert v <= var * (1.0 + 1e-12)
    else:
        assert v <= independent * (1.0 + 1e-12)
        assert v > 0.0


@pytest.mark.req("P-004-08")
@pytest.mark.oracle("analytical", "for N >= 2 the variance increases with rho (a smaller correlation blends better)")
@CFG
@given(n=st.integers(2, 10**6), a=RHO, b=RHO)
def test_variance_increases_with_rho(n: int, a: float, b: float) -> None:
    assume(abs(a - b) > 1e-6)
    lo, hi = sorted((a, b))
    assert float(B.gy_blending_variance(1.0, n, lo)) < float(B.gy_blending_variance(1.0, n, hi))

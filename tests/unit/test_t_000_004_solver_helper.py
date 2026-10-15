"""T-000-004 (FR-000-17): the solver helper raises ConvergenceError and never returns an unconverged value.

Expected API, module `minephys._solve` (plan 000, Design table):

    bracketed_root(f, lo, hi, *, rtol=1e-12, max_iter=200) -> float
        Root of the scalar function f in the sign-changing bracket [lo, hi]. Converged means the relative step or
        bracket width is <= rtol. f(lo) and f(hi) must differ in sign (or one of them is exactly 0), otherwise
        InputError(argument="lo" or "hi" or "bracket"); non-finite lo or hi raise InputError.
    fixed_point(g, x0, *, rtol=1e-12, max_iter=200) -> float
        Iterates x <- g(x) from x0 until |g(x) - x| <= rtol * max(|x|, 1) or max_iter applications were made.

On failure (no convergence within max_iter, or a non-finite iterate) both raise `minephys.ConvergenceError` with
    last_iterate  the latest iterate x_k (for fixed_point: x_k after k applications of g),
    residual      |f(last_iterate)| (bracketed_root) or |g(last_iterate) - last_iterate| (fixed_point),
    iterations    the number of iterations performed, equal to max_iter when the cap was hit,
    argument      None.

Oracles: closed forms (sqrt(2), cube root of 27, the divergent map x -> 2x + 1 whose k-th iterate from 0 is 2**k - 1)
and the published Dottie number, the fixed point of cos (OEIS A003957: 0.7390851332151606416553...). Tolerance class
TC-3 (rtol 1e-9).
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import minephys
from minephys import _solve as S

DOTTIE = 0.7390851332151607  # OEIS A003957, rounded to float64


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "root of x^2 - 2 on [0, 2] is sqrt(2)")
def test_bracketed_root_sqrt2() -> None:
    r = S.bracketed_root(lambda x: x * x - 2.0, 0.0, 2.0)
    assert r == pytest.approx(math.sqrt(2.0), rel=1e-9)


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "cube root of 27 is 3; a decreasing function and a reversed bracket both work")
@pytest.mark.parametrize(
    ("f", "lo", "hi", "root"),
    [
        (lambda x: x**3 - 27.0, 0.0, 10.0, 3.0),
        (lambda x: 27.0 - x**3, 0.0, 10.0, 3.0),
        (lambda x: x**3 - 27.0, 10.0, 0.0, 3.0),
        (lambda x: x - 1e-6, -1.0, 1.0, 1e-6),
        (lambda x: x - 1e9, 0.0, 1e12, 1e9),
    ],
)
def test_bracketed_root_other_shapes(f, lo, hi, root) -> None:
    assert S.bracketed_root(f, lo, hi) == pytest.approx(root, rel=1e-9)


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "an endpoint that is exactly a root is returned")
def test_root_at_an_endpoint() -> None:
    assert S.bracketed_root(lambda x: x - 2.0, 2.0, 5.0) == pytest.approx(2.0, rel=1e-12)
    assert S.bracketed_root(lambda x: x - 5.0, 2.0, 5.0) == pytest.approx(5.0, rel=1e-12)


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "published Dottie number, OEIS A003957: the fixed point of cos")
def test_fixed_point_of_cosine_is_the_dottie_number() -> None:
    assert S.fixed_point(math.cos, 1.0) == pytest.approx(DOTTIE, rel=1e-9)


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "g(x) = x/2 + 1 has the fixed point 2; the start is irrelevant")
@pytest.mark.parametrize("x0", [-1e6, 0.0, 2.0, 1e6])
def test_fixed_point_of_a_contraction(x0: float) -> None:
    assert S.fixed_point(lambda x: x / 2.0 + 1.0, x0, max_iter=500) == pytest.approx(2.0, rel=1e-9)


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "the divergent map x -> 2x + 1 from 0 has the k-th iterate 2**k - 1")
def test_divergent_map_raises_with_the_documented_attributes() -> None:
    with pytest.raises(minephys.ConvergenceError) as ei:
        S.fixed_point(lambda x: 2.0 * x + 1.0, 0.0, max_iter=10)
    e = ei.value
    assert e.argument is None
    assert e.iterations == 10
    assert e.last_iterate == 2.0**10 - 1.0
    assert e.residual == pytest.approx(abs(2.0 * e.last_iterate + 1.0 - e.last_iterate), rel=1e-12)
    assert isinstance(e, RuntimeError)


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "invariant: a divergent map never returns, whatever the cap")
@settings(max_examples=60, deadline=None)
@given(max_iter=st.integers(1, 40), x0=st.floats(-10.0, 10.0))
def test_property_unconverged_value_is_never_returned(max_iter: int, x0: float) -> None:
    # x_{k+1} = 2 x_k + 1 has the fixed point -1; any start other than -1 diverges geometrically.
    if abs(x0 + 1.0) < 1e-3:
        x0 = 3.0
    with pytest.raises(minephys.ConvergenceError) as ei:
        S.fixed_point(lambda x: 2.0 * x + 1.0, x0, max_iter=max_iter)
    assert ei.value.iterations == max_iter
    assert ei.value.residual > 0.0


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "a bracket of width 2 cannot reach rtol 1e-15 in 3 bisection-type steps")
def test_bracketed_root_cap_raises_with_the_residual() -> None:
    f = lambda x: x * x - 2.0  # noqa: E731
    with pytest.raises(minephys.ConvergenceError) as ei:
        S.bracketed_root(f, 0.0, 2.0, rtol=1e-15, max_iter=3)
    e = ei.value
    assert e.argument is None
    assert e.iterations == 3
    assert e.residual == pytest.approx(abs(f(e.last_iterate)), rel=1e-9, abs=1e-15)
    assert math.isfinite(e.last_iterate)


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "a non-finite iterate is a convergence failure, not a returned NaN or inf")
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_iterate_raises_convergence_error(bad: float) -> None:
    with pytest.raises(minephys.ConvergenceError):
        S.fixed_point(lambda x: bad, 1.0, max_iter=50)


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "overflow of the iteration to inf is a convergence failure")
def test_overflowing_iteration_raises_convergence_error() -> None:
    with pytest.raises(minephys.ConvergenceError):
        S.fixed_point(lambda x: x * 1e200 + 1.0, 1.0, max_iter=100)


@pytest.mark.req("FR-000-17")
@pytest.mark.req("FR-000-14")
@pytest.mark.oracle("analytical", "x^2 + 1 has no sign change on [0, 2]")
def test_bracket_without_a_sign_change_is_an_input_error() -> None:
    with pytest.raises(minephys.InputError):
        S.bracketed_root(lambda x: x * x + 1.0, 0.0, 2.0)


@pytest.mark.req("FR-000-17")
@pytest.mark.req("FR-000-10")
@pytest.mark.oracle("hand-calculation", "non-finite bracket ends are hostile input")
@pytest.mark.parametrize("lo", [math.nan, -math.inf, math.inf])
def test_non_finite_bracket_is_an_input_error(lo: float) -> None:
    with pytest.raises(minephys.InputError):
        S.bracketed_root(lambda x: x - 1.0, lo, 2.0)
    with pytest.raises(minephys.InputError):
        S.bracketed_root(lambda x: x - 1.0, 0.0, lo)


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "metamorphic: scaling f by a non-zero constant leaves the root unchanged")
@settings(max_examples=60, deadline=None)
@given(r=st.floats(0.1, 100.0), c=st.sampled_from([-1e6, -3.0, 0.25, 7.0, 1e5]))
def test_property_root_is_invariant_to_scaling_f(r: float, c: float) -> None:
    f = lambda x: x**3 - r**3  # noqa: E731
    base = S.bracketed_root(f, 0.0, 200.0)
    scaled = S.bracketed_root(lambda x: c * f(x), 0.0, 200.0)
    assert base == pytest.approx(r, rel=1e-9)
    assert scaled == pytest.approx(base, rel=1e-9)


@pytest.mark.req("FR-000-17")
@pytest.mark.oracle("analytical", "metamorphic: shifting the unknown shifts the root by the same amount")
@settings(max_examples=60, deadline=None)
@given(r=st.floats(1.0, 50.0), shift=st.floats(0.0, 1000.0))
def test_property_root_shifts_with_the_unknown(r: float, shift: float) -> None:
    got = S.bracketed_root(lambda x: x - (r + shift), 0.0, 2000.0)
    assert got == pytest.approx(r + shift, rel=1e-9)

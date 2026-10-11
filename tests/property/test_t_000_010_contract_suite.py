"""T-000-010 (FR-000-05, FR-000-07, P-000-01, P-000-02, P-000-03): the shared contract suite, proven on fixtures.

Expected deliverable: the test-support module `tests/_contract_suite.py` (importable as `_contract_suite`, because
`tests/conftest.py` puts `tests/` on `sys.path`). Every check raises AssertionError when the function under test
violates the property and returns None otherwise; `kwargs` maps argument names to values, ndarray values are the
broadcastable operands, every other value (bool, str, None, int options) is passed through unchanged.

    check_purity(fn, kwargs)                         P-000-02, FR-000-05
        two calls give bitwise-identical results (same type, dtype, shape, bytes) and leave every ndarray in kwargs
        bitwise unchanged.
    check_elementwise(fn, kwargs)                    P-000-01, FR-000-07
        fn on the arrays equals fn on the scalars at each broadcast index (rtol 1e-14, atol 1e-14 * max|f|, TC-6);
        the array result is a float64 ndarray of the broadcast shape and the all-scalar result is numpy.float64.
    check_dtype_invariance(fn, kwargs)               P-000-03
        for ndarray operands whose values are exactly representable in float32, float32 and (when integral) int32
        variants give BITWISE the result of the float64 operands.
    check_seeded(fn, kwargs, rng_name="rng")         P-000-04, FR-000-18
        the same integer seed, or default_rng(seed), gives bitwise-identical output and two different seeds differ.
    check_hostile(fn, kwargs, argument, *, allow_posinf=False, boolean=False)       FR-000-10, FR-000-11
        for `argument` (a numerical operand of kwargs): NaN, -inf (and +inf unless allowed) as a scalar and as one
        array element raise InputError with .argument == argument (array: the message carries the flat index);
        str, bytes, None, complex, bool, object, datetime64 values raise InputTypeError with .argument == argument;
        with boolean=True the argument is a flag: 0, 1, 1.0 and "yes" must raise InputTypeError.
    check_shape_hostile(fn, kwargs, first, second)   FR-000-12
        arrays of shapes (3,) and (4,) for `first` and `second` raise InputError naming both arguments and shapes.

The fixtures below are built from the T-000-003 helpers (`minephys._validate`); the bad ones are the oracles for the
failure branches (hand-written violations).
"""

from __future__ import annotations

import _contract_suite as CS
import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from minephys import _random
from minephys import _validate as V

# ------------------------------------------------------------------ fixture functions


def good_scale(a, b):
    a = V.check_finite(V.as_float_array(a, "a"), "a")
    b = V.check_finite(V.as_float_array(b, "b"), "b")
    a, b = V.broadcast_all(a=a, b=b)
    return V.finalize(a * b + 0.1 * a, a, b)


def good_flagged(a, *, flag):
    a = V.check_finite(V.as_float_array(a, "a"), "a")
    V.check_bool(flag, "flag")
    return V.finalize(a * 2.0 if bool(np.all(flag)) else a, a)


def good_sampler(n, rng):
    return _random.as_generator(rng).normal(size=n)


_COUNTER = {"n": 0}


def impure_counter(a):
    _COUNTER["n"] += 1
    a = V.as_float_array(a, "a")
    return V.finalize(a + _COUNTER["n"], a)


def mutating(a):
    a = np.asarray(a)
    a *= 2.0
    return a.copy()


def non_elementwise(a):
    a = V.as_float_array(a, "a")
    return a - a.mean()


def python_float_result(a):
    a = V.as_float_array(a, "a")
    return float(a) if a.ndim == 0 else a * 1.0


def dtype_sensitive(a):
    return np.asarray(a) * 0.1  # NEP 50: a float32 operand stays float32 here


def unseeded(n, rng):
    return np.random.default_rng().normal(size=n)


def seed_ignoring(n, rng):
    return np.random.default_rng(7).normal(size=n)


def lax_nan_passthrough(a):
    return np.asarray(a, dtype=float) * 2.0


def lax_wrong_type(a):
    a = np.asarray(a, dtype=object).astype(float)
    return a * 2.0


def lax_shape(a, b):
    return np.asarray(a, dtype=float)


A_VALUES = np.array([[0.1, 0.25], [3.0, -7.5]])
B_VALUES = np.array([0.5, 2.0])


# ------------------------------------------------------------------ the good fixtures pass every check


@pytest.mark.req("FR-000-05")
@pytest.mark.req("P-000-02")
@pytest.mark.oracle("hand-calculation", "a pure fixture passes the purity check")
def test_purity_accepts_a_pure_function() -> None:
    CS.check_purity(good_scale, {"a": A_VALUES, "b": B_VALUES})
    CS.check_purity(good_scale, {"a": np.float64(2.0), "b": np.float64(3.0)})


@pytest.mark.req("FR-000-05")
@pytest.mark.req("P-000-02")
@pytest.mark.oracle("hand-calculation", "a counter in global state breaks bitwise repeatability")
def test_purity_rejects_global_state() -> None:
    with pytest.raises(AssertionError):
        CS.check_purity(impure_counter, {"a": np.array([1.0, 2.0])})


@pytest.mark.req("FR-000-05")
@pytest.mark.req("P-000-02")
@pytest.mark.oracle("hand-calculation", "writing into the caller's array is detected by the bitwise comparison")
def test_purity_rejects_input_mutation() -> None:
    with pytest.raises(AssertionError):
        CS.check_purity(mutating, {"a": np.array([1.0, 2.0])})


@pytest.mark.req("FR-000-07")
@pytest.mark.req("P-000-01")
@pytest.mark.oracle("hand-calculation", "an elementwise fixture passes; its result type rules are checked")
def test_elementwise_accepts_an_elementwise_function() -> None:
    CS.check_elementwise(good_scale, {"a": A_VALUES, "b": B_VALUES})
    CS.check_elementwise(good_scale, {"a": np.float64(2.0), "b": np.float64(3.0)})
    CS.check_elementwise(good_scale, {"a": np.empty(0), "b": np.float64(1.0)})
    CS.check_elementwise(good_flagged, {"a": A_VALUES, "flag": True})


@pytest.mark.req("FR-000-07")
@pytest.mark.req("P-000-01")
@pytest.mark.oracle("hand-calculation", "a - mean(a) couples the elements, so array and scalar evaluation disagree")
def test_elementwise_rejects_a_coupled_function() -> None:
    with pytest.raises(AssertionError):
        CS.check_elementwise(non_elementwise, {"a": np.array([1.0, 2.0, 6.0])})


@pytest.mark.req("FR-000-07")
@pytest.mark.oracle("hand-calculation", "FR-000-07: all-scalar inputs must return numpy.float64, not a Python float")
def test_elementwise_rejects_a_python_float_result() -> None:
    with pytest.raises(AssertionError):
        CS.check_elementwise(python_float_result, {"a": np.float64(2.0)})


@pytest.mark.req("P-000-03")
@pytest.mark.oracle("hand-calculation", "float32 and int32 operands give bitwise the float64 result")
def test_dtype_invariance_accepts_the_good_fixture_and_rejects_dtype_sensitive() -> None:
    CS.check_dtype_invariance(good_scale, {"a": np.array([0.5, 0.25, 4.0, -8.0]), "b": np.array([1.0, 2.0, 3.0, 4.0])})
    with pytest.raises(AssertionError):
        CS.check_dtype_invariance(dtype_sensitive, {"a": np.array([3.0, 7.0, 10.0, 1.0 / 8.0])})


@pytest.mark.req("P-000-03")
@pytest.mark.oracle("hand-calculation", "integral float64 values are also cast to int32 and compared bitwise")
def test_dtype_invariance_covers_integer_operands() -> None:
    CS.check_dtype_invariance(good_scale, {"a": np.array([1.0, 2.0, -3.0]), "b": np.array([4.0, 5.0, 6.0])})


@pytest.mark.req("FR-000-18")
@pytest.mark.req("P-000-04")
@pytest.mark.oracle("hand-calculation", "seeded sampler passes; an unseeded or seed-ignoring one fails")
def test_seeded_check() -> None:
    CS.check_seeded(good_sampler, {"n": 5})
    with pytest.raises(AssertionError):
        CS.check_seeded(unseeded, {"n": 5})
    with pytest.raises(AssertionError):
        CS.check_seeded(seed_ignoring, {"n": 5})


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("hand-calculation", "the validated fixture passes the hostile battery on both operands")
def test_hostile_battery_accepts_a_validated_function() -> None:
    CS.check_hostile(good_scale, {"a": A_VALUES, "b": B_VALUES}, "a")
    CS.check_hostile(good_scale, {"a": A_VALUES, "b": B_VALUES}, "b")
    CS.check_hostile(good_flagged, {"a": A_VALUES, "flag": True}, "flag", boolean=True)


@pytest.mark.req("FR-000-10")
@pytest.mark.oracle("hand-calculation", "allow_posinf: +inf is accepted for that argument only")
def test_hostile_battery_honours_allow_posinf() -> None:
    def f(limit):
        x = V.check_finite(V.as_float_array(limit, "limit"), "limit", allow_posinf=True)
        return V.finalize(np.where(np.isinf(x), 0.0, x), x)

    CS.check_hostile(f, {"limit": np.array([1.0, 2.0])}, "limit", allow_posinf=True)
    with pytest.raises(AssertionError):
        CS.check_hostile(f, {"limit": np.array([1.0, 2.0])}, "limit", allow_posinf=False)


@pytest.mark.req("FR-000-10")
@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("hand-calculation", "a function that lets NaN or a wrong type through is caught")
def test_hostile_battery_rejects_lax_functions() -> None:
    with pytest.raises(AssertionError):
        CS.check_hostile(lax_nan_passthrough, {"a": A_VALUES}, "a")
    with pytest.raises(AssertionError):
        CS.check_hostile(lax_wrong_type, {"a": A_VALUES}, "a")


@pytest.mark.req("FR-000-12")
@pytest.mark.oracle("hand-calculation", "(3,) and (4,) must not broadcast")
def test_shape_hostile() -> None:
    CS.check_shape_hostile(good_scale, {"a": A_VALUES, "b": B_VALUES}, "a", "b")
    with pytest.raises(AssertionError):
        CS.check_shape_hostile(lax_shape, {"a": A_VALUES, "b": B_VALUES}, "a", "b")


# ------------------------------------------------------------------ the suite is usable under Hypothesis


@pytest.mark.req("P-000-01")
@pytest.mark.req("P-000-02")
@pytest.mark.req("P-000-03")
@pytest.mark.oracle("hand-calculation", "properties P-000-01..03 hold for random float32-representable operands")
@settings(max_examples=60, deadline=None)
@given(
    a=st.lists(st.floats(-1e3, 1e3, width=32), min_size=0, max_size=12),
    b=st.floats(-1e3, 1e3, width=32),
)
def test_property_good_fixture_satisfies_all_checks(a: list[float], b: float) -> None:
    kwargs = {"a": np.array(a, dtype=np.float64), "b": np.float64(b)}
    CS.check_purity(good_scale, kwargs)
    CS.check_elementwise(good_scale, kwargs)
    CS.check_dtype_invariance(good_scale, kwargs)

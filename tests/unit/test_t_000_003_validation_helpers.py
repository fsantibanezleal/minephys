"""T-000-003 (FR-000-07, FR-000-10 to FR-000-16): the validation helpers, proven on fixture functions.

Expected API, module `minephys._validate` (plan 000, Design table; the argument names below are fixed by this test):

    as_float_array(value, name) -> ndarray[float64]
        Python real scalars, NumPy real scalars and arrays of any real dtype become float64 (0-d for a scalar).
        Raises InputTypeError(argument=name) for str, bytes, None, complex, bool, object, datetime64 and
        timedelta64 values and arrays. A Python int that cannot be represented as float64 raises InputError(name).
    check_finite(arr, name, *, allow_posinf=False) -> arr
        InputError(argument=name) on NaN, -inf and (unless allowed) +inf; for arrays the message carries the flat
        index of the FIRST offending element.
    check_domain(arr, name, *, lo=None, hi=None, lo_open=False, hi_open=False) -> arr
        InputError(argument=name); the message carries the violated bound and the received value.
    check_option(value, name, allowed) -> value
        InputError(argument=name) listing the allowed values; exact, case-sensitive match.
    check_bool(value, name) -> bool or ndarray[bool]
        InputTypeError(argument=name) unless the value is a bool, numpy bool_ or a boolean array.
    check_rank(arr, name, ndim) -> arr
        InputError(argument=name) naming the shape when arr.ndim != ndim.
    check_size(arr, name, *, min_size=None, max_size=None) -> arr
        InputError(argument=name) naming the received size and the violated bound (aggregate functions).
    broadcast_all(**named_arrays) -> tuple[ndarray, ...]    (in keyword order)
        InputError naming the arguments and their shapes when NumPy cannot broadcast them.
    finalize(result, *inputs) -> numpy.float64 | ndarray[float64]
        numpy.float64 when every input is 0-d, else a float64 ndarray of the broadcast shape.
    warn_validity(arr, name, lo, hi, row) -> None
        emits ValidityWarning(argument=name, bounds=(lo, hi), row=row) if any element lies outside [lo, hi]; the
        message names the argument, the received value or range, the bounds and the row id; execution continues.

Oracles: hand-written expectations from spec 000 FR-000-07 and FR-000-10 to FR-000-16 (hand calculation) and NumPy's
own `astype(float64)` as the reference cast. Hostile inputs: empty, NaN, inf, wrong dtype, huge, unicode.
"""

from __future__ import annotations

import re
import warnings

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra import numpy as hnp

import minephys
from minephys import _validate as V

REAL_DTYPES = [
    np.int8,
    np.int16,
    np.int32,
    np.int64,
    np.uint8,
    np.uint16,
    np.uint32,
    np.uint64,
    np.float16,
    np.float32,
    np.float64,
]


def fx_scale(a, b):
    """Fixture elementwise function a*b built from the helpers only."""
    a = V.check_finite(V.as_float_array(a, "a"), "a")
    b = V.check_finite(V.as_float_array(b, "b"), "b")
    a, b = V.broadcast_all(a=a, b=b)
    return V.finalize(a * b, a, b)


# ---------------------------------------------------------------- FR-000-07


@pytest.mark.req("FR-000-07")
@pytest.mark.oracle("hand-calculation", "scalars in, numpy.float64 out; 3.0 * 2.0 = 6.0")
@pytest.mark.parametrize("a", [3, 3.0, np.float32(3), np.int64(3), np.uint8(3), np.float16(3)])
def test_all_scalar_kinds_return_numpy_float64(a) -> None:
    r = fx_scale(a, 2.0)
    assert type(r) is np.float64
    assert r == 6.0


@pytest.mark.req("FR-000-07")
@pytest.mark.oracle("hand-calculation", "[1,2,3] * 2 = [2,4,6]; broadcast of (3,1) with (4,) is (3,4)")
def test_arrays_broadcast_and_return_float64_ndarray() -> None:
    r = fx_scale(np.array([1, 2, 3], dtype=np.int16), 2.0)
    assert type(r) is np.ndarray
    assert r.dtype == np.float64
    np.testing.assert_array_equal(r, [2.0, 4.0, 6.0])
    out = fx_scale(np.arange(3.0).reshape(3, 1), np.arange(4.0))
    assert out.shape == (3, 4)
    assert out.dtype == np.float64
    np.testing.assert_array_equal(out, np.arange(3.0).reshape(3, 1) * np.arange(4.0))


@pytest.mark.req("FR-000-07")
@pytest.mark.oracle("hand-calculation", "a 0-d array is a scalar for the return rule only when every input is 0-d")
def test_one_array_input_makes_the_result_an_array() -> None:
    r = fx_scale(np.float64(2.0), np.array([4.0]))
    assert isinstance(r, np.ndarray)
    assert r.shape == (1,)


@pytest.mark.req("FR-000-07")
@pytest.mark.oracle("reference-implementation", "numpy astype(float64) is the reference cast")
@pytest.mark.parametrize("dtype", REAL_DTYPES)
def test_every_real_dtype_is_upcast_exactly_like_numpy(dtype) -> None:
    info = np.iinfo(dtype) if np.issubdtype(dtype, np.integer) else np.finfo(dtype)
    raw = np.array([0, 1, 2, info.max], dtype=dtype)
    got = V.as_float_array(raw, "x")
    assert got.dtype == np.float64
    np.testing.assert_array_equal(got, raw.astype(np.float64))


@pytest.mark.req("FR-000-07")
@pytest.mark.oracle("hand-calculation", "empty arrays: empty float64 result of the broadcast shape")
def test_empty_arrays_return_empty_float64_of_the_broadcast_shape() -> None:
    r = fx_scale(np.empty(0), 2.0)
    assert r.shape == (0,)
    assert r.dtype == np.float64
    r2 = fx_scale(np.empty((0, 3)), np.ones(3))
    assert r2.shape == (0, 3)
    assert r2.dtype == np.float64
    r3 = fx_scale(np.empty(0, dtype=np.int32), np.empty((2, 0), dtype=np.float32))
    assert r3.shape == (2, 0)
    assert r3.dtype == np.float64


@pytest.mark.req("FR-000-07")
@pytest.mark.req("FR-000-12")
@pytest.mark.oracle("hand-calculation", "(0,) cannot broadcast with (3,)")
def test_empty_array_with_a_mismatched_nonempty_shape_does_not_broadcast() -> None:
    with pytest.raises(minephys.InputError) as ei:
        fx_scale(np.empty(0), np.ones(3))
    assert ei.value.argument in {"a", "b", "a, b", "a and b"} or "a" in str(ei.value)


@pytest.mark.req("FR-000-07")
@pytest.mark.oracle("reference-implementation", "numpy astype(float64); P-000-03 float32 == cast-first")
@settings(max_examples=100, deadline=None)
@given(
    hnp.arrays(
        dtype=st.sampled_from([np.float32, np.int32, np.int16, np.uint8]),
        shape=hnp.array_shapes(max_dims=2, max_side=6, min_side=0),
        elements=None,
    )
)
def test_property_narrow_dtypes_give_bitwise_the_float64_cast(arr) -> None:
    if arr.dtype.kind == "f":
        arr = np.where(np.isfinite(arr), arr, np.float32(0)).astype(arr.dtype)
    expected = fx_scale(arr.astype(np.float64), 1.5)
    got = fx_scale(arr, 1.5)
    assert got.tobytes() == expected.tobytes()
    assert got.shape == expected.shape


@pytest.mark.req("FR-000-07")
@pytest.mark.req("FR-000-10")
@pytest.mark.oracle("hand-calculation", "an integer larger than float64 max is not finite after the cast")
def test_python_int_beyond_float64_range_is_an_input_error_not_an_overflow_error() -> None:
    with pytest.raises(minephys.InputError) as ei:
        V.as_float_array(10**400, "huge")
    assert ei.value.argument == "huge"


# ---------------------------------------------------------------- FR-000-10


@pytest.mark.req("FR-000-10")
@pytest.mark.oracle("hand-calculation", "NaN, +inf and -inf scalars are rejected naming the argument")
@pytest.mark.parametrize(
    "bad", [np.nan, np.inf, -np.inf, float("nan"), float("inf"), np.float32("nan"), np.float16("inf")]
)
def test_non_finite_scalar_raises_input_error_naming_the_argument(bad) -> None:
    with pytest.raises(minephys.InputError) as ei:
        fx_scale(bad, 1.0)
    assert ei.value.argument == "a"
    assert "a" in str(ei.value)
    with pytest.raises(minephys.InputError) as ei2:
        fx_scale(1.0, bad)
    assert ei2.value.argument == "b"


@pytest.mark.req("FR-000-10")
@pytest.mark.oracle(
    "hand-calculation", "the first offending element of a (2,3) array filled in C order is flat index 4"
)
def test_array_message_names_the_flat_index_of_the_first_offender() -> None:
    arr = np.ones((2, 3))
    arr[1, 1] = np.nan  # flat index 4
    arr[1, 2] = np.inf  # flat index 5, must not be the one reported
    with pytest.raises(minephys.InputError) as ei:
        V.check_finite(V.as_float_array(arr, "samples"), "samples")
    msg = str(ei.value)
    assert ei.value.argument == "samples"
    assert "samples" in msg
    assert re.search(r"\b4\b", msg), msg
    assert not re.search(r"\b5\b", msg), msg


@pytest.mark.req("FR-000-10")
@pytest.mark.oracle("hand-calculation", "a module spec may allow +inf (speed_limit); NaN and -inf stay errors")
def test_allow_posinf_accepts_plus_infinity_only() -> None:
    out = V.check_finite(V.as_float_array(np.array([1.0, np.inf]), "limit"), "limit", allow_posinf=True)
    assert out[1] == np.inf
    for bad in (np.nan, -np.inf):
        with pytest.raises(minephys.InputError) as ei:
            V.check_finite(V.as_float_array(np.array([1.0, bad]), "limit"), "limit", allow_posinf=True)
        assert ei.value.argument == "limit"
    with pytest.raises(minephys.InputError):
        V.check_finite(V.as_float_array(np.inf, "limit"), "limit")


@pytest.mark.req("FR-000-10")
@pytest.mark.oracle("hand-calculation", "invariant: any single non-finite element is found at its flat index")
@settings(max_examples=150, deadline=None)
@given(
    shape=hnp.array_shapes(min_dims=1, max_dims=3, min_side=1, max_side=5),
    bad=st.sampled_from([np.nan, np.inf, -np.inf]),
    data=st.data(),
)
def test_property_any_single_non_finite_element_is_reported_at_its_index(shape, bad, data) -> None:
    size = int(np.prod(shape))
    idx = data.draw(st.integers(0, size - 1))
    arr = np.zeros(size)
    arr[idx] = bad
    with pytest.raises(minephys.InputError) as ei:
        V.check_finite(V.as_float_array(arr.reshape(shape), "v"), "v")
    assert ei.value.argument == "v"
    assert re.search(rf"(?<![0-9.]){idx}(?![0-9.])", str(ei.value).replace(str(shape), "")), str(ei.value)


@pytest.mark.req("FR-000-10")
@pytest.mark.oracle("hand-calculation", "finite arrays pass through unchanged, including empty ones")
def test_finite_arrays_pass_unchanged() -> None:
    arr = np.array([-1e308, 0.0, 1e308])
    assert V.check_finite(arr, "x") is arr or np.array_equal(V.check_finite(arr, "x"), arr)
    assert V.check_finite(np.empty(0), "x").shape == (0,)


# ---------------------------------------------------------------- FR-000-11


@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("hand-calculation", "non-real-numeric values are a TypeError subclass naming the argument")
@pytest.mark.parametrize(
    "bad",
    [
        "3.0",
        "",
        "\uff13",
        b"3",
        None,
        1 + 2j,
        np.complex128(1),
        True,
        np.bool_(True),
        np.array([True, False]),
        np.array([1 + 0j]),
        np.array(["a", "b"]),
        np.array([b"a"]),
        np.array([None], dtype=object),
        np.array([1.0], dtype=object),
        np.datetime64("2026-10-11"),
        np.array(["2026-10-11"], dtype="datetime64[D]"),
        np.timedelta64(5, "s"),
        np.array([5], dtype="timedelta64[s]"),
        object(),
    ],
    ids=repr,
)
def test_non_real_numeric_values_raise_input_type_error(bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        V.as_float_array(bad, "mass")
    assert ei.value.argument == "mass"
    assert "mass" in str(ei.value)
    with pytest.raises(TypeError):
        fx_scale(bad, 1.0)


@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("hand-calculation", "a declared boolean flag must be boolean, 1 and 'yes' are not")
@pytest.mark.parametrize("good", [True, False, np.bool_(True), np.array([True, False, True])])
def test_check_bool_accepts_booleans(good) -> None:
    out = V.check_bool(good, "on_trolley")
    assert np.asarray(out).dtype == np.bool_


@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("hand-calculation", "a declared boolean flag must be boolean, 1 and 'yes' are not")
@pytest.mark.parametrize(
    "bad", [1, 0, 1.0, "yes", None, np.array([1, 0]), np.array([0.0, 1.0]), np.array(["a"])], ids=repr
)
def test_check_bool_rejects_non_booleans(bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        V.check_bool(bad, "on_trolley")
    assert ei.value.argument == "on_trolley"


# ---------------------------------------------------------------- FR-000-12


@pytest.mark.req("FR-000-12")
@pytest.mark.oracle("hand-calculation", "(3,) and (4,) do not broadcast; the message names both arguments and shapes")
def test_incompatible_shapes_raise_naming_arguments_and_shapes() -> None:
    with pytest.raises(minephys.InputError) as ei:
        fx_scale(np.ones(3), np.ones(4))
    msg = str(ei.value)
    assert "a" in msg
    assert "b" in msg
    assert "(3,)" in msg
    assert "(4,)" in msg


@pytest.mark.req("FR-000-12")
@pytest.mark.oracle("hand-calculation", "a 2-D array where a 1-D array is required is a rank error naming the shape")
def test_wrong_rank_raises_naming_the_argument_and_shape() -> None:
    with pytest.raises(minephys.InputError) as ei:
        V.check_rank(np.ones((2, 3)), "length", 1)
    assert ei.value.argument == "length"
    assert "(2, 3)" in str(ei.value)
    with pytest.raises(minephys.InputError):
        V.check_rank(np.float64(1.0).reshape(()), "length", 1)
    ok = np.ones(4)
    assert V.check_rank(ok, "length", 1).shape == (4,)


# ---------------------------------------------------------------- FR-000-13


@pytest.mark.req("FR-000-13")
@pytest.mark.oracle("hand-calculation", "min 2 and cap 5: sizes 1 and 6 raise, 2 and 5 pass")
@pytest.mark.parametrize(("n", "ok"), [(0, False), (1, False), (2, True), (5, True), (6, False)])
def test_aggregate_size_bounds(n: int, ok: bool) -> None:
    arr = np.ones(n)
    if ok:
        assert V.check_size(arr, "stations", min_size=2, max_size=5).shape == (n,)
        return
    with pytest.raises(minephys.InputError) as ei:
        V.check_size(arr, "stations", min_size=2, max_size=5)
    msg = str(ei.value)
    assert ei.value.argument == "stations"
    assert str(n) in msg  # the received size
    assert ("2" in msg) if n < 2 else ("5" in msg)  # the violated bound


@pytest.mark.req("FR-000-13")
@pytest.mark.oracle("hand-calculation", "a huge cap is a bound like any other")
def test_huge_array_over_the_cap_is_rejected() -> None:
    arr = np.zeros(100_001)
    with pytest.raises(minephys.InputError) as ei:
        V.check_size(arr, "length", min_size=1, max_size=100_000)
    assert ei.value.argument == "length"
    assert "100001" in str(ei.value).replace(",", "").replace("_", "")


# ---------------------------------------------------------------- FR-000-14


@pytest.mark.req("FR-000-14")
@pytest.mark.oracle("hand-calculation", "spec FR-000-14 example: a negative mass names the argument, bound and value")
def test_negative_mass_names_argument_bound_and_value() -> None:
    with pytest.raises(minephys.InputError) as ei:
        V.check_domain(V.as_float_array(-3.0, "mass"), "mass", lo=0.0, lo_open=True)
    msg = str(ei.value)
    assert ei.value.argument == "mass"
    assert "mass" in msg
    assert "-3" in msg
    assert "0" in msg


@pytest.mark.req("FR-000-14")
@pytest.mark.oracle("hand-calculation", "closed versus open bounds on [0, 1]")
@pytest.mark.parametrize(
    ("value", "kwargs", "ok"),
    [
        (0.0, {"lo": 0.0}, True),
        (0.0, {"lo": 0.0, "lo_open": True}, False),
        (1.0, {"hi": 1.0}, True),
        (1.0, {"hi": 1.0, "hi_open": True}, False),
        (0.5, {"lo": 0.0, "hi": 1.0}, True),
        (1.0 + 2**-52, {"lo": 0.0, "hi": 1.0}, False),
        (-(2.0**-1074), {"lo": 0.0}, False),
        (1e308, {"lo": 0.0}, True),
        (-1e308, {"hi": 0.0}, True),
    ],
)
def test_domain_bounds(value: float, kwargs: dict, ok: bool) -> None:
    arr = V.as_float_array(value, "fraction")
    if ok:
        assert V.check_domain(arr, "fraction", **kwargs) is not None
    else:
        with pytest.raises(minephys.InputError) as ei:
            V.check_domain(arr, "fraction", **kwargs)
        assert ei.value.argument == "fraction"


@pytest.mark.req("FR-000-14")
@pytest.mark.oracle("hand-calculation", "one violating element of an array is enough")
@settings(max_examples=100, deadline=None)
@given(
    xs=st.lists(st.floats(0.0, 1.0), min_size=1, max_size=20),
    pos=st.integers(0, 19),
    outside=st.sampled_from([-0.25, 1.25, -1e9, 7.0]),
)
def test_property_a_single_out_of_domain_element_raises(xs, pos, outside) -> None:
    arr = np.array(xs)
    V.check_domain(arr, "p", lo=0.0, hi=1.0)
    arr[pos % len(arr)] = outside
    with pytest.raises(minephys.InputError) as ei:
        V.check_domain(arr, "p", lo=0.0, hi=1.0)
    assert ei.value.argument == "p"


# ---------------------------------------------------------------- FR-000-15


@pytest.mark.req("FR-000-15")
@pytest.mark.oracle("hand-calculation", "allowed values are listed; match is exact and case-sensitive")
def test_option_accepts_only_exact_allowed_strings() -> None:
    allowed = ("queue", "delay")
    assert V.check_option("queue", "station_type", allowed) == "queue"
    for bad in ("Queue", "QUEUE", " queue", "queue ", "delay\n", "", "que", "\uff51ueue", "q\u057deue", "\u017fueue"):
        with pytest.raises(minephys.InputError) as ei:
            V.check_option(bad, "station_type", allowed)
        assert ei.value.argument == "station_type"
        assert "queue" in str(ei.value)
        assert "delay" in str(ei.value)


@pytest.mark.req("FR-000-15")
@pytest.mark.oracle("hand-calculation", "a non-string option is not one of the allowed values either")
@pytest.mark.parametrize("bad", [None, 1, 2.5, b"queue", ("queue",)], ids=repr)
def test_option_rejects_non_strings(bad) -> None:
    with pytest.raises((minephys.InputError, minephys.InputTypeError)) as ei:
        V.check_option(bad, "station_type", ("queue", "delay"))
    assert ei.value.argument == "station_type"


# ---------------------------------------------------------------- FR-000-16


@pytest.mark.req("FR-000-16")
@pytest.mark.oracle("hand-calculation", "12.5 lies outside [0, 10]: one warning with its attributes; inside: none")
def test_validity_warning_content_and_attributes() -> None:
    arr = V.as_float_array(12.5, "ucs")
    with pytest.warns(minephys.ValidityWarning) as rec:
        V.warn_validity(arr, "ucs", 0.0, 10.0, "ucs_validity")
    assert len(rec) == 1
    w = rec[0].message
    assert w.argument == "ucs"
    assert tuple(w.bounds) == (0.0, 10.0)
    assert w.row == "ucs_validity"
    msg = str(w)
    for token in ("ucs", "12.5", "10", "ucs_validity"):
        assert token in msg, (token, msg)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        V.warn_validity(V.as_float_array(10.0, "ucs"), "ucs", 0.0, 10.0, "ucs_validity")  # bounds are inclusive
        V.warn_validity(V.as_float_array(0.0, "ucs"), "ucs", 0.0, 10.0, "ucs_validity")
        V.warn_validity(np.empty(0), "ucs", 0.0, 10.0, "ucs_validity")


@pytest.mark.req("FR-000-16")
@pytest.mark.oracle("hand-calculation", "a unit tripwire uses the row id 'tripwire'")
def test_tripwire_row_and_the_function_still_returns() -> None:
    def fx(grade):
        g = V.check_finite(V.as_float_array(grade, "grade"), "grade")
        V.warn_validity(g, "grade", -0.3, 0.3, "tripwire")
        return V.finalize(g * 2.0, g)

    with pytest.warns(minephys.ValidityWarning) as rec:
        out = fx(30.0)  # percent passed as a fraction
    assert out == 60.0
    assert rec[0].message.row == "tripwire"
    assert rec[0].message.argument == "grade"
    assert "30" in str(rec[0].message)


@pytest.mark.req("FR-000-16")
@pytest.mark.oracle("hand-calculation", "arrays: the received range reaches the message")
def test_array_range_reaches_the_message() -> None:
    arr = V.as_float_array(np.array([1.0, 12.5, 15.0]), "x")
    with pytest.warns(minephys.ValidityWarning) as rec:
        V.warn_validity(arr, "x", 0.0, 10.0, "row_x")
    assert "15" in str(rec[0].message)


@pytest.mark.req("FR-000-16")
@pytest.mark.oracle("hand-calculation", "invariant: a warning is emitted iff some element is outside [lo, hi]")
@settings(max_examples=150, deadline=None)
@given(
    xs=st.lists(st.floats(-100, 100), min_size=0, max_size=10),
    lo=st.floats(-50, 0),
    hi=st.floats(0, 50),
)
def test_property_warns_iff_any_element_is_outside(xs, lo, hi) -> None:
    arr = np.array(xs, dtype=float)
    outside = bool(np.any((arr < lo) | (arr > hi)))
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        V.warn_validity(arr, "x", lo, hi, "r")
    got = [w for w in rec if issubclass(w.category, minephys.ValidityWarning)]
    assert (len(got) >= 1) is outside

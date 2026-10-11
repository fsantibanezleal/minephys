"""T-000-005 (FR-000-18, P-000-04): the random-source helper.

Expected API, module `minephys._random`:

    as_generator(rng) -> numpy.random.Generator
        `rng` has NO default (a sampling function takes it as a required argument).
        * an integer seed 0 <= seed <= 2**32 - 1 (Python int or NumPy integer) gives `numpy.random.default_rng(seed)`;
        * a `numpy.random.Generator` is returned as the very same object (so the caller's stream advances);
        * None, floats, strings, bytes, bool, SeedSequence, legacy RandomState and arrays raise
          `minephys.InputTypeError(argument="rng")`;
        * an integer outside [0, 2**32 - 1] raises `minephys.InputError(argument="rng")`.
    The helper never touches NumPy's global random state.

Oracle: `numpy.random.default_rng(seed)` is the reference implementation; fixture sampling functions are built from
the helper only. Tolerance: exact (bitwise).
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import minephys
from minephys import _random as R


def fx_sample(n, rng):
    """Fixture sampling function: n normal draws from the helper's generator."""
    g = R.as_generator(rng)
    return g.normal(size=n)


@pytest.mark.req("FR-000-18")
@pytest.mark.oracle("reference-implementation", "numpy.random.default_rng(seed)")
@given(seed=st.integers(0, 2**32 - 1))
@settings(max_examples=100, deadline=None)
def test_integer_seed_matches_default_rng_bitwise(seed: int) -> None:
    got = fx_sample(7, seed)
    ref = np.random.default_rng(seed).normal(size=7)
    assert got.tobytes() == ref.tobytes()


@pytest.mark.req("FR-000-18")
@pytest.mark.req("P-000-04")
@pytest.mark.oracle("reference-implementation", "numpy.random.default_rng(seed)")
@given(seed=st.integers(0, 2**32 - 1), n=st.integers(0, 50))
@settings(max_examples=100, deadline=None)
def test_property_same_seed_or_generator_from_it_is_bitwise_identical(seed: int, n: int) -> None:
    a = fx_sample(n, seed)
    b = fx_sample(n, seed)
    c = fx_sample(n, np.random.default_rng(seed))
    assert a.tobytes() == b.tobytes() == c.tobytes()
    assert a.dtype == np.float64
    assert a.shape == (n,)


@pytest.mark.req("FR-000-18")
@pytest.mark.req("P-000-04")
@pytest.mark.oracle("reference-implementation", "different default_rng seeds start different streams")
@given(s1=st.integers(0, 2**32 - 1), s2=st.integers(0, 2**32 - 1), n=st.integers(2, 30))
@settings(max_examples=100, deadline=None)
def test_property_different_seeds_give_different_output(s1: int, s2: int, n: int) -> None:
    if s1 == s2:
        s2 = (s1 + 1) % 2**32
    assert fx_sample(n, s1).tobytes() != fx_sample(n, s2).tobytes()


@pytest.mark.req("FR-000-18")
@pytest.mark.oracle("reference-implementation", "a Generator is consumed in place: two draws of 3 equal one draw of 6")
def test_generator_is_passed_through_not_copied() -> None:
    g = np.random.default_rng(2026)
    assert R.as_generator(g) is g
    g1 = np.random.default_rng(2026)
    first = fx_sample(3, g1)
    second = fx_sample(3, g1)
    ref = np.random.default_rng(2026).normal(size=6)
    assert np.concatenate([first, second]).tobytes() == ref.tobytes()


@pytest.mark.req("FR-000-18")
@pytest.mark.oracle("hand-calculation", "seeds 0 and 2**32 - 1 are the inclusive ends of the accepted range")
@pytest.mark.parametrize("seed", [0, 1, 2**32 - 1, np.int64(5), np.uint32(2**32 - 1), np.int32(7)])
def test_seed_range_ends_and_numpy_integers_are_accepted(seed) -> None:
    assert isinstance(R.as_generator(seed), np.random.Generator)
    ref = np.random.default_rng(int(seed)).random(3)
    assert R.as_generator(seed).random(3).tobytes() == ref.tobytes()


@pytest.mark.req("FR-000-18")
@pytest.mark.oracle("hand-calculation", "an integer outside 0 .. 2**32 - 1 is an input error naming rng")
@pytest.mark.parametrize("seed", [-1, 2**32, 2**64, -(2**40), np.int64(-3)])
def test_out_of_range_integer_seed_raises_input_error(seed) -> None:
    with pytest.raises(minephys.InputError) as ei:
        R.as_generator(seed)
    assert ei.value.argument == "rng"


@pytest.mark.req("FR-000-18")
@pytest.mark.oracle(
    "hand-calculation", "hostile: None, float, str, bytes, bool, arrays and legacy generators are not seeds"
)
@pytest.mark.parametrize(
    "bad",
    [
        None,
        1.0,
        float("nan"),
        "42",
        b"42",
        True,
        np.bool_(False),
        np.array([1, 2]),
        np.random.RandomState(1),
        np.random.SeedSequence(1),
        object(),
        1 + 0j,
    ],
    ids=repr,
)
def test_non_seed_types_raise_input_type_error(bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        R.as_generator(bad)
    assert ei.value.argument == "rng"


@pytest.mark.req("FR-000-18")
@pytest.mark.oracle("hand-calculation", "spec FR-000-18: rng is an argument with no default")
def test_rng_has_no_default() -> None:
    params = inspect.signature(R.as_generator).parameters
    (only,) = params.values()
    assert only.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        R.as_generator()  # type: ignore[call-arg]


@pytest.mark.req("FR-000-18")
@pytest.mark.oracle("hand-calculation", "the global NumPy random state is neither read nor advanced")
def test_global_numpy_state_is_untouched() -> None:
    np.random.seed(123)  # noqa: NPY002
    before = np.random.get_state()  # noqa: NPY002
    fx_sample(10, 5)
    fx_sample(10, np.random.default_rng(6))
    after = np.random.get_state()  # noqa: NPY002
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]

"""T-005-040 (P-005-14, FR-005-24, FR-005-25): property tests of the size-distribution helpers.

Public API under test (`minephys.comminution`): `passing_size(sizes, passing, fraction=0.8)`,
`class_masses(sizes, passing)`, `cumulative_passing(masses)` (see tests/unit/test_t_005_040_psd.py).

Relations
- P-005-14: equivariance (scaling every size by lambda scales the result by lambda) and monotonicity (the result is
  non-decreasing in `fraction`); lambda log-uniform in [1e-3, 1e3], TC-1;
- the interpolated size lies between its two bracketing grid sizes and reproduces the passing value when the curve is
  evaluated back (round trip on the log-log segment);
- `cumulative_passing(class_masses(.))` is the identity and the class masses are non-negative and add up to P(s_1).
Curves are generated from Hypothesis seeds: 3 to 60 points, sizes decreasing from 1 m in log steps of 0.02 to 0.19 (down to
about 10 um), passing values strictly decreasing from 1 with ratios 0.85 to 0.999.
"""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

CI = settings(max_examples=200, deadline=None)


def _c():
    return importlib.import_module("minephys.comminution")


def curve(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Coarse-to-fine sizes (log steps of 0.02 to 0.19, from 1 m) and strictly decreasing cumulative passing from 1."""
    rng = np.random.default_rng(seed)
    steps = rng.uniform(0.02, 0.19, n)
    steps[0] = 0.0
    sizes = np.exp(-np.cumsum(steps))
    factors = rng.uniform(0.85, 0.999, n)
    factors[0] = 1.0
    passing = np.cumprod(factors)
    return sizes, passing

SEEDS = st.integers(0, 2**32 - 1)
COUNTS = st.integers(3, 60)


@pytest.mark.req("P-005-14")
@pytest.mark.oracle("analytical", "only size ratios enter a log-log interpolation: scaling the sizes scales the answer")
@CI
@given(n=COUNTS, seed=SEEDS, lam=st.floats(math.log(1e-3), math.log(1e3)).map(math.exp), frac=st.floats(0.0, 1.0))
def test_p_005_14_equivariance(n: int, seed: int, lam: float, frac: float) -> None:
    c = _c()
    sizes, passing = curve(n, seed)
    f = passing[-1] + frac * (passing[0] - passing[-1])
    base = c.passing_size(sizes, passing, f)
    scaled = c.passing_size(lam * sizes, passing, f)
    np.testing.assert_allclose(scaled, lam * base, rtol=1e-12, atol=0)


@pytest.mark.req("P-005-14")
@CI
@given(n=COUNTS, seed=SEEDS, f1=st.floats(0.0, 1.0), f2=st.floats(0.0, 1.0))
def test_p_005_14_monotone_in_fraction(n: int, seed: int, f1: float, f2: float) -> None:
    c = _c()
    sizes, passing = curve(n, seed)
    lo, hi = sorted((f1, f2))
    p_lo = passing[-1] + lo * (passing[0] - passing[-1])
    p_hi = passing[-1] + hi * (passing[0] - passing[-1])
    assert c.passing_size(sizes, passing, p_lo) <= c.passing_size(sizes, passing, p_hi) * (1.0 + 1e-12)


@pytest.mark.req("FR-005-24")
@CI
@given(n=COUNTS, seed=SEEDS, frac=st.floats(0.0, 1.0))
def test_interpolated_size_is_bracketed_by_the_grid(n: int, seed: int, frac: float) -> None:
    c = _c()
    sizes, passing = curve(n, seed)
    f = passing[-1] + frac * (passing[0] - passing[-1])
    x = c.passing_size(sizes, passing, f)
    assert sizes[-1] * (1.0 - 1e-12) <= x <= sizes[0] * (1.0 + 1e-12)
    # the log-log segment that brackets f returns f when evaluated at x
    i = int(np.searchsorted(-passing, -f, side="right")) - 1
    i = min(max(i, 0), n - 2)
    slope = (math.log(passing[i + 1]) - math.log(passing[i])) / (math.log(sizes[i + 1]) - math.log(sizes[i]))
    back = math.exp(math.log(passing[i]) + slope * (math.log(x) - math.log(sizes[i])))
    np.testing.assert_allclose(back, f, rtol=1e-9, atol=0)


@pytest.mark.req("FR-005-25")
@pytest.mark.oracle("analytical", "class_masses and cumulative_passing are exact inverses; masses are non-negative")
@CI
@given(n=COUNTS, seed=SEEDS)
def test_class_masses_round_trip(n: int, seed: int) -> None:
    c = _c()
    sizes, passing = curve(n, seed)
    m = c.class_masses(sizes, passing)
    assert np.all(m >= 0.0)
    np.testing.assert_allclose(m.sum(), passing[0], rtol=1e-12, atol=1e-15)
    np.testing.assert_allclose(c.cumulative_passing(m), passing, rtol=1e-11, atol=1e-14)

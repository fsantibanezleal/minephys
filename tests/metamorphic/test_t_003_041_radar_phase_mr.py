# ruff: noqa: E501
"""T-003-041 (P-003-12, FR-003-19): metamorphic properties of the phase functions.

P-003-12: `wrap_phase` is 2 pi periodic and idempotent and returns values in (-pi, pi];
`los_from_phase(los_phase(d, lam), lam) = d`; `wrap_phase(los_phase(d, lam)) = los_phase(d, lam)` exactly when
|d| < lam / 4 (and it differs outside the limit). Further relations: los_phase is odd and linear in d and
inversely proportional to the wavelength; the wrapped phase differs from the phase by a whole number of turns;
two scans a step s apart have a wrapped phase difference equal to the true phase difference when |s| < lam /
4.

Generators: |phi| <= 1e3 rad, lam in [1e-3, 0.3] m, d in [-lam, lam] (about +-4 ambiguity limits), spans of up
to 8 limits. Tolerances: TC-1 (rtol 1e-12), periodicity rtol 1e-12 |phi| as in the spec, away from the branch
cut by at least 1e-6 rad (at the cut the rounding of phi + 2 pi k may land on either side).

Oracle: analytical (closed forms of the phase relation), Monserrat et al. 2014 eqs. 4 and 7.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

CFG = settings(deadline=None)
PI = math.pi
PHASE = st.floats(-1e3, 1e3)
LAMBDA = st.floats(1e-3, 0.3)


def away_from_the_cut(phi: float) -> None:
    assume(abs(float(G.wrap_phase(phi))) < PI - 1e-6)


@pytest.mark.req("P-003-12")
@pytest.mark.oracle(
    "analytical", "wrap_phase returns (-pi, pi] and differs from its argument by a whole number of turns"
)
@CFG
@given(phi=PHASE)
def test_range_and_turns(phi: float) -> None:
    w = float(G.wrap_phase(phi))
    assert -PI < w <= PI
    turns = (phi - w) / (2.0 * PI)
    assert abs(turns - round(turns)) < 1e-9


@pytest.mark.req("P-003-12")
@pytest.mark.oracle(
    "analytical", "2 pi periodicity: wrap(phi + 2 pi k) = wrap(phi), tolerance 1e-12 |phi| (away from the cut)"
)
@CFG
@given(phi=PHASE, k=st.integers(-50, 50))
def test_periodicity(phi: float, k: int) -> None:
    away_from_the_cut(phi)
    shifted = phi + 2.0 * PI * k
    assume(abs(shifted) <= 1e3)
    assert float(G.wrap_phase(shifted)) == pytest.approx(
        float(G.wrap_phase(phi)), abs=1e-12 * max(abs(phi), abs(shifted), 1.0)
    )


@pytest.mark.req("P-003-12")
@pytest.mark.oracle("analytical", "idempotence: wrap(wrap(phi)) = wrap(phi), exactly")
@CFG
@given(phi=PHASE)
def test_idempotence(phi: float) -> None:
    once = G.wrap_phase(phi)
    assert G.wrap_phase(once) == once


@pytest.mark.req("P-003-12")
@pytest.mark.oracle("analytical", "round trip: los_from_phase(los_phase(d, lam), lam) = d")
@CFG
@given(d=st.floats(-10.0, 10.0), lam=LAMBDA)
def test_round_trip(d: float, lam: float) -> None:
    assert G.los_from_phase(G.los_phase(d, lam), lam) == pytest.approx(d, rel=1e-12, abs=1e-300)


@pytest.mark.req("P-003-12")
@pytest.mark.req("FR-003-19")
@pytest.mark.oracle("analytical", "wrap(phase(d)) = phase(d) exactly for |d| < lam / 4, and not for lam / 4 < |d|")
@CFG
@given(lam=LAMBDA, frac=st.floats(0.0, 8.0), sign=st.sampled_from([-1.0, 1.0]))
def test_ambiguity_limit(lam: float, frac: float, sign: float) -> None:
    limit = float(G.max_unambiguous_los_step(lam))
    assert limit == pytest.approx(lam / 4.0, rel=1e-14)
    assume(abs(frac - 1.0) > 1e-9)  # not on the limit itself
    d = sign * frac * limit
    ph = G.los_phase(d, lam)
    if frac < 1.0:
        assert G.wrap_phase(ph) == ph
    else:
        assert G.wrap_phase(ph) != ph


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle("analytical", "odd, linear in d, inversely proportional to the wavelength")
@CFG
@given(
    d1=st.floats(-1.0, 1.0),
    d2=st.floats(-1.0, 1.0),
    a=st.floats(-10.0, 10.0),
    b=st.floats(-10.0, 10.0),
    lam=LAMBDA,
    k=st.floats(0.1, 10.0),
)
def test_phase_is_linear_odd_and_inverse_in_lambda(
    d1: float, d2: float, a: float, b: float, lam: float, k: float
) -> None:
    assert G.los_phase(-d1, lam) == -G.los_phase(d1, lam)
    lhs = float(G.los_phase(a * d1 + b * d2, lam))
    rhs = a * float(G.los_phase(d1, lam)) + b * float(G.los_phase(d2, lam))
    assert lhs == pytest.approx(rhs, rel=1e-9, abs=1e-12 * (abs(a) + abs(b)) / lam)
    assert G.los_phase(d1, k * lam) == pytest.approx(float(G.los_phase(d1, lam)) / k, rel=1e-12, abs=1e-300)


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "analytical",
    "two scans less than lam / 4 apart: the wrapped phase difference is the true phase difference (phase unwrapping)",
)
@CFG
@given(lam=LAMBDA, d0=st.floats(-5.0, 5.0), frac=st.floats(-0.99, 0.99))
def test_unwrapping_a_small_step(lam: float, d0: float, frac: float) -> None:
    step = frac * float(G.max_unambiguous_los_step(lam))
    p0 = float(G.los_phase(d0, lam))
    p1 = float(G.los_phase(d0 + step, lam))
    diff = float(G.wrap_phase(p1 - p0))
    assert diff == pytest.approx(float(G.los_phase(step, lam)), abs=1e-9 * (1.0 + abs(p0)))


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "analytical",
    "a wrapped phase pins the displacement modulo lam / 2: d - los_from_phase(wrap(phase(d))) is a whole number of half wavelengths",
)
@CFG
@given(lam=LAMBDA, d=st.floats(-10.0, 10.0))
def test_wrapped_phase_recovers_the_displacement_modulo_half_a_wavelength(lam: float, d: float) -> None:
    back = float(G.los_from_phase(G.wrap_phase(G.los_phase(d, lam)), lam))
    turns = (d - back) / (lam / 2.0)
    assert abs(turns - round(turns)) < 1e-8

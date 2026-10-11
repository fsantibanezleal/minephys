# ruff: noqa: E501
"""T-004-030 (FR-004-08, FR-004-12): Gy's fundamental sampling error.

Expected API, module `minephys.bulk` (elementwise, float64; a scalar call gives a NumPy float64):

    gy_fundamental_sampling_error(sample_mass, lot_mass, top_size, mineralogical_factor, shape_factor,
    granulometric_factor,
                                  liberation_factor) -> (1 / M_S - 1 / M_L) c f g l d^3                    [1] (relative variance)
        M_S, M_L [kg], d (top size) [m], c [kg/m^3], f, g, l [1]; none of the factors has a default. The mass term is
        evaluated as (M_L - M_S) / (M_S M_L) so that M_S close to M_L does not cancel. sample_mass > lot_mass is an
        `InputError` naming `sample_mass` (FR-004-12); sample_mass = lot_mass gives exactly 0. The function reads only
        documented PARAMETER rows (never model constants), so it emits no UnverifiedParameterWarning.

Oracles: spec 004 section 7.4 (M_S = 1 kg, M_L = 1000 kg, d = 0.01 m, c = 1e4 kg/m^3, f = 0.5, g = 0.25, l =
0.1: 1.24875e-4, relative standard deviation 1.1175 %, the same value in Gy's cgs units 1000 g, 1e6 g, 1 cm,
10 g/cm^3; TC-2), exact rational arithmetic (`Fraction`) for the cancellation-prone case M_S close to M_L, and
hand identities (d^3 scaling, the lot-mass limit c f g l d^3 / M_S). Closed forms TC-1.
"""

from __future__ import annotations

import inspect
import math
import warnings
from fractions import Fraction

import numpy as np
import pytest
from minephys.knowledge import UnverifiedParameterWarning

import minephys
from minephys import bulk as B

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

SPEC = {
    "sample_mass": 1.0,
    "lot_mass": 1000.0,
    "top_size": 0.01,
    "mineralogical_factor": 1.0e4,
    "shape_factor": 0.5,
    "granulometric_factor": 0.25,
    "liberation_factor": 0.1,
}


def fse(**over):
    return B.gy_fundamental_sampling_error(**{**SPEC, **over})


@pytest.mark.req("FR-004-08")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 7.4: gy_fundamental_sampling_error(1.0, 1000.0, 0.01, 1.0e4, 0.5, 0.25, 0.1) = 1.24875e-4 (relative sd 1.1175 %)",
)
def test_spec_worked_value() -> None:
    v = B.gy_fundamental_sampling_error(1.0, 1000.0, 0.01, 1.0e4, 0.5, 0.25, 0.1)
    assert type(v) is np.float64
    assert v == pytest.approx(1.24875e-4, abs=5e-10)  # TC-2: six significant figures
    assert v == pytest.approx(0.999 * 1.0e4 * 0.5 * 0.25 * 0.1 * 1e-6, rel=1e-13)
    assert math.sqrt(float(v)) * 100.0 == pytest.approx(1.1175, abs=5e-5)  # relative standard deviation in percent


@pytest.mark.req("FR-004-08")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 004 7.4: the same value in Gy's cgs units (1000 g, 1e6 g, 1 cm, 10 g/cm^3): the variance is dimensionless",
)
def test_spec_cgs_identity() -> None:
    cgs = B.gy_fundamental_sampling_error(1000.0, 1.0e6, 1.0, 10.0, 0.5, 0.25, 0.1)
    assert cgs == pytest.approx(1.24875e-4, abs=5e-10)
    assert cgs == pytest.approx(float(fse()), rel=1e-12)


@pytest.mark.req("FR-004-08")
@pytest.mark.oracle(
    "analytical", "the argument order of the signature and the absence of defaults (every factor is the user's)"
)
def test_signature_has_no_defaults() -> None:
    params = inspect.signature(B.gy_fundamental_sampling_error).parameters
    assert list(params) == [
        "sample_mass",
        "lot_mass",
        "top_size",
        "mineralogical_factor",
        "shape_factor",
        "granulometric_factor",
        "liberation_factor",
    ]
    for name, p in params.items():
        assert p.default is inspect.Parameter.empty, f"{name} must have no default"
    with pytest.raises(TypeError):
        B.gy_fundamental_sampling_error(1.0, 1000.0, 0.01, 1.0e4, 0.5, 0.25)  # type: ignore[call-arg]


@pytest.mark.req("FR-004-08")
@pytest.mark.oracle(
    "analytical",
    "exact rational arithmetic: (M_L - M_S) / (M_S M_L) c f g l d^3 with M_S very close to M_L (no cancellation, rtol 1e-12)",
)
@pytest.mark.parametrize("gap", [2.0**-20, 2.0**-10, 2.0**-30, 1.0])
def test_no_cancellation_near_equal_masses(gap: float) -> None:
    ms = 1000.0
    ml = ms + gap  # exactly representable
    exact = (
        (Fraction(ml) - Fraction(ms))
        / (Fraction(ms) * Fraction(ml))
        * Fraction(1.0e4)
        * Fraction(0.5)
        * Fraction(0.25)
        * Fraction(0.1)
        * Fraction(0.01) ** 3
    )
    got = fse(sample_mass=ms, lot_mass=ml)
    assert got == pytest.approx(float(exact), rel=1e-12)


@pytest.mark.req("FR-004-08")
@pytest.mark.oracle("analytical", "exact rational arithmetic on a grid of masses and sizes (TC-1)")
@pytest.mark.parametrize("ms", [0.001, 0.25, 3.0, 125.0])
@pytest.mark.parametrize("ratio", [1.0, 1.5, 10.0, 1e6])
@pytest.mark.parametrize("d", [1e-5, 0.004, 0.3])
def test_exact_grid(ms: float, ratio: float, d: float) -> None:
    ml = ms * ratio
    exact = (
        (Fraction(ml) - Fraction(ms))
        / (Fraction(ms) * Fraction(ml))
        * Fraction(2.5e3)
        * Fraction(0.4)
        * Fraction(0.5)
        * Fraction(0.3)
        * Fraction(d) ** 3
    )
    got = B.gy_fundamental_sampling_error(ms, ml, d, 2.5e3, 0.4, 0.5, 0.3)
    assert got == pytest.approx(float(exact), rel=1e-12, abs=0.0)


@pytest.mark.req("FR-004-08")
@pytest.mark.oracle("analytical", "the sample is the whole lot: the variance is exactly zero")
@pytest.mark.parametrize("m", [1e-3, 1.0, 1234.5, 1e3])
def test_whole_lot_has_no_error(m: float) -> None:
    out = fse(sample_mass=m, lot_mass=m)
    assert type(out) is np.float64
    assert out == 0.0


@pytest.mark.req("FR-004-08")
@pytest.mark.oracle("analytical", "as the lot grows the variance tends to c f g l d^3 / M_S (infinite lot)")
def test_infinite_lot_limit() -> None:
    limit = 1.0e4 * 0.5 * 0.25 * 0.1 * 0.01**3 / 1.0
    for ml in (1e6, 1e9, 1e12, 1e18):
        assert fse(lot_mass=ml) == pytest.approx(limit * (1.0 - 1.0 / ml), rel=1e-12)
    assert fse(lot_mass=1e18) == pytest.approx(limit, rel=1e-12)


@pytest.mark.req("FR-004-08")
@pytest.mark.oracle("analytical", "the top size enters cubed; each factor enters linearly")
def test_powers_of_the_factors() -> None:
    base = float(fse())
    assert float(fse(top_size=0.02)) == pytest.approx(8.0 * base, rel=1e-13)
    assert float(fse(top_size=0.005)) == pytest.approx(base / 8.0, rel=1e-13)
    for name in ("mineralogical_factor", "shape_factor", "granulometric_factor", "liberation_factor"):
        assert float(fse(**{name: SPEC[name] / 2.0})) == pytest.approx(base / 2.0, rel=1e-13), name


@pytest.mark.req("FR-004-08")
@pytest.mark.oracle("analytical", "strictly decreasing in the sample mass; elementwise over arrays")
def test_decreasing_in_sample_mass_and_arrays() -> None:
    ms = np.array([[0.1], [1.0], [10.0], [100.0]])
    d = np.array([0.005, 0.01])
    v = B.gy_fundamental_sampling_error(ms, 1000.0, d, 1.0e4, 0.5, 0.25, 0.1)
    assert v.shape == (4, 2)
    assert v.dtype == np.float64
    assert np.all(np.diff(v, axis=0) < 0.0)
    assert np.all(np.diff(v, axis=1) > 0.0)
    ref = (1.0 / ms - 1.0 / 1000.0) * 1.0e4 * 0.5 * 0.25 * 0.1 * d**3
    np.testing.assert_allclose(v, ref, rtol=1e-12)


@pytest.mark.req("FR-004-08")
@pytest.mark.oracle(
    "analytical",
    "spec 004 7.6: the fundamental error reads only PARAMETER rows: no UnverifiedParameterWarning, no tripwire on the worked case",
)
def test_no_warnings_on_the_worked_case() -> None:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        fse()
    assert [w for w in rec if issubclass(w.category, (UnverifiedParameterWarning, minephys.ValidityWarning))] == []


@pytest.mark.req("FR-004-12")
@pytest.mark.oracle(
    "hand-calculation", "spec 004 FR-004-12: sample_mass > lot_mass is an InputError naming sample_mass"
)
@pytest.mark.parametrize(
    ("ms", "ml"),
    [(1000.0000001, 1000.0), (2.0, 1.0), (1e3, 1.0), (math.nextafter(1.0, 2.0), 1.0), (5.0, 4.999999999999999)],
)
def test_sample_larger_than_the_lot(ms: float, ml: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        fse(sample_mass=ms, lot_mass=ml)
    assert ei.value.argument == "sample_mass"
    assert "sample_mass" in str(ei.value)


@pytest.mark.req("FR-004-12")
@pytest.mark.oracle(
    "analytical",
    "one element of an array with sample_mass > lot_mass raises, naming sample_mass; elements are paired by broadcasting",
)
def test_sample_larger_than_the_lot_in_arrays() -> None:
    with pytest.raises(minephys.InputError) as ei:
        fse(sample_mass=np.array([1.0, 2.0, 1500.0]))
    assert ei.value.argument == "sample_mass"
    with pytest.raises(minephys.InputError) as ei2:
        fse(lot_mass=np.array([1000.0, 0.5]))
    assert ei2.value.argument == "sample_mass"
    out = fse(sample_mass=np.array([1.0, 2.0, 1000.0]))
    assert out.shape == (3,)
    assert out[2] == 0.0

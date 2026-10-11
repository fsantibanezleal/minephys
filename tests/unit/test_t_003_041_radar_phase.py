# ruff: noqa: E501
"""T-003-041 (FR-003-19, FR-003-20, FR-003-21, FR-003-23): interferometric phase, wrapping, inverse and ambiguity
limit.

Expected API, module `minephys.geotech` (all elementwise, float64 results, shapes broadcast, scalars give
float64 scalars):

    los_phase(los_displacement, wavelength, noise_sd=0, rng=None) -> unwrapped phase [rad] = 4 pi d / lambda  (no
    minus sign:
        a positive d, a range increase, is a positive phase), plus Gaussian noise of standard deviation `noise_sd`
        [rad] drawn independently per element from `rng` (a Generator or an integer seed) when noise_sd > 0; noise_sd
        > 0 without `rng` is an `InputError` naming rng.
    wrap_phase(phase) -> the phase mapped to (-pi, pi]  (pi maps to pi, -pi maps to pi).
    los_from_phase(phase, wavelength) -> lambda * phase / (4 pi)  [m].
    max_unambiguous_los_step(wavelength) -> lambda / 4  [m]: the largest line-of-sight step between two scans that the
        wrapped phase can represent.
    wavelength > 0 (InputError), noise_sd >= 0, NaN/inf/wrong dtypes are errors naming the argument; a wavelength
    below 1e-4 m or above 1 m warns (`ValidityWarning`, row `tripwire_wavelength_range`, argument `wavelength`)
    and still returns.

Oracles: spec 003 section 7.4 (radar at the origin, target at (1000, 0, 0) m, u = (-0.01, 0.01, 0) m, lambda =
0.0175 m: d = -0.01 m, phase -7.1807832 rad, wrapped -0.8975979 rad, lambda / 4 = 4.375 mm; a wall at 50.8
mm/day scanned 240 times a day moves 0.21167 mm = 0.15199 rad per scan: no wrapping), Monserrat, Crosetto and
Luzi (2014) eq. 4 (the phase relation and its sign) and eq. 7 (the lambda / 4 limit), hand evaluation of the
wrapping rule on named angles, and the standard normal distribution for the noise (TC-4). Printed values TC-2,
closed forms TC-1.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

import minephys
from minephys import geotech as G

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

LAM = 0.0175  # Ku band, spec 003 7.5 (not a default)
PI = math.pi


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: d = -0.01 m, lambda = 0.0175 m: phase -7.1807832 rad, wrapped -0.8975979 rad, lambda / 4 = 4.375 mm",
)
def test_spec_worked_values() -> None:
    d = G.slope_radar_los(np.array([-0.01, 0.01, 0.0]), np.zeros(3), np.array([1000.0, 0.0, 0.0]))
    assert d == pytest.approx(-0.01, rel=1e-12)
    ph = G.los_phase(d, LAM)
    assert type(ph) is np.float64
    assert ph == pytest.approx(-7.1807832, abs=5e-8)  # TC-2
    assert ph == pytest.approx(4.0 * PI * -0.01 / LAM, rel=1e-13)
    assert G.wrap_phase(ph) == pytest.approx(-0.8975979, abs=5e-8)  # TC-2
    assert G.wrap_phase(ph) == pytest.approx(ph + 2.0 * PI, rel=1e-12)
    assert G.max_unambiguous_los_step(LAM) == pytest.approx(0.004375, rel=1e-14)
    assert G.los_from_phase(ph, LAM) == pytest.approx(-0.01, rel=1e-12)


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "hand-calculation",
    "spec 003 7.4: 50.8 mm/day sampled 240 times a day: 0.21167 mm = 0.15199 rad per scan, far below lambda / 4: no wrapping",
)
def test_spec_scan_to_scan_step() -> None:
    step = 50.8e-3 / 240.0  # m per scan
    assert step == pytest.approx(0.21167e-3, abs=5e-9)  # TC-2: 5 significant figures
    ph = G.los_phase(step, LAM)
    assert ph == pytest.approx(0.15199, abs=5e-6)  # TC-2
    assert abs(float(ph)) < PI
    assert G.wrap_phase(ph) == ph, "the wrapped phase of a small step is the phase itself, bit for bit"
    assert step < G.max_unambiguous_los_step(LAM)


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "worked-example",
    "monserrat2014 eq. 4: delta phi = 4 pi (R2 - R1) / lambda; a range increase gives a positive phase",
)
def test_sign_and_formula() -> None:
    for d, lam in ((0.001, 0.0175), (-0.25, 0.03), (3.0, 0.0175), (1e-9, 0.1), (0.0, 0.0175)):
        assert G.los_phase(d, lam) == pytest.approx(4.0 * PI * d / lam, rel=1e-13, abs=0.0)
    assert float(G.los_phase(0.002, LAM)) > 0.0
    assert float(G.los_phase(-0.002, LAM)) < 0.0
    assert G.los_phase(0.0, LAM) == 0.0
    # one half wavelength of range change is 2 pi of phase for a one-way path; the two-way path used by a radar gives 4 pi per
    # wavelength of displacement, i.e. a displacement of lambda / 2 is one full cycle
    assert G.los_phase(LAM / 2.0, LAM) == pytest.approx(2.0 * PI, rel=1e-13)
    assert G.los_phase(LAM / 4.0, LAM) == pytest.approx(PI, rel=1e-13)


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle("analytical", "hand evaluation of the wrapping rule on named angles")
@pytest.mark.parametrize(
    ("phi", "expected"),
    [
        (0.0, 0.0),
        (1.0, 1.0),
        (-1.0, -1.0),
        (PI, PI),  # pi maps to pi
        (-PI, PI),  # -pi maps to pi, the interval is (-pi, pi]
        (2.0 * PI, 0.0),
        (-2.0 * PI, 0.0),
        (4.0, 4.0 - 2.0 * PI),  # -2.2831853
        (-4.0, -4.0 + 2.0 * PI),  # +2.2831853
        (PI / 2.0 + 2.0 * PI, PI / 2.0),
        (-PI / 2.0 - 4.0 * PI, -PI / 2.0),
        (100.0, 100.0 - 32.0 * PI),  # 100 / (2 pi) = 15.9, nearest cycle 16 -> 100 - 32 pi
    ],
)
def test_wrap_named_angles(phi: float, expected: float) -> None:
    out = G.wrap_phase(phi)
    assert type(out) is np.float64
    assert out == pytest.approx(expected, abs=1e-12)


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "analytical",
    "the convention at the cut: pi is kept as pi, -pi is mapped to pi (spec plan: phi - 2 pi ceil((phi - pi) / 2 pi))",
)
def test_wrap_at_the_cut_is_exact() -> None:
    assert G.wrap_phase(math.pi) == math.pi
    assert G.wrap_phase(-math.pi) == math.pi
    just_above = math.nextafter(math.pi, 4.0)
    just_below = math.nextafter(-math.pi, -4.0)
    assert -math.pi < float(G.wrap_phase(just_above)) < -3.0  # wraps to about -pi + 4e-16
    assert 3.0 < float(G.wrap_phase(just_below)) <= math.pi
    inside = math.nextafter(math.pi, 0.0)
    assert G.wrap_phase(inside) == inside


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle("analytical", "the result is in (-pi, pi] for a wide sweep of phases, arrays keep their shape")
def test_wrap_range_sweep() -> None:
    phi = np.linspace(-2000.0, 2000.0, 20_001) + 0.0123  # generic points, none on a multiple of pi
    out = G.wrap_phase(phi)
    assert out.shape == phi.shape
    assert out.dtype == np.float64
    assert np.all(out > -PI)
    assert np.all(out <= PI)
    cycles = (phi - out) / (2.0 * PI)
    np.testing.assert_allclose(cycles, np.round(cycles), atol=1e-9)  # the same angle up to whole turns


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "analytical",
    "huge phases: up to 1e6 rad the result is in (-pi, pi]; beyond, the call raises InputError or returns a finite number, never NaN or inf",
)
@pytest.mark.parametrize("phi", [1e6, -1e6, 1e12, 1e16, -1e16, 1e300, -1e300])
def test_wrap_huge(phi: float) -> None:
    try:
        out = float(G.wrap_phase(phi))
    except minephys.InputError:
        return
    assert math.isfinite(out)
    if abs(phi) <= 1e6:
        assert -PI < out <= PI


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle("analytical", "the inverse relation lambda phi / (4 pi) and the ambiguity limit lambda / 4")
@pytest.mark.parametrize("lam", [1e-4, 0.0175, 0.03, 0.3, 1.0])
def test_inverse_and_limit(lam: float) -> None:
    for d in (-0.01, 0.0, 0.001, 0.123):
        assert G.los_from_phase(G.los_phase(d, lam), lam) == pytest.approx(d, rel=1e-12, abs=1e-18)
        assert G.los_from_phase(1.0, lam) == pytest.approx(lam / (4.0 * PI), rel=1e-14)
    assert G.max_unambiguous_los_step(lam) == pytest.approx(lam / 4.0, rel=1e-14)
    assert G.los_phase(G.max_unambiguous_los_step(lam) * 0.999, lam) == pytest.approx(0.999 * PI, rel=1e-12)


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle("analytical", "wrapping is lossless exactly inside the ambiguity limit and lossy outside it")
def test_ambiguity_limit() -> None:
    limit = float(G.max_unambiguous_los_step(LAM))
    for frac in (0.0, 0.1, 0.5, 0.9, 0.999, -0.1, -0.5, -0.9, -0.999):
        ph = G.los_phase(frac * limit, LAM)
        assert G.wrap_phase(ph) == ph
    for frac in (1.001, 1.5, 2.0, 7.3, -1.001, -1.5, -2.0, -7.3):
        ph = G.los_phase(frac * limit, LAM)
        assert G.wrap_phase(ph) != ph
        # the true displacement is recovered up to a whole number of half wavelengths
        back = float(G.los_from_phase(G.wrap_phase(ph), LAM))
        turns = (frac * limit - back) / (LAM / 2.0)
        assert turns == pytest.approx(round(turns), abs=1e-9)


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "analytical", "elementwise over broadcast arrays: every element equals the scalar call; shapes broadcast"
)
def test_elementwise_and_broadcasting() -> None:
    d = np.array([[0.001], [-0.004], [0.02]])  # (3, 1)
    lam = np.array([0.0175, 0.03, 0.1, 0.3])  # (4,)
    ph = G.los_phase(d, lam)
    assert ph.shape == (3, 4)
    assert ph.dtype == np.float64
    for i in range(3):
        for j in range(4):
            assert ph[i, j] == pytest.approx(float(G.los_phase(float(d[i, 0]), float(lam[j]))), rel=1e-14)
    back = G.los_from_phase(ph, lam)
    np.testing.assert_allclose(back, np.broadcast_to(d, (3, 4)), rtol=1e-12)
    assert G.max_unambiguous_los_step(lam).shape == (4,)
    np.testing.assert_allclose(G.max_unambiguous_los_step(lam), lam / 4.0, rtol=1e-15)
    assert G.wrap_phase(ph).shape == (3, 4)


@pytest.mark.req("FR-000-13")
@pytest.mark.oracle("analytical", "empty arrays give empty float64 arrays")
def test_empty() -> None:
    for fn, args in (
        (G.los_phase, (np.empty(0), LAM)),
        (G.wrap_phase, (np.empty(0),)),
        (G.los_from_phase, (np.empty(0), LAM)),
        (G.max_unambiguous_los_step, (np.empty(0),)),
    ):
        out = fn(*args)
        assert out.shape == (0,)
        assert out.dtype == np.float64


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle("analytical", "float32 and integer operands give the float64 result; inputs are not modified")
def test_dtypes_and_purity() -> None:
    d = np.array([0.5, -0.25, 0.0, 2.0])
    lam = np.array([1.0, 0.5, 0.25, 0.125])
    ref = G.los_phase(d, lam)
    assert G.los_phase(d.astype(np.float32), lam.astype(np.float32)).tobytes() == ref.tobytes()
    assert G.los_phase(np.array([1, 0, -1]), np.array([1, 2, 4])).dtype == np.float64
    snap = (d.copy(), lam.copy())
    G.los_phase(d, lam)
    assert np.array_equal(d, snap[0])
    assert np.array_equal(lam, snap[1])


# ------------------------------------------------------------------ noise


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "analytical", "noise_sd = 0 (the default) adds nothing, with or without an rng; the clean phase is exact"
)
def test_no_noise() -> None:
    d = np.linspace(-0.01, 0.01, 11)
    clean = G.los_phase(d, LAM)
    assert np.array_equal(G.los_phase(d, LAM, noise_sd=0.0), clean)
    assert np.array_equal(G.los_phase(d, LAM, noise_sd=0, rng=3), clean)
    assert np.array_equal(G.los_phase(d, LAM, 0.0, np.random.default_rng(3)), clean)


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "analytical",
    "N(0, sd^2) noise per element: sample mean within 4 SE, sample sd within 4 SE of sd, no serial correlation (TC-4)",
)
@pytest.mark.parametrize("sd", [0.01, 0.3, 2.0])
def test_noise_statistics(sd: float) -> None:
    n = 200_000
    d = np.full(n, 0.002)
    clean = G.los_phase(d, LAM)
    noisy = G.los_phase(d, LAM, noise_sd=sd, rng=20261011)
    resid = noisy - clean
    assert noisy.shape == (n,)
    assert float(np.mean(resid)) == pytest.approx(0.0, abs=4.0 * sd / math.sqrt(n))
    assert float(np.std(resid, ddof=1)) == pytest.approx(sd, rel=4.0 / math.sqrt(2.0 * n))
    lag1 = float(np.mean(resid[1:] * resid[:-1])) / sd**2
    assert abs(lag1) < 4.0 / math.sqrt(n)
    # normality: the fraction beyond one and two standard deviations (two-sided 0.317311 and 0.045500)
    for k, p in ((1.0, 0.3173105), (2.0, 0.0455003)):
        frac = float(np.mean(np.abs(resid) > k * sd))
        assert frac == pytest.approx(p, abs=4.0 * math.sqrt(p * (1.0 - p) / n))


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "analytical", "the noise scales with noise_sd (same seed, same stream): sd 0.2 gives twice the deviations of sd 0.1"
)
def test_noise_scales_with_sd() -> None:
    d = np.zeros(1000)
    a = G.los_phase(d, LAM, noise_sd=0.1, rng=5)
    b = G.los_phase(d, LAM, noise_sd=0.2, rng=5)
    np.testing.assert_allclose(b, 2.0 * a, rtol=1e-12, atol=1e-15)


@pytest.mark.req("FR-003-19")
@pytest.mark.req("P-000-04")
@pytest.mark.oracle(
    "analytical",
    "determinism: same seed, same Generator state: bitwise equal; other seeds differ; a Generator advances",
)
def test_noise_determinism() -> None:
    d = np.linspace(0.0, 0.01, 50)
    a = G.los_phase(d, LAM, noise_sd=0.1, rng=9)
    b = G.los_phase(d, LAM, noise_sd=0.1, rng=9)
    c = G.los_phase(d, LAM, noise_sd=0.1, rng=np.random.default_rng(9))
    assert a.tobytes() == b.tobytes() == c.tobytes()
    assert a.tobytes() != G.los_phase(d, LAM, noise_sd=0.1, rng=10).tobytes()
    gen = np.random.default_rng(9)
    first = G.los_phase(d, LAM, noise_sd=0.1, rng=gen)
    second = G.los_phase(d, LAM, noise_sd=0.1, rng=gen)
    assert first.tobytes() != second.tobytes()


@pytest.mark.req("FR-003-19")
@pytest.mark.oracle(
    "analytical", "a scalar input with noise gives a scalar; broadcast shapes carry independent noise per element"
)
def test_noise_shapes() -> None:
    one = G.los_phase(0.001, LAM, noise_sd=0.1, rng=1)
    assert np.ndim(one) == 0
    out = G.los_phase(np.zeros((4, 5)), np.array([0.0175] * 5), noise_sd=0.1, rng=2)
    assert out.shape == (4, 5)
    assert len(np.unique(out)) == 20, "every element gets its own draw"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "noise_sd > 0 without rng is an InputError naming rng (also for tiny noise_sd)")
@pytest.mark.parametrize("sd", [1e-300, 1e-6, 0.1, 5.0])
def test_noise_without_rng(sd: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.los_phase(np.array([0.001, 0.002]), LAM, noise_sd=sd)
    assert ei.value.argument == "rng"
    with pytest.raises(minephys.InputError) as ei2:
        G.los_phase(0.001, LAM, noise_sd=sd, rng=None)
    assert ei2.value.argument == "rng"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "with noise requested, rng must be a Generator or an integer seed in 0..2**32-1")
@pytest.mark.parametrize("bad", [1.5, "7", b"7", True, np.array([1, 2]), np.random.RandomState(1), object()])
def test_bad_rng_type(bad) -> None:
    with pytest.raises(minephys.InputTypeError) as ei:
        G.los_phase(0.001, LAM, noise_sd=0.1, rng=bad)
    assert ei.value.argument == "rng"


@pytest.mark.req("FR-003-23")
@pytest.mark.oracle("analytical", "an integer seed out of range is an InputError naming rng")
@pytest.mark.parametrize("bad", [-1, 2**32, 2**64])
def test_bad_rng_value(bad: int) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.los_phase(0.001, LAM, noise_sd=0.1, rng=bad)
    assert ei.value.argument == "rng"


# ------------------------------------------------------------------ domain, tripwire and hostile inputs


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "spec 003 7.2: wavelength > 0 (zero and negative are InputError), noise_sd >= 0")
@pytest.mark.parametrize("bad", [0.0, -0.0175, -1e-300, -1.0])
def test_wavelength_domain(bad: float) -> None:
    for fn, args in (
        (G.los_phase, (0.001, bad)),
        (G.los_from_phase, (1.0, bad)),
        (G.max_unambiguous_los_step, (bad,)),
    ):
        with pytest.raises(minephys.InputError) as ei:
            fn(*args)
        assert ei.value.argument == "wavelength"


@pytest.mark.req("FR-003-20")
@pytest.mark.oracle("analytical", "a negative noise_sd is an InputError naming noise_sd, even with an rng")
@pytest.mark.parametrize("bad", [-1e-12, -0.1, -5.0])
def test_noise_sd_domain(bad: float) -> None:
    with pytest.raises(minephys.InputError) as ei:
        G.los_phase(0.001, LAM, noise_sd=bad, rng=1)
    assert ei.value.argument == "noise_sd"


@pytest.mark.req("FR-003-20")
@pytest.mark.req("FR-000-10")
@pytest.mark.oracle("analytical", "NaN and infinity are InputError naming the argument, scalar or inside an array")
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite(bad: float) -> None:
    cases = (
        (G.los_phase, "los_displacement", (bad, LAM)),
        (G.los_phase, "wavelength", (0.001, bad)),
        (G.los_phase, "noise_sd", (0.001, LAM, bad, 1)),
        (G.wrap_phase, "phase", (bad,)),
        (G.los_from_phase, "phase", (bad, LAM)),
        (G.los_from_phase, "wavelength", (1.0, bad)),
        (G.max_unambiguous_los_step, "wavelength", (bad,)),
    )
    for fn, arg, args in cases:
        with pytest.raises(minephys.InputError) as ei:
            fn(*args)
        assert ei.value.argument == arg
    with pytest.raises(minephys.InputError) as ei2:
        G.wrap_phase(np.array([0.1, bad, 0.3]))
    assert ei2.value.argument == "phase"
    with pytest.raises(minephys.InputError) as ei3:
        G.los_phase(np.array([0.001, bad]), LAM)
    assert ei3.value.argument == "los_displacement"


@pytest.mark.req("FR-000-11")
@pytest.mark.oracle("analytical", "wrong dtypes are InputTypeError naming the argument")
@pytest.mark.parametrize(
    "bad", ["1.0", b"1", None, 1 + 1j, True, object(), np.datetime64("2026-01-01"), np.array([1 + 1j])]
)
def test_wrong_types(bad) -> None:
    cases = (
        (G.los_phase, "los_displacement", (bad, LAM)),
        (G.los_phase, "wavelength", (0.001, bad)),
        (G.los_phase, "noise_sd", (0.001, LAM, bad, 1)),
        (G.wrap_phase, "phase", (bad,)),
        (G.los_from_phase, "phase", (bad, LAM)),
        (G.los_from_phase, "wavelength", (1.0, bad)),
        (G.max_unambiguous_los_step, "wavelength", (bad,)),
    )
    for fn, arg, args in cases:
        with pytest.raises(minephys.InputTypeError) as ei:
            fn(*args)
        assert ei.value.argument == arg


@pytest.mark.req("FR-000-12")
@pytest.mark.oracle(
    "analytical", "shapes (3,) and (4,) cannot broadcast: InputError naming both arguments and both shapes"
)
def test_shape_mismatch() -> None:
    for fn, a, b in (
        (G.los_phase, "los_displacement", "wavelength"),
        (G.los_from_phase, "phase", "wavelength"),
    ):
        with pytest.raises(minephys.InputError) as ei:
            fn(np.full(3, 0.001), np.full(4, 0.0175))
        msg = str(ei.value)
        assert a in msg
        assert b in msg
        assert "(3,)" in msg
        assert "(4,)" in msg


@pytest.mark.req("FR-003-21")
@pytest.mark.oracle(
    "analytical",
    "spec 003 7.3: wavelength below 1e-4 m or above 1 m warns (tripwire_wavelength_range) and still returns",
)
@pytest.mark.parametrize("lam", [9.99e-5, 1e-6, 1.0001, 3.0, 175.0])
def test_wavelength_tripwire_warns(lam: float) -> None:
    for fn, args in (
        (G.los_phase, (0.001, lam)),
        (G.los_from_phase, (1.0, lam)),
        (G.max_unambiguous_los_step, (lam,)),
    ):
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            out = fn(*args)
        hits = [w for w in rec if issubclass(w.category, minephys.ValidityWarning)]
        assert hits, fn.__name__
        assert hits[0].message.row == "tripwire_wavelength_range"
        assert hits[0].message.argument == "wavelength"
        assert "wavelength" in str(hits[0].message)
        assert math.isfinite(float(out))


@pytest.mark.req("FR-003-21")
@pytest.mark.oracle("analytical", "wavelengths from 1e-4 m to 1 m inclusive, and the Ku-band value, stay silent")
@pytest.mark.parametrize("lam", [1e-4, 0.0175, 0.03, 0.3, 1.0])
def test_wavelength_tripwire_is_silent(lam: float) -> None:
    for fn, args in (
        (G.los_phase, (0.001, lam)),
        (G.los_from_phase, (1.0, lam)),
        (G.max_unambiguous_los_step, (lam,)),
    ):
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            fn(*args)
        assert [w for w in rec if issubclass(w.category, minephys.ValidityWarning)] == []


@pytest.mark.req("FR-003-21")
@pytest.mark.oracle("analytical", "one out-of-range element of an array is enough to warn")
def test_tripwire_on_one_element() -> None:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        G.max_unambiguous_los_step(np.array([0.0175, 0.03, 5.0]))
    assert any(issubclass(w.category, minephys.ValidityWarning) for w in rec)

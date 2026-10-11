# ruff: noqa: E501
"""T-004-030 (P-004-07, FR-004-08): metamorphic properties of Gy's fundamental sampling error.

P-004-07: the error is the same in SI and in Gy's cgs units (g, cm, g/cm^3: sample and lot mass x 1e3, top
size x 1e2, mineralogical factor x 1e-3), scales as d^3, is strictly decreasing in sample mass, is 0 when
`sample_mass = lot_mass`, and tends to c f g l d^3 / M_S as the lot mass grows. Further: linear in each of the
four factors, linear in the product when the mass term is fixed.

Generators (spec 004 P-004-07): M_S in [1e-3, 1e3] kg, M_L = M_S (1 + u) with u in [0, 1e9], d in [1e-5, 0.3]
m, c in [100, 1e5] kg/m^3, f in [0.1, 1], g in [0.05, 1], l in [0.01, 1]. Tolerance TC-1 (rtol 1e-12; the
cancellation-free mass term keeps the relative error of (M_L - M_S) / (M_S M_L) at a few ulp); strict ordering
compares sample masses at least a relative 1e-6 apart.

Oracle: analytical (unit analysis: the variance is dimensionless, so a change of the mass, length and density
units that leaves c d^3 / M invariant leaves it unchanged).
"""

from __future__ import annotations

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from minephys import bulk as B

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

CFG = settings(deadline=None)


@st.composite
def case(draw):
    ms = draw(st.floats(1e-3, 1e3))
    return {
        "sample_mass": ms,
        "lot_mass": ms * (1.0 + draw(st.floats(0.0, 1e9))),
        "top_size": draw(st.floats(1e-5, 0.3)),
        "mineralogical_factor": draw(st.floats(100.0, 1e5)),
        "shape_factor": draw(st.floats(0.1, 1.0)),
        "granulometric_factor": draw(st.floats(0.05, 1.0)),
        "liberation_factor": draw(st.floats(0.01, 1.0)),
    }


def fse(c: dict, **over) -> float:
    return float(B.gy_fundamental_sampling_error(**{**c, **over}))


@pytest.mark.req("P-004-07")
@pytest.mark.oracle(
    "analytical",
    "SI = cgs: masses x 1e3 (kg -> g), top size x 1e2 (m -> cm), mineralogical factor x 1e-3 (kg/m^3 -> g/cm^3)",
)
@CFG
@given(c=case())
def test_si_and_cgs_agree(c: dict) -> None:
    assume(c["lot_mass"] >= 1.001 * c["sample_mass"])  # the scaled masses keep the gap M_L - M_S to 1e-13 relative
    cgs = fse(
        c,
        sample_mass=1e3 * c["sample_mass"],
        lot_mass=1e3 * c["lot_mass"],
        top_size=1e2 * c["top_size"],
        mineralogical_factor=1e-3 * c["mineralogical_factor"],
    )
    assert cgs == pytest.approx(fse(c), rel=1e-12, abs=0.0)


@pytest.mark.req("P-004-07")
@pytest.mark.oracle("analytical", "the top size enters as d^3: scaling it by lambda scales the variance by lambda^3")
@CFG
@given(c=case(), lam=st.floats(1e-3, 1e3))
def test_cubic_in_top_size(c: dict, lam: float) -> None:
    assert fse(c, top_size=lam * c["top_size"]) == pytest.approx(lam**3 * fse(c), rel=1e-12, abs=0.0)


@pytest.mark.req("P-004-07")
@pytest.mark.oracle(
    "analytical", "linear in each of c, f, g and l (f, g, l are scaled down so that they stay in (0, 1])"
)
@CFG
@given(c=case(), k=st.floats(1e-3, 1.0), kc=st.floats(1e-3, 1e3))
def test_linear_in_each_factor(c: dict, k: float, kc: float) -> None:
    base = fse(c)
    assert fse(c, mineralogical_factor=kc * c["mineralogical_factor"]) == pytest.approx(kc * base, rel=1e-12, abs=0.0)
    for name in ("shape_factor", "granulometric_factor", "liberation_factor"):
        assert fse(c, **{name: k * c[name]}) == pytest.approx(k * base, rel=1e-12, abs=0.0)


@pytest.mark.req("P-004-07")
@pytest.mark.oracle(
    "analytical", "strictly decreasing in the sample mass (the lot fixed), reaching zero at sample = lot"
)
@CFG
@given(c=case(), t1=st.floats(0.0, 1.0), t2=st.floats(0.0, 1.0))
def test_decreasing_in_sample_mass(c: dict, t1: float, t2: float) -> None:
    lot = c["lot_mass"]
    lo, hi = sorted((t1, t2))
    m_small = c["sample_mass"] + lo * (lot - c["sample_mass"])
    m_large = c["sample_mass"] + hi * (lot - c["sample_mass"])
    assume(m_large > m_small * (1.0 + 1e-6))
    assume(m_large <= lot)
    assert fse(c, sample_mass=m_small) > fse(c, sample_mass=m_large)


@pytest.mark.req("P-004-07")
@pytest.mark.oracle("analytical", "zero when the sample is the whole lot")
@CFG
@given(c=case())
def test_zero_for_the_whole_lot(c: dict) -> None:
    assert fse(c, lot_mass=c["sample_mass"]) == 0.0


@pytest.mark.req("P-004-07")
@pytest.mark.oracle(
    "analytical", "tends to c f g l d^3 / M_S as the lot mass grows, from below, by exactly the factor (1 - M_S / M_L)"
)
@CFG
@given(c=case(), growth=st.floats(1e3, 1e15))
def test_infinite_lot_limit(c: dict, growth: float) -> None:
    limit = (
        c["mineralogical_factor"]
        * c["shape_factor"]
        * c["granulometric_factor"]
        * c["liberation_factor"]
        * c["top_size"] ** 3
        / c["sample_mass"]
    )
    big = c["sample_mass"] * growth
    value = fse(c, lot_mass=big)
    assert value == pytest.approx(limit * (1.0 - 1.0 / growth), rel=1e-12, abs=0.0)
    assert value <= limit * (1.0 + 1e-12)


@pytest.mark.req("FR-004-08")
@pytest.mark.oracle(
    "analytical",
    "the closed form (1 / M_S - 1 / M_L) c f g l d^3 recomputed in float arithmetic where the difference does not cancel",
)
@CFG
@given(c=case())
def test_closed_form(c: dict) -> None:
    assume(c["lot_mass"] >= 2.0 * c["sample_mass"])  # no cancellation in the naive difference
    ref = (
        (1.0 / c["sample_mass"] - 1.0 / c["lot_mass"])
        * c["mineralogical_factor"]
        * c["shape_factor"]
        * c["granulometric_factor"]
        * c["liberation_factor"]
        * c["top_size"] ** 3
    )
    assert fse(c) == pytest.approx(ref, rel=1e-12, abs=0.0)

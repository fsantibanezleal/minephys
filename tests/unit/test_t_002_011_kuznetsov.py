"""T-002-011 (FR-002-02, FR-002-18): Kuznetsov's mean fragment size with both exponent variants.

Expected API: `B.kuznetsov_x50(rock_factor, powder_factor, charge, rws, variant="cunningham1983")` -> x50 in m:

    x50 = A * K^(-0.8) * Q^(1/6) * (115 / RWS)^e   [cm]  ->  / 100  [m]

with e = 19/30 for `variant="cunningham1983"` (the default; its row `kuzram_rws_exponent_1983` is UNVERIFIED,
so the default emits `minephys.knowledge.UnverifiedParameterWarning` naming the row and its citation key
`mutinda2021`) and e = 19/20 for `variant="cunningham2005"` (verified, Cunningham 2005 eq. 1 p. 201; no such
warning). `rws` is the relative weight strength with ANFO = 100, 115 that of TNT. Any other `variant` raises
`InputError` naming `variant` and listing both.

Oracles: spec 002 section 7.4 worked example 1 (x50 = 0.29940630 m and 0.31295501 m, ratio 1.0452519; TC-2),
the published equation (Cunningham 2005 eq. 1, p. 201) evaluated in this file from the example's inputs, and
the knowledge rows of the table, pinned with `knowledge` markers.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest
from _table_helpers_a import rows_by_id
from minephys.knowledge import UnverifiedParameterWarning

import minephys
from minephys import blasting as B

# worked example 1 of spec 002 section 7.4 (illustrative design, unrounded intermediate values)
Q = 850.0 * math.pi / 4.0 * 0.25**2 * 7.2  # 300.41479749952396 kg
K = Q / (6.0 * 7.0 * 12.0)  # 0.5960611061498491 kg/m^3
A = 7.0


def x50_formula(a: float, k: float, q: float, rws: float, e: float) -> float:
    return a * k**-0.8 * q ** (1.0 / 6.0) * (115.0 / rws) ** e / 100.0


def silently(fn, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return fn(*args, **kwargs)


@pytest.mark.req("FR-002-02")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: kuznetsov_x50 (default, 19/30) = 0.29940630 m")
def test_printed_value_default_variant() -> None:
    got = silently(B.kuznetsov_x50, A, K, Q, 100.0)
    assert type(got) is np.float64
    assert got == pytest.approx(0.29940630, abs=5e-9)  # TC-2: 8 decimals
    assert got == pytest.approx(x50_formula(A, K, Q, 100.0, 19.0 / 30.0), rel=1e-12)


@pytest.mark.req("FR-002-02")
@pytest.mark.oracle("hand-calculation", "spec 002 7.4: variant cunningham2005 (19/20) = 0.31295501 m, ratio 1.0452519")
def test_printed_value_2005_variant() -> None:
    got = B.kuznetsov_x50(A, K, Q, 100.0, variant="cunningham2005")
    assert got == pytest.approx(0.31295501, abs=5e-9)
    assert got == pytest.approx(x50_formula(A, K, Q, 100.0, 19.0 / 20.0), rel=1e-12)
    old = silently(B.kuznetsov_x50, A, K, Q, 100.0, variant="cunningham1983")
    assert got / old == pytest.approx(1.0452519, abs=5e-8)


@pytest.mark.req("FR-002-02")
@pytest.mark.oracle("analytical", "Cunningham 2005 eq. 1 on a grid of inputs, both variants")
@pytest.mark.parametrize("variant", ["cunningham1983", "cunningham2005"])
@pytest.mark.parametrize(
    ("a", "k", "q", "rws"),
    [
        (0.8, 0.1, 1.0, 50.0),
        (22.0, 3.0, 3000.0, 200.0),
        (5.0, 0.5, 100.0, 85.0),
        (10.0, 1.0, 1.0, 115.0),
        (7.0, 0.35, 2500.0, 130.0),
    ],
)
def test_equation_on_a_grid(variant: str, a: float, k: float, q: float, rws: float) -> None:
    e = 19.0 / 30.0 if variant == "cunningham1983" else 19.0 / 20.0
    got = silently(B.kuznetsov_x50, a, k, q, rws, variant=variant)
    assert got == pytest.approx(x50_formula(a, k, q, rws, e), rel=1e-12)


@pytest.mark.req("FR-002-02")
@pytest.mark.oracle("analytical", "TNT (RWS = 115) is the reference: both variants coincide exactly")
def test_variants_coincide_at_rws_115() -> None:
    a = silently(B.kuznetsov_x50, A, K, Q, 115.0, variant="cunningham1983")
    b = silently(B.kuznetsov_x50, A, K, Q, 115.0, variant="cunningham2005")
    assert a == b


@pytest.mark.req("FR-002-02")
@pytest.mark.oracle("hand-calculation", "arrays broadcast: rock factors (row) by RWS (column)")
def test_broadcasting() -> None:
    a = np.array([4.0, 7.0, 10.0])
    rws = np.array([[80.0], [100.0]])
    out = B.kuznetsov_x50(a, K, Q, rws, variant="cunningham2005")
    assert out.shape == (2, 3)
    for i in range(2):
        for j in range(3):
            assert out[i, j] == pytest.approx(x50_formula(float(a[j]), K, Q, float(rws[i, 0]), 19.0 / 20.0), rel=1e-12)
    assert B.kuznetsov_x50(np.empty(0), K, Q, 100.0, variant="cunningham2005").shape == (0,)


@pytest.mark.req("FR-002-02")
@pytest.mark.oracle(
    "hand-calculation", "FR-008-12: the default (UNVERIFIED 19/30) warns, naming the row and its citation key"
)
def test_default_variant_emits_the_unverified_warning() -> None:
    with pytest.warns(UnverifiedParameterWarning) as rec:
        B.kuznetsov_x50(A, K, Q, 100.0)
    text = " ".join(str(w.message) for w in rec)
    assert "kuzram_rws_exponent_1983" in text
    assert "mutinda2021" in text
    with pytest.warns(UnverifiedParameterWarning):
        B.kuznetsov_x50(A, K, Q, 100.0, variant="cunningham1983")


@pytest.mark.req("FR-002-02")
@pytest.mark.oracle("hand-calculation", "the verified 2005 variant is silent about UNVERIFIED rows")
def test_2005_variant_is_silent() -> None:
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        B.kuznetsov_x50(A, K, Q, 100.0, variant="cunningham2005")
    assert [w for w in rec if issubclass(w.category, UnverifiedParameterWarning)] == []


@pytest.mark.req("FR-002-18")
@pytest.mark.oracle("hand-calculation", "FR-000-15: an unknown variant lists the allowed values; matching is exact")
@pytest.mark.parametrize(
    "bad",
    [
        "cunningham2000",
        "Cunningham2005",
        "CUNNINGHAM1983",
        "cunningham2005 ",
        " cunningham1983",
        "",
        "2005",
        "kuz-ram",
        "cunningham" + chr(0x0661) + "983",  # an Arabic-Indic digit one, not the ASCII 1
    ],
)
def test_unknown_variant(bad: str) -> None:
    with pytest.raises(minephys.InputError) as ei:
        silently(B.kuznetsov_x50, A, K, Q, 100.0, variant=bad)
    assert ei.value.argument == "variant"
    assert "cunningham1983" in str(ei.value)
    assert "cunningham2005" in str(ei.value)


@pytest.mark.req("FR-002-18")
@pytest.mark.oracle("hand-calculation", "a non-string variant is not an allowed value either")
@pytest.mark.parametrize("bad", [None, 1983, 2005.0, b"cunningham1983", ("cunningham1983",)], ids=repr)
def test_non_string_variant(bad) -> None:
    with pytest.raises((minephys.InputError, minephys.InputTypeError)) as ei:
        silently(B.kuznetsov_x50, A, K, Q, 100.0, variant=bad)
    assert ei.value.argument == "variant"


# ---------------------------------------------------------------- knowledge rows pinned (verified rows)


@pytest.mark.req("FR-002-02")
@pytest.mark.knowledge("kuznetsov_powder_factor_exponent")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 201: x50 = A K^(-0.8) Q^(1/6) (115/RWS)^(19/20)")
def test_row_powder_factor_exponent() -> None:
    assert rows_by_id("blasting")["kuznetsov_powder_factor_exponent"]["value"] == -0.8
    base = B.kuznetsov_x50(A, K, Q, 100.0, variant="cunningham2005")
    assert B.kuznetsov_x50(A, 2.0 * K, Q, 100.0, variant="cunningham2005") == pytest.approx(base * 2.0**-0.8, rel=1e-12)


@pytest.mark.req("FR-002-02")
@pytest.mark.knowledge("kuznetsov_charge_exponent")
@pytest.mark.oracle(
    "worked-example", "cunningham2005 p. 201: the charge enters as Q^(1/6): 64 times the charge doubles x50"
)
def test_row_charge_exponent() -> None:
    assert rows_by_id("blasting")["kuznetsov_charge_exponent"]["value"] == "1/6"
    base = B.kuznetsov_x50(A, K, Q, 100.0, variant="cunningham2005")
    assert B.kuznetsov_x50(A, K, 64.0 * Q, 100.0, variant="cunningham2005") == pytest.approx(2.0 * base, rel=1e-12)


@pytest.mark.req("FR-002-02")
@pytest.mark.knowledge("kuznetsov_tnt_relative_weight_strength")
@pytest.mark.oracle(
    "worked-example", "cunningham2005 p. 201: 115 is the RWS of TNT, so RWS = 115 removes the strength term"
)
def test_row_tnt_relative_weight_strength() -> None:
    assert rows_by_id("blasting")["kuznetsov_tnt_relative_weight_strength"]["value"] == 115
    assert B.kuznetsov_x50(A, K, Q, 115.0, variant="cunningham2005") == pytest.approx(
        A * K**-0.8 * Q ** (1.0 / 6.0) / 100.0, rel=1e-12
    )


@pytest.mark.req("FR-002-02")
@pytest.mark.knowledge("kuzram_rws_exponent_2005")
@pytest.mark.oracle("worked-example", "cunningham2005 p. 201: the strength exponent is 19/20")
def test_row_rws_exponent_2005() -> None:
    assert rows_by_id("blasting")["kuzram_rws_exponent_2005"]["value"] == "19/20"
    lo = B.kuznetsov_x50(A, K, Q, 80.0, variant="cunningham2005")
    hi = B.kuznetsov_x50(A, K, Q, 160.0, variant="cunningham2005")
    assert lo / hi == pytest.approx(2.0**0.95, rel=1e-12)

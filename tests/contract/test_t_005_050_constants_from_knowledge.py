"""T-005-050 (FR-005-34): every constant of FR-005-01 to FR-005-11, FR-005-32 and FR-005-33 is read through `get_value`.

Method (fixture knowledge layout, implementation independent): each case runs a fresh interpreter in which
`minephys.knowledge.get_value` is replaced, before the first call of any comminution function, by a wrapper that returns a
replacement value for the rows named in the case and the real value for every other row (the attribute is replaced in the
package and in every already imported `minephys.*` module that bound the name). A fresh interpreter makes the check
independent of any lazy cache inside the module. The function result with the replaced row must change by the analytical
amount:
- a row that scales the result (the Bond coefficient 10 -> 20, the Bond ball-mill constant, the short-ton factor, the Morrell
  coefficient 4 -> 8, the Ws factor 0.19 -> 0.38, Mib's constant) multiplies it by the same ratio;
- an exponent or scale row changes it by the closed-form ratio or by the hand formula evaluated with the replacement
  (written out below);
- the `limit` rows (70 um, 45 um) move the thresholds of the validity warnings.
Values are given in the units of the rows as published (um, kWh/t, ...).

Oracle: analytical sensitivity (hand calculation); the baseline is the unmodified function from the same interpreter, so
only ratios and hand formulas enter the assertions.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]

PREAMBLE = """
import json, sys, warnings
import minephys.knowledge as K
import minephys.comminution as C
OVER = json.loads(sys.argv[1])
orig = K.get_value
def patched(row_id):
    if row_id in OVER:
        return float(OVER[row_id])
    return orig(row_id)
K.get_value = patched
for name, mod in list(sys.modules.items()):
    if name.startswith("minephys") and getattr(mod, "get_value", None) is orig:
        mod.get_value = patched
def count_validity(fn):
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        value = float(fn())
    return {"value": value, "warnings": sum(1 for r in rec if r.category.__name__ == "ValidityWarning")}
"""


def run(expression: str, overrides: dict[str, float] | None = None) -> Any:
    script = PREAMBLE + f"\nprint(json.dumps({expression}))\n"
    proc = subprocess.run(
        [sys.executable, "-c", script, json.dumps(overrides or {})],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=120,
    )
    assert proc.returncode == 0, f"fresh interpreter failed:\n{proc.stderr[-1500:]}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def f_of(x_um: float, c: float = 0.295, scale: float = 1e6) -> float:
    return -(c + x_um / scale)


# ----------------------------------------------------------------------------------------------- Bond

BOND = "float(C.bond_energy(5.4e4, 2e-3, 1.5e-4))"
BOND_IO = "float(C.bond_operating_work_index(3.0e4, 2.5e-3, 2.12e-4))"
BOND_BM = "float(C.bond_ball_mill_work_index(1.06e-4, 1.825e-3, 2.7461e-3, 7.97e-5))"


@pytest.mark.req("FR-005-34")
@pytest.mark.oracle("analytical", "replacing the Bond coefficient 10 by 20 doubles W and halves Wio")
def test_fr_005_34_bond_law_coefficient() -> None:
    base, doubled = run(BOND), run(BOND, {"bond_law_coefficient": 20})
    assert doubled == pytest.approx(2.0 * base, rel=1e-12)
    base_io, halved = run(BOND_IO), run(BOND_IO, {"bond_law_coefficient": 20})
    assert halved == pytest.approx(0.5 * base_io, rel=1e-12)


@pytest.mark.req("FR-005-34")
@pytest.mark.parametrize(
    ("row", "value", "factor"),
    [
        ("bond_bm_constant", 89.0, 2.0),
        ("bond_short_ton_to_metric", 2.205, 2.0),
        ("bond_bm_exponent_screen", 0.46, 106.0 ** -(0.46 - 0.23)),  # P1 = 106 um enters as P1^-e
        ("bond_bm_exponent_grindability", 1.64, 1.825 ** -(1.64 - 0.82)),  # Gbp = 1.825 g/rev enters as Gbp^-e
    ],
)
def test_fr_005_34_ball_mill_test_constants(row: str, value: float, factor: float) -> None:
    base = run(BOND_BM)
    assert run(BOND_BM, {row: value}) == pytest.approx(factor * base, rel=1e-12)


@pytest.mark.req("FR-005-34")
@pytest.mark.oracle("analytical", "the 70 um limit row moves the validity threshold")
def test_fr_005_34_bond_validity_limit_row() -> None:
    expr = "count_validity(lambda: C.bond_energy(5.4e4, 5e-3, 8e-5))"
    assert run(expr)["warnings"] == 0  # 80 um is above the published 70 um
    assert run(expr, {"bond_min_product_size": 100})["warnings"] >= 1  # but below a 100 um limit
    expr_low = "count_validity(lambda: C.bond_energy(5.4e4, 5e-3, 5e-5))"
    assert run(expr_low)["warnings"] >= 1
    assert run(expr_low, {"bond_min_product_size": 40})["warnings"] == 0


# --------------------------------------------------------------------------------------------- Morrell

MORRELL = "float(C.morrell_energy(2.0e4, 2e-3, 1.5e-4))"


@pytest.mark.req("FR-005-34")
def test_fr_005_34_morrell_coefficient_scales_every_energy_function() -> None:
    for expr in (
        MORRELL,
        "float(C.morrell_tumbling_fine(6.8e4, 1.06e-4))",
        "float(C.morrell_tumbling_coarse(7.0e4, 0.1, False))",
        "float(C.morrell_crusher(2.6e4, 0.1, 0.035, True, 'secondary'))",
        "float(C.morrell_hpgr(5.0e4, 0.035, 0.004, True))",
        "float(C.morrell_size_distribution_correction(7.0e4, 0.1, 6.5e-3))",
    ):
        assert run(expr, {"morrell_coefficient": 8}) == pytest.approx(2.0 * run(expr), rel=1e-12), expr


@pytest.mark.req("FR-005-34")
def test_fr_005_34_morrell_exponent_rows_follow_the_hand_formula() -> None:
    mi, x1, x2 = 2.0e4, 2000.0, 150.0
    got = run(MORRELL, {"morrell_f_constant": 0.395})
    expected = mi * 4.0 * (x2 ** f_of(x2, c=0.395) - x1 ** f_of(x1, c=0.395))
    assert got == pytest.approx(expected, rel=1e-12)
    got = run(MORRELL, {"morrell_f_scale": 2.0e6})
    expected = mi * 4.0 * (x2 ** f_of(x2, scale=2e6) - x1 ** f_of(x1, scale=2e6))
    assert got == pytest.approx(expected, rel=1e-12)


@pytest.mark.req("FR-005-34")
def test_fr_005_34_coarse_fine_boundary_row() -> None:
    g = lambda x: x ** f_of(x)  # noqa: E731
    mia, mib = 7.0e4, 6.8e4
    coarse = run("float(C.morrell_tumbling_coarse(7.0e4, 0.1, False))", {"morrell_coarse_fine_boundary": 1000})
    assert coarse == pytest.approx(mia * 4.0 * (g(1000.0) - g(1.0e5)), rel=1e-12)
    fine = run("float(C.morrell_tumbling_fine(6.8e4, 1.06e-4))", {"morrell_coarse_fine_boundary": 1000})
    assert fine == pytest.approx(mib * 4.0 * (g(106.0) - g(1000.0)), rel=1e-12)


@pytest.mark.req("FR-005-34")
@pytest.mark.parametrize(
    ("row", "value", "expr", "factor"),
    [
        ("morrell_k1_pebble_crusher", 0.9, "float(C.morrell_tumbling_coarse(7.0e4, 0.1, True))", 0.9 / 0.95),
        ("morrell_k2_open_circuit", 1.5, "float(C.morrell_crusher(2.6e4, 0.1, 0.035, False, 'secondary'))", 1.5 / 1.19),
        ("morrell_k3_open_circuit", 1.5, "float(C.morrell_hpgr(5.0e4, 0.035, 0.004, False))", 1.5 / 1.19),
        ("morrell_ks_crusher", 27.5, "float(C.morrell_crusher(2.6e4, 0.1, 0.035, True, 'secondary'))", 0.5),
        ("morrell_ks_hpgr", 17.5, "float(C.morrell_hpgr(5.0e4, 0.035, 0.004, True))", 0.5),
        ("morrell_ws_factor", 0.38, "float(C.morrell_size_distribution_correction(7.0e4, 0.1, 6.5e-3))", 2.0),
        ("morrell_mib_constant", 36.36, "float(C.morrell_mib(1.06e-4, 1.825e-3, 2.7461e-3, 7.97e-5))", 2.0),
        (
            "morrell_mib_screen_exponent",
            0.59,
            "float(C.morrell_mib(1.06e-4, 1.825e-3, 2.7461e-3, 7.97e-5))",
            106.0 ** -(0.59 - 0.295) * 1.0,
        ),
    ],
)
def test_fr_005_34_morrell_factor_rows(row: str, value: float, expr: str, factor: float) -> None:
    # morrell_mib_screen_exponent is the exponent of P100 in the denominator of Mib: raising it divides Mib by P100^delta
    base = run(expr)
    assert run(expr, {row: value}) == pytest.approx(factor * base, rel=1e-12)


@pytest.mark.req("FR-005-34")
def test_fr_005_34_size_factor_exponent_row() -> None:
    x1, x2 = 1.0e5, 3.5e4
    base = 7.2 * 3600.0 * 4.0
    g = lambda x: x ** f_of(x)  # noqa: E731
    stage = base * (g(x2) - g(x1))
    sc = min(55.0 * (x1 * x2) ** -0.3, 1.0)
    got = run("float(C.morrell_crusher(2.592e4, 0.1, 0.035, True, 'secondary'))", {"morrell_s_exponent": -0.3})
    assert got == pytest.approx(sc * stage, rel=1e-12)


@pytest.mark.req("FR-005-34")
@pytest.mark.oracle("analytical", "the 45 um limit row moves the validity threshold of the fine term")
def test_fr_005_34_morrell_validity_limit_row() -> None:
    expr30 = "count_validity(lambda: C.morrell_tumbling_fine(6.8e4, 3e-5))"
    assert run(expr30)["warnings"] >= 1  # 30 um is below the published 45 um
    assert run(expr30, {"morrell_fine_grind_limit": 20})["warnings"] == 0
    expr60 = "count_validity(lambda: C.morrell_tumbling_fine(6.8e4, 6e-5))"
    assert run(expr60)["warnings"] == 0
    assert run(expr60, {"morrell_fine_grind_limit": 80})["warnings"] >= 1

"""T-005-001 (DC-005-02, FR-008-14): literal `@pytest.mark.knowledge("<equation id>")` pins for the verified comminution equations.

The comminution equation entries that were read on the two guidelines (`mcivor2016bondgmsg`, `gmsg2016morrell`) are `verified`
in `src/minephys/knowledge/catalogue/equations.yaml`; every verified equation needs a literal knowledge marker in the test
tree (spec 008 FR-008-14, SC-008-01). Each test below pins one entry and checks it against the form printed in the guideline
(hand transcription of the formula, spec 005 section 7), independently of the loader (`yaml.safe_load`).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

EQUATIONS = Path(__file__).resolve().parents[2] / "src" / "minephys" / "knowledge" / "catalogue" / "equations.yaml"


def _entry(equation_id: str) -> dict[str, Any]:
    entries = {e["id"]: e for e in yaml.safe_load(EQUATIONS.read_text(encoding="utf-8"))["equations"]}
    assert equation_id in entries, f"{equation_id} is not in the equations catalogue"
    return entries[equation_id]


def _check(equation_id: str, function: str, citation: str, *must_contain: str) -> None:
    e = _entry(equation_id)
    assert e["verification"] == "verified" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e["verified_on"]))
    assert e["function"] == f"minephys.comminution.{function}"
    assert e["citation"] == citation and e["domain"] == "comminution"
    for token in must_contain:
        assert token in e["latex"], f"{equation_id}: {token!r} is not in the LaTeX {e['latex']!r}"


@pytest.mark.req("DC-005-02")
@pytest.mark.oracle("hand-calculation", "Bond's law as printed in mcivor2016bondgmsg p. 1: W = 10 Wi (1/sqrt(P80) - 1/sqrt(F80))")
@pytest.mark.knowledge("comminution_bond_energy")
def test_pin_comminution_bond_energy() -> None:
    _check("comminution_bond_energy", "bond_energy", "mcivor2016bondgmsg", "10", "P_{80}", "F_{80}")


@pytest.mark.req("DC-005-02")
@pytest.mark.oracle("hand-calculation", "Bond operating work index as printed in mcivor2016bondgmsg pp. 1-2")
@pytest.mark.knowledge("comminution_bond_operating_work_index")
def test_pin_comminution_bond_operating_work_index() -> None:
    _check("comminution_bond_operating_work_index", "bond_operating_work_index", "mcivor2016bondgmsg", "W_{io}", "10")


@pytest.mark.req("DC-005-02")
@pytest.mark.oracle("hand-calculation", "Bond ball-mill test equation as printed in mcivor2016bondgmsg p. 10: 44.5, 0.23, 0.82, 1.1025")
@pytest.mark.knowledge("comminution_bond_ball_mill_work_index")
def test_pin_comminution_bond_ball_mill_work_index() -> None:
    _check("comminution_bond_ball_mill_work_index", "bond_ball_mill_work_index", "mcivor2016bondgmsg", "1.1025", "44.5", "0.23", "0.82")


@pytest.mark.req("DC-005-02")
@pytest.mark.oracle("hand-calculation", "Morrell relation as printed in gmsg2016morrell eq. 2: W = Mi 4 (x2^f(x2) - x1^f(x1))")
@pytest.mark.knowledge("comminution_morrell_energy")
def test_pin_comminution_morrell_energy() -> None:
    _check("comminution_morrell_energy", "morrell_energy", "gmsg2016morrell", "M_i", "0.295", "10^6")


@pytest.mark.req("DC-005-02")
@pytest.mark.oracle("hand-calculation", "Morrell coarse tumbling term, gmsg2016morrell eq. B2: K1 Mia 4 (750^f(750) - x1^f(x1))")
@pytest.mark.knowledge("comminution_morrell_tumbling_coarse")
def test_pin_comminution_morrell_tumbling_coarse() -> None:
    _check("comminution_morrell_tumbling_coarse", "morrell_tumbling_coarse", "gmsg2016morrell", "K_1", "750")


@pytest.mark.req("DC-005-02")
@pytest.mark.oracle("hand-calculation", "Morrell fine tumbling term, gmsg2016morrell eq. B3: Mib 4 (P80^f(P80) - 750^f(750))")
@pytest.mark.knowledge("comminution_morrell_tumbling_fine")
def test_pin_comminution_morrell_tumbling_fine() -> None:
    _check("comminution_morrell_tumbling_fine", "morrell_tumbling_fine", "gmsg2016morrell", "M_{ib}", "750")


@pytest.mark.req("DC-005-02")
@pytest.mark.oracle("hand-calculation", "Morrell crushing term, gmsg2016morrell eqs. B4-B5: Sc K2 Mic 4 (...), Sc = min(55 (x1 x2)^-0.2, 1)")
@pytest.mark.knowledge("comminution_morrell_crusher")
def test_pin_comminution_morrell_crusher() -> None:
    _check("comminution_morrell_crusher", "morrell_crusher", "gmsg2016morrell", "55", "K_2", "-0.2")


@pytest.mark.req("DC-005-02")
@pytest.mark.oracle("hand-calculation", "Morrell HPGR term, gmsg2016morrell eq. B6: Sh K3 Mih 4 (...), Sh = min(35 (x1 x2)^-0.2, 1)")
@pytest.mark.knowledge("comminution_morrell_hpgr")
def test_pin_comminution_morrell_hpgr() -> None:
    _check("comminution_morrell_hpgr", "morrell_hpgr", "gmsg2016morrell", "35", "K_3", "-0.2")


@pytest.mark.req("DC-005-02")
@pytest.mark.oracle("hand-calculation", "Morrell size-distribution correction, gmsg2016morrell section B.2.4: Ws = 0.19 Mia 4 (...)")
@pytest.mark.knowledge("comminution_morrell_size_distribution_correction")
def test_pin_comminution_morrell_size_distribution_correction() -> None:
    _check("comminution_morrell_size_distribution_correction", "morrell_size_distribution_correction", "gmsg2016morrell", "0.19")


@pytest.mark.req("DC-005-02")
@pytest.mark.oracle("hand-calculation", "Morrell Mib relation, gmsg2016morrell eq. 1: 18.18 / (P100^0.295 Gbp (P80^f(P80) - F80^f(F80)))")
@pytest.mark.knowledge("comminution_morrell_mib")
def test_pin_comminution_morrell_mib() -> None:
    _check("comminution_morrell_mib", "morrell_mib", "gmsg2016morrell", "18.18", "0.295", "P_{100}")

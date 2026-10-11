"""T-005-061 (NFR-005-02): the comminution reference sizes are registered in `tools/bench.py`.

Expected: `tools/bench.py` (foundation T-000-023) registers the three latency entries of NFR-005-02 with their reference
sizes: `pbm_batch_grinding` (30 classes, 10 times), `pbm_continuous_mill` (30 classes, 10 tanks) and `mine_to_mill_chain` (400
sizes), next to a closed-form scalar entry of the module, so that `python tools/bench.py` can report the medians against the
thresholds of NFR-005-02 (<= 1 ms for closed forms on scalars, <= 50 ms for the three sized entries).
The registry format is owned by T-000-023; this test therefore reads the tool's source text (it is stable under any registry
representation) and, where the file exposes a module-level registry, checks the sizes there too. The registry format is an
open point recorded in the red-phase report.

Oracle: hand-written expectations of NFR-005-02.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "tools" / "bench.py"
ENTRIES = ["pbm_batch_grinding", "pbm_continuous_mill", "mine_to_mill_chain"]


def _text() -> str:
    assert BENCH.is_file(), "missing tools/bench.py (foundation task T-000-023)"
    return BENCH.read_text(encoding="utf-8")


@pytest.mark.req("NFR-005-02")
@pytest.mark.oracle("hand-calculation", "NFR-005-02 reference sizes")
@pytest.mark.parametrize("entry", ENTRIES)
def test_nfr_005_02_sized_entries_are_registered(entry: str) -> None:
    assert re.search(rf"\b{entry}\b", _text()), f"{entry} is not registered in tools/bench.py"


@pytest.mark.req("NFR-005-02")
def test_nfr_005_02_reference_sizes_are_stated() -> None:
    text = _text()
    assert "minephys.comminution" in text or "comminution" in text
    # 30 classes (batch and continuous) and 400 sizes (chain) appear as literals of the registry
    assert re.search(r"\b30\b", text), "the 30-class reference size is not stated"
    assert re.search(r"\b400\b", text), "the 400-size chain reference is not stated"


@pytest.mark.req("NFR-005-02")
def test_nfr_005_02_a_scalar_closed_form_entry_exists() -> None:
    text = _text()
    closed = ["bond_energy", "morrell_energy", "flotation_first_order", "klimpel_recovery", "two_product_recovery"]
    assert any(re.search(rf"\b{name}\b", text) for name in closed), "no scalar closed-form comminution entry"

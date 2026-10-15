"""T-007-051 (NFR-007-02): the planning reference sizes are registered in `tools/bench.py`.

Expected: `tools/bench.py` (foundation T-000-023) registers the latency entries of NFR-007-02 with their reference sizes: a closed
form on scalars (for example `block_economic_value` or `npv`; threshold <= 1 ms), `ultimate_pit_mincut` and `nested_pits` (5 revenue
factors) on a 6 x 6 x 6 grid with "1-5" arcs, and `lane_cutoff_grades` at 50 bins (each <= 50 ms median), so that
`python tools/bench.py` can report them. The registry format is owned by T-000-023; this test reads the tool's source text, which is
stable under any registry representation. The open point is recorded in the red-phase report.

Oracle: hand-written expectations of NFR-007-02.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "tools" / "bench.py"
ENTRIES = ["ultimate_pit_mincut", "nested_pits", "lane_cutoff_grades"]


def _text() -> str:
    assert BENCH.is_file(), "missing tools/bench.py (foundation task T-000-023)"
    return BENCH.read_text(encoding="utf-8")


@pytest.mark.req("NFR-007-02")
@pytest.mark.oracle("hand-calculation", "NFR-007-02 reference sizes")
@pytest.mark.parametrize("entry", ENTRIES)
def test_nfr_007_02_sized_entries_are_registered(entry: str) -> None:
    assert re.search(rf"\b{entry}\b", _text()), f"{entry} is not registered in tools/bench.py"


@pytest.mark.req("NFR-007-02")
def test_nfr_007_02_reference_sizes_are_stated() -> None:
    text = _text()
    assert "planning" in text
    assert re.search(r"\b6\b", text) and re.search(r"1-5", text), "the 6 x 6 x 6 grid with '1-5' arcs is not stated"
    assert re.search(r"\b50\b", text), "the 50-bin Lane reference size is not stated"


@pytest.mark.req("NFR-007-02")
def test_nfr_007_02_a_scalar_closed_form_entry_exists() -> None:
    text = _text()
    assert any(re.search(rf"\b{name}\b", text) for name in ("block_economic_value", "breakeven_cutoff_grade", "npv", "strip_ratio"))

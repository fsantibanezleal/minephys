"""T-006-051 (NFR-006-02): the environment reference sizes are registered in `tools/bench.py`.

Expected: `tools/bench.py` (foundation T-000-023) registers the two latency entries of NFR-006-02 with their reference sizes: a
closed-form scalar call of the module (for example `ap42_unpaved_emission_factor` or `pasquill_sigmas`; threshold <= 1 ms) and
`gaussian_plume` over a 1,000 x 1,000 receptor grid (threshold <= 0.5 s median), so that `python tools/bench.py` can report them.
The registry format is owned by T-000-023; this test reads the tool's source text, which is stable under any registry
representation. The open point is recorded in the red-phase report.

Oracle: hand-written expectations of NFR-006-02.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "tools" / "bench.py"


def _text() -> str:
    assert BENCH.is_file(), "missing tools/bench.py (foundation task T-000-023)"
    return BENCH.read_text(encoding="utf-8")


@pytest.mark.req("NFR-006-02")
@pytest.mark.oracle("hand-calculation", "NFR-006-02 reference sizes")
def test_nfr_006_02_the_plume_grid_entry_is_registered() -> None:
    text = _text()
    assert re.search(r"\bgaussian_plume\b", text), "gaussian_plume is not registered in tools/bench.py"
    assert re.search(r"\b1000\b|1_000|1e3", text), "the 1,000 x 1,000 receptor grid size is not stated"


@pytest.mark.req("NFR-006-02")
def test_nfr_006_02_a_scalar_closed_form_entry_exists() -> None:
    text = _text()
    closed = [
        "ap42_unpaved_emission_factor",
        "pasquill_sigmas",
        "beer_lambert_transmittance",
        "lidar_dust_return",
        "precipitation_correction",
    ]
    assert "environment" in text
    assert any(re.search(rf"\b{name}\b", text) for name in closed), "no scalar closed-form environment entry"

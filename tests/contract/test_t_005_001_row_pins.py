"""T-005-001 (DC-005-01): literal `@pytest.mark.knowledge("<row id>")` pins for the verified comminution rows that no other test pins literally.

`tests/contract/test_t_005_001_comminution_knowledge.py` pins every verified row through a marker built at import time
(`pytest.mark.knowledge(row_id)`); tools that look for the pins by source text (`tools/check_knowledge.py`, the SC-008-01 and FR-008-14
checks of spec 008, `tools/trace.py`) read only string literals, so each such row also needs a literal marker somewhere. The rows
of the section 7 list that are verified and are not pinned by a literal marker in the unit tests are listed here, each with the
printed value of spec 005 section 7 (hand transcription, the YAML parsed with `yaml.safe_load` independently of the loader).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

TABLE = Path(__file__).resolve().parents[2] / "src" / "minephys" / "knowledge" / "comminution.yaml"


def _row(row_id: str) -> dict[str, Any]:
    assert TABLE.is_file(), "missing src/minephys/knowledge/comminution.yaml"
    rows = {r["id"]: r for r in yaml.safe_load(TABLE.read_text(encoding="utf-8"))["rows"]}
    assert row_id in rows, f"{row_id} is not in the comminution table"
    return rows[row_id]


@pytest.mark.req("DC-005-01")
@pytest.mark.oracle("hand-calculation", "published value transcribed from spec section 7")
@pytest.mark.knowledge("morrell_relative_error_sd")
def test_pin_morrell_relative_error_sd() -> None:
    row = _row("morrell_relative_error_sd")
    assert row["value"] == 0.065
    assert row["verification"] == "verified"

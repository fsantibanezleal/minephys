"""T-005-090 (SC-005-02): the mutation score of `src/minephys/comminution/` is recorded and meets the threshold.

Expected: the mutation run of foundation T-000-024 is executed on `src/minephys/comminution/` and its score is recorded in the
log line of task T-005-090 in `specs/005-comminution/tasks.md`: the task is ticked `[x]` and the line carries `score 0.NN`
(or `score: 0.NN`). The test fails below `mutation.numerical_core_min` of `specs/000-foundation/thresholds.yaml` (0.80).
The record location is the one named by the plan ("record the score in the task log"); an open point on the exact line format
is listed in the red-phase report.

Oracle: the threshold file (hand-written gate) and the recorded score.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def _threshold() -> float:
    data = yaml.safe_load((ROOT / "specs" / "000-foundation" / "thresholds.yaml").read_text(encoding="utf-8"))
    return float(data["mutation"]["numerical_core_min"])


def _log_line() -> str:
    for line in (ROOT / "specs" / "005-comminution" / "tasks.md").read_text(encoding="utf-8").splitlines():
        if "T-005-090" in line:
            return line
    raise AssertionError("task T-005-090 not found in specs/005-comminution/tasks.md")


@pytest.mark.req("SC-005-02")
@pytest.mark.oracle("hand-calculation", "thresholds.yaml mutation.numerical_core_min (0.80, only ratchets upwards)")
def test_sc_005_02_mutation_score_is_recorded_and_meets_the_threshold() -> None:
    assert _threshold() >= 0.80
    line = _log_line()
    assert re.match(r"\s*-\s*\[[xX]\]", line), "T-005-090 is not ticked"
    m = re.search(r"score[:= ]+\s*(0?\.\d+|1(?:\.0+)?)", line)
    assert m, "no 'score 0.NN' recorded on the T-005-090 line of tasks.md"
    assert float(m.group(1)) >= _threshold()
    assert (ROOT / "src" / "minephys" / "comminution").is_dir()

"""STANDARD_GRAVITY (the exact ratio 980665/100000 of minephys._constants) equals the `standard_gravity` knowledge row."""

from __future__ import annotations

import pytest

from minephys import _constants, knowledge


@pytest.mark.req("FR-000-19")
@pytest.mark.oracle("analytical", "the code constant and the units table row both state g0 = 9.80665 m/s^2 exactly")
def test_standard_gravity_equals_the_row() -> None:
    assert float(knowledge.get_value("standard_gravity")) == _constants.STANDARD_GRAVITY  # type: ignore[arg-type]

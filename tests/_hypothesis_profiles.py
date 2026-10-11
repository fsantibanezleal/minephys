"""Hypothesis profiles (T-000-024, NFR-000-08): `dev`, `ci` and `release`, selected by `HYPOTHESIS_PROFILE`.

The example counts of `ci` and `release` come from `specs/000-foundation/thresholds.yaml` (`property_tests`), the only
source of truth; `dev` is a fast local profile of 50 examples. Every profile disables the deadline. An unknown profile
name is an error, never a silent default. Loaded by pytest through `addopts = ["-p", "_hypothesis_profiles"]`.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from hypothesis import settings

THRESHOLDS = Path(__file__).resolve().parents[1] / "specs" / "000-foundation" / "thresholds.yaml"
_DEV_EXAMPLES = 50


def _examples() -> dict[str, int]:
    doc = yaml.safe_load(THRESHOLDS.read_text(encoding="utf-8"))["property_tests"]
    return {
        "dev": _DEV_EXAMPLES,
        "ci": int(doc["ci_examples_per_test"]),
        "release": int(doc["release_examples_per_test"]),
    }


PROFILES = _examples()
for _name, _count in PROFILES.items():
    settings.register_profile(_name, max_examples=_count, deadline=None)

_selected = os.environ.get("HYPOTHESIS_PROFILE")
if _selected is not None:
    if _selected not in PROFILES:
        raise SystemExit(f"unknown HYPOTHESIS_PROFILE {_selected!r}; the profiles are {sorted(PROFILES)}")
    settings.load_profile(_selected)
else:
    settings.load_profile("dev")

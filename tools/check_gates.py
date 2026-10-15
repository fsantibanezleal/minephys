"""Numeric quality-gate evaluator (spec 000 NFR-000-08).

Usage:  python tools/check_gates.py [--thresholds FILE] [--branch-coverage X] [--changed-lines-coverage X]
                                    [--mutation-score X] [--hypothesis-examples N --profile ci|release]
Fractions are in [0, 1]. Exit 1 with a `FAIL` line when a measured value is below its minimum, 0 with `OK` (and a `warn`
line when the mutation score lies in [fail_below, numerical_core_min)), 2 for usage errors (no traceback).
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parents[1]
DEFAULT = HERE / "specs" / "000-foundation" / "thresholds.yaml"
PROFILES = {"ci": "ci_examples_per_test", "release": "release_examples_per_test"}


class UsageError(Exception):
    pass


def fraction(text: str, flag: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise UsageError(f"{flag}: {text!r} is not a number") from None
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise UsageError(f"{flag}: {text!r} is not a fraction in [0, 1]")
    return value


def load(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        return {
            "branch": float(doc["coverage"]["branch_core_min"]),
            "changed": float(doc["coverage"]["changed_lines_min"]),
            "mutation_min": float(doc["mutation"]["numerical_core_min"]),
            "mutation_fail": float(doc["mutation"]["numerical_core_fail_below"]),
            "examples": {k: int(doc["property_tests"][v]) for k, v in PROFILES.items()},
        }
    except (OSError, yaml.YAMLError, KeyError, TypeError, ValueError) as err:
        raise UsageError(f"{path}: cannot read the thresholds ({type(err).__name__})") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thresholds", type=Path, default=DEFAULT)
    parser.add_argument("--branch-coverage")
    parser.add_argument("--changed-lines-coverage")
    parser.add_argument("--mutation-score")
    parser.add_argument("--hypothesis-examples")
    parser.add_argument("--profile")
    args = parser.parse_args(argv)
    try:
        limits = load(args.thresholds)
        lines: list[str] = []
        failed = False

        def gate(label: str, value: float, minimum: float) -> None:
            nonlocal failed
            if value < minimum:
                failed = True
                lines.append(f"FAIL {label} {value} is below {minimum}")
            else:
                lines.append(f"OK {label} {value} (minimum {minimum})")

        if args.branch_coverage is not None:
            gate("branch coverage", fraction(args.branch_coverage, "--branch-coverage"), limits["branch"])
        if args.changed_lines_coverage is not None:
            gate(
                "changed-lines coverage",
                fraction(args.changed_lines_coverage, "--changed-lines-coverage"),
                limits["changed"],
            )
        if args.mutation_score is not None:
            score = fraction(args.mutation_score, "--mutation-score")
            if score < limits["mutation_fail"]:
                failed = True
                lines.append(f"FAIL mutation score {score} is below {limits['mutation_fail']}")
            elif score < limits["mutation_min"]:
                lines.append(f"OK with warn: mutation score {score} is below {limits['mutation_min']}")
            else:
                lines.append(f"OK mutation score {score} (minimum {limits['mutation_min']})")
        if args.hypothesis_examples is not None:
            if args.profile not in PROFILES:
                raise UsageError("--hypothesis-examples needs --profile ci or release")
            try:
                n = int(args.hypothesis_examples)
            except ValueError:
                raise UsageError(f"--hypothesis-examples: {args.hypothesis_examples!r} is not an integer") from None
            minimum = limits["examples"][args.profile]
            if n < minimum:
                failed = True
                lines.append(f"FAIL {n} Hypothesis examples per test is below {minimum} for the {args.profile} profile")
            else:
                lines.append(f"OK {n} Hypothesis examples per test (minimum {minimum})")
    except UsageError as err:
        print(str(err), file=sys.stderr)
        return 2
    print("\n".join(lines) if lines else "nothing to check")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

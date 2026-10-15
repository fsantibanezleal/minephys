# Approval ledger

`tools/check_tdd.py` reads the "Waivers" table below. A listed commit is accepted for exactly the listed rule (1 to 4
of the docstring of `tools/check_tdd.py`) and for no other; an unlisted commit gets no waiver. The ledger exists for
the few commits that are already pushed and cannot carry a `Test-Change-Approved:` trailer: pushed history is never
rewritten. A new commit that changes a locked test carries the trailer instead and needs no entry here.

## Waivers

| Commit | Rule | Decision | Note |
|---|---|---|---|
| 89af289 | 1 | owner 2026-10-12 (all listed test-change requests approved, most robust variant) | T-007-002 [green] adds the test-only oracle dependency (networkx, dev group) and has no earlier [red] commit: a dependency-only task with no runtime change |
| 524835d | 1 | owner 2026-10-12 (all listed test-change requests approved, most robust variant) | T-008-002 [green] adds the test-only reference validator dependency (jsonschema, dev group) and has no earlier [red] commit: a dependency-only task with no runtime change |
| b79ef46 | 4 | owner 2026-10-12 (all listed test-change requests approved, most robust variant) | The ledger commit itself: the fixture text of its unit test for rule 4 spelled the marker literally in a string; spelled in two parts since the next commit |

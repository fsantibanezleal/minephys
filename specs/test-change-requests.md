# Test change requests

When a locked test looks wrong, do not edit it. Add an entry here and stop that task. A locked test changes only with
a spec change and a commit carrying a `Test-Change-Approved: <reason>` trailer.

| Date | Task | Locked test | Why it looks wrong (evidence) | Decision |
|---|---|---|---|---|
| 2026-10-11 | T-003-040 | tests/metamorphic/test_t_003_040_radar_los_mr.py::test_linearity | Hypothesis finds a=0, b=5e-324: the left side is 5e-324 and the right side rounds to 0.0, while the absolute tolerance 1e-14*(abs(a)+abs(b)) underflows to 0.0, so no tolerance remains. Any IEEE-754 implementation of the line-of-sight projection fails this case; the defect is in the tolerance, not in the function. Proposed fix: add a floor such as abs=1e-300 to the tolerance. | Open: accepted as a known failure of one generated case until the test is changed with a Test-Change-Approved commit. |

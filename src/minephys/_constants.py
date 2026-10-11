"""Constants that must exist at import time without reading a knowledge table (spec 000 FR-000-06).

`STANDARD_GRAVITY` is the exact defined value of the knowledge row `standard_gravity` (NIST SP 811, Appendix B.8),
written as an exact ratio of integers so that no floating-point literal and no file read is needed in a signature
default; a unit test keeps it equal to the row.
"""

from __future__ import annotations

STANDARD_GRAVITY: float = 980665 / 100000

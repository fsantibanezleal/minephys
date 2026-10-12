"""Pyodide smoke subset (spec 000 FR-000-25): import every public subpackage and check one worked value of each.

Runs inside Pyodide (see run_smoke.mjs) and also under CPython. Each module prints `SMOKE OK <module>`; the runner
prints the final `SMOKE OK`. Values are the worked examples of specs 001 to 004 (section 7.4) as printed there.
"""

import math
import warnings

warnings.simplefilter("ignore")

import minephys.blasting as blasting
import minephys.bulk as bulk
import minephys.geotech as geotech
import minephys.haulage as haulage
import minephys.knowledge as knowledge
import minephys.units as units

charge = 850.0 * math.pi / 4.0 * 0.25**2 * 7.2
powder = charge / (6.0 * 7.0 * 12.0)

# minephys.haulage, spec 001 section 7.4
assert abs(float(haulage.rimpull_limited_speed(1.8e6, 400000.0, 0.12)) - 3.8239358) <= 5e-8
print("SMOKE OK haulage")

# minephys.blasting, spec 002 section 7.4
assert abs(float(blasting.kuznetsov_x50(7.0, powder, charge, 100.0)) - 0.2994063) <= 5e-8
print("SMOKE OK blasting")

# minephys.geotech, spec 003 section 7.4
assert abs(float(geotech.hoek_brown_parameters(50.0, 10.0, 0.0)[0]) - 1.676772) <= 5e-7
print("SMOKE OK geotech")

# minephys.bulk, spec 004 section 7.4
assert abs(float(bulk.beverloo_discharge(0.3, 0.02, 1600.0, 0.56, 1.5)) - 106.28641) <= 5e-6
print("SMOKE OK bulk")

# minephys.knowledge and minephys.units load their tables lazily
assert "bulk" in knowledge.list_tables()
assert units.__all__
print("SMOKE OK knowledge")

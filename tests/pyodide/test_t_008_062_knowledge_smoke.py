"""T-008-062 (NFR-008-03, FR-000-25): knowledge smoke subset for the Pyodide job.

Marked `pyodide`: the CI Pyodide job runs these tests inside Pyodide from the installed wheel (the loader reads the package data through
`importlib.resources`, so it works from a wheel); they are excluded from the CPython wheel run by `-m "not gpu and not pyodide and not kit"`
(FR-000-24) and also run unchanged on CPython (`pytest -m pyodide`). One published value per kind of use:
- constants of the foundation `units` table (spec 000, section A7; NIST SP 811 Appendix B.8, NIST Handbook 44 (2026) Appendix C): the
  standard acceleration of free fall 9.80665 m/s^2, the inch 0.0254 m, the foot 0.3048 m, the avoirdupois pound 0.45359237 kg, the US
  gallon 231 cubic inches and the kilowatt hour 3.6e6 J are exact by definition, and verified rows raise no warning;
- the loader: `validate_tables()` reports no error, `list_parameters()` is not empty and holds the `units` rows, `export()` is JSON
  serialisable and its summary counts agree with `list_parameters()`, `equations()` and `glossary()` return tuples, and `render_pages`
  writes pages (UTF-8) into a folder.
The model-specific rows are exercised by the smoke tests of the module specs.
"""

from __future__ import annotations

import importlib
import json
import warnings
from pathlib import Path

import pytest

pytestmark = [pytest.mark.pyodide, pytest.mark.req("NFR-008-03")]


def _k():
    return importlib.import_module("minephys.knowledge")


@pytest.mark.oracle("published", "NIST SP 811 Appendix B.8 and NIST Handbook 44 (2026) Appendix C exact values")
def test_nfr_008_03_unit_constants_are_the_published_exact_values() -> None:
    k = _k()
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # verified rows must not warn
        assert k.get_value("standard_gravity") == 9.80665
        assert k.get_value("inch") == 0.0254
        assert k.get_value("foot") == 0.3048
        assert k.get_value("pound") == 0.45359237
        assert k.get_value("us_gallon_cubic_inches") == 231.0
        assert k.get_value("kilowatt_hour") == 3.6e6


@pytest.mark.oracle("hand-calculation", "the packaged knowledge validates and is listed")
def test_nfr_008_03_the_packaged_knowledge_validates_and_is_listed() -> None:
    k = _k()
    report = k.validate_tables()
    assert list(report.errors) == []
    rows = k.list_parameters()
    assert len(rows) == report.rows >= 6
    assert {"standard_gravity", "inch", "foot", "pound", "us_gallon_cubic_inches", "kilowatt_hour"} <= {
        r.id for r in rows
    }
    assert sum(r.verification == "UNVERIFIED" for r in rows) == report.unverified


@pytest.mark.oracle("hand-calculation", "export serialises and its counts agree with the listing")
def test_nfr_008_03_export_is_serialisable_and_consistent() -> None:
    k = _k()
    exported = k.export()
    text = k.export_json()
    assert json.loads(text) == json.loads(json.dumps(exported))
    assert exported["summary"]["rows"]["total"] == len(k.list_parameters())
    assert isinstance(k.equations(), tuple) and isinstance(k.glossary(), tuple)


@pytest.mark.oracle("hand-calculation", "render_pages writes UTF-8 pages")
def test_nfr_008_03_render_pages_writes_pages(tmp_path: Path) -> None:
    k = _k()
    k.render_pages(tmp_path)
    pages = sorted(tmp_path.glob("*.md"))
    assert {"bibliography.md", "equations.md", "glossary.md"} <= {p.name for p in pages}
    for p in pages:
        assert p.read_bytes().decode("utf-8").strip()

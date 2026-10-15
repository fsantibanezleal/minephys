"""Test-support helpers for the knowledge specification (spec 008): fixture knowledge trees and subprocess runners.

Nothing here is a model or an oracle. It writes hand-made knowledge files (valid documents and one-field mutations of them), and it
runs the code under test in a fresh interpreter in which `importlib.resources.files` is redirected to a fixture tree, so that the
loader of `minephys.knowledge` (which must read the package data through `importlib.resources`, FR-008-01) serves the fixture
knowledge instead of the packaged one. The fixture tree has the layout of a package root:

    <base>/knowledge/*.yaml                      tables
    <base>/knowledge/share-alike/*.yaml          share-alike tables
    <base>/knowledge/references.bib              bibliography
    <base>/knowledge/catalogue/equations.yaml    equations catalogue (optional)
    <base>/knowledge/catalogue/glossary.yaml     glossary (optional)

`validate_tables(path)` and `knowledge_changes(old, new)` take the knowledge folder itself (`<base>/knowledge`).
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

GOOD_BIB = """\
% a comment line between entries is allowed

@article{doe2020,
  author = {Doe, Jane and Munoz, Maria},
  title = {A Sourced Model of Comminution Energy},
  journal = {Journal of Tests},
  year = {2020},
  doi = {10.1000/xyz123},
  access = {open}
}

@techreport{agency2025,
  organization = {Example Agency},
  title = {Emission factors},
  year = 2025,
  url = {https://example.org/factors.pdf},
  access = {regulation}
}

@book{sharealike2019,
  author = {Roe, Richard},
  title = {A share-alike handbook},
  publisher = {Open Press},
  year = {2019},
  url = {https://example.org/handbook},
  access = {open},
  licence = {CC-BY-SA-4.0}
}

@misc{epa2025ghghub,
  organization = {US EPA},
  title = "GHG Emission Factors Hub",
  year = {2025},
  url = {https://www.epa.gov/climateleadership/ghg-emission-factors-hub},
  access = {regulation}
}
"""


def row(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "diesel_co2_factor",
        "quantity": "diesel fuel combustion CO2 emission factor",
        "value": 10.21,
        "units": "kg CO2 / US gal",
        "role": "model_constant",
        "citation": "epa2025ghghub",
        "page": "Table 2, p. 2",
        "verification": "verified",
        "verified_on": "2026-10-06",
        "symbol": "minephys.haulage.co2_from_diesel",
        "notes": "combustion CO2 only",
    }
    base.update(over)
    return {k: v for k, v in base.items() if v is not _DROP}


_DROP = object()
DROP = _DROP  # `row(notes=DROP)` removes a field


def good_tables() -> dict[str, dict[str, Any]]:
    haulage = {
        "schema_version": 1,
        "table": "haulage",
        "title": "Haulage constants and parameters",
        "licence": "CC-BY-4.0",
        "rows": [
            row(),
            row(
                id="rolling_resistance_default",
                quantity="typical rolling resistance of a haul road",
                value="19/30",
                units="1",
                role="parameter",
                citation="doe2020",
                page="p. 4",
                verification="UNVERIFIED",
                verified_on=DROP,
                symbol=["minephys.haulage.rolling_resistance", "minephys.haulage.cycle_time"],
                notes=DROP,
            ),
            row(
                id="max_grade",
                quantity="maximum ramp grade",
                value=DROP,
                range={"min": 0.0, "max": 0.15},
                units="1",
                role="limit",
                citation="agency2025",
                page="section 3",
                verification="UNVERIFIED",
                verified_on=DROP,
                symbol="minephys.haulage.ramp_speed",
                notes=DROP,
            ),
        ],
    }
    blasting = {
        "schema_version": 1,
        "table": "blasting",
        "title": "Blasting constants",
        "licence": "CC-BY-4.0",
        "rows": [
            row(
                id="inch",
                quantity="inch",
                value=0.0254,
                units="m",
                role="conversion",
                citation="agency2025",
                page="Appendix B.8",
                symbol="minephys.blasting.hole_diameter",
                notes=DROP,
            ),
            row(
                id="powder_factor_typical",
                quantity="typical powder factor of a hard-rock bench",
                value=0.35,
                units="kg/m3",
                role="parameter",
                citation="doe2020",
                page="p. 12",
                verification="UNVERIFIED",
                verified_on=DROP,
                symbol="minephys.blasting.powder_factor",
                notes=DROP,
            ),
        ],
    }
    return {"haulage": _clean(haulage), "blasting": _clean(blasting)}


def good_share_alike() -> dict[str, dict[str, Any]]:
    return {
        "geotech_sa": _clean(
            {
                "schema_version": 1,
                "table": "geotech_sa",
                "title": "Share-alike geotechnical values",
                "licence": "CC-BY-SA-4.0",
                "rows": [
                    row(
                        id="sa_cohesion_default",
                        quantity="cohesion of the shared sample",
                        value=25.0,
                        units="kPa",
                        role="parameter",
                        citation="sharealike2019",
                        page="Table 3",
                        verification="UNVERIFIED",
                        verified_on=DROP,
                        symbol="minephys.geotech.mohr_coulomb",
                        notes=DROP,
                    )
                ],
            }
        )
    }


def good_equations() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "title": "Equations catalogue",
        "licence": "CC-BY-4.0",
        "equations": [
            {
                "id": "co2_from_diesel",
                "title": "CO2 from diesel combustion",
                "domain": "haulage",
                "latex": "m = f V",
                "symbols": [
                    {"symbol": "m", "meaning": "mass of CO2", "units": "kg"},
                    {"symbol": "f", "meaning": "emission factor", "units": "kg CO2 / US gal"},
                    {"symbol": "V", "meaning": "fuel volume", "units": "US gal"},
                ],
                "function": "minephys.haulage.co2_from_diesel",
                "citation": "epa2025ghghub",
                "page": "Table 2, p. 2",
                "verification": "verified",
                "verified_on": "2026-10-06",
                "rows": ["diesel_co2_factor"],
            },
            {
                "id": "powder_factor",
                "title": "Powder factor",
                "domain": "blasting",
                "latex": "q = W / V",
                "symbols": [{"symbol": "q", "meaning": "powder factor", "units": "kg/m3"}],
                "function": "minephys.blasting.powder_factor",
                "citation": "doe2020",
                "page": "p. 12",
                "verification": "UNVERIFIED",
            },
        ],
    }


def good_glossary() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "title": "Glossary",
        "licence": "CC-BY-4.0",
        "terms": [
            {
                "id": "powder_factor_term",
                "domain": "blasting",
                "term_en": "powder factor",
                "term_es": "factor de carga",
                "definition_en": "Explosive mass per unit volume of rock.",
                "definition_es": "Masa de explosivo por unidad de volumen de roca.",
                "citation": "doe2020",
                "see_also": ["bench"],
            },
            {
                "id": "bench",
                "domain": "general",
                "term_en": "bench",
                "term_es": "banco",
                "definition_en": "A horizontal level of an open pit.",
                "definition_es": "Nivel horizontal de un rajo abierto, con acentos: ángulo, aceleración, tamaño.",
            },
            {
                "id": "haul_truck",
                "domain": "haulage",
                "term_en": "haul truck",
                "term_es": "camión de extracción",
                "definition_en": "A large off-highway truck.",
                "definition_es": "Un camión fuera de carretera de gran tamaño.",
            },
        ],
    }


def _clean(table: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(table)
    out["rows"] = [{k: v for k, v in r.items() if v is not _DROP} for r in out["rows"]]
    return out


def dump(doc: Any) -> str:
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, default_flow_style=False)


def write_tree(
    root: Path,
    *,
    tables: dict[str, Any] | None = None,
    share_alike: dict[str, Any] | None = None,
    bib: str | None = GOOD_BIB,
    equations: Any = "default",
    glossary: Any = "default",
) -> Path:
    """Write a knowledge folder at `root` (documents or raw strings); returns `root`."""
    tables = good_tables() if tables is None else tables
    share_alike = {} if share_alike is None else share_alike
    root.mkdir(parents=True, exist_ok=True)
    for name, doc in tables.items():
        (root / f"{name}.yaml").write_text(doc if isinstance(doc, str) else dump(doc), encoding="utf-8", newline="\n")
    if share_alike:
        (root / "share-alike").mkdir(exist_ok=True)
        for name, doc in share_alike.items():
            (root / "share-alike" / f"{name}.yaml").write_text(
                doc if isinstance(doc, str) else dump(doc), encoding="utf-8", newline="\n"
            )
    if bib is not None:
        (root / "references.bib").write_text(bib, encoding="utf-8", newline="\n")
    for name, doc, default in (("equations", equations, good_equations), ("glossary", glossary, good_glossary)):
        if doc is None:
            continue
        (root / "catalogue").mkdir(exist_ok=True)
        content = default() if isinstance(doc, str) and doc == "default" else doc
        (root / "catalogue" / f"{name}.yaml").write_text(
            content if isinstance(content, str) else dump(content), encoding="utf-8", newline="\n"
        )
    return root


def write_package_tree(base: Path, **kw: Any) -> Path:
    """Write the fixture below `<base>/knowledge`, the layout `importlib.resources.files("minephys")` is redirected to."""
    write_tree(base / "knowledge", **kw)
    return base


PRELUDE = """
import importlib.resources as _R
import json, os, pathlib, sys, warnings

_BASE = pathlib.Path(os.environ["MINEPHYS_FIXTURE_BASE"])
_orig_files = _R.files


def _files(package, *args, **kwargs):
    name = package if isinstance(package, str) else getattr(package, "__name__", "")
    if name == "minephys":
        return _BASE
    if name.startswith("minephys.knowledge"):
        sub = name[len("minephys.knowledge"):].strip(".").replace(".", "/")
        return _BASE / "knowledge" / sub if sub else _BASE / "knowledge"
    return _orig_files(package, *args, **kwargs)


_R.files = _files
import minephys.knowledge as K


def _err(e):
    return {"type": type(e).__name__, "msg": str(e), "file": str(getattr(e, "file", "")), "index": getattr(e, "index", None),
            "field": getattr(e, "field", None), "argument": getattr(e, "argument", None),
            "is_value_error": isinstance(e, ValueError), "is_type_error": isinstance(e, TypeError)}
"""


def run_script(
    base: Path, script: str, *, env: dict[str, str] | None = None, timeout: int = 180, args: list[str] | None = None
) -> subprocess.CompletedProcess[str]:
    import os

    full_env = dict(os.environ)
    full_env["MINEPHYS_FIXTURE_BASE"] = str(base)
    full_env["PYTHONDONTWRITEBYTECODE"] = "1"
    full_env["PYTHONUTF8"] = "1"  # the child writes UTF-8 whatever the console code page is
    full_env["PYTHONIOENCODING"] = "utf-8"
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, "-c", PRELUDE + "\n" + script, *(args or [])],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
        env=full_env,
        timeout=timeout,
    )


def run_api(base: Path, script: str, **kw: Any) -> Any:
    """Run `script` (which must `print(json.dumps(...))` as its last output line) against the fixture tree; return the parsed JSON."""
    proc = run_script(base, script, **kw)
    assert proc.returncode == 0, f"fixture interpreter failed ({proc.returncode}):\n{proc.stderr[-2500:]}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def run_cli(
    args: list[str], base: Path | None = None, *, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run `python -m minephys.knowledge <args>`; with `base` the packaged knowledge is replaced by the fixture tree."""
    import os

    if base is None:
        full_env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        if env:
            full_env.update(env)
        return subprocess.run(
            [sys.executable, "-m", "minephys.knowledge", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=ROOT,
            env=full_env,
            timeout=180,
        )
    script = "import runpy, sys\nsys.argv = ['minephys.knowledge'] + sys.argv[1:]\nrunpy.run_module('minephys.knowledge', run_name='__main__')\n"
    return run_script(base, script, env=env, args=args)

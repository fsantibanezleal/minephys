"""T-008-040 (P-008-04): counting conservation of the export summary and of the UNVERIFIED labels.

Public API under test (`minephys.knowledge`): `export()` and `render_pages(out_dir)` served a generated fixture package tree
(tests/_knowledge_fixtures.py) in a fresh interpreter.

P-008-04: the export summary equals the number of rows per status, table and role, and the number of "UNVERIFIED" labels in the
rendered pages equals the number of UNVERIFIED rows plus UNVERIFIED equations. The labels are counted in the item part of each page
(from the first item id onward), so that the counts a page may print at its head do not take part; the layout is otherwise free.
Trees: 1 to 3 tables of 1 to 8 rows with random role and status, an
equations catalogue of 1 to 5 entries with random status and a glossary; the expected counts are counted from the generated documents.
15 examples (one interpreter each).
Oracle: counting the generated documents.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import _knowledge_fixtures as fx
import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

SEEDS = st.integers(0, 2**32 - 1)
ROLES = ["model_constant", "parameter", "limit", "conversion"]

SCRIPT = """
import pathlib, tempfile
out = pathlib.Path(tempfile.mkdtemp(prefix="mpk-pages-", dir=os.environ["MINEPHYS_TMP"]))
K.render_pages(out)
pages = {p.name: p.read_text(encoding="utf-8") for p in sorted(out.iterdir())}
print(json.dumps({"summary": K.export()["summary"], "pages": pages}))
"""


def _tree(seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    tables: dict[str, Any] = {}
    for t in range(int(rng.integers(1, 4))):
        name = f"tab_{t}"
        rows = []
        for i in range(int(rng.integers(1, 9))):
            unverified = bool(rng.random() < 0.5)
            rows.append(
                fx.row(
                    id=f"row_{t}_{i}",
                    quantity=f"quantity number {i}",
                    value=float(rng.normal()),
                    units="m",
                    role=str(rng.choice(ROLES)),
                    citation=str(rng.choice(["doe2020", "agency2025", "epa2025ghghub"])),
                    page=f"p. {i + 1}",
                    verification="UNVERIFIED" if unverified else "verified",
                    verified_on=fx.DROP if unverified else "2026-10-06",
                    symbol="minephys.haulage.f",
                    notes=fx.DROP,
                )
            )
        tables[name] = {"schema_version": 1, "table": name, "title": f"Table {t}", "licence": "CC-BY-4.0", "rows": rows}
    equations = fx.good_equations()
    equations["equations"] = []
    for i in range(int(rng.integers(1, 6))):
        unverified = bool(rng.random() < 0.5)
        e = {
            "id": f"eq_{i}",
            "title": f"Equation {i}",
            "domain": "haulage",
            "latex": "y = a x",
            "symbols": [{"symbol": "y", "meaning": "result", "units": "m"}],
            "function": "minephys.haulage.f",
            "citation": "doe2020",
            "page": "p. 1",
            "verification": "UNVERIFIED" if unverified else "verified",
        }
        if not unverified:
            e["verified_on"] = "2026-10-06"
        equations["equations"].append(e)
    return {"tables": tables, "equations": equations}


def _labels(page: str, ids: list[str]) -> int:
    """Number of UNVERIFIED labels in the item part of a page (the text from the first item id onward)."""
    return page[min(page.index(i) for i in ids) :].count("UNVERIFIED")


@pytest.mark.req("P-008-04")
@pytest.mark.oracle("analytical", "counting the generated rows and equations by status, table and role")
@settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(seed=SEEDS)
def test_p_008_04_summary_and_labels_conserve_the_counts(seed: int) -> None:
    tree = _tree(seed)
    with tempfile.TemporaryDirectory(prefix="mpk-") as tmp:
        base = fx.write_package_tree(
            Path(tmp) / "pkg", tables=tree["tables"], equations=tree["equations"], glossary=None
        )
        got = fx.run_api(base, SCRIPT, env={"MINEPHYS_TMP": tmp})
    rows = [r for t in tree["tables"].values() for r in t["rows"]]
    unv_rows = sum(r["verification"] == "UNVERIFIED" for r in rows)
    eqs = tree["equations"]["equations"]
    unv_eqs = sum(e["verification"] == "UNVERIFIED" for e in eqs)
    summary = got["summary"]
    assert summary["rows"] == {"total": len(rows), "unverified": unv_rows}
    assert summary["equations"] == {"total": len(eqs), "unverified": unv_eqs}
    for name, t in tree["tables"].items():
        assert summary["per_table"][name] == {
            "total": len(t["rows"]),
            "unverified": sum(r["verification"] == "UNVERIFIED" for r in t["rows"]),
        }
    for role in ROLES:
        sel = [r for r in rows if r["role"] == role]
        assert summary["per_role"][role] == {
            "total": len(sel),
            "unverified": sum(r["verification"] == "UNVERIFIED" for r in sel),
        }
    # per page: a table page carries exactly one label per UNVERIFIED row, the equations page one per UNVERIFIED equation
    labels = 0
    for name, t in tree["tables"].items():
        n = _labels(got["pages"][f"{name}.md"], [r["id"] for r in t["rows"]])
        assert n == sum(r["verification"] == "UNVERIFIED" for r in t["rows"]), name
        labels += n
    n_eq = _labels(got["pages"]["equations.md"], [e["id"] for e in eqs])
    assert n_eq == unv_eqs
    assert labels + n_eq == unv_rows + unv_eqs, (
        f"{labels + n_eq} labels for {unv_rows} UNVERIFIED rows and {unv_eqs} UNVERIFIED equations"
    )

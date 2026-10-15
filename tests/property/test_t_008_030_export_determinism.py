"""T-008-030 (P-008-03): determinism and order invariance of the export and the rendered pages.

Public API under test (`minephys.knowledge`): `export_json()` and `render_pages(out_dir)` served a fixture package tree
(tests/_knowledge_fixtures.py) in a fresh interpreter.

P-008-03: `export_json()` and `render_pages` are byte-identical across repeated calls, across fresh interpreters with different
`PYTHONHASHSEED`, and across any permutation of the rows inside a table, of the entries of `references.bib` and of the entries of the
catalogues. Generated trees: the fixture knowledge plus up to 12 extra rows (finite floats, rational strings, ranges, both statuses)
in the haulage table; the second tree holds the same documents in a seeded random order. 15 examples (two interpreters each).
Oracle: byte equality of two renderings of the same knowledge in different orders (an invariant, no expected values).
"""

from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any

import _knowledge_fixtures as fx
import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

SEEDS = st.integers(0, 2**32 - 1)

SCRIPT = """
import pathlib, tempfile
out = pathlib.Path(tempfile.mkdtemp(prefix="mpk-pages-", dir=os.environ["MINEPHYS_TMP"]))
K.render_pages(out)
pages = {p.name: p.read_bytes().decode("utf-8") for p in sorted(out.iterdir())}
print(json.dumps({"json": K.export_json(), "pages": pages}))
"""


def _extra_rows(rng: np.random.Generator, n: int) -> list[dict[str, Any]]:
    rows = []
    for i in range(n):
        kind = int(rng.integers(0, 3))
        r = fx.row(
            id=f"gen_{i}",
            quantity=f"generated quantity {i}",
            units=str(rng.choice(["m", "kg/m3", "1", "kPa"])),
            role=str(rng.choice(["model_constant", "parameter", "limit", "conversion"])),
            citation=str(rng.choice(["doe2020", "agency2025", "epa2025ghghub"])),
            page=f"p. {int(rng.integers(1, 99))}",
            symbol="minephys.haulage.gen",
            notes=fx.DROP,
        )
        if rng.random() < 0.5:
            r["verification"] = "UNVERIFIED"
            r.pop("verified_on", None)
        if kind == 0:
            r["value"] = float(rng.normal() * 10 ** int(rng.integers(-300, 300)))
        elif kind == 1:
            r["value"] = f"{int(rng.integers(-99, 99))}/{int(rng.integers(1, 99))}"
        else:
            r.pop("value")
            a = float(rng.normal())
            r["range"] = {"min": a, "max": a + abs(float(rng.normal()))}
        rows.append(r)
    return rows


def _trees(seed: int, extra: int) -> tuple[dict[str, Any], dict[str, Any]]:
    rng = np.random.default_rng(seed)
    tables = fx.good_tables()
    tables["haulage"]["rows"].extend(_extra_rows(rng, extra))
    eq, gl = fx.good_equations(), fx.good_glossary()
    chunks = [
        "@" + c.strip() for c in fx.GOOD_BIB.split("\n@")[1:]
    ]  # the four entries (the leading comment line is dropped)
    base = {"tables": tables, "equations": eq, "glossary": gl, "bib": fx.GOOD_BIB, "share_alike": fx.good_share_alike()}
    shuffled = copy.deepcopy(base)
    for t in shuffled["tables"].values():
        t["rows"] = [t["rows"][i] for i in rng.permutation(len(t["rows"]))]
    shuffled["equations"]["equations"] = [shuffled["equations"]["equations"][i] for i in rng.permutation(2)]
    shuffled["glossary"]["terms"] = [shuffled["glossary"]["terms"][i] for i in rng.permutation(3)]
    order = rng.permutation(len(chunks))
    shuffled["bib"] = "% reordered\n\n" + "\n\n".join(chunks[i] for i in order) + "\n"
    return base, shuffled


def _render(tmp: Path, name: str, tree: dict[str, Any], hash_seed: str) -> dict[str, Any]:
    base = fx.write_package_tree(
        tmp / name,
        tables=tree["tables"],
        share_alike=tree["share_alike"],
        bib=tree["bib"],
        equations=tree["equations"],
        glossary=tree["glossary"],
    )
    return fx.run_api(base, SCRIPT, env={"PYTHONHASHSEED": hash_seed, "MINEPHYS_TMP": str(tmp)})


@pytest.mark.req("P-008-03")
@pytest.mark.oracle("analytical", "invariance under permutation of rows, bibliography entries and catalogue entries")
@settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(seed=SEEDS, extra=st.integers(0, 12), hash_a=st.integers(0, 4000), hash_b=st.integers(0, 4000))
def test_p_008_03_export_and_pages_do_not_depend_on_order_or_hash_seed(
    seed: int, extra: int, hash_a: int, hash_b: int
) -> None:
    base, shuffled = _trees(seed, extra)
    with tempfile.TemporaryDirectory(prefix="mpk-") as tmp:
        a = _render(Path(tmp), "a", base, str(hash_a))
        b = _render(Path(tmp), "b", shuffled, str(hash_b))
    assert a["json"] == b["json"]
    assert a["pages"] == b["pages"]
    assert set(a["pages"]) >= {
        "haulage.md",
        "blasting.md",
        "geotech_sa.md",
        "equations.md",
        "bibliography.md",
        "glossary.md",
    }


@pytest.mark.req("P-008-03")
@pytest.mark.oracle("analytical", "the same tree rendered twice in one interpreter gives the same bytes")
def test_p_008_03_repeated_calls_are_byte_identical(tmp_path: Path) -> None:
    base = fx.write_package_tree(tmp_path / "pkg", share_alike=fx.good_share_alike())
    got = fx.run_api(
        base,
        """
import pathlib, tempfile
runs = []
for _ in range(2):
    out = pathlib.Path(tempfile.mkdtemp(prefix="mpk-pages-", dir=os.environ["MINEPHYS_TMP"]))
    K.render_pages(out)
    runs.append({p.name: p.read_bytes().decode("utf-8") for p in sorted(out.iterdir())})
print(json.dumps({"pages_equal": runs[0] == runs[1], "json_equal": K.export_json() == K.export_json()}))
""",
        env={"MINEPHYS_TMP": str(tmp_path)},
    )
    assert got == {"pages_equal": True, "json_equal": True}

"""T-000-032 (SC-000-03, SC-000-04): the release evidence report (honesty and portability summary).

Expected CLI, `tools/release_evidence.py`:

    python tools/release_evidence.py [--root PATH] --matrix FILE [--json]

`--root` is a repository-like tree (default: this repository, layout of `tools/check_knowledge.py`); `--matrix` is a
JSON file written by the CI matrix: `{"smoke": {"<runtime>": "pass" | "fail" | "not_run", ...}}`.
The report (stdout JSON with `--json`) is

    {"honesty": {"unverified_parameter_defaults": [{"function": str, "row": str}, ...],
                 "verified_rows": int, "verified_rows_pinned": int, "pinned_pct": float, "unpinned": [row ids]},
     "portability": {"required": ["3.12", "3.13", "3.14", "wheel", "pyodide"],
                     "passed": [...], "failed": [...], "missing": [...]},
     "ok": bool}

SC-000-03: `unverified_parameter_defaults` lists every UNVERIFIED `parameter` row named under `Knowledge rows` in the
docstring of an exported function (it must be empty) and `pinned_pct` is 100 * pinned / verified (100.0 when there is no
verified row; every verified row must be pinned by an `@pytest.mark.knowledge("<row id>")` test).
SC-000-04: every required runtime must be `pass` in the matrix; `fail` goes to `failed`, `not_run` or absent to
`missing`; `kit` is optional (never required, never reported as missing). Exit status 0 iff `ok`, 1 otherwise, 2 for
usage errors (unreadable or malformed matrix, unknown status, non-mapping `smoke`) with the path named, no traceback.

Oracle: hand-written fixture trees and matrices (plan 000: SC-000-03 and SC-000-04 rows of the test strategy).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _mini_repo import GOOD_BIB, REPO_ROOT, row, run_tool, table, write_repo

REQUIRED = ["3.12", "3.13", "3.14", "wheel", "pyodide"]
ALL_PASS = {"smoke": dict.fromkeys(REQUIRED, "pass")}

DEMO_INIT = '__all__ = ["f"]\nfrom ._f import f\n'
DEMO_F = '''def f(x):
    """Demo.

    Parameters
    ----------
    x : float [m]

    Returns
    -------
    float [m]

    Knowledge rows
    --------------
    {rows}
    """
    return x
'''


def tree(tmp: Path, *, listed: str = "model_const", pinned: tuple[str, ...] = ("v1", "v2", "v3")) -> Path:
    rows = [
        row("v1", verification="verified", role="parameter"),
        row("v2", verification="verified", role="model_constant"),
        row("v3", verification="verified", role="limit"),
        row("model_const", verification="UNVERIFIED", role="model_constant"),
        row("raw_param", verification="UNVERIFIED", role="parameter"),
    ]
    marks = "import pytest\n\n" + "".join(
        f'@pytest.mark.knowledge("{r}")\ndef test_{r}():\n    pass\n\n' for r in pinned
    )
    root = write_repo(
        tmp,
        tables={"demo": table("demo", rows)},
        bib=GOOD_BIB,
        src_files={"demo/__init__.py": DEMO_INIT, "demo/_f.py": DEMO_F.format(rows=listed)},
        test_files={"unit/test_pins.py": marks},
    )
    return root


def matrix(tmp: Path, doc: object) -> Path:
    p = tmp / "matrix.json"
    p.write_text(doc if isinstance(doc, str) else json.dumps(doc), encoding="utf-8")
    return p


def report(root: Path, mx: Path):
    assert (REPO_ROOT / "tools" / "release_evidence.py").is_file(), "missing tools/release_evidence.py"
    return run_tool("release_evidence.py", "--root", str(root), "--matrix", str(mx), "--json")


@pytest.mark.req("SC-000-03")
@pytest.mark.req("SC-000-04")
@pytest.mark.oracle("hand-calculation", "an honest tree with every runtime green: ok, 100 % pinned, no defaults")
def test_clean_tree_and_green_matrix(tmp_path: Path) -> None:
    proc = report(tree(tmp_path / "t"), matrix(tmp_path, ALL_PASS))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert data["honesty"]["unverified_parameter_defaults"] == []
    assert data["honesty"]["verified_rows"] == 3
    assert data["honesty"]["verified_rows_pinned"] == 3
    assert data["honesty"]["pinned_pct"] == pytest.approx(100.0)
    assert data["honesty"]["unpinned"] == []
    assert data["portability"]["required"] == REQUIRED
    assert data["portability"]["passed"] == REQUIRED
    assert data["portability"]["failed"] == []
    assert data["portability"]["missing"] == []


@pytest.mark.req("SC-000-03")
@pytest.mark.oracle("hand-calculation", "one UNVERIFIED parameter row used as a default fails, naming function and row")
def test_unverified_parameter_default_fails(tmp_path: Path) -> None:
    proc = report(tree(tmp_path / "t", listed="model_const, raw_param"), matrix(tmp_path, ALL_PASS))
    assert proc.returncode == 1
    data = json.loads(proc.stdout)
    assert data["ok"] is False
    assert data["honesty"]["unverified_parameter_defaults"] == [{"function": "f", "row": "raw_param"}]


@pytest.mark.req("SC-000-03")
@pytest.mark.oracle(
    "hand-calculation", "2 pinned of 3 verified rows is 66.67 %: the unpinned row is named and the gate fails"
)
def test_pinned_percentage(tmp_path: Path) -> None:
    proc = report(tree(tmp_path / "t", pinned=("v1", "v3")), matrix(tmp_path, ALL_PASS))
    assert proc.returncode == 1
    h = json.loads(proc.stdout)["honesty"]
    assert h["verified_rows"] == 3
    assert h["verified_rows_pinned"] == 2
    assert h["pinned_pct"] == pytest.approx(200.0 / 3.0, rel=1e-9)
    assert h["unpinned"] == ["v2"]


@pytest.mark.req("SC-000-03")
@pytest.mark.oracle("hand-calculation", "UNVERIFIED rows and a table with no verified row are not penalised")
def test_no_verified_rows_means_100_percent(tmp_path: Path) -> None:
    root = write_repo(
        tmp_path / "t",
        tables={"demo": table("demo", [row("only", verification="UNVERIFIED")])},
        bib=GOOD_BIB,
        src_files={"demo/__init__.py": DEMO_INIT, "demo/_f.py": DEMO_F.format(rows="none")},
    )
    data = json.loads(report(root, matrix(tmp_path, ALL_PASS)).stdout)
    assert data["honesty"]["verified_rows"] == 0
    assert data["honesty"]["pinned_pct"] == pytest.approx(100.0)
    assert data["ok"] is True


@pytest.mark.req("SC-000-04")
@pytest.mark.oracle("hand-calculation", "failed, not_run and absent runtimes are reported; kit is optional")
@pytest.mark.parametrize(
    ("smoke", "failed", "missing", "ok"),
    [
        ({**ALL_PASS["smoke"], "pyodide": "fail"}, ["pyodide"], [], False),
        ({**ALL_PASS["smoke"], "pyodide": "not_run"}, [], ["pyodide"], False),
        ({k: v for k, v in ALL_PASS["smoke"].items() if k != "wheel"}, [], ["wheel"], False),
        ({**ALL_PASS["smoke"], "3.12": "fail", "3.14": "not_run"}, ["3.12"], ["3.14"], False),
        ({**ALL_PASS["smoke"], "kit": "not_run"}, [], [], True),
        ({**ALL_PASS["smoke"], "kit": "fail"}, [], [], True),
        ({**ALL_PASS["smoke"], "3.15": "fail"}, [], [], True),
    ],
)
def test_portability_matrix(tmp_path: Path, smoke: dict, failed: list, missing: list, ok: bool) -> None:
    proc = report(tree(tmp_path / "t"), matrix(tmp_path, {"smoke": smoke}))
    assert proc.returncode == (0 if ok else 1), proc.stdout + proc.stderr
    p = json.loads(proc.stdout)["portability"]
    assert p["failed"] == failed
    assert p["missing"] == missing
    assert p["passed"] == [r for r in REQUIRED if smoke.get(r) == "pass"]


@pytest.mark.req("SC-000-04")
@pytest.mark.oracle("hand-calculation", "hostile matrices are usage errors naming the file")
@pytest.mark.parametrize(
    "document",
    [
        "{not json",
        "",
        "[]",
        '{"smoke": "all green"}',
        '{"smoke": {"3.12": "green"}}',
        '{"smoke": {"3.12": 1}}',
        '{"results": {}}',
    ],
)
def test_hostile_matrix(tmp_path: Path, document: str) -> None:
    mx = matrix(tmp_path, document)
    proc = report(tree(tmp_path / "t"), mx)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "matrix.json" in proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr


@pytest.mark.req("SC-000-04")
@pytest.mark.oracle("hand-calculation", "a missing matrix file is a usage error")
def test_missing_matrix_file(tmp_path: Path) -> None:
    proc = report(tree(tmp_path / "t"), tmp_path / "absent.json")
    assert proc.returncode == 2
    assert "absent.json" in proc.stdout + proc.stderr

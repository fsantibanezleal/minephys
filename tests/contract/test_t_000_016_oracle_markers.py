"""T-000-016 (FR-000-33, SC-000-02): the oracle-marker inventory and report, `tools/oracle_inventory.py`.

Expected CLI:

    python tools/oracle_inventory.py [--root PATH] [--json] [--strict] [--release]

It scans `<root>/tests/**/*.py` with the AST (a test is a function named `test_*`, at module level or in a class;
a parametrised test counts once) and prints, with `--json`, one JSON object:

    {"tests": int,
     "kinds": {"analytical": n, "worked-example": n, "reference-implementation": n, "hand-calculation": n},
     "unmarked": ["tests/unit/test_x.py::test_y", ...],      # a `req` marker but no `oracle` marker
     "violations": [{"test": "tests/unit/test_x.py::test_y", "message": "..."}, ...],
     "functions": {"f": {"tests": n, "non_hand_calculation": m}, ...},   # exported model functions, see below
     "uncovered": ["g", ...]}                                  # no test with a non-hand-calculation oracle

Rules (FR-000-33): `@pytest.mark.oracle(kind, reference)` takes two string literals; `kind` is one of analytical,
worked-example, reference-implementation, hand-calculation; `reference` is non-empty; for a worked example it is
`<BibTeX key> <page locator>` (for example `doe2020 p. 12`, `agency2025 Table 2`) and the key exists in
`<root>/src/minephys/knowledge/references.bib`. A marker with a non-literal argument cannot be audited and is a
violation. Violations make the exit status 1; `unmarked` tests do so only with `--strict`.
The `message` of a violation contains: the offending kind (for example `magic`, `Analytical`); the word `reference`
when it is missing or blank; `worked-example` when a worked-example reference has no `<key> <locator>` form; `page`
when only a key is given; the unknown key (for example `nobody1999`); `literal` for a non-literal argument;
`argument` for a wrong number of arguments; `positional` when keyword arguments are used.
SC-000-02: `functions` has one entry per name in the `__all__` of every subpackage `src/minephys/<sub>/__init__.py`
that is a function name referenced (as a Name or an attribute) by a test; a name with no referencing test appears with
zero counts; `uncovered` lists, sorted, the names whose `non_hand_calculation` is 0 and that the optional file
`<root>/specs/000-foundation/oracle-exceptions.yaml` (mapping name -> non-empty reason) does not document; with
`--release` a non-empty `uncovered` makes the exit status 1.

Oracle: hand-written fixture test trees, one defect per case (hand calculation).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _mini_repo import GOOD_BIB, REPO_ROOT, run_tool, write_repo

DEMO_INIT = '__all__ = ["f", "g", "h"]\nfrom ._m import f, g, h\n'
DEMO_M = "def f(x):\n    return x\n\n\ndef g(x):\n    return x\n\n\ndef h(x):\n    return x\n"


def mk_tests(*blocks: str) -> str:
    return "import pytest\nfrom minephys.demo import f, g, h\n\n" + "\n\n".join(blocks) + "\n"


def case(decorators: list[str], name: str = "test_a", body: str = "    assert f(1) == 1") -> str:
    return "\n".join(decorators) + f"\ndef {name}():\n{body}"


REQ = '@pytest.mark.req("FR-000-05")'


def build(tmp: Path, files: dict[str, str], *, exceptions: str | None = None) -> Path:
    root = write_repo(
        tmp,
        bib=GOOD_BIB,
        src_files={"demo/__init__.py": DEMO_INIT, "demo/_m.py": DEMO_M},
        test_files=files,
    )
    if exceptions is not None:
        d = root / "specs" / "000-foundation"
        d.mkdir(parents=True, exist_ok=True)
        (d / "oracle-exceptions.yaml").write_text(exceptions, encoding="utf-8")
    return root


def report(root: Path, *flags: str) -> tuple[int, dict]:
    proc = run_tool("oracle_inventory.py", "--root", str(root), "--json", *flags)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise AssertionError(f"no JSON on stdout:\n{proc.stdout}\n{proc.stderr}") from None
    return proc.returncode, data


@pytest.mark.req("FR-000-33")
@pytest.mark.oracle("hand-calculation", "a fixture with one valid marker of each kind is clean and counted")
def test_inventory_counts_each_kind(tmp_path: Path) -> None:
    files = {
        "unit/test_a.py": mk_tests(
            case([REQ, '@pytest.mark.oracle("analytical", "closed form")'], "test_one"),
            case([REQ, '@pytest.mark.oracle("worked-example", "doe2020 p. 12")'], "test_two"),
            case([REQ, '@pytest.mark.oracle("reference-implementation", "numpy.linalg.solve")'], "test_three"),
            case([REQ, '@pytest.mark.oracle("hand-calculation", "by hand")'], "test_four"),
            case([REQ, '@pytest.mark.oracle("hand-calculation", "by hand again")'], "test_five"),
        )
    }
    code, data = report(build(tmp_path, files))
    assert code == 0, data
    assert data["tests"] == 5
    assert data["kinds"] == {
        "analytical": 1,
        "worked-example": 1,
        "reference-implementation": 1,
        "hand-calculation": 2,
    }
    assert data["violations"] == []
    assert data["unmarked"] == []


@pytest.mark.req("FR-000-33")
@pytest.mark.oracle("hand-calculation", "each marker defect is a violation naming the test")
@pytest.mark.parametrize(
    ("marker", "needle"),
    [
        ('@pytest.mark.oracle("magic", "x")', "magic"),
        ('@pytest.mark.oracle("analytical")', "reference"),
        ('@pytest.mark.oracle("analytical", "")', "reference"),
        ('@pytest.mark.oracle("analytical", "   ")', "reference"),
        ('@pytest.mark.oracle("worked-example", "Fredlund and Krahn")', "worked-example"),
        ('@pytest.mark.oracle("worked-example", "doe2020")', "page"),
        ('@pytest.mark.oracle("worked-example", "nobody1999 p. 3")', "nobody1999"),
        ('@pytest.mark.oracle("Analytical", "x")', "Analytical"),
        ("@pytest.mark.oracle(KIND, 'x')", "literal"),
        ('@pytest.mark.oracle("analytical", "x", "extra")', "argument"),
        ('@pytest.mark.oracle(kind="analytical", reference="x")', "positional"),
    ],
)
def test_marker_defects_are_violations(tmp_path: Path, marker: str, needle: str) -> None:
    files = {"unit/test_a.py": mk_tests(case([REQ, marker], "test_bad"))}
    code, data = report(build(tmp_path, files))
    assert code == 1
    msgs = [v for v in data["violations"] if "test_a.py::test_bad" in v["test"]]
    assert msgs, data
    assert any(needle.lower() in v["message"].lower() for v in msgs), msgs


@pytest.mark.req("FR-000-33")
@pytest.mark.oracle("hand-calculation", "markers on test methods of a class and stacked markers are found")
def test_class_methods_and_stacked_markers(tmp_path: Path) -> None:
    text = (
        "import pytest\n\n\nclass TestK:\n"
        '    @pytest.mark.req("FR-000-05")\n    @pytest.mark.req("FR-000-06")\n'
        '    @pytest.mark.oracle("analytical", "closed form")\n'
        "    def test_m(self):\n        assert True\n"
    )
    code, data = report(build(tmp_path, {"unit/test_k.py": text}))
    assert code == 0
    assert data["tests"] == 1
    assert data["kinds"]["analytical"] == 1


@pytest.mark.req("FR-000-33")
@pytest.mark.oracle("hand-calculation", "a parametrised test counts once, however many cases it has")
def test_parametrised_test_counts_once(tmp_path: Path) -> None:
    text = mk_tests(
        case(
            [REQ, '@pytest.mark.oracle("analytical", "closed form")', '@pytest.mark.parametrize("x", [1, 2, 3, 4])'],
            "test_p",
            "    assert f(1) == 1",
        )
    )
    _, data = report(build(tmp_path, {"unit/test_p.py": text}))
    assert data["tests"] == 1


@pytest.mark.req("FR-000-33")
@pytest.mark.oracle("hand-calculation", "a test with a req marker and no oracle is unmarked; --strict makes it fatal")
def test_unmarked_tests_and_strict(tmp_path: Path) -> None:
    files = {"unit/test_u.py": mk_tests(case([REQ], "test_no_oracle"))}
    root = build(tmp_path, files)
    code, data = report(root)
    assert code == 0
    assert data["unmarked"] == ["tests/unit/test_u.py::test_no_oracle"]
    code_strict, _ = report(root, "--strict")
    assert code_strict == 1


@pytest.mark.req("FR-000-33")
@pytest.mark.oracle("hand-calculation", "a test without a req marker is not part of the requirement inventory")
def test_helper_tests_without_req_are_not_unmarked(tmp_path: Path) -> None:
    files = {"unit/test_h.py": mk_tests(case([], "test_helper"))}
    code, data = report(build(tmp_path, files), "--strict")
    assert code == 0
    assert data["unmarked"] == []


@pytest.mark.req("FR-000-33")
@pytest.mark.oracle("hand-calculation", "hostile: a syntactically broken test file is reported, not a crash")
def test_unparsable_test_file(tmp_path: Path) -> None:
    root = build(tmp_path, {"unit/test_ok.py": mk_tests(case([REQ, '@pytest.mark.oracle("analytical", "x")']))})
    (root / "tests" / "unit" / "test_broken.py").write_text("def test_x(:\n", encoding="utf-8")
    proc = run_tool("oracle_inventory.py", "--root", str(root), "--json")
    assert proc.returncode == 1
    assert "test_broken.py" in proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr


@pytest.mark.req("SC-000-02")
@pytest.mark.oracle("hand-calculation", "f has an analytical oracle, g only a hand calculation, h no test")
def test_function_coverage_report(tmp_path: Path) -> None:
    files = {
        "unit/test_f.py": mk_tests(
            case([REQ, '@pytest.mark.oracle("analytical", "closed form")'], "test_f", "    assert f(1) == 1"),
            case([REQ, '@pytest.mark.oracle("hand-calculation", "by hand")'], "test_g", "    assert g(2) == 2"),
            case(
                [REQ, '@pytest.mark.oracle("hand-calculation", "by hand")'],
                "test_also_f",
                "    import minephys.demo as d\n    assert d.f(3) == 3",
            ),
        )
    }
    code, data = report(build(tmp_path, files))
    assert code == 0
    assert data["functions"]["f"] == {"tests": 2, "non_hand_calculation": 1}
    assert data["functions"]["g"] == {"tests": 1, "non_hand_calculation": 0}
    assert data["functions"]["h"] == {"tests": 0, "non_hand_calculation": 0}
    assert data["uncovered"] == ["g", "h"]


@pytest.mark.req("SC-000-02")
@pytest.mark.oracle("hand-calculation", "--release fails on uncovered functions unless a reason is documented")
def test_release_mode_and_documented_exceptions(tmp_path: Path) -> None:
    files = {
        "unit/test_f.py": mk_tests(
            case([REQ, '@pytest.mark.oracle("analytical", "closed form")'], "test_f", "    assert f(1) == 1")
        )
    }
    root = build(tmp_path / "a", files)
    code, data = report(root, "--release")
    assert code == 1
    assert data["uncovered"] == ["g", "h"]
    documented = build(
        tmp_path / "b", files, exceptions="g: no published worked example exists\nh: closed form only, see docs\n"
    )
    code, data = report(documented, "--release")
    assert code == 0, data
    assert data["uncovered"] == []
    blank_reason = build(tmp_path / "c", files, exceptions='g: ""\nh: closed form only\n')
    code, data = report(blank_reason, "--release")
    assert code == 1
    assert data["uncovered"] == ["g"]


@pytest.mark.req("FR-000-33")
@pytest.mark.req("SC-000-02")
@pytest.mark.oracle("hand-calculation", "this repository's own tests carry valid oracle markers (no violations)")
def test_the_real_test_tree_has_no_marker_violations() -> None:
    proc = run_tool("oracle_inventory.py", "--json")
    data = json.loads(proc.stdout)
    assert proc.returncode == 0, data["violations"]
    assert data["violations"] == []
    assert data["tests"] > 0
    assert sum(data["kinds"].values()) > 0
    assert REPO_ROOT.is_dir()

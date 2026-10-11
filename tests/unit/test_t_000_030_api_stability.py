"""T-000-030 (FR-000-28, FR-000-29, DC-000-04): API snapshot writer and checker, and the deprecation helper.

Expected `tools/check_api.py`:

    python tools/check_api.py --write [--out FILE]
        writes the public API (`__all__` of `minephys` and of every public subpackage, and `minephys.units`) as the
        JSON document of DC-000-04: `{"version": <VERSION file>, "objects": [...]}`, objects sorted by `name`, unique,
        `kind` in function|class|constant|module, functions carry `parameters` `[{name, kind, default, unit}]` in
        signature order (`default` is the `repr` or null; `unit` is the bracketed unit of the docstring WITHOUT the
        brackets, or null), and `deprecated` is null or `{since, removal, replacement}` read from the object's
        `__minephys_deprecated__` attribute. The default output is `docs/reference/api-snapshot.json`; the bytes are
        deterministic.
    python tools/check_api.py --previous PREV.json --current CUR.json [--changelog CHANGELOG.md]
        compares two snapshots. Exit 1, one line per problem naming the object (and parameter), when the current
        snapshot REMOVES or RENAMES an object or a parameter, CHANGES a default or a documented unit, unless BOTH
        (a) the major version X of `current` is greater than that of `previous` and (b) the changelog has a bullet
        under a `### Deprecated` heading naming the dotted object (and, for a parameter, its name). Additions never
        fail. Exit 0 and `OK` otherwise. A missing file or unreadable JSON exits 2 naming the file.

Expected `minephys._deprecate`:

    deprecated(*, since, removal, replacement) -> decorator
        wraps a function: each call emits ONE `DeprecationWarning` per call site (stacklevel so that the warning is
        attributed to the caller) whose message names the replacement and the removal version; the wrapper keeps
        `__name__`, `__doc__`, `__wrapped__` and sets `__minephys_deprecated__ = {"since", "removal", "replacement"}`.
        `since` and `removal` must be `X.YY.ZZZ` strings and `removal` later than `since`, else `InputError`.
    warn_deprecated_parameter(function, parameter, *, since, removal, replacement) -> None
        the same warning for a deprecated parameter or default of `function`.

Oracle: hand-written snapshot fixtures and changelogs (plan 000: "hand-written fixture snapshots").
"""

from __future__ import annotations

import importlib
import inspect
import json
import warnings
from pathlib import Path

import pytest
from _mini_repo import REPO_ROOT, run_tool

import minephys


def api(*args: str):
    assert (REPO_ROOT / "tools" / "check_api.py").is_file(), "missing tools/check_api.py"
    return run_tool("check_api.py", *args)


def param(name: str, default: str | None = None, unit: str | None = "m", kind: str = "positional_or_keyword") -> dict:
    return {"name": name, "kind": kind, "default": default, "unit": unit}


def obj(
    name: str, kind: str = "function", parameters: list[dict] | None = None, deprecated: dict | None = None
) -> dict:
    out = {"name": name, "kind": kind, "deprecated": deprecated}
    if kind == "function":
        out["parameters"] = parameters if parameters is not None else [param("x"), param("y", "1.0", "1")]
    return out


def snapshot(version: str, *objects: dict) -> dict:
    return {"version": version, "objects": sorted(objects, key=lambda o: o["name"])}


BASE = (
    obj("minephys.InputError", "class"),
    obj("minephys.__version__", "constant"),
    obj("minephys.haulage", "module"),
    obj("minephys.haulage.f"),
    obj("minephys.haulage.g", parameters=[param("a", None, "kg")]),
)


def write(tmp: Path, name: str, doc: dict) -> Path:
    p = tmp / name
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return p


CHANGELOG_DEPRECATION = (
    "# Changelog\n\n## [Unreleased]\n### Deprecated\n"
    "- `minephys.haulage.g` is deprecated since 1.01.000 and removed in 2.00.000; use `minephys.haulage.f`.\n"
    "- `minephys.haulage.f`: parameter `y` is deprecated since 1.01.000, removed in 2.00.000; use `z`.\n"
    "- `minephys.haulage.f`: the default of `y` changes in 2.00.000.\n"
)


def compare(tmp: Path, previous: dict, current: dict, changelog: str | None = None):
    args = ["--previous", str(write(tmp, "prev.json", previous)), "--current", str(write(tmp, "cur.json", current))]
    if changelog is not None:
        (tmp / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
        args += ["--changelog", str(tmp / "CHANGELOG.md")]
    return api(*args)


# ------------------------------------------------------------------ the checker


@pytest.mark.req("FR-000-28")
@pytest.mark.req("DC-000-04")
@pytest.mark.oracle("hand-calculation", "identical snapshots and pure additions are fine")
def test_identical_and_additive_changes_pass(tmp_path: Path) -> None:
    prev = snapshot("1.01.000", *BASE)
    assert compare(tmp_path, prev, prev).returncode == 0
    extra = obj("minephys.haulage.h", parameters=[param("q")])
    grown = [obj("minephys.haulage.f", parameters=[param("x"), param("y", "1.0", "1"), param("z", "0.0", "1")])]
    cur = snapshot("1.02.000", *BASE[:3], *grown, BASE[4], extra)
    proc = compare(tmp_path, prev, cur)
    assert proc.returncode == 0, proc.stdout
    assert "OK" in proc.stdout


@pytest.mark.req("FR-000-28")
@pytest.mark.oracle("hand-calculation", "each breaking change fails, naming the object")
@pytest.mark.parametrize(
    ("label", "needle"),
    [
        ("removed_object", "minephys.haulage.g"),
        ("renamed_object", "minephys.haulage.g"),
        ("removed_parameter", "y"),
        ("renamed_parameter", "y"),
        ("changed_default", "y"),
        ("changed_unit", "x"),
    ],
)
def test_breaking_changes_fail(tmp_path: Path, label: str, needle: str) -> None:
    prev = snapshot("1.01.000", *BASE)
    objs = {o["name"]: o for o in BASE}
    if label == "removed_object":
        del objs["minephys.haulage.g"]
    elif label == "renamed_object":
        gone = objs.pop("minephys.haulage.g")
        objs["minephys.haulage.g2"] = {**gone, "name": "minephys.haulage.g2"}
    elif label == "removed_parameter":
        objs["minephys.haulage.f"] = obj("minephys.haulage.f", parameters=[param("x")])
    elif label == "renamed_parameter":
        objs["minephys.haulage.f"] = obj("minephys.haulage.f", parameters=[param("x"), param("z", "1.0", "1")])
    elif label == "changed_default":
        objs["minephys.haulage.f"] = obj("minephys.haulage.f", parameters=[param("x"), param("y", "2.0", "1")])
    elif label == "changed_unit":
        objs["minephys.haulage.f"] = obj(
            "minephys.haulage.f", parameters=[param("x", None, "mm"), param("y", "1.0", "1")]
        )
    cur = snapshot("1.02.000", *objs.values())
    proc = compare(tmp_path, prev, cur)
    assert proc.returncode == 1, proc.stdout
    assert any(needle in line for line in proc.stdout.splitlines()), proc.stdout


@pytest.mark.req("FR-000-28")
@pytest.mark.oracle("hand-calculation", "a break needs BOTH an X bump and an earlier deprecation entry")
def test_breaking_change_needs_both_a_major_bump_and_a_changelog_entry(tmp_path: Path) -> None:
    prev = snapshot("1.01.000", *BASE)
    cur_objs = [o for o in BASE if o["name"] != "minephys.haulage.g"]
    minor = snapshot("1.02.000", *cur_objs)
    major = snapshot("2.00.000", *cur_objs)
    for sub in "abcd":
        (tmp_path / sub).mkdir()
    no_changelog = compare(tmp_path / "a", prev, major, None)
    assert no_changelog.returncode == 1, "a major bump alone does not justify the removal"
    unrelated = compare(tmp_path / "b", prev, major, "# Changelog\n\n## [Unreleased]\n### Added\n- stuff\n")
    assert unrelated.returncode == 1
    assert compare(tmp_path / "c", prev, minor, CHANGELOG_DEPRECATION).returncode == 1, "no X bump"
    ok = compare(tmp_path / "d", prev, major, CHANGELOG_DEPRECATION)
    assert ok.returncode == 0, ok.stdout


@pytest.mark.req("FR-000-28")
@pytest.mark.oracle(
    "hand-calculation", "a deprecation bullet must name the object; a bullet under another heading does not count"
)
def test_changelog_entry_must_be_a_deprecation_naming_the_object(tmp_path: Path) -> None:
    prev = snapshot("1.01.000", *BASE)
    major = snapshot("2.00.000", *[o for o in BASE if o["name"] != "minephys.haulage.g"])
    other_object = "# Changelog\n\n### Deprecated\n- `minephys.haulage.other` is deprecated.\n"
    wrong_heading = "# Changelog\n\n### Removed\n- `minephys.haulage.g` was removed.\n"
    for i, text in enumerate((other_object, wrong_heading)):
        d = tmp_path / f"x{i}"
        d.mkdir()
        assert compare(d, prev, major, text).returncode == 1, text


@pytest.mark.req("FR-000-28")
@pytest.mark.oracle(
    "hand-calculation", "parameter and default changes are justified by deprecation entries naming them"
)
def test_parameter_changes_are_justified_by_named_entries(tmp_path: Path) -> None:
    prev = snapshot("1.01.000", *BASE)
    changed = obj("minephys.haulage.f", parameters=[param("x"), param("y", "2.0", "1")])
    cur = snapshot("2.00.000", *[o for o in BASE if o["name"] != "minephys.haulage.f"], changed)
    assert compare(tmp_path, prev, cur, CHANGELOG_DEPRECATION).returncode == 0


@pytest.mark.req("FR-000-28")
@pytest.mark.oracle("hand-calculation", "hostile: missing and unreadable snapshot files exit 2 naming the file")
def test_missing_or_unreadable_files(tmp_path: Path) -> None:
    good = write(tmp_path, "good.json", snapshot("1.01.000", *BASE))
    proc = api("--previous", str(tmp_path / "absent.json"), "--current", str(good))
    assert proc.returncode == 2
    assert "absent.json" in proc.stdout + proc.stderr
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    proc2 = api("--previous", str(good), "--current", str(bad))
    assert proc2.returncode == 2
    assert "bad.json" in proc2.stdout + proc2.stderr
    assert "Traceback" not in proc.stderr + proc2.stderr


# ------------------------------------------------------------------ the writer


@pytest.mark.req("FR-000-28")
@pytest.mark.req("DC-000-04")
@pytest.mark.oracle("hand-calculation", "the written snapshot lists the exported objects, sorted, with their kinds")
def test_write_lists_the_public_api(tmp_path: Path) -> None:
    out = tmp_path / "snap.json"
    proc = api("--write", "--out", str(out))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["version"] == (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    names = [o["name"] for o in doc["objects"]]
    assert names == sorted(names)
    assert len(names) == len(set(names))
    by = {o["name"]: o for o in doc["objects"]}
    for cls in ("InputError", "InputTypeError", "ValidityWarning", "ConvergenceError"):
        assert by[f"minephys.{cls}"]["kind"] == "class"
    assert by["minephys.__version__"]["kind"] == "constant"
    f = by["minephys.units.deg_to_rad"]
    assert f["kind"] == "function"
    assert [p["name"] for p in f["parameters"]] == list(
        inspect.signature(importlib.import_module("minephys.units").deg_to_rad).parameters
    )
    for o in doc["objects"]:
        assert "deprecated" in o
        if o["kind"] == "function":
            for p in o["parameters"]:
                assert set(p) == {"name", "kind", "default", "unit"}
                assert p["unit"] is None or (isinstance(p["unit"], str) and not p["unit"].startswith("["))


@pytest.mark.req("FR-000-28")
@pytest.mark.req("DC-000-04")
@pytest.mark.oracle("reference-implementation", "jsonschema validation of the written snapshot against contracts/")
def test_written_snapshot_conforms_to_the_schema(tmp_path: Path) -> None:
    out = tmp_path / "snap.json"
    assert api("--write", "--out", str(out)).returncode == 0
    from jsonschema import Draft202012Validator

    schema = json.loads((REPO_ROOT / "contracts" / "api-snapshot.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(json.loads(out.read_text(encoding="utf-8"))))
    assert errors == []


@pytest.mark.req("FR-000-28")
@pytest.mark.oracle(
    "hand-calculation", "determinism: two writes are byte-identical; a written snapshot compares clean to itself"
)
def test_write_is_deterministic_and_self_consistent(tmp_path: Path) -> None:
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    assert api("--write", "--out", str(a)).returncode == 0
    assert api("--write", "--out", str(b)).returncode == 0
    assert a.read_bytes() == b.read_bytes()
    assert api("--previous", str(a), "--current", str(b)).returncode == 0


# ------------------------------------------------------------------ the deprecation helper


def deprecate():
    return importlib.import_module("minephys._deprecate")


def make_old_name():
    @deprecate().deprecated(since="0.02.000", removal="1.00.000", replacement="minephys.haulage.new_name")
    def old_name(x: float) -> float:
        """Old function.

        Parameters
        ----------
        x : float [m]
        """
        return x * 2.0

    return old_name


@pytest.mark.req("FR-000-29")
@pytest.mark.oracle("hand-calculation", "FR-000-29: the call returns its result and warns once per call site")
def test_deprecated_function_warns_once_per_call_site() -> None:
    old_name = make_old_name()
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("default")
        for _ in range(3):
            assert old_name(2.0) == 4.0  # one call site, three calls
    dep = [w for w in rec if issubclass(w.category, DeprecationWarning)]
    assert len(dep) == 1
    msg = str(dep[0].message)
    assert "minephys.haulage.new_name" in msg
    assert "1.00.000" in msg
    assert dep[0].filename == __file__, "the warning is attributed to the caller"


@pytest.mark.req("FR-000-29")
@pytest.mark.oracle("hand-calculation", "two different call sites are two warnings")
def test_two_call_sites_give_two_warnings() -> None:
    old_name = make_old_name()
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("default")
        old_name(1.0)
        old_name(1.0)
    dep = [w for w in rec if issubclass(w.category, DeprecationWarning)]
    assert len(dep) == 2
    assert dep[0].lineno != dep[1].lineno


@pytest.mark.req("FR-000-29")
@pytest.mark.oracle("hand-calculation", "the wrapper keeps the function's identity and records the deprecation")
def test_wrapper_metadata() -> None:
    old_name = make_old_name()
    assert old_name.__name__ == "old_name"
    assert "Old function." in (old_name.__doc__ or "")
    assert list(inspect.signature(old_name).parameters) == ["x"]
    assert old_name.__minephys_deprecated__ == {
        "since": "0.02.000",
        "removal": "1.00.000",
        "replacement": "minephys.haulage.new_name",
    }
    assert hasattr(old_name, "__wrapped__")


@pytest.mark.req("FR-000-29")
@pytest.mark.oracle("hand-calculation", "a deprecated parameter warns the same way, naming the replacement and removal")
def test_deprecated_parameter_helper() -> None:
    def f(old=None, new=None):
        if old is not None:
            deprecate().warn_deprecated_parameter(
                "minephys.haulage.f", "old", since="0.02.000", removal="1.00.000", replacement="new"
            )
        return new if old is None else old

    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("default")
        assert f(old=3) == 3
    dep = [w for w in rec if issubclass(w.category, DeprecationWarning)]
    assert len(dep) == 1
    msg = str(dep[0].message)
    for token in ("minephys.haulage.f", "old", "new", "1.00.000"):
        assert token in msg
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert f(new=5) == 5  # not using the parameter: silent


@pytest.mark.req("FR-000-29")
@pytest.mark.oracle("hand-calculation", "hostile: malformed versions or removal not later than since are input errors")
@pytest.mark.parametrize(
    ("since", "removal"),
    [
        ("0.2.0", "1.00.000"),
        ("v0.02.000", "1.00.000"),
        ("0.02.000", "1.0"),
        ("", "1.00.000"),
        ("0.02.000", "0.02.000"),
        ("0.03.000", "0.02.999"),
        ("1.00.000", "0.99.000"),
    ],
)
def test_decorator_validates_its_versions(since: str, removal: str) -> None:
    with pytest.raises(minephys.InputError):
        deprecate().deprecated(since=since, removal=removal, replacement="minephys.x.y")(lambda x: x)

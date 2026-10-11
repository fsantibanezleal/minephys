"""T-000-002 (FR-000-27, FR-000-32): exceptions, warnings, `__version__` and the registered markers.

Expected API (module `minephys._errors`, re-exported by `minephys`):
    InputError(message, *, argument)                     subclass of ValueError, attribute `argument: str`
    InputTypeError(message, *, argument)                 subclass of TypeError, attribute `argument: str`
    ValidityWarning(message, *, argument, bounds, row)   subclass of UserWarning; `argument: str`,
                                                         `bounds: tuple[float, float]`, `row: str`
    ConvergenceError(message, *, last_iterate, residual, iterations)
                                                         subclass of RuntimeError; `argument is None`
and `minephys.__version__` (str, equal to the stripped content of the `VERSION` file) with the package metadata
version equal to its normalised form (`X.Y.Z`, integer segments). `minephys.__all__` lists the four classes,
`__version__` and every public (non-underscore) subpackage directory of `src/minephys/`.
pyproject.toml registers the markers req, oracle, knowledge, gpu, slow, pyodide and kit.

Oracle: hand calculation (the class hierarchy and attributes stated in spec 000 FR-000-32 and data-model section 4;
the version rule in FR-000-27).
"""

from __future__ import annotations

import importlib.metadata
import re
import tomllib
from pathlib import Path

import pytest

import minephys

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.req("FR-000-32")
@pytest.mark.oracle("hand-calculation", "spec 000 FR-000-32: class hierarchy")
@pytest.mark.parametrize(
    ("name", "base"),
    [
        ("InputError", ValueError),
        ("InputTypeError", TypeError),
        ("ValidityWarning", UserWarning),
        ("ConvergenceError", RuntimeError),
    ],
)
def test_exported_classes_subclass_their_stated_base(name: str, base: type) -> None:
    cls = getattr(minephys, name)
    assert isinstance(cls, type)
    assert issubclass(cls, base)
    assert name in minephys.__all__


@pytest.mark.req("FR-000-32")
@pytest.mark.oracle("hand-calculation", "data-model.md section 4: attributes of the exceptions and the warning")
def test_attributes_are_carried() -> None:
    e = minephys.InputError("f(): argument 'x' must be finite", argument="x")
    assert e.argument == "x"
    assert isinstance(e, ValueError)
    assert "x" in str(e)
    t = minephys.InputTypeError("f(): argument 'y' must be real", argument="y")
    assert t.argument == "y"
    assert isinstance(t, TypeError)
    w = minephys.ValidityWarning("outside", argument="rock_mass", bounds=(0.0, 100.0), row="tripwire")
    assert w.argument == "rock_mass"
    assert w.bounds == (0.0, 100.0)
    assert w.row == "tripwire"
    c = minephys.ConvergenceError("no convergence", last_iterate=1.5, residual=0.25, iterations=40)
    assert c.argument is None
    assert (c.last_iterate, c.residual, c.iterations) == (1.5, 0.25, 40)


@pytest.mark.req("FR-000-32")
@pytest.mark.oracle("hand-calculation", "a caller must be able to catch the family by its builtin base")
def test_builtin_base_classes_catch_the_library_errors() -> None:
    with pytest.raises(ValueError, match="bad"):
        raise minephys.InputError("bad", argument="a")
    with pytest.raises(TypeError, match="worse"):
        raise minephys.InputTypeError("worse", argument="b")
    with pytest.raises(RuntimeError, match="stuck"):
        raise minephys.ConvergenceError("stuck", last_iterate=0.0, residual=1.0, iterations=1)
    # the two input errors are not interchangeable
    assert not issubclass(minephys.InputError, TypeError)
    assert not issubclass(minephys.InputTypeError, ValueError)


@pytest.mark.req("FR-000-32")
@pytest.mark.oracle("hand-calculation", "spec 000 FR-000-32: __all__ lists classes, __version__ and the subpackages")
def test_all_lists_classes_version_and_every_public_subpackage() -> None:
    expected = {"InputError", "InputTypeError", "ValidityWarning", "ConvergenceError", "__version__"}
    pkg_dir = ROOT / "src" / "minephys"
    subpackages = {
        p.name for p in pkg_dir.iterdir() if p.is_dir() and (p / "__init__.py").is_file() and not p.name.startswith("_")
    }
    assert expected | subpackages <= set(minephys.__all__)
    assert len(minephys.__all__) == len(set(minephys.__all__)), "duplicate names in __all__"


@pytest.mark.req("FR-000-27")
@pytest.mark.oracle("hand-calculation", "spec 000 FR-000-27: __version__ equals the VERSION file")
def test_version_equals_the_version_file() -> None:
    text = (ROOT / "VERSION").read_text(encoding="utf-8")
    assert minephys.__version__ == text.strip()
    assert re.fullmatch(r"\d+\.\d{2}\.\d{3}", minephys.__version__)


@pytest.mark.req("FR-000-27")
@pytest.mark.oracle("hand-calculation", "PEP 440 normalisation drops the zero padding: 0.01.002 -> 0.1.2")
def test_version_normalises_to_the_distribution_metadata_version() -> None:
    x, y, z = (int(p) for p in minephys.__version__.split("."))
    normalised = f"{x}.{y}.{z}"
    assert importlib.metadata.version("minephys") == normalised
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == normalised


@pytest.mark.req("FR-000-27")
@pytest.mark.oracle("hand-calculation", "hostile: a padded version must be a str, never a float or tuple")
def test_version_is_a_plain_string() -> None:
    assert type(minephys.__version__) is str


@pytest.mark.req("FR-000-32")
@pytest.mark.oracle("hand-calculation", "T-000-002: the markers are registered in pyproject.toml")
@pytest.mark.parametrize("marker", ["req", "oracle", "knowledge", "gpu", "slow", "pyodide", "kit"])
def test_pyproject_registers_the_marker(marker: str) -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    markers = pyproject["tool"]["pytest"]["markers"]
    names = {m.split("(")[0].split(":")[0].strip() for m in markers}
    assert marker in names

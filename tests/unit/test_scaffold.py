"""Scaffold invariants: the package imports, ships type information, and the release version has the X.YY.ZZZ form."""

import re
from importlib.resources import files
from pathlib import Path

import minephys

ROOT = Path(__file__).resolve().parents[2]


def test_package_imports() -> None:
    assert minephys.__all__ == []


def test_ships_py_typed() -> None:
    assert files("minephys").joinpath("py.typed").is_file()


def test_version_file_format() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"\d+\.\d{2}\.\d{3}", version), version

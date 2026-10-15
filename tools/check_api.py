"""Public API snapshot writer and checker (spec 000 FR-000-28, FR-000-34, DC-000-04).

Usage:
  python tools/check_api.py --write [--out FILE]
      write the public API of `minephys` (`__all__` of the package, of every public subpackage and of
      `minephys.units`) as the JSON document of DC-000-04 (default `docs/reference/api-snapshot.json`).
  python tools/check_api.py --previous PREV.json --current CUR.json [--changelog CHANGELOG.md]
      compare two snapshots; exit 1 (one line per problem) when the current one removes or renames an object or a
      parameter, or changes a default or a documented unit, unless BOTH the major version X of `current` is greater
      than that of `previous` AND the changelog has a bullet under a `### Deprecated` heading naming the dotted object
      (and, for a parameter, its name). Additions never fail. Exit 2 for an unreadable or invalid file.
Snapshot files are read strictly (FR-000-34): a duplicate object key, a non-finite number or invalid UTF-8 exits
non-zero naming the file and the key or JSON pointer, and nothing is compared.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parents[1]
DEFAULT_OUT = Path("docs") / "reference" / "api-snapshot.json"
MAX_DEPTH = 200
NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
WS = " \t\r\n"


class StrictJsonError(ValueError):
    """A snapshot file that the strict reader refuses."""


class _Reader:
    def __init__(self, text: str) -> None:
        self.s = text
        self.i = 0

    def ws(self) -> None:
        while self.i < len(self.s) and self.s[self.i] in WS:
            self.i += 1

    def value(self, pointer: str, depth: int) -> Any:
        if depth > MAX_DEPTH:
            raise StrictJsonError(f"nesting deeper than {MAX_DEPTH} levels at {pointer or '/'}")
        self.ws()
        if self.i >= len(self.s):
            raise StrictJsonError("unexpected end of document")
        ch = self.s[self.i]
        if ch == "{":
            return self.obj(pointer, depth)
        if ch == "[":
            return self.arr(pointer, depth)
        if ch == '"':
            return self.string()
        for literal, result in (("true", True), ("false", False), ("null", None)):
            if self.s.startswith(literal, self.i):
                self.i += len(literal)
                return result
        for literal in ("NaN", "Infinity", "-Infinity"):
            if self.s.startswith(literal, self.i):
                raise StrictJsonError(f"non-finite number {literal} at {pointer or '/'}")
        m = NUMBER.match(self.s, self.i)
        if not m:
            raise StrictJsonError(f"invalid JSON at character {self.i}")
        self.i = m.end()
        number = float(m.group(0))
        if number in (float("inf"), float("-inf")):
            raise StrictJsonError(f"non-finite number {m.group(0)} at {pointer or '/'}")
        return int(m.group(0)) if re.fullmatch(r"-?[0-9]+", m.group(0)) else number

    def string(self) -> str:
        try:
            text, end = json.decoder.scanstring(self.s, self.i + 1)
        except json.JSONDecodeError as err:
            raise StrictJsonError(f"invalid string: {err.msg}") from None
        self.i = end
        return text

    def obj(self, pointer: str, depth: int) -> dict[str, Any]:
        self.i += 1
        out: dict[str, Any] = {}
        self.ws()
        if self.s[self.i : self.i + 1] == "}":
            self.i += 1
            return out
        while True:
            self.ws()
            if self.s[self.i : self.i + 1] != '"':
                raise StrictJsonError(f"expected a key at character {self.i}")
            key = self.string()
            child = f"{pointer}/{key.replace('~', '~0').replace('/', '~1')}"
            if key in out:
                raise StrictJsonError(f"duplicate key {key!r} at {child}")
            self.ws()
            if self.s[self.i : self.i + 1] != ":":
                raise StrictJsonError(f"expected ':' at character {self.i}")
            self.i += 1
            out[key] = self.value(child, depth + 1)
            self.ws()
            sep = self.s[self.i : self.i + 1]
            self.i += 1
            if sep == "}":
                return out
            if sep != ",":
                raise StrictJsonError(f"expected ',' or '}}' at character {self.i - 1}")

    def arr(self, pointer: str, depth: int) -> list[Any]:
        self.i += 1
        out: list[Any] = []
        self.ws()
        if self.s[self.i : self.i + 1] == "]":
            self.i += 1
            return out
        while True:
            out.append(self.value(f"{pointer}/{len(out)}", depth + 1))
            self.ws()
            sep = self.s[self.i : self.i + 1]
            self.i += 1
            if sep == "]":
                return out
            if sep != ",":
                raise StrictJsonError(f"expected ',' or ']' at character {self.i - 1}")


def read_strict(path: Path) -> Any:
    """Parse `path` as strict JSON; raises StrictJsonError (message without the file name) or OSError."""
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as err:
        raise StrictJsonError(f"invalid UTF-8 at byte offset {err.start}") from None
    reader = _Reader(text)
    value = reader.value("", 0)
    reader.ws()
    if reader.i != len(text):
        raise StrictJsonError(f"trailing data at character {reader.i}")
    return value


# ------------------------------------------------------------------ writer


def _unit_of(doc: str, name: str) -> str | None:
    """The bracketed unit (without brackets) of parameter `name` in the numpydoc Parameters section."""
    in_params = False
    lines = inspect.cleandoc(doc).splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "Parameters" and i + 1 < len(lines) and set(lines[i + 1].strip()) == {"-"}:
            in_params = True
            continue
        if in_params:
            if (
                i + 1 < len(lines)
                and line.strip()
                and set(lines[i + 1].strip()) == {"-"}
                and len(lines[i + 1].strip()) >= 3
            ):
                return None
            m = re.match(rf"^{re.escape(name)}\s*:\s*(.*)$", line)
            if m:
                unit = re.search(r"\[([^\[\]]+)\]", m.group(1))
                return unit.group(1).strip() if unit else None
    return None


def _describe(dotted: str, obj: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {"name": dotted}
    if inspect.ismodule(obj):
        entry["kind"] = "module"
    elif inspect.isclass(obj):
        entry["kind"] = "class"
    elif callable(obj):
        entry["kind"] = "function"
        doc = inspect.getdoc(obj) or ""
        params = [
            {
                "name": p.name,
                "kind": p.kind.name.lower(),
                "default": None if p.default is inspect.Parameter.empty else repr(p.default),
                "unit": _unit_of(doc, p.name),
            }
            for p in inspect.signature(obj).parameters.values()
        ]
        entry["parameters"] = params
    else:
        entry["kind"] = "constant"
    dep = getattr(obj, "__minephys_deprecated__", None)
    entry["deprecated"] = {k: dep[k] for k in ("since", "removal", "replacement")} if isinstance(dep, dict) else None
    return entry


def build_snapshot(root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(root / "src"))
    pkg = importlib.import_module("minephys")
    objects: dict[str, dict[str, Any]] = {}
    for name in pkg.__all__:
        obj = getattr(pkg, name)
        objects[f"minephys.{name}"] = _describe(f"minephys.{name}", obj)
        if inspect.ismodule(obj):
            for member in getattr(obj, "__all__", ()):
                objects[f"minephys.{name}.{member}"] = _describe(f"minephys.{name}.{member}", getattr(obj, member))
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    return {"version": version, "objects": [objects[k] for k in sorted(objects)]}


# ------------------------------------------------------------------ comparison


def _major(version: str) -> int:
    return int(version.split(".")[0])


def _deprecated_bullets(changelog: str) -> list[str]:
    bullets: list[str] = []
    active = False
    for line in changelog.splitlines():
        if line.startswith("#"):
            active = line.strip().lower().startswith("### deprecated")
            continue
        if active and re.match(r"^\s*[-*]\s", line):
            bullets.append(line)
    return bullets


def _named(bullets: list[str], *words: str) -> bool:
    return any(all(re.search(rf"(?<![A-Za-z0-9_.]){re.escape(w)}(?![A-Za-z0-9_])", b) for w in words) for b in bullets)


def compare(previous: dict[str, Any], current: dict[str, Any], changelog: str | None) -> list[str]:
    bumped = _major(current["version"]) > _major(previous["version"])
    bullets = _deprecated_bullets(changelog or "")
    now = {o["name"]: o for o in current["objects"]}
    problems: list[str] = []

    def justified(*words: str) -> bool:
        return bumped and _named(bullets, *words)

    for old in previous["objects"]:
        name = old["name"]
        new = now.get(name)
        if new is None:
            if not justified(name):
                problems.append(f"{name}: removed or renamed without a major version bump and a Deprecated entry")
            continue
        if old.get("kind") == "function" and new.get("kind") == "function":
            new_params = {p["name"]: p for p in new.get("parameters", [])}
            for p in old.get("parameters", []):
                q = new_params.get(p["name"])
                if q is None:
                    if not justified(name, p["name"]):
                        problems.append(f"{name}: parameter {p['name']} removed or renamed without a Deprecated entry")
                    continue
                if q["default"] != p["default"] and not justified(name, p["name"]):
                    problems.append(f"{name}: default of {p['name']} changed from {p['default']} to {q['default']}")
                if q["unit"] != p["unit"] and not justified(name, p["name"]):
                    problems.append(f"{name}: documented unit of {p['name']} changed from {p['unit']} to {q['unit']}")
    return problems


def _load(path: Path) -> dict[str, Any]:
    try:
        doc = read_strict(path)
    except OSError as err:
        raise SystemExit(f"{path}: unreadable: {err.strerror}") from None
    except StrictJsonError as err:
        raise SystemExit(f"{path}: {err}") from None
    if not (
        isinstance(doc, dict)
        and isinstance(doc.get("version"), str)
        and re.fullmatch(r"[0-9]+\.[0-9]{2}\.[0-9]{3}", doc["version"])
        and isinstance(doc.get("objects"), list)
        and all(isinstance(o, dict) and isinstance(o.get("name"), str) for o in doc["objects"])
    ):
        raise SystemExit(f"{path}: not an API snapshot (DC-000-04)")
    return doc


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--previous", type=Path)
    ap.add_argument("--current", type=Path)
    ap.add_argument("--changelog", type=Path)
    args = ap.parse_args(argv[1:])
    if args.write:
        out = args.out or HERE / DEFAULT_OUT
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes((json.dumps(build_snapshot(HERE), indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        print(f"wrote {out}")
        return 0
    if not (args.previous and args.current):
        ap.error("give --write, or --previous and --current")
    try:
        previous, current = _load(args.previous), _load(args.current)
        text = args.changelog.read_text(encoding="utf-8") if args.changelog else None
    except OSError as err:
        print(f"{args.changelog}: unreadable: {err.strerror}")
        return 2
    except SystemExit as err:
        print(err.code)
        return 2
    problems = compare(previous, current, text)
    for line in problems:
        print(line)
    if problems:
        return 1
    print("API OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

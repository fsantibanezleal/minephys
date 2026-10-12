"""NVIDIA Kit smoke import (spec 000 FR-000-26): run the portable smoke subset inside Kit's embedded Python.

Usage:  python tools/kit_smoke.py [--kit-python PATH] [--wheel PATH] [--src PATH] [--target DIR] [--no-discover]
The interpreter is --kit-python, else the environment variable MINEPHYS_KIT_PYTHON, else (unless --no-discover) the
conventional Omniverse install folders. Without a Kit interpreter the tool prints a line saying that the Kit smoke
was not run and exits 3 (never a silent pass). With one, it installs --wheel into --target (no dependencies) or puts
--src on the path, runs tests/pyodide/smoke.py and echoes its `SMOKE OK <module>` lines; exit 0 on success, 1 when an
import or assertion fails.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SMOKE = HERE / "tests" / "pyodide" / "smoke.py"
NOT_RUN = 3
# Conventional Omniverse package folders (UNVERIFIED on this machine: Kit was not installed when written).
PATTERNS = ("AppData/Local/ov/pkg/*/kit/python/python.exe", ".local/share/ov/pkg/*/kit/python/bin/python3")


def find_kit(explicit: str | None, discover: bool) -> Path | None:
    candidate = explicit or os.environ.get("MINEPHYS_KIT_PYTHON")
    if candidate:
        path = Path(candidate)
        return path if path.is_file() else None
    if discover:
        for pattern in PATTERNS:
            found = sorted(Path.home().glob(pattern))
            if found:
                return found[-1]
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit-python")
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--src", type=Path)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--no-discover", action="store_true")
    args = parser.parse_args(argv)
    kit = find_kit(args.kit_python, not args.no_discover)
    if kit is None:
        print("Kit smoke not run: no Kit Python interpreter found (set --kit-python or MINEPHYS_KIT_PYTHON)")
        return NOT_RUN
    path = args.src
    if args.wheel is not None:
        target = args.target or Path(tempfile.mkdtemp(prefix="minephys-kit-"))
        install = subprocess.run(
            [str(kit), "-m", "pip", "install", "--no-deps", "--target", str(target), str(args.wheel)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if install.returncode != 0:
            print(install.stdout + install.stderr, file=sys.stderr)
            return 1
        path = target
    prelude = "import sys; print('Kit Python', '%d.%d' % sys.version_info[:2]); "
    if path is not None:
        prelude += f"sys.path.insert(0, {str(path)!r}); "
    code = prelude + f"exec(compile(open({str(SMOKE)!r}, encoding='utf-8').read(), 'smoke.py', 'exec'))"
    run = subprocess.run([str(kit), "-c", code], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    sys.stdout.write(run.stdout)
    if run.returncode != 0:
        print(run.stderr, file=sys.stderr)
        return 1
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

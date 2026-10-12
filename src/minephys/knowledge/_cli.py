"""Command line of the knowledge base: `validate [PATH]`, `export [--out FILE]`, `render --out-dir DIR` (spec 008
FR-008-18).

Exit codes: 0 success, 1 validation errors (every error is listed), 2 usage errors (unknown subcommand or option, a
path that
is not an existing directory, an output path that is a directory or whose parent does not exist). Nothing is written
on a usage
error.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, NoReturn

__all__ = ["main"]


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="python -m minephys.knowledge", description="Validate, export and render the knowledge base.")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    validate = sub.add_parser("validate", help="validate the packaged knowledge, or the knowledge folder PATH")
    validate.add_argument("path", nargs="?", default=None)
    export = sub.add_parser("export", help="write the deterministic JSON export (standard output by default)")
    export.add_argument("--out", default=None, metavar="FILE")
    render = sub.add_parser("render", help="write the Markdown pages into an existing folder")
    render.add_argument("--out-dir", required=True, metavar="DIR")
    return parser


def _usage(message: str) -> int:
    print(f"python -m minephys.knowledge: error: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args: Any = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    from . import KnowledgeSchemaError, export_json, render_pages, validate_tables

    if args.command == "validate":
        if args.path is not None and not Path(args.path).is_dir():
            return _usage(f"{args.path!r} is not an existing directory")
        report = validate_tables(args.path)
        for error in report.errors:
            print(error)
        if report.errors:
            print(f"{len(report.errors)} error(s) in {report.rows} rows ({report.unverified} UNVERIFIED)")
            return 1
        print(
            f"ok: {report.tables} tables, {report.rows} rows ({report.unverified} UNVERIFIED), "
            f"{report.equations} equations, {report.terms} terms, {report.references} references"
        )
        return 0
    if args.command == "export":
        target = None
        if args.out is not None:
            target = Path(os.fspath(args.out))
            if target.is_dir() or not target.parent.is_dir():
                return _usage(f"cannot write {args.out!r}: it is a directory or its folder does not exist")
        try:
            text = export_json()
        except KnowledgeSchemaError as err:
            print(err, file=sys.stderr)
            return 1
        if target is None:
            sys.stdout.reconfigure(encoding="utf-8", newline="\n")  # type: ignore[union-attr]
            sys.stdout.write(text)
        else:
            target.write_bytes(text.encode("utf-8"))
        return 0
    if not Path(args.out_dir).is_dir():
        return _usage(f"{args.out_dir!r} is not an existing directory")
    try:
        render_pages(args.out_dir)
    except KnowledgeSchemaError as err:
        print(err, file=sys.stderr)
        return 1
    return 0

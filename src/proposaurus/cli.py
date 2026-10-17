"""``proposaurus`` — tools an agent uses to check what it built.

    proposaurus preview <pdf> [--out DIR] [--dpi N]
    proposaurus verify  <pdf|dir>... (--rules FILE | --require P ... --forbid P ...)
    proposaurus diff    <baseline-dir> <new-dir> [--out DIR] [--dpi N]
    proposaurus budget  <xlsx> [-o FILE]

Rendering is not here: each brand's own CLI renders, by calling the library.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import budget_reader
from .diff import compare_dirs
from .preview import preview
from .verify import DEFAULT_MIN_CHARS, Kind, check_pdf, load_rules


def _pdfs(paths: list[str]) -> list[Path]:
    """Files as given; directories searched recursively, skipping virtualenvs."""
    found: list[Path] = []
    for p in map(Path, paths):
        if p.is_dir():
            found += sorted(
                f for f in p.rglob("*.pdf") if not {".venv", "venv"} & set(f.parts)
            )
        else:
            found.append(p)
    return found


def _cmd_preview(args: argparse.Namespace) -> int:
    result = preview(
        args.pdf,
        args.out,
        dpi=args.dpi,
        first=args.first,
        last=args.last,
        sheet=not args.no_sheet,
        columns=args.columns,
    )
    if result.sheet:
        print(f"sheet  {result.sheet}")
    for p in result.pages:
        print(f"page   {p}")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    if args.rules:
        if args.require or args.forbid:
            print("Error: use --rules or --require/--forbid, not both", file=sys.stderr)
            return 2
        kinds, min_chars = load_rules(args.rules)
    else:
        kinds = [Kind("pdf", require=args.require, forbid=args.forbid)]
        min_chars = DEFAULT_MIN_CHARS
    if args.min_chars is not None:
        min_chars = args.min_chars

    pdfs = _pdfs(args.paths)
    if not pdfs:
        print("No PDFs found.")
        return 1

    failed = 0
    for pdf in pdfs:
        kind, problems = check_pdf(pdf, kinds, min_chars)
        label = kind.name if kind else "?"
        if problems:
            failed += 1
            print(f"FAIL  {pdf}  ({label})")
            for p in problems:
                print(f"        {p}")
        else:
            print(f"ok    {pdf}  ({label})")
    print(f"\n{len(pdfs) - failed}/{len(pdfs)} passed")
    return 1 if failed else 0


def _cmd_diff(args: argparse.Namespace) -> int:
    results = compare_dirs(
        args.baseline, args.new, dpi=args.dpi, max_pixels=args.max_pixels, out_dir=args.out
    )
    if not results:
        print("No PDFs in either directory.")
        return 1
    changed = 0
    for r in results:
        if r.same:
            print(f"same     {r.name}")
        else:
            changed += 1
            print(f"CHANGED  {r.name}")
            for p in r.problems:
                print(f"           {p}")
    print(f"\n{len(results) - changed}/{len(results)} identical")
    if changed and args.out:
        print(f"Changed pages (baseline | new | new, changes in red): {args.out}")
    return 1 if changed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="proposaurus",
        description="Check rendered proposal PDFs: preview, verify, diff; and read budgets.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("preview", help="Rasterise a PDF to PNGs and a contact sheet.")
    p.add_argument("pdf")
    p.add_argument(
        "--out",
        help="Directory to write <pdf name>/page-N.png and sheet.png into "
        "(default: preview/ beside the PDF).",
    )
    p.add_argument("--dpi", type=int, default=60)
    p.add_argument("--first", type=int, help="First page to render.")
    p.add_argument("--last", type=int, help="Last page to render.")
    p.add_argument("--columns", type=int, default=4, help="Contact sheet columns.")
    p.add_argument("--no-sheet", action="store_true", help="Skip the contact sheet.")
    p.set_defaults(func=_cmd_preview)

    p = sub.add_parser("verify", help="Check PDFs for required and forbidden phrases.")
    p.add_argument("paths", nargs="+", help="PDFs, or directories to search for them.")
    p.add_argument("--rules", help="TOML file of document kinds (see proposaurus.verify).")
    p.add_argument("--require", action="append", default=[], metavar="PHRASE")
    p.add_argument("--forbid", action="append", default=[], metavar="PHRASE")
    p.add_argument("--min-chars", type=int, help=f"Minimum text length (default {DEFAULT_MIN_CHARS}).")
    p.set_defaults(func=_cmd_verify)

    p = sub.add_parser("diff", help="Compare two directories of PDFs by filename.")
    p.add_argument("baseline")
    p.add_argument("new")
    p.add_argument("--out", help="Save each changed page as a side-by-side PNG here.")
    p.add_argument("--dpi", type=int, default=100)
    p.add_argument("--max-pixels", type=int, default=0, help="Changed pixels tolerated per page.")
    p.set_defaults(func=_cmd_diff)

    p = sub.add_parser("budget", help="Dump a budget Excel file to text.")
    budget_reader.add_arguments(p)
    p.set_defaults(func=budget_reader.run)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

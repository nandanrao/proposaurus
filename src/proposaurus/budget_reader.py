"""Dump a budget Excel file to plain text an agent can read.

Budget spreadsheets vary from project to project, so this does not try to
parse their structure. It walks every sheet and every non-empty cell and
prints the coordinate with its formula (and the cached value the formula last
computed) or its static value. The agent reading it writes the proposal YAML.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from openpyxl import load_workbook


def _value(v):
    return round(v, 6) if isinstance(v, float) else v


def dump_workbook_text(
    path: str | Path, show_formulas: bool = True, show_values: bool = True
) -> str:
    """Plain-text dump of every sheet in a workbook.

    Loads the file twice: once for formulas and once with ``data_only=True``
    for the values they last computed, shown as ``COORD: =FORMULA  =>  value``.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Excel file not found: {path}")

    wb_formulas = load_workbook(str(path), data_only=False)
    wb_values = load_workbook(str(path), data_only=True) if show_values else None

    parts = [f"File: {path.name}", f"Sheets: {wb_formulas.sheetnames}", ""]

    for ws in wb_formulas.worksheets:
        ws_values = (
            wb_values[ws.title]
            if wb_values and ws.title in wb_values.sheetnames
            else None
        )
        lines = [f"=== Sheet: {ws.title} ({ws.max_row} rows x {ws.max_column} cols) ===", ""]

        for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=ws.max_column):
            row_has_content = False
            for cell in row:
                if cell.value is None:
                    continue
                row_has_content = True
                coord = cell.coordinate
                if show_formulas and isinstance(cell.value, str) and cell.value.startswith("="):
                    cached = None
                    if ws_values is not None and ws_values[coord].value is not None:
                        cached = _value(ws_values[coord].value)
                    if cached is not None:
                        lines.append(f"  {coord}: {cell.value}  =>  {cached}")
                    else:
                        lines.append(f"  {coord}: {cell.value}")
                else:
                    lines.append(f"  {coord}: {_value(cell.value)}")
            if row_has_content:
                lines.append("")

        parts.append("\n".join(lines))

    return "\n".join(parts)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("input", help="Path to the .xlsx budget file.")
    parser.add_argument(
        "-o", "--file",
        dest="output_file",
        default=None,
        help="Write the dump to this file instead of stdout.",
    )
    parser.add_argument(
        "--no-formulas",
        action="store_true",
        help="Hide formulas; show only cached/static values.",
    )


def run(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        text = dump_workbook_text(input_path, show_formulas=not args.no_formulas)
    except Exception as e:
        print(f"Error reading Excel file: {e}", file=sys.stderr)
        return 1

    if args.output_file:
        out = Path(args.output_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Budget dump written to: {out}")
    else:
        print(text)
    return 0


def main(argv: list[str] | None = None, prog: str | None = None) -> int:
    """Standalone entry point, for a brand that wants its own command name.

    ``vlab-budget = "vlab_proposals.budget_reader:main"`` where that module
    calls ``main(argv, prog="vlab-budget")``.
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Dump a budget Excel file to text for an agent to read.",
    )
    add_arguments(parser)
    return run(parser.parse_args(argv))

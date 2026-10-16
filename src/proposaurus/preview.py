"""PDF pages to PNG, so an agent can look at what it rendered."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .pdftools import contact_sheet, rasterise


@dataclass
class Preview:
    pages: list[Path]
    sheet: Path | None


def preview(
    pdf: str | Path,
    out_dir: str | Path | None = None,
    *,
    dpi: int = 60,
    first: int | None = None,
    last: int | None = None,
    sheet: bool = True,
    columns: int = 4,
) -> Preview:
    """Rasterise ``pdf`` to ``<out_dir>/<stem>/page-<n>.png``, plus a contact sheet.

    ``out_dir`` defaults to a ``preview/`` directory beside the PDF. The
    sheet (``<stem>/sheet.png``) tiles every rendered page into one image:
    look at it first for layout and page breaks, then at single pages, at a
    higher ``dpi``, for detail.
    """
    pdf = Path(pdf)
    base = Path(out_dir) if out_dir is not None else pdf.parent / "preview"
    target = base / pdf.stem
    pages = rasterise(pdf, target, dpi=dpi, first=first, last=last)
    if not pages:
        raise ValueError(f"no pages rendered from {pdf}")
    sheet_path = (
        contact_sheet(pages, target / "sheet.png", columns=columns) if sheet else None
    )
    return Preview(pages, sheet_path)

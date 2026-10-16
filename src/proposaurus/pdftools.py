"""Thin wrappers over poppler (``pdftoppm``, ``pdfinfo``) and Pillow."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from PIL import Image


def page_count(pdf: str | Path) -> int:
    """Number of pages in a PDF (``pdfinfo``)."""
    out = subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True
    ).stdout
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    if not m:
        raise ValueError(f"pdfinfo reported no page count for {pdf}")
    return int(m.group(1))


def rasterise(
    pdf: str | Path,
    out_dir: str | Path,
    *,
    dpi: int = 100,
    first: int | None = None,
    last: int | None = None,
    prefix: str = "page",
) -> list[Path]:
    """Render pages to ``<out_dir>/<prefix>-<n>.png``. Returns them in page order.

    Earlier ``<prefix>-*.png`` files in ``out_dir`` are removed first, so a
    re-render of a shorter PDF leaves no stale pages behind.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob(f"{prefix}-*.png"):
        old.unlink()
    cmd = ["pdftoppm", "-png", "-r", str(dpi)]
    if first is not None:
        cmd += ["-f", str(first)]
    if last is not None:
        cmd += ["-l", str(last)]
    subprocess.run(cmd + [str(pdf), str(out / prefix)], check=True)
    # pdftoppm zero-pads the page number to the width of the page count.
    return sorted(
        out.glob(f"{prefix}-*.png"),
        key=lambda p: int(p.stem.rsplit("-", 1)[1]),
    )


def contact_sheet(
    pages: list[Path], out: str | Path, *, columns: int = 4, gap: int = 12
) -> Path:
    """Tile page images into one PNG, left to right, top to bottom."""
    images = [Image.open(p).convert("RGB") for p in pages]
    w = max(i.width for i in images)
    h = max(i.height for i in images)
    cols = min(columns, len(images))
    rows = -(-len(images) // cols)
    sheet = Image.new(
        "RGB", (cols * w + (cols + 1) * gap, rows * h + (rows + 1) * gap), "#888888"
    )
    for n, img in enumerate(images):
        r, c = divmod(n, cols)
        sheet.paste(img, (gap + c * (w + gap), gap + r * (h + gap)))
    out = Path(out)
    sheet.save(out)
    return out

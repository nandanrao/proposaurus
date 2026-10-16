"""Compare two renders of the same documents: text, page count, pixels.

The check for a refactor that should change nothing ("same text, same pages,
no visible change"), and a quick way to see what a style change touched.
"""

from __future__ import annotations

import difflib
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageChops

from .pdftools import page_count, rasterise
from .verify import pdf_text


@dataclass
class PdfDiff:
    name: str
    problems: list[str] = field(default_factory=list)
    changed_pages: list[int] = field(default_factory=list)

    @property
    def same(self) -> bool:
        return not self.problems


def _text_problem(a: str, b: str, context: int = 6) -> str | None:
    if a == b:
        return None
    lines = list(
        difflib.unified_diff(
            a.splitlines(), b.splitlines(), "baseline", "new", n=1, lineterm=""
        )
    )
    shown = "\n".join("      " + line for line in lines[: context * 2])
    more = f"\n      … {len(lines) - context * 2} more lines" if len(lines) > context * 2 else ""
    return f"text differs:\n{shown}{more}"


def _side_by_side(a: Image.Image, b: Image.Image, mask: Image.Image) -> Image.Image:
    """baseline | new | new with changed pixels in red."""
    marked = b.copy()
    marked.paste((220, 0, 0), mask=mask)
    out = Image.new("RGB", (a.width * 3 + 24, a.height), "#888888")
    for i, img in enumerate((a, b, marked)):
        out.paste(img, (i * (a.width + 12), 0))
    return out


def compare_pdfs(
    baseline: str | Path,
    new: str | Path,
    *,
    dpi: int = 100,
    max_pixels: int = 0,
    out_dir: str | Path | None = None,
) -> PdfDiff:
    """Compare two PDFs. A page "changed" if more than ``max_pixels`` differ.

    With ``out_dir``, each changed page is saved as
    ``<out_dir>/<stem>-page-<n>.png``: baseline, new, and new with the
    changed pixels in red.
    """
    baseline, new = Path(baseline), Path(new)
    result = PdfDiff(new.name)

    n_a, n_b = page_count(baseline), page_count(new)
    if n_a != n_b:
        result.problems.append(f"page count {n_a} -> {n_b}")

    if problem := _text_problem(pdf_text(baseline), pdf_text(new)):
        result.problems.append(problem)

    with tempfile.TemporaryDirectory() as tmp:
        pages_a = rasterise(baseline, Path(tmp) / "a", dpi=dpi)
        pages_b = rasterise(new, Path(tmp) / "b", dpi=dpi)
        for n, (pa, pb) in enumerate(zip(pages_a, pages_b), start=1):
            a = Image.open(pa).convert("RGB")
            b = Image.open(pb).convert("RGB")
            if a.size != b.size:
                result.changed_pages.append(n)
                continue
            mask = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v else 0)
            changed = mask.histogram()[255]
            if changed > max_pixels:
                result.changed_pages.append(n)
                if out_dir is not None:
                    Path(out_dir).mkdir(parents=True, exist_ok=True)
                    _side_by_side(a, b, mask).save(
                        Path(out_dir) / f"{new.stem}-page-{n}.png"
                    )
    if result.changed_pages:
        result.problems.append(
            "pixels differ on page " + ", ".join(map(str, result.changed_pages))
        )
    return result


def compare_dirs(
    baseline_dir: str | Path,
    new_dir: str | Path,
    **kwargs,
) -> list[PdfDiff]:
    """:func:`compare_pdfs` on every PDF in either directory, matched by filename.

    A PDF present on only one side is reported as a problem.
    """
    a = {p.name: p for p in Path(baseline_dir).glob("*.pdf")}
    b = {p.name: p for p in Path(new_dir).glob("*.pdf")}
    results = []
    for name in sorted(a.keys() | b.keys()):
        if name not in b:
            results.append(PdfDiff(name, ["missing from new"]))
        elif name not in a:
            results.append(PdfDiff(name, ["not in baseline"]))
        else:
            results.append(compare_pdfs(a[name], b[name], **kwargs))
    return results

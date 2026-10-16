"""Jinja environment and PDF writing.

The brand owns its templates and static files; these helpers only wire them
up the same way every time.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from .money import make_money, money_parts
from .text import is_figure, linkify
from .timeline import gantt


def register_filters(env: Environment, currency: str = "USD") -> None:
    """Add the library's filters to ``env``.

    ``money`` (bound to ``currency``), ``money_parts`` (``(symbol, whole,
    cents)`` for a brand that styles the cents), ``gantt``, ``is_figure`` and
    ``linkify``. A brand adds its own filters after this.
    """
    env.filters["money"] = make_money(currency)
    env.filters["money_parts"] = lambda value: money_parts(value, currency)
    env.filters["gantt"] = gantt
    env.filters["is_figure"] = is_figure
    env.filters["linkify"] = linkify


def make_env(
    template_dirs: str | Path | list[str | Path], currency: str = "USD"
) -> Environment:
    """A Jinja environment over ``template_dirs`` with the library filters.

    HTML autoescaping on, and ``trim_blocks`` / ``lstrip_blocks`` so block
    tags don't leave blank lines in the output.
    """
    if not isinstance(template_dirs, list):
        template_dirs = [template_dirs]
    env = Environment(
        loader=FileSystemLoader([str(d) for d in template_dirs]),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    register_filters(env, currency)
    return env


def write_pdf(html: str, output_path: str | Path, *, base_url: str | Path) -> Path:
    """Render an HTML string to a PDF with WeasyPrint. Returns the output path.

    ``base_url`` is the directory relative URLs in the HTML resolve against,
    e.g. ``static/style.css`` and the fonts it imports. Parent directories of
    ``output_path`` are created.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(base_url)).write_pdf(str(out))
    return out

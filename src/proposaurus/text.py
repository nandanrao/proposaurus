"""Small text helpers for templates."""

from __future__ import annotations

import re
from html import escape

from markupsafe import Markup

_FIGURE = re.compile(r"[\d,.%()\s≥≤<>=~+]+")


def is_figure(text: str) -> bool:
    """True when ``text`` is a figure ("50% (500)", ">=40%") rather than prose.

    Lets a template set numbers and words differently, e.g. figures in mono.
    """
    return bool(_FIGURE.fullmatch(text))


def linkify(text: str, phrase: str, url: str | None) -> Markup:
    """Replace ``phrase`` in ``text`` with a plain ``<a href>`` to ``url``.

    Returns Markup so Jinja does not double-escape the link. If ``url`` is
    falsy or ``phrase`` is not in ``text``, the text comes back escaped and
    unlinked. The link carries no class; style it with ``a`` in the brand CSS.
    """
    safe_text = escape(text)
    if not url or phrase not in text:
        return Markup(safe_text)
    link = f'<a href="{escape(url)}">{escape(phrase)}</a>'
    return Markup(text.replace(phrase, link))

"""Budget grouping and totals over a list of line items.

Each item needs ``total_price`` and may have ``part``, ``section`` and
``quantity``; :class:`proposaurus.models.BudgetLineItem` has them. Grouping is
by runs of consecutive items, not by set membership: the input order is the
document order, and a section that appears twice is the author's error to see,
not ours to silently merge.
"""

from __future__ import annotations

from collections.abc import Sequence


def total(items: Sequence) -> float:
    """Sum of every item's ``total_price`` (after discounts), to the cent."""
    return round(sum(i.total_price for i in items), 2)


def effective_total(items: Sequence, override: float | None = None) -> float:
    """The total to display: an explicit ``override`` if given, else :func:`total`."""
    return override if override is not None else total(items)


def has_quantity(items: Sequence) -> bool:
    """True if any item states a quantity, i.e. the table needs that column."""
    return any(i.quantity for i in items)


def has_parts(items: Sequence) -> bool:
    """True if any item declares a ``part``."""
    return any(i.part for i in items)


def has_sections(items: Sequence) -> bool:
    """True if any item declares a ``section``."""
    return any(i.section for i in items)


def sections(items: Sequence) -> list[dict]:
    """Items grouped by ``section``, each group with a ``subtotal``.

    Returns one untitled group when no item declares a section, so a template
    can iterate one way regardless: ``[{"title", "items", "subtotal"}, ...]``.
    """
    groups: list[dict] = []
    for item in items:
        if not groups or groups[-1]["title"] != item.section:
            groups.append({"title": item.section, "items": []})
        groups[-1]["items"].append(item)
    for g in groups:
        g["subtotal"] = total(g["items"])
    return groups


def parts(items: Sequence) -> list[dict]:
    """Items nested two deep: parts, then sections within them.

    A part carries the headline ``total``; a section within it carries a
    quieter ``subtotal``. Items with no ``part`` collect into one untitled
    part, which is what an ungrouped budget produces. ``show_sections`` is
    false when a part has only one unnamed section, i.e. nothing to sub-divide.

    ``[{"title", "total", "show_sections", "sections": [{"title", "items",
    "subtotal"}, ...]}, ...]``
    """
    result: list[dict] = []
    for item in items:
        if not result or result[-1]["title"] != item.part:
            result.append({"title": item.part, "sections": []})
        secs = result[-1]["sections"]
        if not secs or secs[-1]["title"] != item.section:
            secs.append({"title": item.section, "items": []})
        secs[-1]["items"].append(item)
    for part in result:
        for sec in part["sections"]:
            sec["subtotal"] = total(sec["items"])
        part["total"] = round(sum(s["subtotal"] for s in part["sections"]), 2)
        part["show_sections"] = any(s["title"] for s in part["sections"])
    return result

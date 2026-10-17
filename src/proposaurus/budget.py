"""Budget grouping and totals over a list of line items.

Each item needs ``total_price`` and may have ``part``, ``section`` and
``quantity``; :class:`proposaurus.models.BudgetLineItem` has them. Grouping is
by runs of consecutive items, not by set membership: the input order is the
document order, and a section that appears twice is the author's error to see,
not ours to silently merge.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field


# Groups are small objects rather than dicts on purpose: in Jinja, `sec.items`
# on a dict is the dict's .items() method, not the key. These work with either
# `sec.items` or `sec["items"]`.


@dataclass
class Section:
    """A run of consecutive items sharing a ``section`` (``title`` may be ``None``)."""

    title: str | None
    items: list = field(default_factory=list)
    subtotal: float = 0.0


@dataclass
class Part:
    """A run of consecutive items sharing a ``part``, split into sections.

    ``show_sections`` is true when any section in the part has a title. A
    part with a single titled section still shows it, with a subtotal equal
    to the part's ``total``; check ``sections | length > 1`` to hide that.
    """

    title: str | None
    sections: list[Section] = field(default_factory=list)
    total: float = 0.0
    show_sections: bool = False


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


def sections(items: Sequence) -> list[Section]:
    """Items grouped by ``section``, each :class:`Section` with a ``subtotal``.

    Returns one untitled section when no item declares one, so a template
    can iterate one way regardless.
    """
    groups: list[Section] = []
    for item in items:
        if not groups or groups[-1].title != item.section:
            groups.append(Section(item.section))
        groups[-1].items.append(item)
    for g in groups:
        g.subtotal = total(g.items)
    return groups


def parts(items: Sequence) -> list[Part]:
    """Items nested two deep: :class:`Part`, then :class:`Section` within it.

    A part carries the headline ``total``; a section within it carries a
    quieter ``subtotal``. Items with no ``part`` collect into one untitled
    part, which is what an ungrouped budget produces.
    """
    result: list[Part] = []
    for item in items:
        if not result or result[-1].title != item.part:
            result.append(Part(item.part))
        secs = result[-1].sections
        if not secs or secs[-1].title != item.section:
            secs.append(Section(item.section))
        secs[-1].items.append(item)
    for part in result:
        for sec in part.sections:
            sec.subtotal = total(sec.items)
        part.total = round(sum(s.subtotal for s in part.sections), 2)
        part.show_sections = any(s.title for s in part.sections)
    return result

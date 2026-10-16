"""The structure of a contract's clauses. The words are each brand's.

A brand keeps its agreement as data built from these (recitals, numbered
clauses with lettered sub-items, a closing line) so its template can set the
legal text with consistent typography. The text itself never lives here.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SubItem:
    """A lettered sub-clause, e.g. (a) Term. ..."""

    label: str
    text: str


@dataclass(slots=True)
class Clause:
    """A numbered top-level clause with optional paragraphs and lettered sub-items."""

    number: int
    title: str
    paragraphs: list[str] = field(default_factory=list)
    sub_items: list[SubItem] = field(default_factory=list)

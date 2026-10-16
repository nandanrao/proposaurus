"""Pydantic building blocks for a brand's proposal schema.

A brand defines its own root ``Proposal`` (and ``Report``, if it has one) and
composes these into it, or ignores them. They are the shared vocabulary: an
agent that has written one brand's YAML can write another's. None of them has
a default that names a brand. All forbid unknown keys, so a typo in YAML is an
error rather than a silently dropped field.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TimelinePhase(BaseModel):
    """One phase of the project timeline. Feeds :func:`proposaurus.timeline.gantt`."""

    model_config = ConfigDict(extra="forbid")
    phase: str
    # One or two words ("Build", "Fielding"). It labels the phase's bar in a
    # timeline chart, where a description would not fit; falls back to `phase`.
    name: str | None = None
    description: str
    # "Week 3" or "Weeks 3-5" can be charted; anything else is shown as text.
    duration: str


class BudgetLineItem(BaseModel):
    """One budget line. Feeds :mod:`proposaurus.budget`.

    ``unit_price`` and ``total_price`` are numbers (format them with
    :func:`proposaurus.money.format_money`). ``quantity`` is free-form text
    that combines a number with a unit label, e.g. ``"600 Resp."``; if no item
    has one, the table can drop that column (``budget.has_quantity``).
    """

    model_config = ConfigDict(extra="forbid")
    description: str
    unit_price: float
    quantity: str | None = None
    total_price: float
    discount_badge: str | None = None
    list_price: float | None = None
    """Line total before the discount. When set, a template can show it
    struck through above ``total_price``, so the discount reads as money
    rather than as a badge alone."""

    part: str | None = None
    """Top-level grouping. A part gets a prominent total -- it is the number
    the reader is meant to walk away with. Optional, and independent of
    ``section``."""

    section: str | None = None
    """Optional grouping heading. Consecutive items sharing a ``section``
    group under one heading with their own subtotal. Use it when a proposal
    sells two genuinely different things -- a reusable asset and the service
    that runs on it, say -- and the client needs to price them apart."""


class InvoicingMilestone(BaseModel):
    """One row of an invoicing schedule."""

    model_config = ConfigDict(extra="forbid")
    milestone: str
    payment_terms: str


class ScopeSection(BaseModel):
    """A titled group of scope-of-work items.

    Use a list of these instead of one flat list when a proposal covers two
    separable bodies of work, so the numbering does not silently blend them
    into one commitment.
    """

    model_config = ConfigDict(extra="forbid")
    title: str
    items: list[str]


class BulletBlock(BaseModel):
    """A titled block of short bullets.

    Bullets, not paragraphs: a proposal nobody scans is a proposal nobody
    reads.
    """

    model_config = ConfigDict(extra="forbid")
    title: str
    items: list[str]


class ComparisonRow(BaseModel):
    """One capability row in a :class:`ComparisonTable`."""

    model_config = ConfigDict(extra="forbid")
    label: str
    cells: list[str]


class ComparisonTable(BaseModel):
    """A capability-by-option matrix.

    ``columns`` are the option headers; the row-label column is unheaded.
    Every row's ``cells`` must be the same length as ``columns``.
    ``highlight_column`` is a 0-based index into ``columns`` to emphasise --
    normally our own offering.
    """

    model_config = ConfigDict(extra="forbid")
    columns: list[str]
    rows: list[ComparisonRow]
    highlight_column: int | None = None

    @model_validator(mode="after")
    def _rows_match_columns(self):
        width = len(self.columns)
        for row in self.rows:
            if len(row.cells) != width:
                raise ValueError(
                    f"appendix row {row.label!r} has {len(row.cells)} cells "
                    f"but there are {width} columns"
                )
        if self.highlight_column is not None and not (
            0 <= self.highlight_column < width
        ):
            raise ValueError(
                f"highlight_column {self.highlight_column} is outside "
                f"0..{width - 1}"
            )
        return self


class Appendix(BaseModel):
    """An appendix for the "why does this have to be built" question.

    A short lead-in, a capability matrix against what already exists, and a
    few tight blocks of bullets. Deliberately has no free paragraph body.
    """

    model_config = ConfigDict(extra="forbid")
    title: str
    intro: str | None = None
    table: ComparisonTable | None = None
    table_note: str | None = None
    notes: list[BulletBlock] = Field(default_factory=list)


class Signatory(BaseModel):
    """A party in an acceptance / signature block.

    Every field is optional so a draft, which has nowhere to sign, need not
    carry one. A brand sets its own consultant as the default in its root model.
    """

    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    email: str | None = None
    organization: str | None = None
    sign_date: str | None = None
    signature_image: str | None = None

"""Gantt geometry from a list of timeline phases.

Returns data, not markup: which weeks each phase spans and how wide the ruler
is. The brand's template draws it however it likes.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_WEEKS = re.compile(r"^\s*weeks?\s+(\d+)(?:\s*[-–]\s*(\d+))?\s*$", re.I)


def week_span(duration: str) -> tuple[int, int] | None:
    """``"Week 3"`` -> ``(3, 3)``, ``"Weeks 3-5"`` -> ``(3, 5)``; anything else ``None``."""
    m = _WEEKS.match(duration)
    if not m:
        return None
    start, end = int(m.group(1)), int(m.group(2) or m.group(1))
    if end < start:
        return None
    return start, end


def gantt(timeline: Iterable) -> dict | None:
    """Week spans for a timeline chart, or ``None`` if any duration is not in weeks.

    Each phase needs ``duration``, ``phase`` and ``description``, and may have
    a short ``name`` for the bar label (falls back to ``phase``);
    :class:`proposaurus.models.TimelinePhase` has them. Only "Week 3" and
    "Week 3-5" can be placed on a ruler: anything else ("2 weeks", "TBD")
    gives ``None``, and the template should fall back to a plain table.

    Returns ``{"rows": [...], "weeks": <last week>}``, each row a dict of
    ``n`` (1-based), ``name``, ``description``, ``start``, ``end`` and a
    ``label`` such as ``"Wk 3–5"``.
    """
    rows = []
    for i, ph in enumerate(timeline, start=1):
        span = week_span(ph.duration)
        if span is None:
            return None
        start, end = span
        rows.append({
            "n": i,
            "name": ph.name or ph.phase,
            "description": ph.description,
            "start": start,
            "end": end,
            "label": f"Wk {start}" if start == end else f"Wk {start}–{end}",
        })
    if not rows:
        return None
    return {"rows": rows, "weeks": max(r["end"] for r in rows)}

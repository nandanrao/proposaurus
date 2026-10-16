"""Check rendered PDFs for the phrases they must, and must not, contain.

A brand describes its document kinds as data. Each :class:`Kind` says how to
recognise it (``when``: phrases that must all be present), what it must
contain (``require``) and what it must not (``forbid``). The first kind whose
``when`` matches is the one a PDF is checked as, so put the most specific
first: a draft (``when`` = the proposal marker plus "DRAFT") before a proposal
(the marker alone) before a catch-all report (``when`` empty).

Rules can also live in a TOML file for the CLI::

    min_chars = 200

    [[kind]]
    name = "draft"
    when = ["Our team will:", "DRAFT"]
    require = ["Scope of Work", "Budget"]
    forbid = ["By signing below"]

    [[kind]]
    name = "proposal"
    when = ["Our team will:"]
    require = ["Scope of Work", "Budget", "By signing below"]

    [[kind]]
    name = "report"

Text comes from poppler's ``pdftotext``, so check phrases as they extract: a
label set in CSS caps (``text-transform: uppercase``) extracts uppercase.
"""

from __future__ import annotations

import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_MIN_CHARS = 200


@dataclass
class Kind:
    name: str
    when: list[str] = field(default_factory=list)
    require: list[str] = field(default_factory=list)
    forbid: list[str] = field(default_factory=list)

    def matches(self, text: str) -> bool:
        return all(s in text for s in self.when)


def pdf_text(pdf: str | Path) -> str:
    """Extracted text of a PDF (``pdftotext``)."""
    return subprocess.run(
        ["pdftotext", str(pdf), "-"], capture_output=True, text=True, check=True
    ).stdout


def classify(text: str, kinds: list[Kind]) -> Kind | None:
    """The first kind whose ``when`` phrases are all in ``text``."""
    return next((k for k in kinds if k.matches(text)), None)


def check_text(
    text: str, kinds: list[Kind], min_chars: int = DEFAULT_MIN_CHARS
) -> tuple[Kind | None, list[str]]:
    """Classify ``text`` and list its problems. No problems means it passed."""
    if len(text.strip()) < min_chars:
        return None, ["rendered to little or no text"]
    kind = classify(text, kinds)
    if kind is None:
        return None, ["matches none of: " + ", ".join(k.name for k in kinds)]
    problems = [f"missing: {s}" for s in kind.require if s not in text]
    problems += [f"{kind.name} must not contain: {s}" for s in kind.forbid if s in text]
    return kind, problems


def check_pdf(
    pdf: str | Path, kinds: list[Kind], min_chars: int = DEFAULT_MIN_CHARS
) -> tuple[Kind | None, list[str]]:
    """:func:`check_text` on a PDF's extracted text."""
    return check_text(pdf_text(pdf), kinds, min_chars)


def load_rules(path: str | Path) -> tuple[list[Kind], int]:
    """Read ``(kinds, min_chars)`` from a TOML rules file (format above)."""
    with Path(path).open("rb") as f:
        data = tomllib.load(f)
    kinds = [Kind(**k) for k in data.get("kind", [])]
    if not kinds:
        raise ValueError(f"{path} defines no [[kind]] tables")
    return kinds, data.get("min_chars", DEFAULT_MIN_CHARS)

"""Shared logic, building blocks and agent tools for branded PDF proposals.

A brand pack writes its own templates, CSS and CLI, and calls into these
modules where it wants to. Nothing here produces styled markup. See AGENTS.md.

- :mod:`proposaurus.money`     currency formatting
- :mod:`proposaurus.timeline`  Gantt geometry from week durations
- :mod:`proposaurus.budget`    budget grouping and totals
- :mod:`proposaurus.text`      small text helpers (figures, links)
- :mod:`proposaurus.documents` YAML loading, frontmatter, Markdown
- :mod:`proposaurus.render`    Jinja environment and PDF writing
- :mod:`proposaurus.models`    Pydantic building blocks for a brand's schema
- :mod:`proposaurus.terms`     the structure of a contract's clauses
- :mod:`proposaurus.verify`    phrase checks on rendered PDFs
- :mod:`proposaurus.preview`   PDF pages to PNG
- :mod:`proposaurus.diff`      compare two sets of PDFs
- :mod:`proposaurus.budget_reader` Excel budget to text
"""

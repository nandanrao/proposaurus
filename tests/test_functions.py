import pytest
from pydantic import ValidationError

from proposaurus import budget
from proposaurus.documents import markdown_to_html, split_frontmatter
from proposaurus.models import BudgetLineItem, ComparisonRow, ComparisonTable, TimelinePhase
from proposaurus.money import format_money, make_money, money_parts, symbol_for
from proposaurus.terms import Clause, SubItem
from proposaurus.text import is_figure, linkify
from proposaurus.timeline import gantt, week_span


def item(total, part=None, section=None, quantity=None):
    return BudgetLineItem(
        description="x", unit_price=total, total_price=total,
        part=part, section=section, quantity=quantity,
    )


# --- money -------------------------------------------------------------------

def test_format_money():
    assert format_money(4500) == "$4,500.00"
    assert format_money("1234.5", "eur") == "€1,234.50"
    assert format_money(10, "CHF") == "CHF 10.00"
    assert format_money(None) == ""
    assert make_money("GBP")(0.5) == "£0.50"


def test_money_parts():
    assert money_parts(1234.5) == ("$", "1,234", "50")
    assert money_parts(None) is None
    assert symbol_for("usd") == "$"


# --- timeline ----------------------------------------------------------------

def test_week_span():
    assert week_span("Week 3") == (3, 3)
    assert week_span("Weeks 3-5") == (3, 5)
    assert week_span("weeks 3 – 5") == (3, 5)
    assert week_span("2 weeks") is None
    assert week_span("Week 5-3") is None


def test_gantt():
    g = gantt([
        TimelinePhase(phase="Kickoff and design", name="Design", description="d", duration="Week 1"),
        TimelinePhase(phase="Fieldwork", description="f", duration="Weeks 2-6"),
    ])
    assert g["weeks"] == 6
    assert g["rows"][0] == {
        "n": 1, "name": "Design", "description": "d", "start": 1, "end": 1, "label": "Wk 1",
    }
    assert g["rows"][1]["name"] == "Fieldwork"
    assert g["rows"][1]["label"] == "Wk 2–6"


def test_gantt_falls_back():
    assert gantt([TimelinePhase(phase="p", description="d", duration="TBD")]) is None
    assert gantt([]) is None


# --- budget ------------------------------------------------------------------

def test_totals():
    items = [item(0.1), item(0.2)]
    assert budget.total(items) == 0.3
    assert budget.effective_total(items) == 0.3
    assert budget.effective_total(items, 99.0) == 99.0
    assert not budget.has_quantity(items)
    assert budget.has_quantity([item(1, quantity="3 Units")])


def test_sections_group_consecutive_runs():
    groups = budget.sections([item(1, section="A"), item(2, section="A"), item(4, section="B"), item(8, section="A")])
    assert [(g["title"], g["subtotal"]) for g in groups] == [("A", 3), ("B", 4), ("A", 8)]
    assert [g["title"] for g in budget.sections([item(1), item(2)])] == [None]


def test_parts():
    parts = budget.parts([
        item(100, part="Build", section="Platform"),
        item(50, part="Build", section="Hosting"),
        item(10, part="Run"),
    ])
    assert [(p["title"], p["total"], p["show_sections"]) for p in parts] == [
        ("Build", 150, True),
        ("Run", 10, False),
    ]
    assert [s["subtotal"] for s in parts[0]["sections"]] == [100, 50]
    assert budget.has_parts([item(1, part="x")]) and not budget.has_parts([item(1)])
    assert budget.has_sections([item(1, section="x")])


# --- text and documents ------------------------------------------------------

def test_is_figure():
    assert is_figure("50% (500)")
    assert is_figure(">=40%")
    assert not is_figure("Even spread")


def test_linkify():
    assert linkify("see the sheet", "the sheet", "https://e.x/?a=1&b=2") == (
        'see <a href="https://e.x/?a=1&amp;b=2">the sheet</a>'
    )
    assert linkify("a <b>", "zzz", "https://e.x") == "a &lt;b&gt;"
    assert linkify("a b", "a", None) == "a b"


def test_frontmatter():
    front, body = split_frontmatter("---\ntitle: T\n---\n# Body\n")
    assert front == {"title": "T"} and body == "# Body\n"
    assert split_frontmatter("# No front") == ({}, "# No front")


def test_markdown_tables():
    html = markdown_to_html("| a | b |\n|---|---|\n| 1 | 2 |\n")
    assert "<table>" in html and "<td>1</td>" in html


# --- models ------------------------------------------------------------------

def test_models_forbid_unknown_keys():
    with pytest.raises(ValidationError):
        TimelinePhase(phase="p", description="d", duration="Week 1", typo=1)


def test_comparison_table_widths():
    ComparisonTable(columns=["Us", "Them"], rows=[ComparisonRow(label="r", cells=["y", "n"])], highlight_column=0)
    with pytest.raises(ValidationError):
        ComparisonTable(columns=["Us", "Them"], rows=[ComparisonRow(label="r", cells=["y"])])
    with pytest.raises(ValidationError):
        ComparisonTable(columns=["Us"], rows=[], highlight_column=1)


def test_clause():
    c = Clause(1, "Services", sub_items=[SubItem("(a)", "Term.")])
    assert c.paragraphs == [] and c.sub_items[0].label == "(a)"

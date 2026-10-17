# AGENTS.md — building a brand pack on proposaurus

proposaurus is the shared part of every brand's proposal builder. You, the agent, write
the brand's part: its templates, CSS, fonts, legal text, schema root and CLI. This file
is everything you need to do that without reading another brand's code.

## What is here, and what is not

| proposaurus has | The brand pack has |
|---|---|
| Functions: money, Gantt geometry, budget grouping and totals, YAML/Markdown loading, Jinja env, PDF writing | Templates (`proposal.html`, `report.html`, …), CSS, fonts |
| Pydantic building blocks (`proposaurus.models`) | The root `Proposal` / `Report` models, brand-specific models and defaults (the consultant) |
| The clause structure (`proposaurus.terms`) | The words of its agreement |
| The `proposaurus` CLI: `preview`, `verify`, `diff`, `budget` | Its own CLI that renders (`<brand>-proposal`), and its verify rules |

No markup lives here. Helpers return data (a dict of week spans, a list of budget
groups); your template lays it out however the brand wants. The two exceptions are
Markdown → HTML and `linkify`'s bare `<a href>`, which carry no classes.

Never put client material (projects, transcripts, budgets) or anything brand-specific
(names, colours, fonts, legal text) in this repo. Tests use made-up data.

## Setting up a brand pack

```
<brand>-proposals/
├── pyproject.toml
├── verify.toml                  # document kinds for `proposaurus verify`
├── examples/<made-up>.yaml
└── src/<brand>_proposals/
    ├── schema.py                # root Proposal, built from proposaurus.models
    ├── terms.py                 # the agreement, as Clause / SubItem data
    ├── render.py                # make_env + write_pdf
    ├── cli.py                   # <brand>-proposal <yaml> [out.pdf]
    ├── templates/proposal.html
    └── static/style.css, fonts.css, fonts/*.woff2
```

`pyproject.toml` depends on proposaurus through uv. proposaurus needs Python 3.14, and
the brand needs a build backend or `[project.scripts]` won't install its CLI:

```toml
[project]
name = "acme-proposals"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = ["proposaurus"]

[project.scripts]
acme-proposal = "acme_proposals.cli:main"

[build-system]
requires = ["uv_build>=0.12.22,<0.13.0"]
build-backend = "uv_build"

[tool.uv.sources]
proposaurus = { path = "../proposaurus", editable = true }   # relative to the brand repo
```

### schema.py

```python
from proposaurus import budget
from proposaurus.models import BudgetLineItem, InvoicingMilestone, Signatory, TimelinePhase
from pydantic import BaseModel, ConfigDict, Field

class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid")      # a YAML typo is an error
    file_name: str
    title: str
    draft: bool = False
    scope_of_work: list[str]
    timeline: list[TimelinePhase]
    currency: str = "USD"
    budget_line_items: list[BudgetLineItem]
    budget_total: float | None = None
    invoicing: list[InvoicingMilestone] = Field(default_factory=list)
    client: Signatory = Field(default_factory=Signatory)
    consultant: Signatory = Field(default_factory=lambda: Signatory(name="…", organization="…"))

    @property
    def budget_parts(self):
        return budget.parts(self.budget_line_items)

    @property
    def total(self):
        return budget.effective_total(self.budget_line_items, self.budget_total)
```

Use as many or as few of the building blocks as the brand needs; add your own models
beside them. The example is the minimum: a real cover usually wants a date, the client's
display name, and perhaps a subtitle or one-line goal. Those are the brand's fields.

### Draft mode

A draft is a costing sent to shape a conversation, not a contract: it has nowhere to
sign. Implement it in the template: `{% if not p.draft %}` around the agreement, the
acceptance line and the signature block, and a visible "DRAFT" marker (on the cover,
say) when it is set. The marker is also what `verify` uses to tell a draft from a
proposal.

### render.py and cli.py

```python
from pathlib import Path
from proposaurus.documents import load_yaml
from proposaurus.render import make_env, write_pdf
from . import terms
from .schema import Proposal

PKG = Path(__file__).resolve().parent

def render_pdf(yaml_path, out):
    p = load_yaml(yaml_path, Proposal)
    env = make_env(PKG / "templates", currency=p.currency)
    html = env.get_template("proposal.html").render(p=p, terms=terms)
    return write_pdf(html, out, base_url=PKG)   # "static/style.css" resolves against PKG
```

The CLI is a few lines of `argparse` around `render_pdf`. A useful convention: with no
output path, write to `<input dir>/output/<file_name>.pdf`, so each project's PDFs stay
beside its YAML.

## Library reference

**`proposaurus.render`**
- `make_env(template_dirs, currency="USD")`: Jinja `Environment` (autoescape on,
  `trim_blocks`, `lstrip_blocks`) with the filters below. Add your own after:
  `env.filters["x"] = …`.
- `register_filters(env, currency)`: the same filters, for an environment you built.
  Filters: `money` (`1500 | money` → `$1,500.00`), `money_parts` (→ `("$", "1,500", "00")`,
  to style the cents), `gantt`, `is_figure`, `linkify`.
- `write_pdf(html, output_path, *, base_url)`: WeasyPrint. Creates parent directories.

**`proposaurus.money`**: `format_money(value, currency)`, `money_parts`, `symbol_for`,
`make_money`. Anglo number format in every currency; `None` → `""`. Codes without a symbol
render as `"CHF 10.00"`.

**`proposaurus.timeline`**
- `gantt(phases)` → `None` unless every `duration` is `"Week N"` or `"Weeks N-M"`; then
  `{"weeks": 6, "rows": [{"n": 1, "name": "Design", "description": …, "start": 1, "end": 2,
  "label": "Wk 1–2"}, …]}`. `name` falls back to `phase`. On `None`, show a plain table.
- `week_span("Weeks 3-5")` → `(3, 5)`.

In a template, use the filter: `{% set g = p.timeline | gantt %}{% if g %}…chart…{% else
%}…table…{% endif %}`.

A chart that works: a `<table>` with `table-layout: fixed`, one `<col>` per week, empty
`<td>`s before `start`, one `<td colspan="end-start+1">` holding the bar, empty `<td>`s
after.

**`proposaurus.budget`**: all take the list of line items; grouping is by consecutive runs.
- `parts(items)` → list of `Part(title, sections, total, show_sections)`, each section a
  `Section(title, items, subtotal)`. Ungrouped items form one part with `title` `None`.
  `show_sections` is true when any section in the part has a title, so a part with one
  titled section shows a subtotal equal to its total; use `part.sections | length > 1`
  if that should be hidden.
- `sections(items)` → list of `Section`.
- `total`, `effective_total(items, override)`, `has_quantity` (drop the quantity column if
  false), `has_parts`, `has_sections`.

**`proposaurus.models`**: `TimelinePhase`, `BudgetLineItem` (with `part`, `section`,
`list_price` for a struck-through pre-discount price, `discount_badge`),
`InvoicingMilestone`, `ScopeSection`, `BulletBlock`, `ComparisonTable` / `ComparisonRow`
(validated widths, `highlight_column`), `Appendix`, `Signatory` (all optional). All
`extra="forbid"`; read the docstrings for intent.

**`proposaurus.terms`**: `Clause(number, title, paragraphs=[], sub_items=[])`,
`SubItem(label, text)`. Keep the agreement as module-level data (`RECITALS`, `CLAUSES`,
`ACCEPTANCE_LINE`, …) and pass the module to the template.

**`proposaurus.documents`**: `load_yaml(path, Model)`, `split_frontmatter(text)` →
`(dict, body)`, `markdown_to_html(text)` (tables, attr_list, sane_lists, footnotes,
md_in_html). For a free-form report: frontmatter validates a cover model; the body is
Markdown.

**`proposaurus.text`**: `is_figure("50% (500)")` (set numbers apart from prose),
`linkify(text, phrase, url)`.

## The loop: render → preview → verify → diff

You cannot see a PDF by reading its HTML. After every change that could move something:

1. **Render** with the brand's CLI.
2. **Preview**: `uv run proposaurus preview out.pdf` writes
   `preview/<name>/sheet.png` (every page tiled) and `page-N.png` beside the PDF. Look at
   the sheet for page breaks and overall layout, then at single pages (`--dpi 150`,
   `--first 2 --last 2`) for detail. Check what the brand's design calls for, not only
   whether it rendered.
3. **Verify**: `uv run proposaurus verify --rules verify.toml examples/output/` checks the
   phrases each kind of document must and must not contain. Typically: a proposal must
   contain the agreement and the signature block; a draft must not. Phrases are matched
   against `pdftotext` output, so text set with `text-transform: uppercase` must be
   written uppercase in the rules. Format:

   ```toml
   min_chars = 200
   [[kind]]                       # first matching kind wins: most specific first
   name = "draft"
   when = ["Scope of Work", "DRAFT"]
   require = ["Scope of Work", "Budget"]
   forbid = ["By signing below"]
   [[kind]]
   name = "proposal"
   when = ["Scope of Work"]
   require = ["Scope of Work", "Budget", "By signing below"]
   [[kind]]
   name = "report"                # empty `when`: matches anything left
   ```

   Phrases are plain substring matches, so pick ones that occur only where you mean:
   "Budget" also matches "the Budget" inside an agreement. A draft's `forbid` list works
   best with the agreement's own title and a signature-block label.

   For a one-off: `proposaurus verify out.pdf --require "TOTAL" --forbid "TODO"`. From
   Python: `proposaurus.verify.Kind` and `check_pdf`.
4. **Diff**: before a refactor or style change, render everything into `before/`;
   after, into `after/`; then `uv run proposaurus diff before/ after/ --out diffs/`.
   It compares extracted text, page counts, and pixels at 100 dpi, matched by filename,
   and saves each changed page as baseline | new | new with changes in red. WeasyPrint
   output is deterministic, so a refactor that changes nothing shows `N/N identical`
   with the default `--max-pixels 0`.

`uv run proposaurus budget file.xlsx` dumps a budget spreadsheet (formulas and their last
values) to text, for reading a client's costing before writing the YAML.

## WeasyPrint, learned the hard way

- **Bundle the fonts.** Font files (`.woff2`, `.otf` and `.ttf` all work) in
  `static/fonts/`, declared with `@font-face` in a `fonts.css` that `style.css` imports,
  with URLs relative to `base_url`. They embed in the PDF and render the same on every
  machine. If a face is missing, WeasyPrint silently falls back to a system font. Give
  bundled faces a family name no system font has, so a fallback is visible in `pdffonts
  out.pdf` instead of hidden behind a same-named system font. A weight or style you didn't
  bundle is synthesised (fake bold, fake oblique): bundle every one the CSS uses.
- **`base_url` decides every relative URL.** `href="static/style.css"` in the template
  resolves against the `base_url` passed to `write_pdf`, usually the package directory.
- **Page furniture is `@page`.** Size and margins there; running footers and page numbers
  in margin boxes (`@bottom-left { content: "Brand" }`, `@bottom-right { content:
  counter(page) }`). A full-bleed cover: `@page :first { margin: 0 }` and clear the margin
  boxes with `content: none`.
- **Control breaks explicitly.** `break-inside: avoid` on table rows, clauses, signature
  blocks and anything that must not split; `break-after: avoid` on headings so they don't
  strand at a page bottom, and on header *rows* inside tables too (`thead`, a budget's
  part and section rows); `break-before: page` for sections that start a page (an
  appendix); `break-after: page` on the cover.
- **`<thead>` and `<tfoot>` repeat on every page a table spans.** Good for column
  headers; wrong for a grand total, which would print mid-budget at the foot of the first
  page (and satisfy a verify phrase on the wrong page). Put totals in a final `<tbody>`.
- **No JavaScript.** Everything is decided at render time in Jinja and CSS.
- **Tables are the reliable layout tool** for anything tabular (budgets, timelines,
  signature grids). Check any other layout in the preview.
- **Turn hyphenation off** unless the brand wants it: `hyphens: none`.
- System requirements: WeasyPrint's Pango, and poppler (`pdftoppm`, `pdftotext`,
  `pdfinfo`) for the CLI.

## Changing proposaurus itself

Change it only for something genuinely shared by more than one brand, and keep it
returning data rather than markup. Run `uv run pytest` here, then re-render every brand
that depends on it and `proposaurus diff` against a render from before the change.
Decisions are in `DECISIONS.md`.

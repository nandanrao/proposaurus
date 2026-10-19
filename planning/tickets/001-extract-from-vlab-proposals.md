# 001 — Extract proposaurus from vlab-proposals

status: done (2026-10-16)
depends: —

## Goal
Move the shared machinery out of `vlab-research/proposals` into this repo, so every
brand's builder (Virtual Lab's, opencore's, later ones) uses one copy of the money logic,
Gantt geometry, budget totals, PDF rendering and verification instead of forking them.

Source: `vlab-research/proposals` (`src/vlab_proposals/`), private.
Shape: D-001.

## What moves here

### Functions
- `money` formatting by currency (`filters.py`: `symbol_for`, `make_money`)
- Gantt geometry (`gantt` → dict)
- Budget grouping and totals (`budget_parts`, `budget_sections`, `computed_total`,
  `effective_total`, `has_quantity_column`), as functions over line items rather than
  methods on vlab's `Proposal`
- `split_frontmatter`, Markdown → HTML with the standard extensions
- `write_pdf(html, base_url, out)` (WeasyPrint)
- `is_figure`, `linkify`
- Excel budget reader (`budget_reader.py`)
- A helper to register the filters on a Jinja `Environment` the brand creates

### Concepts (Pydantic building blocks)
`TimelinePhase`, `BudgetLineItem`, `InvoicingMilestone`, `Signatory`, `ComparisonTable`
/ `ComparisonRow`, `BulletBlock`, `Appendix`, `ScopeSection`, and the `Clause` /
`SubItem` structure from `terms.py`. A brand composes its own root `Proposal` /
`Report` from them, or ignores them.

### Agent tools (`proposaurus` CLI)
Each subcommand works on any brand's PDFs. Rendering is not a subcommand: each brand's
own CLI does that by calling the library's functions.
- `preview <pdf>`: rasterise pages to PNG so the agent can look at the result
- `verify <pdf…> --require … --forbid …` (or a phrases file the brand keeps):
  generalises vlab's `scripts/verify_pdfs.py`, which today hard-codes "Virtual Lab
  will:", the consultant's name and email, and the repo root
- `diff <baseline-dir> <new-dir>`: extracted text, page count, and per-page raster diff
  (`pdftoppm` at 100 dpi). This ticket's own acceptance check uses it.
- `budget <xlsx>`: Excel → text

### Knowledge
`AGENTS.md`: what each piece is for, how to start a new brand pack, the
render → preview → verify → diff loop, and WeasyPrint gotchas (`@page`, local fonts,
page breaks). The vlab brand pack is referenced as a worked example; nothing imports it.

## What stays in each brand's repo
Templates, CSS, fonts, legal text (`terms.py` content), default consultant, root schema
and brand-specific models (e.g. vlab's `NarrativeSection`, whose default text names
Virtual Lab), CLI and its entry-point names, verify phrase lists, draft-mode rules (the
template decides what a draft drops; proposaurus only checks it), and all client
projects (D-003).

## Steps
0. ~~Commit the WIP in `vlab-research/proposals`~~ Done 2026-10-16 (`f20209d` toolchain
   and brand, `96686d0` client projects). Not yet pushed.
1. Render every `examples/*.yaml`, `projects/*/*.yaml` and Markdown report
   (`projects/*/*-report.md`, via `vlab-report`) in the vlab repo; save as baseline
   PDFs outside both repos.
2. Move the functions, concepts and tools here, with tests for the functions. Fixtures
   use made-up data only.
3. Rewire `vlab_proposals` onto proposaurus (uv path dependency). Its templates and CSS
   do not change; only Python moves. `scripts/verify_pdfs.py` becomes vlab's phrase list
   plus a call to `proposaurus verify`.
4. Re-render everything and run `proposaurus diff` against the baseline.
5. Write `AGENTS.md`.

## Done when
- Every example, project and report PDF re-renders with identical extracted text and
  page count, and the raster diff shows no visible change.
- `make all`, `make verify`, `make budget` and `vlab-report` work unchanged in the vlab
  repo; its CLI names and README workflow are unchanged.
- A fresh agent session, given only proposaurus and its AGENTS.md, builds a throwaway
  second brand pack (own templates, CSS, terms, consultant) that renders a made-up
  proposal, with no edits to library code.
- No vlab name, colour, font, legal text, markup or client material is in this repo.

## Outcome (2026-10-16)
- Baseline: 15 PDFs (5 examples, 8 project proposals, 1 project report, 1 collateral
  report). Two renders of unchanged code are pixel-identical, so the bar was exact.
- After the rewire (vlab `3d0a427`) and after the budget-group change below:
  `proposaurus diff` reports 15/15 identical (text, page count, pixels at 100 dpi).
- `make all`, `make verify` (14/14, output byte-identical to the old script's),
  `make budget` (dump byte-identical to the old reader's), `vlab-report` all work.
- A fresh agent given only this repo built "Hollow Pine Studio" (own templates, CSS,
  fonts, terms, consultant; Gantt, grouped budget, draft mode) with no library edits;
  `proposaurus verify` 2/2. Its findings changed the library and AGENTS.md:
  - budget groups are now `Part` / `Section` dataclasses, not dicts (`sec.items` on a
    dict is the `.items` method in Jinja, which crashed its first render);
  - AGENTS.md gained: Python 3.14 and a build backend in the sample `pyproject.toml`,
    draft mode, `<tfoot>` repeating on every page, header rows needing
    `break-after: avoid`, font fallbacks and synthesised weights, substring matching
    in verify rules, `show_sections` semantics.
- Published at `github.com/nandanrao/proposaurus` (D-005). vlab depends on it as a uv
  git dependency, pinned in its `uv.lock` (2026-10-19, still 15/15 identical).

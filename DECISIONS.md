# Decisions

The decision log for proposaurus. Two halves: what is **settled** (do not relitigate)
and what is **open** (do not decide alone).

**Format.** `D-nnn` numbers are permanent. A reversed decision is marked
`Superseded by D-nnn` and kept.

**If you are an agent:** check this file before asking the user a question and before
making an assumption. An `OPEN` decision is the user's: surface it, recommend, and wait.

---

## Settled

### D-001 — The library ships logic, concepts, tools and knowledge, not markup
**Status:** Settled · 2026-10-16

Its user is an agent building brand packs. An agent rewriting a brand's whole template
and CSS is cheap; getting totals, geometry, WeasyPrint and contract checks right is not.
So each brand writes its own templates, CSS and CLI. The library provides:
1. **Functions:** money formatting, Gantt geometry, budget grouping and totals,
   frontmatter and Markdown, PDF writing, the Excel budget reader.
2. **Concepts:** Pydantic building blocks that brands compose into their own root
   models, or ignore. No defaults that name a brand.
3. **Agent tools:** a CLI to preview, verify and diff PDFs.
4. **Knowledge:** an AGENTS.md on using all of the above.

No shared templates, macros, template loader or `Brand` object. Helpers return data, not
HTML. The exceptions carry no classes and no structure a brand would style: Markdown →
HTML, and `linkify`'s bare `<a href>`. vlab's `money_html` (cents in a styled span)
therefore stays in vlab, built on the library's `money_parts`.

### D-002 — Agent tools are a CLI
**Status:** Settled · 2026-10-16

Not an MCP server, for now. An MCP server can be added later on top of the same code.

### D-003 — Its own repo, consumed as a uv dependency; never any client material
**Status:** Settled · 2026-10-16

Brand packs depend on it through uv (a path dependency during development, git later).
It contains no client projects, transcripts, budgets or anything client-specific; tests
and fixtures use made-up data. Client material lives in each brand's own private repo.

### D-004 — Name: proposaurus
**Status:** Settled · 2026-10-16

---

## Open

### D-005 — Public or private
**Status:** OPEN.

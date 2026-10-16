# proposaurus

Shared code for building branded PDF proposals and reports. Each brand (Virtual Lab,
opencore, …) keeps its own repo, its own templates and CSS, and its own clients.
proposaurus is the part they share: the logic, the data building blocks, and the CLI an
agent uses to check what it built.

It is written for an agent building and maintaining brand packs, not for a person
customising a template. There is no shared markup.

Status: being extracted from `vlab-research/proposals`. See `planning/tickets/001`.

- `DECISIONS.md`: what is settled and what is open
- `planning/`: tickets

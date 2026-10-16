"""Loading source documents: YAML into a model, Markdown with frontmatter."""

from __future__ import annotations

import re
from pathlib import Path

import markdown as md
import yaml
from pydantic import BaseModel

# Leading YAML frontmatter block: --- ... --- at the very start of the file.
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# `tables` matters most: reports are mostly tables. `attr_list` lets an author
# tag a block, e.g. `{: .callout }`, for the brand CSS to style.
MARKDOWN_EXTENSIONS = ["tables", "attr_list", "sane_lists", "footnotes", "md_in_html"]


def load_yaml[M: BaseModel](path: str | Path, model: type[M]) -> M:
    """Read a YAML file and validate it into ``model``."""
    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return model.model_validate(data)


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Split a Markdown document into its YAML frontmatter and body.

    Returns ``({}, text)`` unchanged when there is no frontmatter block.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    data = yaml.safe_load(match.group(1)) or {}
    return data, text[match.end() :]


def markdown_to_html(text: str, extensions: list[str] | None = None) -> str:
    """Markdown to plain HTML, with :data:`MARKDOWN_EXTENSIONS` by default."""
    return md.markdown(
        text,
        extensions=MARKDOWN_EXTENSIONS if extensions is None else extensions,
        output_format="html",
    )

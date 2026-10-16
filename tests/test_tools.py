from pathlib import Path

import pytest

from proposaurus.cli import main
from proposaurus.diff import compare_dirs, compare_pdfs
from proposaurus.pdftools import page_count
from proposaurus.preview import preview
from proposaurus.render import make_env, write_pdf
from proposaurus.verify import Kind, check_text, load_rules

LOREM = "A made-up proposal for a made-up client, long enough to count as text. " * 4

TEMPLATE = """<!doctype html><html><head><style>
@page { size: A5; margin: 1cm }
.page2 { break-before: page }
</style></head><body>
<h1>{{ title }}</h1><p>Our team will:</p><p>{{ total | money }}</p><p>{{ body }}</p>
{% if second %}<p class="page2">Second page</p>{% endif %}
</body></html>"""


def render(tmp: Path, name: str, **ctx) -> Path:
    (tmp / "tpl").mkdir(exist_ok=True)
    (tmp / "tpl" / "doc.html").write_text(TEMPLATE)
    env = make_env(tmp / "tpl", currency="EUR")
    html = env.get_template("doc.html").render(
        {"title": "Proposal", "total": 1500, "body": LOREM, "second": False} | ctx
    )
    return write_pdf(html, tmp / name, base_url=tmp)


@pytest.fixture
def pdf(tmp_path):
    return render(tmp_path, "base/doc.pdf")


def test_render_and_preview(pdf, tmp_path):
    assert page_count(pdf) == 1
    result = preview(pdf, tmp_path / "pv")
    assert [p.name for p in result.pages] == ["page-1.png"]
    assert result.sheet and result.sheet.exists()


def test_preview_clears_stale_pages(tmp_path):
    long =render(tmp_path, "long/doc.pdf", second=True)
    assert len(preview(long, tmp_path / "pv").pages) == 2
    short = render(tmp_path, "short/doc.pdf")
    assert len(preview(short, tmp_path / "pv").pages) == 1


def test_verify_kinds():
    kinds = [
        Kind("draft", when=["Our team will:", "DRAFT"], require=["Budget"], forbid=["By signing"]),
        Kind("proposal", when=["Our team will:"], require=["Budget", "By signing"]),
        Kind("report"),
    ]
    body = LOREM + " Our team will: Budget "
    assert check_text(body + "By signing", kinds)[0].name == "proposal"
    kind, problems = check_text(body + "DRAFT By signing", kinds)
    assert kind.name == "draft" and problems == ["draft must not contain: By signing"]
    assert check_text(body, kinds)[1] == ["missing: By signing"]
    assert check_text(LOREM, kinds) == (kinds[2], [])
    assert check_text("short", kinds)[1] == ["rendered to little or no text"]
    assert check_text(LOREM, kinds[:1])[1] == ["matches none of: draft"]


def test_load_rules(tmp_path):
    rules = tmp_path / "rules.toml"
    rules.write_text('min_chars = 10\n[[kind]]\nname = "p"\nrequire = ["x"]\n')
    kinds, min_chars = load_rules(rules)
    assert min_chars == 10 and kinds == [Kind("p", require=["x"])]


def test_verify_cli(pdf, capsys):
    assert main(["verify", str(pdf.parent), "--require", "€1,500.00"]) == 0
    assert main(["verify", str(pdf), "--forbid", "Our team will:"]) == 1
    assert "must not contain: Our team will:" in capsys.readouterr().out


def test_diff_identical(pdf, tmp_path):
    again = render(tmp_path, "new/doc.pdf")
    assert compare_pdfs(pdf, again).same
    assert all(r.same for r in compare_dirs(pdf.parent, again.parent))


def test_diff_catches_changes(pdf, tmp_path):
    changed = render(tmp_path, "new/doc.pdf", title="Proposal v2")
    r = compare_pdfs(pdf, changed, out_dir=tmp_path / "d")
    assert not r.same and r.changed_pages == [1]
    assert any(p.startswith("text differs") for p in r.problems)
    assert (tmp_path / "d" / "doc-page-1.png").exists()

    longer = render(tmp_path, "longer/doc.pdf", second=True)
    assert "page count 1 -> 2" in compare_pdfs(pdf, longer).problems


def test_diff_dirs_reports_missing(pdf, tmp_path):
    (tmp_path / "empty").mkdir()
    assert compare_dirs(pdf.parent, tmp_path / "empty")[0].problems == ["missing from new"]
    assert main(["diff", str(pdf.parent), str(tmp_path / "empty")]) == 1

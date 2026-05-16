from __future__ import annotations

import argparse
import glob
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from markdown_it import MarkdownIt
except ImportError:  # pragma: no cover - exercised as a friendly runtime error
    MarkdownIt = None  # type: ignore[assignment]


DEFAULT_CSS = """
:root {
  color-scheme: light;
  --ink: #172033;
  --muted: #647084;
  --soft: #f5f7fb;
  --softer: #fafbfe;
  --line: #dbe3ef;
  --accent: #4f46e5;
  --accent-2: #0891b2;
  --code-bg: #101827;
  --code-ink: #eef4ff;
}

* { box-sizing: border-box; }
html { font-size: 16px; }
body {
  margin: 0;
  color: var(--ink);
  font-family: ui-serif, Georgia, Cambria, "Times New Roman", Times, serif;
  line-height: 1.55;
  background: white;
}

.document {
  max-width: 760px;
  margin: 0 auto;
  padding: 0 0 2rem;
}

.title-page {
  min-height: 38vh;
  padding: 3.2rem 0 2.4rem;
  margin-bottom: 1.4rem;
  border-bottom: 1px solid var(--line);
  position: relative;
}
.title-kicker {
  color: var(--accent);
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 1.1rem;
}
.title-page h1 {
  margin: 0;
  font-size: 2.85rem;
  line-height: 1.04;
  letter-spacing: -0.045em;
  max-width: 12em;
}
.doc-meta {
  margin-top: 1.4rem;
  color: var(--muted);
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.9rem;
}

main > h1:first-child { display: none; }
h1, h2, h3, h4 {
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.18;
  letter-spacing: -0.025em;
  break-after: avoid;
}
h1 { font-size: 2.2rem; margin: 2.2rem 0 1rem; }
h2 {
  font-size: 1.45rem;
  margin: 2.1rem 0 0.7rem;
  padding-top: 0.45rem;
  border-top: 1px solid var(--line);
}
h3 { font-size: 1.12rem; margin: 1.35rem 0 0.45rem; color: #243049; }
h4 { font-size: 1rem; margin: 1rem 0 0.35rem; color: #243049; }
p { margin: 0.72rem 0; }
a { color: var(--accent-2); text-decoration-thickness: 0.08em; text-underline-offset: 0.14em; }
ul, ol { margin: 0.7rem 0 1rem 1.35rem; padding: 0; }
li { margin: 0.22rem 0; padding-left: 0.1rem; }
li::marker { color: var(--accent); }
hr { border: none; border-top: 1px solid var(--line); margin: 2rem 0; }

blockquote {
  margin: 1.05rem 0;
  padding: 0.9rem 1rem 0.9rem 1.15rem;
  border-left: 0.24rem solid var(--accent);
  background: linear-gradient(90deg, #f0f3ff, var(--softer));
  color: #25304a;
  border-radius: 0 0.55rem 0.55rem 0;
  break-inside: avoid;
}
blockquote p:first-child { margin-top: 0; }
blockquote p:last-child { margin-bottom: 0; }

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 0.88em;
  background: #eef2f7;
  color: #172033;
  padding: 0.08rem 0.25rem;
  border-radius: 0.25rem;
}
pre {
  margin: 1rem 0;
  padding: 0.95rem 1rem;
  background: var(--code-bg);
  color: var(--code-ink);
  border-radius: 0.7rem;
  overflow: hidden;
  white-space: pre-wrap;
  break-inside: avoid;
}
pre code { background: transparent; color: inherit; padding: 0; }

table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.9rem;
}
th, td { border: 1px solid var(--line); padding: 0.45rem 0.55rem; vertical-align: top; }
th { background: var(--soft); text-align: left; }

img { max-width: 100%; border-radius: 0.45rem; }
strong { color: #101827; }
em { color: #3a465c; }

@page { size: Letter; margin: 0.72in 0.78in 0.84in; }
@media print {
  body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .document { max-width: none; }
  h2, h3, h4, blockquote, pre, table { break-inside: avoid; }
}
"""


@dataclass(frozen=True)
class RenderedMarkdown:
    title: str
    html_body: str


def slug_to_title(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").title()


def extract_title(markdown: str, path: Path) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return re.sub(r"[*_`]+", "", match.group(1)).strip()
    return slug_to_title(path)


def render_markdown(markdown: str, path: Path) -> RenderedMarkdown:
    if MarkdownIt is None:
        raise RuntimeError(
            "Missing dependency markdown-it-py. Install with `uv pip install -e .[pdf]` "
            "or run via `uv run --extra pdf anders-md-pdf ...`."
        )
    md = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])
    return RenderedMarkdown(title=extract_title(markdown, path), html_body=md.render(markdown))


def build_html(rendered: RenderedMarkdown, source: Path) -> str:
    title = html.escape(rendered.title)
    source_label = html.escape(str(source))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>{DEFAULT_CSS}</style>
</head>
<body>
  <article class="document">
    <section class="title-page">
      <div class="title-kicker">Anders PDF Export</div>
      <h1>{title}</h1>
      <div class="doc-meta">Source: {source_label}</div>
    </section>
    <main>
{rendered.html_body}
    </main>
  </article>
</body>
</html>
"""


def default_output_path(input_path: Path, data_repo: Path | None = None) -> Path:
    source = input_path.resolve()
    repo = data_repo.resolve() if data_repo else None
    parts = source.parts

    if "briefings" in parts and "days" in parts:
        try:
            days_index = parts.index("days")
            day_folder = Path(*parts[: days_index + 2])
            return day_folder / "exports" / f"{source.stem}.pdf"
        except (ValueError, IndexError):
            pass

    if "content" in parts:
        content_index = parts.index("content")
        content_root = Path(*parts[: content_index + 1])
        return content_root / "pdfs" / f"{source.stem}.pdf"

    if repo and source.is_relative_to(repo):
        return repo / "exports" / f"{source.stem}.pdf"

    return source.parent / "exports" / f"{source.stem}.pdf"


def expand_inputs(patterns: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        if any(ch in pattern for ch in "*?["):
            expanded = [Path(match) for match in sorted(glob.glob(pattern, recursive=True))]
        else:
            expanded = [Path(pattern)]
        paths.extend(expanded)
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def render_pdf(html_doc: str, output_path: Path, title: str) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - friendly runtime error
        raise RuntimeError(
            "Missing dependency playwright. Install with `uv pip install -e .[pdf]` "
            "and then `python -m playwright install chromium`."
        ) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 960, "height": 1280})
        page.set_content(html_doc, wait_until="networkidle")
        safe_title = html.escape(title[:70])
        page.pdf(
            path=str(output_path),
            format="Letter",
            print_background=True,
            display_header_footer=True,
            margin={"top": "0.72in", "right": "0.78in", "bottom": "0.84in", "left": "0.78in"},
            header_template="<div></div>",
            footer_template=(
                "<div style='font-size:8px;color:#7b8496;width:100%;padding:0 0.78in;"
                "font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;'>"
                f"<span>{safe_title}</span>"
                "<span style='float:right;'>Page <span class='pageNumber'></span> of "
                "<span class='totalPages'></span></span></div>"
            ),
        )
        browser.close()


def convert_one(input_path: Path, output_path: Path, *, keep_html: bool = False) -> Path:
    markdown = input_path.read_text(encoding="utf-8")
    rendered = render_markdown(markdown, input_path)
    html_doc = build_html(rendered, input_path)
    render_pdf(html_doc, output_path, rendered.title)
    if keep_html:
        output_path.with_suffix(".html").write_text(html_doc, encoding="utf-8")
    return output_path


def cmd_export(args: argparse.Namespace) -> int:
    data_repo = Path(args.data_repo).expanduser() if args.data_repo else None
    inputs = expand_inputs(args.inputs)
    if not inputs:
        print("No matching Markdown inputs.", file=sys.stderr)
        return 2

    outputs: list[Path] = []
    for input_path in inputs:
        if not input_path.exists():
            print(f"Missing input: {input_path}", file=sys.stderr)
            return 2
        if input_path.suffix.lower() not in {".md", ".markdown"}:
            print(f"Skipping non-Markdown input: {input_path}", file=sys.stderr)
            continue
        if args.output and len(inputs) > 1:
            print("--output can only be used with one input", file=sys.stderr)
            return 2
        output_path = Path(args.output).expanduser().resolve() if args.output else default_output_path(input_path, data_repo)
        outputs.append(convert_one(input_path, output_path, keep_html=args.keep_html))

    for output in outputs:
        print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anders-md-pdf",
        description="Render Markdown drafts and briefing notes to polished local PDFs.",
    )
    parser.add_argument("inputs", nargs="+", help="Markdown file(s) or shell glob(s) to export")
    parser.add_argument("--data-repo", help="Private data repo root, used for default export paths")
    parser.add_argument("-o", "--output", help="PDF output path; only valid for a single input")
    parser.add_argument("--keep-html", action="store_true", help="Also write the intermediate themed HTML next to the PDF")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return cmd_export(args)
    except Exception as exc:  # noqa: BLE001 - CLIs should print a concise friendly error
        print(f"anders-md-pdf: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

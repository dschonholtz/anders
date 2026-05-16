# anders-md-pdf

Render local Markdown drafts and daily briefing notes into polished PDFs for review or sharing.

The tool keeps reusable rendering code in `anders`; private Markdown inputs and generated PDFs should stay in a private data repo such as `anders-life`.

## Setup

```bash
cd ~/repos/anders
uv pip install -e '.[pdf]'
python -m playwright install chromium
```

You can also run without installing into the current environment:

```bash
cd ~/repos/anders
uv run --extra pdf python -m playwright install chromium
uv run --extra pdf anders-md-pdf --help
```

## Usage

Export a draft from `anders-life`:

```bash
cd ~/repos/anders-life
uv run --project ../anders --extra pdf anders-md-pdf \
  content/drafts/backend-to-ai-engineer.md \
  --data-repo .
```

Default output paths:

- `content/drafts/example.md` -> `content/pdfs/example.pdf`
- `briefings/days/YYYY-MM-DD/summary.md` -> `briefings/days/YYYY-MM-DD/exports/summary.pdf`
- anything else -> sibling `exports/` folder

Export several files:

```bash
uv run --project ../anders --extra pdf anders-md-pdf \
  'content/drafts/*.md' \
  'briefings/days/2026-05-16/*.md' \
  --data-repo .
```

Write a specific output path for one input:

```bash
anders-md-pdf content/drafts/backend-to-ai-engineer.md -o content/pdfs/ai-engineer.pdf
```

Add `--keep-html` to save the intermediate themed HTML next to the PDF for debugging the print layout.

## Theme

The default theme includes:

- title page with source path
- readable serif body typography and sans-serif headings
- styled links, lists, blockquotes/callouts, tables, and code blocks
- print-safe colors and page footer with page numbers

PDF generation is local-only through Playwright/Chromium. The tool does not upload content or generated PDFs.

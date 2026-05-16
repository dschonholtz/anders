from pathlib import Path

from anders.md_pdf import default_output_path, extract_title


def test_extract_title_from_first_h1() -> None:
    assert extract_title("Intro\n\n# My **Draft**\n\nBody", Path("draft.md")) == "My Draft"


def test_default_content_pdf_path() -> None:
    source = Path("/Users/example/anders-life/content/drafts/backend-to-ai-engineer.md")
    assert default_output_path(source) == Path(
        "/Users/example/anders-life/content/pdfs/backend-to-ai-engineer.pdf"
    )


def test_default_briefing_export_path() -> None:
    source = Path("/Users/example/anders-life/briefings/days/2026-05-16/summary.md")
    assert default_output_path(source) == Path(
        "/Users/example/anders-life/briefings/days/2026-05-16/exports/summary.pdf"
    )

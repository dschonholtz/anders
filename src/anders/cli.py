from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path


def resolve_day(value: str) -> date:
    today = date.today()
    if value == "today":
        return today
    if value == "yesterday":
        return today - timedelta(days=1)
    return date.fromisoformat(value)


def ensure_day(data_repo: Path, day: date) -> Path:
    root = data_repo / "briefings" / "days" / day.isoformat()
    (root / "raw").mkdir(parents=True, exist_ok=True)
    files = {
        "README.md": f"# {day.isoformat()} Briefing Folder\n\nDaily goals, source context, follow-ups, and summary notes.\n",
        "goals.md": f"# Goals — {day.isoformat()}\n\n## Top priorities\n\n- TBD\n",
        "followups.md": f"# Follow-ups — {day.isoformat()}\n\n## Needs attention\n\n- TBD\n",
        "sources.md": f"# Sources — {day.isoformat()}\n\n## Available sources\n\n- TBD\n",
        "summary.md": f"# Daily Summary — {day.isoformat()}\n\n## Summary\n\n- TBD\n",
    }
    for name, content in files.items():
        p = root / name
        if not p.exists():
            p.write_text(content)
    return root


def cmd_init_day(args: argparse.Namespace) -> int:
    day = resolve_day(args.date)
    root = ensure_day(Path(args.data_repo).expanduser(), day)
    print(root)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="anders")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init-day", help="Create a dated briefing folder in the data repo")
    p.add_argument("--date", default="today", help="today, yesterday, or YYYY-MM-DD")
    p.add_argument("--data-repo", required=True, help="Path to private data repo")
    p.set_defaults(func=cmd_init_day)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

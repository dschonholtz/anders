from __future__ import annotations

import argparse
import os
from datetime import date, timedelta
from pathlib import Path

from .adapters.google import collect_calendar, collect_gmail, day_bounds, token_from_command
from .adapters.linkedin import normalize_linkedin_notifications
from .io import raw_dir, read_jsonl, write_jsonl, write_markdown_list

DEFAULT_TOKEN_COMMAND = "gcloud auth application-default print-access-token"


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


def data_repo_path(args: argparse.Namespace) -> Path:
    return Path(args.data_repo or os.environ.get("ANDERS_DATA_REPO", ".")).expanduser()


def google_token(args: argparse.Namespace) -> str:
    if args.token:
        return args.token
    if args.token_env and os.environ.get(args.token_env):
        return os.environ[args.token_env]
    return token_from_command(args.token_command)


def cmd_init_day(args: argparse.Namespace) -> int:
    day = resolve_day(args.date)
    root = ensure_day(data_repo_path(args), day)
    print(root)
    return 0


def cmd_collect_gmail(args: argparse.Namespace) -> int:
    day = resolve_day(args.date)
    repo = data_repo_path(args)
    ensure_day(repo, day)
    token = google_token(args)
    items = collect_gmail(token, query=args.query, max_results=args.max_results, body=args.include_body)
    out = raw_dir(repo, day.isoformat()) / "email.jsonl"
    count = write_jsonl(out, items)
    write_markdown_list(repo / "briefings" / "days" / day.isoformat() / "email.md", f"Email — {day.isoformat()}", items)
    print(f"wrote {count} email items to {out}")
    return 0


def cmd_collect_calendar(args: argparse.Namespace) -> int:
    day = resolve_day(args.date)
    repo = data_repo_path(args)
    ensure_day(repo, day)
    token = google_token(args)
    time_min, time_max = (args.time_min, args.time_max) if args.time_min and args.time_max else day_bounds(day)
    items = collect_calendar(token, time_min=time_min, time_max=time_max, calendar_id=args.calendar_id, max_results=args.max_results)
    out = raw_dir(repo, day.isoformat()) / "calendar.jsonl"
    count = write_jsonl(out, items)
    write_markdown_list(repo / "briefings" / "days" / day.isoformat() / "calendar.md", f"Calendar — {day.isoformat()}", items)
    print(f"wrote {count} calendar items to {out}")
    return 0


def cmd_extract_linkedin(args: argparse.Namespace) -> int:
    day = resolve_day(args.date)
    repo = data_repo_path(args)
    ensure_day(repo, day)
    source = Path(args.source_jsonl).expanduser() if args.source_jsonl else raw_dir(repo, day.isoformat()) / "email.jsonl"
    email_items = read_jsonl(source)
    items = normalize_linkedin_notifications(email_items)
    out = raw_dir(repo, day.isoformat()) / "linkedin-notifications.jsonl"
    count = write_jsonl(out, items)
    write_markdown_list(repo / "briefings" / "days" / day.isoformat() / "linkedin.md", f"LinkedIn — {day.isoformat()}", items)
    print(f"wrote {count} LinkedIn notification items to {out}")
    return 0


def add_common_data_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--date", default="today", help="today, yesterday, or YYYY-MM-DD")
    p.add_argument("--data-repo", help="Path to private data repo; defaults to ANDERS_DATA_REPO or cwd")


def add_google_auth_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--token", help="OAuth access token; avoid shell history for real use")
    p.add_argument("--token-env", default="GOOGLE_ACCESS_TOKEN", help="Environment variable containing access token")
    p.add_argument("--token-command", default=DEFAULT_TOKEN_COMMAND, help="Command that prints an OAuth access token")


def main() -> int:
    parser = argparse.ArgumentParser(prog="anders")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init-day", help="Create a dated briefing folder in the data repo")
    add_common_data_args(p)
    p.set_defaults(func=cmd_init_day)

    p = sub.add_parser("collect-gmail", help="Collect Gmail messages into the data repo")
    add_common_data_args(p)
    add_google_auth_args(p)
    p.add_argument("--query", default="newer_than:1d", help="Gmail search query")
    p.add_argument("--max-results", type=int, default=25)
    p.add_argument("--include-body", action="store_true", help="Fetch full message payloads instead of metadata/snippets")
    p.set_defaults(func=cmd_collect_gmail)

    p = sub.add_parser("collect-calendar", help="Collect Google Calendar events into the data repo")
    add_common_data_args(p)
    add_google_auth_args(p)
    p.add_argument("--calendar-id", default="primary")
    p.add_argument("--time-min", help="RFC3339 lower bound; defaults to selected day start")
    p.add_argument("--time-max", help="RFC3339 upper bound; defaults to selected day end")
    p.add_argument("--max-results", type=int, default=50)
    p.set_defaults(func=cmd_collect_calendar)

    p = sub.add_parser("extract-linkedin", help="Extract LinkedIn notification signals from collected email JSONL")
    add_common_data_args(p)
    p.add_argument("--source-jsonl", help="Source email JSONL; defaults to day raw/email.jsonl")
    p.set_defaults(func=cmd_extract_linkedin)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

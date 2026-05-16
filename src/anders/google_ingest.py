from __future__ import annotations

import argparse
import base64
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
]
DEFAULT_TZ = "America/New_York"
DEFAULT_CLIENT_SECRET = "private-config/google/oauth-client.local.json"
DEFAULT_TOKEN = "private-config/google/token.local.json"

IMPORTANT_QUERY = "newer_than:14d (is:important OR category:primary) -category:promotions -category:social"
UNREAD_INBOX_QUERY = "in:inbox is:unread newer_than:30d"
OLD_UNREAD_QUERY = "is:unread older_than:180d (-in:sent)"

MUTATION_REFUSAL = (
    "Mutation commands are intentionally disabled in this scaffold. "
    "Future mark-read/archive/unsubscribe work must require an explicit policy file, "
    "a dry-run manifest, and a human approval flag."
)


@dataclass(frozen=True)
class DayPaths:
    data_repo: Path
    day: str

    @property
    def briefing_root(self) -> Path:
        return self.data_repo / "briefings" / "days" / self.day

    @property
    def manifest_dir(self) -> Path:
        return self.briefing_root / "google"

    @property
    def raw_dir(self) -> Path:
        return self.briefing_root / "raw" / "google"

    @property
    def google_root(self) -> Path:
        return self.data_repo / "google"

    @property
    def gmail_messages_dir(self) -> Path:
        return self.google_root / "gmail" / "messages"

    @property
    def calendar_events_dir(self) -> Path:
        return self.google_root / "calendar" / "events"


def today(tz: str = DEFAULT_TZ) -> str:
    return dt.datetime.now(ZoneInfo(tz)).date().isoformat()


def now_iso(tz: str = DEFAULT_TZ) -> str:
    return dt.datetime.now(ZoneInfo(tz)).isoformat(timespec="seconds")


def ensure_paths(paths: DayPaths) -> None:
    for path in [paths.manifest_dir, paths.raw_dir, paths.gmail_messages_dir, paths.calendar_events_dir]:
        path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload)


def slug(value: str, fallback: str = "item") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._")
    return cleaned[:120] or fallback


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def decode_b64url(data: str | None) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8", errors="replace")
    except Exception:
        return ""


def header_map(headers: Iterable[dict[str, str]]) -> dict[str, str]:
    return {h.get("name", "").lower(): h.get("value", "") for h in headers if h.get("name")}


def parse_email_date(value: str) -> str | None:
    if not value:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.isoformat()


def walk_parts(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    yield payload
    for part in payload.get("parts", []) or []:
        yield from walk_parts(part)


def extract_bodies(payload: dict[str, Any]) -> dict[str, str]:
    text_parts: list[str] = []
    html_parts: list[str] = []
    for part in walk_parts(payload):
        body = decode_b64url((part.get("body") or {}).get("data"))
        if not body:
            continue
        mime = part.get("mimeType", "")
        if mime == "text/plain":
            text_parts.append(body)
        elif mime == "text/html":
            html_parts.append(body)
    text_body = "\n\n".join(p.strip() for p in text_parts if p.strip())
    html_body = "\n\n".join(p.strip() for p in html_parts if p.strip())
    if not text_body and html_body:
        text_body = html_to_text(html_body)
    return {"text": text_body, "html": html_body}


def html_to_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value)
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"(?i)</p>", "\n\n", value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def normalize_gmail_message(raw: dict[str, Any], include_body: bool = True) -> dict[str, Any]:
    payload = raw.get("payload", {}) or {}
    headers = header_map(payload.get("headers", []) or [])
    bodies = extract_bodies(payload) if include_body else {"text": "", "html": ""}
    return {
        "source": "gmail",
        "id": raw.get("id"),
        "thread_id": raw.get("threadId"),
        "label_ids": raw.get("labelIds", []) or [],
        "history_id": raw.get("historyId"),
        "internal_date_ms": raw.get("internalDate"),
        "date": parse_email_date(headers.get("date", "")),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "subject": headers.get("subject", ""),
        "message_id": headers.get("message-id", ""),
        "list_unsubscribe": headers.get("list-unsubscribe", ""),
        "list_id": headers.get("list-id", ""),
        "snippet": raw.get("snippet", ""),
        "body_text": bodies["text"],
        "body_html": bodies["html"],
    }


def gmail_markdown(message: dict[str, Any]) -> str:
    body = message.get("body_text") or message.get("snippet") or ""
    return "\n".join(
        [
            f"# {message.get('subject') or '(no subject)'}",
            "",
            f"- Source: Gmail",
            f"- Message ID: `{message.get('id')}`",
            f"- Thread ID: `{message.get('thread_id')}`",
            f"- Date: {message.get('date') or ''}",
            f"- From: {message.get('from') or ''}",
            f"- To: {message.get('to') or ''}",
            f"- Labels: {', '.join(message.get('label_ids') or [])}",
            "",
            "## Snippet",
            "",
            message.get("snippet") or "",
            "",
            "## Body",
            "",
            body,
            "",
        ]
    )


def normalize_calendar_event(raw: dict[str, Any], calendar_id: str) -> dict[str, Any]:
    start = raw.get("start", {}) or {}
    end = raw.get("end", {}) or {}
    return {
        "source": "google_calendar",
        "calendar_id": calendar_id,
        "id": raw.get("id"),
        "ical_uid": raw.get("iCalUID"),
        "status": raw.get("status"),
        "summary": raw.get("summary", "(no title)"),
        "description": raw.get("description", ""),
        "location": raw.get("location", ""),
        "start": start.get("dateTime") or start.get("date"),
        "end": end.get("dateTime") or end.get("date"),
        "html_link": raw.get("htmlLink", ""),
        "organizer": (raw.get("organizer") or {}).get("email", ""),
        "attendees": [a.get("email", "") for a in raw.get("attendees", []) or [] if a.get("email")],
    }


def sender_domain(from_header: str) -> str:
    _, addr = email.utils.parseaddr(from_header or "")
    if "@" not in addr:
        return "unknown"
    return addr.rsplit("@", 1)[1].lower()


def triage_recommendation(message: dict[str, Any]) -> dict[str, Any]:
    labels = set(message.get("label_ids") or [])
    domain = sender_domain(message.get("from", ""))
    subject = (message.get("subject") or "").lower()
    list_unsub = bool(message.get("list_unsubscribe"))
    reasons: list[str] = []
    action = "keep_review"
    confidence = "low"

    if "UNREAD" in labels:
        reasons.append("unread")
    if list_unsub:
        reasons.append("has List-Unsubscribe header")
    if "CATEGORY_PROMOTIONS" in labels or "CATEGORY_SOCIAL" in labels:
        reasons.append("promotion/social category")
    if any(word in subject for word in ["sale", "discount", "offer", "webinar", "newsletter"]):
        reasons.append("marketing-like subject")
    if domain in {"noreply.github.com", "linkedin.com"}:
        reasons.append(f"known notification domain: {domain}")

    if list_unsub and ("CATEGORY_PROMOTIONS" in labels or any(w in subject for w in ["sale", "discount", "offer", "newsletter"])):
        action = "unsubscribe_candidate"
        confidence = "medium"
    elif "UNREAD" in labels and ("CATEGORY_PROMOTIONS" in labels or "CATEGORY_SOCIAL" in labels):
        action = "archive_or_mark_read_candidate"
        confidence = "medium"
    elif "UNREAD" in labels and list_unsub:
        action = "old_unread_list_candidate"
        confidence = "medium"

    return {
        "message_id": message.get("id"),
        "thread_id": message.get("thread_id"),
        "from": message.get("from"),
        "domain": domain,
        "subject": message.get("subject"),
        "date": message.get("date"),
        "labels": sorted(labels),
        "recommended_action": action,
        "confidence": confidence,
        "reasons": reasons,
        "dry_run_only": True,
    }


def sender_summary(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for msg in messages:
        domain = sender_domain(msg.get("from", ""))
        bucket = buckets.setdefault(domain, {"domain": domain, "count": 0, "unread": 0, "senders": {}})
        bucket["count"] += 1
        if "UNREAD" in set(msg.get("label_ids") or []):
            bucket["unread"] += 1
        sender = msg.get("from") or "unknown"
        bucket["senders"][sender] = bucket["senders"].get(sender, 0) + 1
    output = []
    for bucket in buckets.values():
        top = sorted(bucket["senders"].items(), key=lambda x: x[1], reverse=True)[:10]
        output.append({**bucket, "senders": [{"sender": s, "count": c} for s, c in top]})
    return sorted(output, key=lambda b: b["count"], reverse=True)


def load_google_services(args: argparse.Namespace) -> tuple[Any, Any]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise SystemExit(
            "Missing Google client libraries. Install anders with the google extra or run: "
            "python -m pip install google-api-python-client google-auth google-auth-oauthlib"
        ) from exc

    data_repo = Path(args.data_repo).expanduser()
    token_path = Path(args.token_file).expanduser()
    if not token_path.is_absolute():
        token_path = data_repo / token_path
    client_path = Path(args.client_secret).expanduser()
    if not client_path.is_absolute():
        client_path = data_repo / client_path

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_path.exists():
                raise SystemExit(f"OAuth client file not found: {client_path}")
            flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())
    gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
    calendar = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return gmail, calendar


def gmail_list(gmail: Any, query: str, max_results: int, include_body: bool = False) -> list[dict[str, Any]]:
    ids: list[dict[str, str]] = []
    request = gmail.users().messages().list(userId="me", q=query, maxResults=min(max_results, 500))
    while request is not None and len(ids) < max_results:
        response = request.execute()
        ids.extend(response.get("messages", []) or [])
        request = gmail.users().messages().list_next(request, response)
    out: list[dict[str, Any]] = []
    fmt = "full" if include_body else "metadata"
    metadata_headers = ["From", "To", "Cc", "Subject", "Date", "Message-ID", "List-Unsubscribe", "List-ID"]
    for item in ids[:max_results]:
        kwargs = {"userId": "me", "id": item["id"], "format": fmt}
        if fmt == "metadata":
            kwargs["metadataHeaders"] = metadata_headers
        raw = gmail.users().messages().get(**kwargs).execute()
        out.append(normalize_gmail_message(raw, include_body=include_body))
    return out


def calendar_list(calendar: Any, calendar_id: str, time_min: str, time_max: str, max_results: int) -> list[dict[str, Any]]:
    events = []
    request = calendar.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        maxResults=min(max_results, 2500),
    )
    while request is not None and len(events) < max_results:
        response = request.execute()
        events.extend(response.get("items", []) or [])
        request = calendar.events().list_next(request, response)
    return [normalize_calendar_event(e, calendar_id=calendar_id) for e in events[:max_results]]


def write_gmail_artifacts(paths: DayPaths, messages: list[dict[str, Any]], query_name: str, query: str) -> dict[str, Any]:
    ensure_paths(paths)
    refs = []
    for msg in messages:
        mid = msg.get("id") or short_hash(json.dumps(msg, sort_keys=True))
        base = paths.gmail_messages_dir / slug(mid)
        json_path = base.with_suffix(".json")
        md_path = base.with_suffix(".md")
        write_json(json_path, msg)
        write_text(md_path, gmail_markdown(msg))
        refs.append({"id": mid, "json": str(json_path.relative_to(paths.data_repo)), "markdown": str(md_path.relative_to(paths.data_repo))})
    manifest = {
        "source": "gmail",
        "query_name": query_name,
        "query": query,
        "captured_at": now_iso(),
        "count": len(messages),
        "messages": refs,
        "sender_summary": sender_summary(messages),
    }
    write_json(paths.manifest_dir / f"gmail-{slug(query_name)}.manifest.json", manifest)
    return manifest


def write_calendar_artifacts(paths: DayPaths, events: list[dict[str, Any]], window_name: str) -> dict[str, Any]:
    ensure_paths(paths)
    refs = []
    for event in events:
        calendar_id = event.get("calendar_id") or "primary"
        eid = event.get("id") or short_hash(json.dumps(event, sort_keys=True))
        rel_dir = paths.calendar_events_dir / slug(calendar_id, "calendar")
        json_path = rel_dir / f"{slug(eid)}.json"
        write_json(json_path, event)
        refs.append({"id": eid, "json": str(json_path.relative_to(paths.data_repo))})
    manifest = {
        "source": "google_calendar",
        "window_name": window_name,
        "captured_at": now_iso(),
        "count": len(events),
        "events": refs,
    }
    write_json(paths.manifest_dir / f"calendar-{slug(window_name)}.manifest.json", manifest)
    return manifest


def cmd_gmail_query(args: argparse.Namespace) -> int:
    gmail, _ = load_google_services(args)
    messages = gmail_list(gmail, args.query, args.max_results, include_body=args.include_body)
    if args.write:
        paths = DayPaths(Path(args.data_repo).expanduser(), args.date or today(args.timezone))
        manifest = write_gmail_artifacts(paths, messages, args.name, args.query)
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(messages, indent=2, ensure_ascii=False))
    return 0


def cmd_gmail_read(args: argparse.Namespace) -> int:
    gmail, _ = load_google_services(args)
    raw = gmail.users().messages().get(userId="me", id=args.message_id, format="full").execute()
    message = normalize_gmail_message(raw, include_body=True)
    if args.write:
        paths = DayPaths(Path(args.data_repo).expanduser(), args.date or today(args.timezone))
        manifest = write_gmail_artifacts(paths, [message], "read", f"id:{args.message_id}")
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(message, indent=2, ensure_ascii=False))
    return 0


def cmd_calendar_query(args: argparse.Namespace) -> int:
    _, calendar = load_google_services(args)
    tz = ZoneInfo(args.timezone)
    start = dt.datetime.now(tz)
    if args.window == "today":
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + dt.timedelta(days=1)
    elif args.window == "week":
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + dt.timedelta(days=7)
    else:
        end = start + dt.timedelta(hours=args.hours)
    events = calendar_list(calendar, args.calendar_id, start.isoformat(), end.isoformat(), args.max_results)
    if args.write:
        paths = DayPaths(Path(args.data_repo).expanduser(), args.date or today(args.timezone))
        manifest = write_calendar_artifacts(paths, events, args.window)
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(events, indent=2, ensure_ascii=False))
    return 0


def cmd_triage_dry_run(args: argparse.Namespace) -> int:
    gmail, _ = load_google_services(args)
    messages = gmail_list(gmail, args.query, args.max_results, include_body=False)
    recommendations = [triage_recommendation(m) for m in messages]
    payload = {
        "source": "gmail",
        "mode": "dry_run",
        "query": args.query,
        "captured_at": now_iso(),
        "count": len(recommendations),
        "recommendations": recommendations,
        "safety": MUTATION_REFUSAL,
    }
    if args.write:
        paths = DayPaths(Path(args.data_repo).expanduser(), args.date or today(args.timezone))
        ensure_paths(paths)
        write_json(paths.manifest_dir / "gmail-triage-dry-run.json", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_mutate_refuse(args: argparse.Namespace) -> int:
    print(MUTATION_REFUSAL)
    return 2


def cmd_smoke(args: argparse.Namespace) -> int:
    sample = [
        {
            "id": "sample-message",
            "thread_id": "sample-thread",
            "label_ids": ["UNREAD", "CATEGORY_PROMOTIONS", "INBOX"],
            "date": "2026-05-16T12:00:00-04:00",
            "from": "Deals <deals@example.com>",
            "to": "Doug <doug@example.net>",
            "subject": "Weekend sale newsletter",
            "snippet": "Save now",
            "list_unsubscribe": "<mailto:unsubscribe@example.com>",
            "list_id": "example deals",
            "body_text": "Sample body for offline smoke test.",
            "body_html": "",
        }
    ]
    payload = {
        "triage": [triage_recommendation(m) for m in sample],
        "sender_summary": sender_summary(sample),
    }
    if args.data_repo:
        paths = DayPaths(Path(args.data_repo).expanduser(), args.date or today(args.timezone))
        write_gmail_artifacts(paths, sample, "smoke", "offline-sample")
        ensure_paths(paths)
        write_json(paths.manifest_dir / "gmail-triage-smoke.json", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def add_auth_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data-repo", required=True, help="Private anders-life repo path")
    parser.add_argument("--client-secret", default=DEFAULT_CLIENT_SECRET, help="OAuth client JSON path, relative to data repo by default")
    parser.add_argument("--token-file", default=DEFAULT_TOKEN, help="Local token JSON path, relative to data repo by default")
    parser.add_argument("--timezone", default=DEFAULT_TZ)


def add_write_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--write", action="store_true", help="Write canonical artifacts and day manifests into the private data repo")
    parser.add_argument("--date", help="Briefing day YYYY-MM-DD; defaults to today in --timezone")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="anders-google", description="Read-only Google/Gmail/Calendar ingestion for Anders")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("gmail-query", help="List/fetch Gmail messages for a Gmail search query")
    add_auth_args(p)
    add_write_args(p)
    p.add_argument("--name", default="query", help="Manifest query name")
    p.add_argument("--query", default=UNREAD_INBOX_QUERY)
    p.add_argument("--max-results", type=int, default=25)
    p.add_argument("--include-body", action="store_true", help="Fetch full body instead of metadata-only listing")
    p.set_defaults(func=cmd_gmail_query)

    p = sub.add_parser("gmail-read", help="Fetch one Gmail message by id with full body")
    add_auth_args(p)
    add_write_args(p)
    p.add_argument("message_id")
    p.set_defaults(func=cmd_gmail_read)

    p = sub.add_parser("calendar-query", help="Fetch Google Calendar events")
    add_auth_args(p)
    add_write_args(p)
    p.add_argument("--calendar-id", default="primary")
    p.add_argument("--window", choices=["next", "today", "week"], default="next")
    p.add_argument("--hours", type=int, default=48)
    p.add_argument("--max-results", type=int, default=100)
    p.set_defaults(func=cmd_calendar_query)

    p = sub.add_parser("triage-dry-run", help="Recommend Gmail triage candidates without mutating anything")
    add_auth_args(p)
    add_write_args(p)
    p.add_argument("--query", default=OLD_UNREAD_QUERY)
    p.add_argument("--max-results", type=int, default=100)
    p.set_defaults(func=cmd_triage_dry_run)

    p = sub.add_parser("mutate", help="Refusing stub for future explicit-policy Gmail mutations")
    p.set_defaults(func=cmd_mutate_refuse)

    p = sub.add_parser("smoke", help="Offline smoke test; no Google auth required")
    p.add_argument("--data-repo", help="Optional private repo path to write sample artifacts")
    p.add_argument("--date")
    p.add_argument("--timezone", default=DEFAULT_TZ)
    p.set_defaults(func=cmd_smoke)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

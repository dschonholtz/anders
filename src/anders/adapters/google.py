from __future__ import annotations

import base64
import json
import subprocess
import urllib.parse
import urllib.request
from datetime import date
from typing import Any

from anders.models import SourceItem, now_iso

GMAIL_API = "https://gmail.googleapis.com/gmail/v1"
CALENDAR_API = "https://www.googleapis.com/calendar/v3"


class GoogleApiError(RuntimeError):
    pass


def token_from_command(command: str) -> str:
    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def request_json(url: str, token: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise GoogleApiError(f"Google API HTTP {e.code}: {body}") from e


def _headers(payload: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for header in payload.get("headers", []):
        name = header.get("name", "").lower()
        value = header.get("value", "")
        if name:
            out[name] = value
    return out


def _decode_body(data: str | None) -> str | None:
    if not data:
        return None
    padded = data + "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
    except Exception:
        return None


def _snippet_or_body(message: dict[str, Any]) -> str | None:
    snippet = message.get("snippet")
    if snippet:
        return snippet
    payload = message.get("payload", {})
    body = payload.get("body", {})
    text = _decode_body(body.get("data"))
    if text:
        return text[:500]
    for part in payload.get("parts", []) or []:
        if part.get("mimeType") == "text/plain":
            text = _decode_body(part.get("body", {}).get("data"))
            if text:
                return text[:500]
    return None


def list_gmail_message_ids(token: str, query: str, max_results: int = 25) -> list[dict[str, str]]:
    params = urllib.parse.urlencode({"q": query, "maxResults": max_results})
    data = request_json(f"{GMAIL_API}/users/me/messages?{params}", token)
    return data.get("messages", []) or []


def get_gmail_message(token: str, message_id: str, fmt: str = "metadata") -> dict[str, Any]:
    params = urllib.parse.urlencode({"format": fmt})
    return request_json(f"{GMAIL_API}/users/me/messages/{message_id}?{params}", token)


def collect_gmail(token: str, query: str = "newer_than:1d", max_results: int = 25, body: bool = False) -> list[SourceItem]:
    fmt = "full" if body else "metadata"
    captured_at = now_iso()
    items: list[SourceItem] = []
    for ref in list_gmail_message_ids(token, query=query, max_results=max_results):
        msg = get_gmail_message(token, ref["id"], fmt=fmt)
        hdr = _headers(msg.get("payload", {}))
        subject = hdr.get("subject") or "(no subject)"
        sender = hdr.get("from")
        occurred = hdr.get("date")
        summary = _snippet_or_body(msg) if body else msg.get("snippet")
        items.append(
            SourceItem(
                source="gmail",
                source_id=msg.get("id", ref["id"]),
                captured_at=captured_at,
                occurred_at=occurred,
                person=sender,
                title=subject,
                summary=summary,
                url=f"https://mail.google.com/mail/u/0/#all/{msg.get('id', ref['id'])}",
                confidence=1.0,
                privacy="personal",
                metadata={
                    "thread_id": msg.get("threadId"),
                    "labels": msg.get("labelIds", []),
                },
            )
        )
    return items


def collect_calendar(
    token: str,
    time_min: str,
    time_max: str,
    calendar_id: str = "primary",
    max_results: int = 50,
) -> list[SourceItem]:
    params = urllib.parse.urlencode(
        {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": max_results,
        }
    )
    data = request_json(f"{CALENDAR_API}/calendars/{urllib.parse.quote(calendar_id)}/events?{params}", token)
    captured_at = now_iso()
    out: list[SourceItem] = []
    for event in data.get("items", []) or []:
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        end = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")
        attendees = [a.get("email") for a in event.get("attendees", []) or [] if a.get("email")]
        out.append(
            SourceItem(
                source="google_calendar",
                source_id=event.get("id", ""),
                captured_at=captured_at,
                occurred_at=start,
                person=event.get("organizer", {}).get("email"),
                title=event.get("summary") or "(no title)",
                summary=event.get("description"),
                url=event.get("htmlLink"),
                confidence=1.0,
                privacy="personal",
                metadata={"start": start, "end": end, "location": event.get("location"), "attendees": attendees},
            )
        )
    return out


def day_bounds(day: date) -> tuple[str, str]:
    start = f"{day.isoformat()}T00:00:00-05:00"
    end = f"{day.isoformat()}T23:59:59-05:00"
    return start, end

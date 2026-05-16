from __future__ import annotations

import re
from typing import Any

from anders.models import SourceItem, now_iso

LINKEDIN_HINTS = (
    "linkedin.com",
    "linkedin",
    "inmail",
    "invitation",
    "connection request",
    "sent you a message",
)


def looks_like_linkedin_email(item: dict[str, Any]) -> bool:
    text = " ".join(
        str(item.get(k, ""))
        for k in ("source", "person", "title", "summary", "url")
    ).lower()
    return any(hint in text for hint in LINKEDIN_HINTS)


def classify_linkedin_signal(item: dict[str, Any]) -> str:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    if "sent you a message" in text or "new message" in text or "inmail" in text:
        return "message"
    if "invitation" in text or "connection request" in text or "connect" in text:
        return "connection"
    if "mentioned" in text or "commented" in text or "replied" in text:
        return "engagement"
    if "viewed your profile" in text:
        return "profile_view"
    return "notification"


def extract_linkedin_url(text: str) -> str | None:
    match = re.search(r"https?://[^\s)>\]]*linkedin\.com[^\s)>\]]*", text, re.I)
    return match.group(0) if match else None


def normalize_linkedin_notifications(email_items: list[dict[str, Any]]) -> list[SourceItem]:
    captured_at = now_iso()
    out: list[SourceItem] = []
    for item in email_items:
        if not looks_like_linkedin_email(item):
            continue
        signal = classify_linkedin_signal(item)
        joined = f"{item.get('summary', '')} {item.get('url', '')}"
        url = extract_linkedin_url(joined) or item.get("url")
        out.append(
            SourceItem(
                source="linkedin_notification",
                source_id=f"{item.get('source', 'email')}:{item.get('source_id', item.get('title', 'unknown'))}",
                captured_at=captured_at,
                occurred_at=item.get("occurred_at"),
                person=item.get("person"),
                title=item.get("title") or "LinkedIn notification",
                summary=item.get("summary"),
                url=url,
                confidence=0.75 if signal in {"message", "connection"} else 0.55,
                privacy="personal",
                metadata={"signal": signal, "derived_from": item.get("source")},
            )
        )
    return out

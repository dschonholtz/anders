from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class SourceItem:
    """Normalized source item written to briefing raw JSONL files."""

    source: str
    source_id: str
    captured_at: str
    title: str
    occurred_at: str | None = None
    person: str | None = None
    summary: str | None = None
    url: str | None = None
    confidence: float | None = None
    privacy: str = "personal"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None and v != {}}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

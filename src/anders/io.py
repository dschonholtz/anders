from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import SourceItem


def day_dir(data_repo: Path, day: str) -> Path:
    return data_repo / "briefings" / "days" / day


def raw_dir(data_repo: Path, day: str) -> Path:
    path = day_dir(data_repo, day) / "raw"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_jsonl(path: Path, items: Iterable[SourceItem | dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            data = item.to_dict() if isinstance(item, SourceItem) else item
            f.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_markdown_list(path: Path, title: str, items: Iterable[SourceItem]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(items)
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        if not rows:
            f.write("No items captured.\n")
        for item in rows:
            person = f" — {item.person}" if item.person else ""
            when = f" ({item.occurred_at})" if item.occurred_at else ""
            f.write(f"- **{item.title}**{person}{when}\n")
            if item.summary:
                f.write(f"  - {item.summary}\n")
            if item.url:
                f.write(f"  - Source: {item.url}\n")
    return len(rows)

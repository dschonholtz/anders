# iMessage signal ingestion plan

Doug clarified that iMessage should contribute summarized signals to briefings/accountability context, not copied conversations.

## Goal

Fold important or missed iMessage activity from the past day into the morning brief:

- "People who may need a reply"
- "Time-sensitive or important items"
- "Missed follow-ups"
- "Unusual spikes/threads worth checking"

The tool should help Doug notice what matters while leaving Messages as the source of truth.

## Non-goals

- No full iMessage conversation export.
- No per-thread transcript archive.
- No long-term raw message mirror.
- No automated replies or state changes by default.

## Findings from local probe

- OpenClaw has the `bluebubbles` plugin installed.
- `channels.bluebubbles` is present but disabled.
- A BlueBubbles server URL/password are configured, but because the channel is disabled it should be treated as not active for workflows.
- `~/Library/Messages/chat.db` exists locally.
- A read-only SQLite connection from this environment failed with `unable to open database file`; likely next setup work is macOS Full Disk Access/TCC for the runner and/or using a safe copy of the DB plus WAL/SHM sidecars.
- A basic AppleScript probe can address the Messages app, but AppleScript is better for opening or composing approved messages than for robust daily signal extraction.

## Recommended design

### Source adapter

Build a small `anders-imessage` adapter that runs locally on Doug's Mac and uses SQLite in read-only mode.

Query policy:

- Default lookback: yesterday + today, capped to 48h.
- Include unread messages, inbound messages not replied to, and high-signal recent inbound threads.
- Include attachment presence/type metadata but do not copy attachments.
- Limit text access to the minimum needed for classification and summarization.

### Output policy

Persist only a daily signal artifact under `anders-life`, for example:

```text
briefings/days/YYYY-MM-DD/sources/imessage/signals.json
briefings/days/YYYY-MM-DD/sources/imessage/summary.md
```

Suggested JSON shape:

```json
{
  "generated_at": "ISO-8601",
  "window": { "start": "ISO-8601", "end": "ISO-8601" },
  "source": "macos-messages-sqlite-readonly",
  "items": [
    {
      "kind": "needs_reply|important|missed|info",
      "chat_label": "redacted or contact display name",
      "last_message_at": "ISO-8601",
      "unread_count": 1,
      "reason": "Brief assistant summary; no transcript",
      "snippet": "Optional short snippet only if needed"
    }
  ]
}
```

Do not commit raw DB copies, tokens, attachments, or full message bodies.

### Brief integration

The morning brief should merge iMessage signals with Gmail/LinkedIn/calendar follow-ups. Use compact language:

- "iMessage: 3 threads may need attention — Alice logistics for tonight, Bob unanswered question, family thread has travel update."

The brief should avoid quoting sensitive messages unless necessary.

## Future replies

Reply capability is separate from signal ingestion.

If Doug asks to reply:

1. Show the proposed recipient/thread and exact outgoing text.
2. Wait for explicit approval.
3. Use the safest available transport, likely OpenClaw BlueBubbles once enabled/configured or Messages automation.
4. Record only that a reply was sent and the approved outgoing text if Doug wants it in the briefing log.

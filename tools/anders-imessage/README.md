# `anders-imessage`

Purpose: collect privacy-preserving iMessage signals for daily briefings.

Use when: preparing the morning brief and needing to notice important or missed iMessage items from the last day without exporting full conversations.

Status: design/recommended setup only. No implementation yet.

## Scope

`anders-imessage` should be a read-mostly signal tool, not a conversation archive.

Allowed default outputs:

- Counts by time window, unread status, sender/chat, and direction.
- A small "needs attention" list with contact/chat identifier, timestamp, and a terse assistant-written reason.
- Short redacted snippets only when needed to explain why something may matter.
- Links/pointers to the local source record when available, so Doug can open Messages himself.

Out of scope by default:

- Bulk iMessage export.
- Canonical per-conversation transcript files.
- Copying historical conversations into git.
- Sending, reacting, marking read, or otherwise mutating Messages state without explicit approval.

## Recommended access path

Prefer a local macOS Messages database reader for summarization:

1. Read `~/Library/Messages/chat.db` in SQLite read-only mode.
2. Restrict queries to a short lookback window, normally 24-48 hours.
3. Select only fields needed for triage: message id/guid, chat id, handle/contact, service, date, direction, read/unread status, attachment presence, and limited text for classification.
4. Generate ephemeral summaries in memory.
5. Persist only the daily signal summary/manifest into `anders-life` briefing folders.

This likely requires Full Disk Access for the process running the tool. In the current probe, the DB file exists but SQLite read failed with `unable to open database file`, consistent with macOS privacy/TCC or related database sidecar access constraints.

## OpenClaw/BlueBubbles role

OpenClaw has a BlueBubbles channel plugin installed, but it is currently disabled in config. BlueBubbles is useful for approved future sends/replies if Doug explicitly asks for them. It should not be the default mechanism for daily read-only briefing ingestion unless its read APIs can be constrained to the same minimal-signal policy.

## Safety rules

- Default to read-only.
- Never store full iMessage conversations in git.
- Never reply/send/react unless Doug explicitly approves the exact action.
- If a message looks sensitive, surface only that there is a sensitive item needing Doug's review.
- Keep raw local caches, if any are ever needed, outside git and with short retention.

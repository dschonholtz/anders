# anders-google

Small, read-first Google ingestion CLI for Anders daily briefings.

It uses official Google API client libraries for Gmail and Google Calendar. It does **not** scrape Gmail/Calendar pages and does **not** mutate mail/calendar state.

## Install

From the public tooling repo:

```bash
python -m pip install -e '.[google]'
```

## Local auth files

Keep OAuth material in the private data repo, not in `anders`:

- OAuth client JSON: `anders-life/private-config/google/oauth-client.local.json`
- Token cache: `anders-life/private-config/google/token.local.json` (created locally, gitignored)

Scopes currently requested:

- `https://www.googleapis.com/auth/gmail.modify`
- `https://www.googleapis.com/auth/calendar.readonly`

`gmail.modify` is deliberately broader than readonly so future approved triage workflows can mark read/archive without permanent deletion. Current CLI commands remain read-only; mutation is a refusing stub.

## Commands

Offline smoke test, no Google auth:

```bash
anders-google smoke --data-repo /Users/douglasschonholtz/repos/anders-life --date 2026-05-16
```

Unread inbox list, metadata only:

```bash
anders-google gmail-query \
  --data-repo /Users/douglasschonholtz/repos/anders-life \
  --name unread-inbox \
  --query 'in:inbox is:unread newer_than:30d' \
  --max-results 25 \
  --write
```

Recent important mail with bodies for briefing artifacts:

```bash
anders-google gmail-query \
  --data-repo /Users/douglasschonholtz/repos/anders-life \
  --name recent-important \
  --query 'newer_than:14d (is:important OR category:primary) -category:promotions -category:social' \
  --include-body \
  --max-results 25 \
  --write
```

Fetch one full message:

```bash
anders-google gmail-read \
  --data-repo /Users/douglasschonholtz/repos/anders-life \
  MESSAGE_ID \
  --write
```

Calendar next 48 hours:

```bash
anders-google calendar-query \
  --data-repo /Users/douglasschonholtz/repos/anders-life \
  --window next \
  --hours 48 \
  --write
```

Dry-run triage recommendations:

```bash
anders-google triage-dry-run \
  --data-repo /Users/douglasschonholtz/repos/anders-life \
  --query 'is:unread older_than:180d (-in:sent)' \
  --max-results 100 \
  --write
```

## Safety policy

Current behavior:

- Reads Gmail message metadata/bodies only when asked.
- Reads Calendar events only.
- Writes normalized artifacts/manifests to the private data repo.
- Produces dry-run triage recommendations only.
- Refuses the `mutate` command.

Future mutation hooks must require all of the following before implementation/use:

1. A committed safety policy describing allowed actions and forbidden actions.
2. A prior dry-run manifest showing exactly which messages/actions are proposed.
3. An explicit human approval flag or approval file for that run.
4. Hard refusal for permanent delete, send reply, external unsubscribe submission, or broad label mutations unless separately approved.

Recommended first allowed mutations, when Doug approves a policy:

- Mark selected stale unread messages as read.
- Archive selected inbox clutter.
- Save unsubscribe instructions/links for human review.

Still forbidden by default:

- Permanent deletion.
- Sending replies.
- Clicking/submitting unsubscribe links automatically.
- Marking broad query results without a reviewed manifest.

## Artifact layout

Canonical artifacts live under the private data repo and are updated by source ID:

```text
anders-life/
  google/
    gmail/
      messages/{gmail_message_id}.json
      messages/{gmail_message_id}.md
    calendar/
      events/{calendar_id}/{event_id}.json
  briefings/
    days/YYYY-MM-DD/
      google/
        gmail-unread-inbox.manifest.json
        gmail-recent-important.manifest.json
        gmail-triage-dry-run.json
        calendar-next.manifest.json
      raw/google/        # reserved for run-local raw dumps if needed
```

Daily manifests point to canonical files instead of duplicating full source content every day. This mirrors the LinkedIn canonical-conversation + day-manifest approach and keeps briefing days reviewable in GitHub.

## Notes

- Raw full exports and tokens should stay out of git unless explicitly reviewed.
- The private repo should gitignore `private-config/google/*.local.json` and token/secret patterns.
- If OAuth opens a browser the first time, complete that locally; later runs should reuse the local token cache.

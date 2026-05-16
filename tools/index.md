# Anders tool index

Small task-specific tools live here. Keep this index short so an agent can quickly choose the right tool.

## Planned tools

### `anders-day`

Purpose: create/check daily briefing folders in the private data repo.

Use when: starting a new day, ensuring required files exist.

### `anders-google`

Purpose: Read-first Gmail and Google Calendar ingestion using official Google API client libraries.

Use when: collecting unread inbox mail, recent important mail, full message briefing artifacts, calendar windows, sender summaries, or dry-run Gmail triage recommendations.

Docs: `tools/anders-google/README.md`

Status: scaffold implemented; current commands are read-only or dry-run. Mutation command intentionally refuses until a reviewed policy/approval flow exists.

### `anders-linkedin`

Purpose: Official LinkedIn Developer API/OAuth access plus conservative LinkedIn signal handling.

Use when: authorizing/querying LinkedIn APIs or extracting LinkedIn follow-up signals without scraping LinkedIn.

Docs: `tools/anders-linkedin/README.md`

Status: LinkedIn app created; token flow/product scopes pending local secret + approved scopes.


### `anders-imessage`

Purpose: Privacy-preserving iMessage signal ingestion for daily briefings.

Use when: folding important or missed iMessage items from the past day into accountability context without exporting full conversations.

Docs: `tools/anders-imessage/README.md` and `docs/imessage-signal-ingestion.md`

Status: design/recommended setup only; implementation pending local macOS read permissions.

### `anders-md-pdf`

Purpose: Render Markdown drafts and briefing notes to polished local PDFs.

Use when: Doug wants shareable/reviewable PDFs from `content/drafts/*.md` or `briefings/days/YYYY-MM-DD/*.md`.

Docs: `tools/anders-md-pdf/README.md`

Status: implemented with Markdown -> themed HTML -> PDF via Playwright/Chromium.

### `anders-brief`

Purpose: render morning briefs from private repo artifacts.

Use when: preparing the 7 AM morning brief.

### `anders-housing`

Purpose: future housing data collection/analysis tools.

Use when: housing/rental/real-estate tracking is added.

Status: placeholder.

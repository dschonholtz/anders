# Anders tool index

Small task-specific tools live here. Keep this index short so an agent can quickly choose the right tool.

## Planned tools

### `anders-day`

Purpose: create/check daily briefing folders in the private data repo.

Use when: starting a new day, ensuring required files exist.

### `anders-google`

Purpose: Google auth/email/calendar orchestration using official Google tooling where possible.

Use when: collecting Gmail or Google Calendar data.

Status: design pending. Prefer official Google CLI/App Script/clasp paths before custom API wrappers.

### `anders-linkedin`

Purpose: Official LinkedIn Developer API/OAuth access plus conservative LinkedIn signal handling.

Use when: authorizing/querying LinkedIn APIs or extracting LinkedIn follow-up signals without scraping LinkedIn.

Docs: `tools/anders-linkedin/README.md`

Status: LinkedIn app created; token flow/product scopes pending local secret + approved scopes.

### `anders-brief`

Purpose: render morning briefs from private repo artifacts.

Use when: preparing the 7 AM morning brief.

### `anders-housing`

Purpose: future housing data collection/analysis tools.

Use when: housing/rental/real-estate tracking is added.

Status: placeholder.

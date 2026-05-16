# anders

Open-source tooling for a file-backed personal assistant briefing system.

`anders` contains reusable code, schemas, templates, and docs. It should not contain personal data, tokens, raw emails, or private briefing artifacts.

Private daily data belongs in a separate data repo such as `anders-life`.

## Intended flow

```bash
anders collect --date today --data-repo ~/repos/anders-life
anders summarize --date today --data-repo ~/repos/anders-life
```

OpenClaw/Codex can invoke the CLI, then read generated briefing files from the private data repo.

## Tool architecture

Anders should be a toolbox of small task-specific CLIs, not one giant command with sprawling docs. See `docs/tool-architecture.md` and `tools/index.md`.

Implemented task tools:

- `anders-google` — read-only/dry-run Gmail + Google Calendar ingestion using official Google API client libraries. See `tools/anders-google/README.md`.
- `anders-md-pdf` — render local Markdown drafts and briefing notes to polished PDFs. See `tools/anders-md-pdf/README.md`.

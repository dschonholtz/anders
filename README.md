# anders

Open-source tooling for a file-backed personal assistant briefing system.

`anders` contains reusable code, schemas, templates, and docs. It should not contain personal data, tokens, raw emails, or private briefing artifacts.

Private daily data belongs in a separate data repo such as `anders-life`.

## Intended flow

```bash
export ANDERS_DATA_REPO=~/repos/anders-life
anders init-day --date today
anders collect-gmail --date today --query 'newer_than:1d'
anders collect-calendar --date today
anders extract-linkedin --date today
```

OpenClaw/Codex can invoke the CLI, then read generated briefing files from the private data repo.

See `docs/source-adapters.md` for Google email/calendar and LinkedIn notification extraction notes.

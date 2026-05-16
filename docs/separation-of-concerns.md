# Separation of concerns

## Public repo: `anders`

Owns reusable tooling:

- CLI and source adapters
- schemas
- templates
- tests
- docs
- anonymized examples

Never commit personal data, real raw source exports, OAuth tokens, cookies, or secrets.

## Private data repo: `anders-life`

Owns Doug-specific state:

- daily and weekly briefings
- goals and follow-ups
- normalized source outputs
- people/project context
- private configuration without secrets

Prefer committing summaries and source metadata. Keep raw full-content exports encrypted or outside git.

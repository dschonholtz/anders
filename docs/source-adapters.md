# Source adapters

Anders keeps source access in narrow adapters that write normalized artifacts into a private data repo.

## Data repo

Set a private data repo path with either:

```bash
export ANDERS_DATA_REPO=/Users/douglasschonholtz/repos/anders-life
```

or pass `--data-repo` on each command.

## Google auth

The Google adapters expect an OAuth access token with the needed scopes.

Recommended local auth shape:

```bash
gcloud auth login --update-adc \
  --scopes=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/calendar.readonly,openid,email
```

Then Anders can use the default token command:

```bash
anders collect-gmail --date today --query 'newer_than:1d'
anders collect-calendar --date today
```

If you manage tokens another way:

```bash
GOOGLE_ACCESS_TOKEN=... anders collect-gmail --date today
anders collect-calendar --token-command './scripts/print-google-token'
```

## Gmail

```bash
anders collect-gmail \
  --date today \
  --query 'newer_than:1d -category:promotions' \
  --max-results 25
```

Outputs:

- `briefings/days/YYYY-MM-DD/raw/email.jsonl`
- `briefings/days/YYYY-MM-DD/email.md`

By default, the Gmail adapter uses metadata/snippets. Use `--include-body` only when you intentionally want fuller content in local artifacts.

## Google Calendar

```bash
anders collect-calendar --date today
```

Outputs:

- `briefings/days/YYYY-MM-DD/raw/calendar.jsonl`
- `briefings/days/YYYY-MM-DD/calendar.md`

## LinkedIn

There is no broad official LinkedIn CLI and direct messaging APIs are restricted. Anders starts with LinkedIn notification extraction from email:

```bash
anders extract-linkedin --date today
```

This reads `raw/email.jsonl` and writes:

- `briefings/days/YYYY-MM-DD/raw/linkedin-notifications.jsonl`
- `briefings/days/YYYY-MM-DD/linkedin.md`

This is intentionally conservative: it treats LinkedIn email notifications as signals and leaves actual LinkedIn actions/manual replies to Doug.

## Privacy

- Do not commit secrets, OAuth refresh tokens, browser cookies, or passwords.
- Prefer metadata/summaries over raw full bodies.
- Keep raw full-content exports encrypted or out of git unless explicitly needed.

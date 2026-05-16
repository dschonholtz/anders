# anders-linkedin

Small helper area for official LinkedIn API access for Anders.

This tool is intentionally narrow. It should not scrape LinkedIn. It should only use official LinkedIn Developer APIs and OAuth tokens Doug authorizes.

## Current Anders app

Public/non-secret app metadata:

- App name: Anders
- Client ID: `78u88p6m85j9ry`

Secrets/tokens belong in the private data repo (`anders-life`) or local environment, never in this public repo.

## OAuth endpoints

LinkedIn OAuth authorization endpoint:

```txt
https://www.linkedin.com/oauth/v2/authorization
```

LinkedIn OAuth token endpoint:

```txt
https://www.linkedin.com/oauth/v2/accessToken
```

## Setup checklist

1. In the LinkedIn Developer app, add a redirect URL. Recommended local value:

   ```txt
   http://localhost:8080/callback
   ```

2. Store the client secret locally, not in git. Example:

   ```bash
   mkdir -p ~/repos/anders-life/private-config/linkedin
   printf '%s' 'PASTE_SECRET_HERE' > ~/repos/anders-life/private-config/linkedin/client-secret.local
   chmod 600 ~/repos/anders-life/private-config/linkedin/client-secret.local
   ```

3. Confirm which product/scopes are available in the app's Products/Auth pages.

Possible scopes depend on approved products. Examples:

- OpenID/basic sign-in: `openid profile email`
- Member Data Portability, if eligible/approved: `r_dma_portability_self_serve`

## Auth URL shape

Replace `SCOPE` with the product scope you are testing:

```bash
CLIENT_ID=78u88p6m85j9ry
REDIRECT_URI='http://localhost:8080/callback'
SCOPE='openid profile email'
STATE="anders-$(date +%s)"
python3 - <<'PY'
import os, urllib.parse
params = {
    'response_type': 'code',
    'client_id': os.environ['CLIENT_ID'],
    'redirect_uri': os.environ['REDIRECT_URI'],
    'scope': os.environ['SCOPE'],
    'state': os.environ['STATE'],
}
print('https://www.linkedin.com/oauth/v2/authorization?' + urllib.parse.urlencode(params))
PY
```

After authorization, LinkedIn redirects to the redirect URI with `?code=...&state=...`. Exchange that code for a token via the token endpoint.

## Token exchange shape

```bash
CLIENT_ID=78u88p6m85j9ry
CLIENT_SECRET="$(cat ~/repos/anders-life/private-config/linkedin/client-secret.local)"
REDIRECT_URI='http://localhost:8080/callback'
CODE='PASTE_AUTH_CODE'

curl -sS -X POST 'https://www.linkedin.com/oauth/v2/accessToken' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode grant_type=authorization_code \
  --data-urlencode code="$CODE" \
  --data-urlencode redirect_uri="$REDIRECT_URI" \
  --data-urlencode client_id="$CLIENT_ID" \
  --data-urlencode client_secret="$CLIENT_SECRET"
```

Do not paste resulting access tokens into chat or public files.

## Query posture

- Use official endpoints only.
- Store normalized outputs in `anders-life/briefings/days/YYYY-MM-DD/raw/`.
- Avoid broad token exposure to unrelated Codex tasks.

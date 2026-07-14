# Credentials configuration

## Required

### DeepSeek

```bash
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash
```

Used by the Python sidecar for all LLM endpoints.

### Google Sheets (n8n OAuth)

1. n8n → Credentials → Google Sheets OAuth2
2. Authorize an account that can edit the CRM spreadsheet
3. Assign to all Google Sheets nodes

### Langfuse

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://langfuse-web:3000
ENVIRONMENT=development
```

Sidecar connects on startup; auth failure is logged as a warning and the service continues.

## Production required

### HubSpot (n8n OAuth — repo default)

1. n8n → Credentials → HubSpot OAuth2
2. Assign to **HubSpot Upsert Contact** (and any HubSpot email HTTP nodes that use the credential)

Repo JSON uses placeholder `HUBSPOT_CREDENTIAL_ID` (`hubspotOAuth2Api`, upsert). Re-bind after import.

**Optional variant:** HubSpot Private App token — do not commit real credential IDs.

**Data strategy:** Google Sheets is the **system of record** for score, routing, review, and email drafts. HubSpot receives base Contact fields (email, name, company, role) and, after human **Assign**, an email **DRAFT** activity. Custom HubSpot properties for score are not written by default.

### Slack (n8n OAuth — repo default)

1. n8n → Credentials → Slack OAuth2
2. Invite the bot to the target channel
3. Set `SLACK_CHANNEL_ID` (env or node)

Placeholder: `SLACK_CREDENTIAL_ID`.

Used for high-score / review / error / daily / weekly / Calendly / booking messages.

**Interactivity (Block Kit buttons):**

1. api.slack.com → App → **Interactivity & Shortcuts** → ON
2. Request URL: `https://<n8n-host>/webhook/slack-interactions`
3. Signing Secret → `SLACK_SIGNING_SECRET` in n8n env
4. Optional `SLACK_ADMIN_USERS` (comma-separated Slack user IDs; empty = allow all in dev)
5. Import and activate **B2B Lead Slack Actions**

See [SLACK_ACTIONS_SETUP.md](SLACK_ACTIONS_SETUP.md).

## Optional

### Tally signing

1. Tally form → Webhooks → enable signing secret
2. `TALLY_WEBHOOK_SIGNING_KEY=<secret>` in n8n env
3. Intake uses `rawBody`; verification is **fail-closed** when a key is configured incorrectly / missing while enforced

### Hunter.io

Optional domain enrichment: `HUNTER_API_KEY` and Enrichment workflow HTTP node with `onError: continueErrorOutput`.

### Calendly

- Static book link: `config_main.calendly_url`
- Webhooks: `CALENDLY_WEBHOOK_SIGNING_KEY` — see [CALENDLY_SETUP.md](CALENDLY_SETUP.md)

Empty signing key skips verification (**development only**).

## Security

Never commit `.env`. Never put API keys in Google Sheets.

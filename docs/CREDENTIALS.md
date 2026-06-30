# Credentials Configuration

## Required

### DeepSeek

```
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash
```

Used by Python sidecar for enrichment and scoring.

### Google Sheets (n8n OAuth)

1. n8n → Credentials → Google Sheets OAuth2
2. Authorize with Google account that owns or can edit the spreadsheet
3. Assign to all Google Sheets nodes in workflows

### Langfuse

```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://langfuse-web:3000
ENVIRONMENT=development
```

Python service connects on startup; warns if auth fails but continues.

## Production required

### HubSpot (n8n OAuth)

1. n8n → Credentials → HubSpot OAuth2
2. Assign to **HubSpot Upsert Contact** node in CRM Sync workflow

**Custom properties** (create in HubSpot before production):

| Property             | Type   | Purpose           |
| -------------------- | ------ | ----------------- |
| `lead_score`         | Number | AI score          |
| `correlation_id`     | Text   | Trace correlation |
| `recommended_action` | Text   | Routing decision  |

### Slack (n8n OAuth)

1. n8n → Credentials → Slack OAuth2
2. Invite bot to target channel
3. Set channel ID in nodes or `SLACK_CHANNEL_ID` env var

Used for: high-score alerts, review reminders, error alerts, daily summary.

## Optional

### Tally

No credential needed — uses webhook URL configured in Tally dashboard.

### Google Forms

Requires Apps Script webhook bridge (see [FIELD_MAPPING.md](FIELD_MAPPING.md)). Posts to `/webhook/google-forms-lead`.

### Clearbit / Hunter.io (domain enrichment)

Optional HTTP enrichment APIs. To enable:

1. Add API key to `.env`: `HUNTER_API_KEY=...`
2. Add HTTP Request node after **Domain Enrichment** in Enrichment Scoring workflow
3. Set `onError: continueErrorOutput` — failures degrade to `enrichment_status=partial`

Example Hunter domain search:

```
GET https://api.hunter.io/v2/domain-search?domain={{ $json.company_domain }}&api_key=YOUR_KEY
```

### Calendly

First version uses static URL from `config_main.calendly_url`. No API credential required.

### Discord / Telegram

Not wired in default workflows. Extend **Build Notification Payload** node to add channels from `config_notifications`.

## n8n internal Postgres

```
POSTGRES_USER=n8n_user
POSTGRES_PASSWORD=change_me
POSTGRES_DB=n8n_db
```

Used only for n8n runtime state — not for business leads.

## Security

Never commit `.env` files. Never store API keys in Google Sheets.

# Installation Guide

## Prerequisites

- Docker and Docker Compose v2.20+
- Sibling repo `platform-n8n` with shared n8n runtime
- External Docker networks `proxy_network` and `n8n_platform`
- Google Cloud project with Sheets API enabled
- DeepSeek API key
- Tally account (free tier) for form intake

## 1. Start shared platform n8n

```bash
cd ../platform-n8n
cp .env.example .env
./scripts/ensure-networks.sh
docker compose -f docker/compose.yml up -d
```

n8n UI: http://localhost:5678

## 2. Configure CRM project

```bash
cd ../crm-workflow
cp .env.example .env
# Edit .env — DeepSeek, Langfuse, GOOGLE_SHEETS_DOCUMENT_ID, etc.
```

Create and share the spreadsheet: [SHEETS_SETUP.md](SHEETS_SETUP.md).  
Confirm **`prompt_registry` has all 6 prompt rows** (template CSV); append missing rows if your live sheet is older.

## 3. Start CRM sidecar

```bash
docker compose -f docker/compose.yml up -d --build
```

| Service | URL | Notes |
|---------|-----|-------|
| n8n (platform) | http://localhost:5678 | Shared editor |
| Python AI | http://localhost:8002/health | CRM LLM sidecar |

```bash
curl http://localhost:8002/health
curl http://localhost:8002/prompts
```

`/prompts` should list six keys including `sales_memo`, `outbound_email`, `weekly_insights`.

Sidecar deploy details: [DEPLOY.md](DEPLOY.md).

## 4. Import n8n workflows

Import into **shared n8n** (Settings → Import from File), preferably in this order:

1. `workflows/B2B Lead Error Handler.json`
2. `workflows/B2B Lead Enrichment Scoring.json`
3. `workflows/B2B Lead CRM Sync Notification.json`
4. `workflows/B2B Lead Intake.json`
5. `workflows/B2B Lead Daily Summary.json`
6. `workflows/B2B Lead Weekly Summary.json`
7. `workflows/B2B Lead Calendly Webhook.json`
8. `workflows/B2B Lead Booking Follow-up.json`
9. `workflows/B2B Lead Slack Actions.json`

### Post-import checklist

- [ ] Reconnect **Google Sheets**, **Slack**, **HubSpot** credentials on every node that needs them (JSON uses placeholders such as `GOOGLE_SHEETS_CREDENTIAL_ID` / `SLACK_CREDENTIAL_ID` / `HUBSPOT_CREDENTIAL_ID`).
- [ ] Confirm spreadsheet document id (`$env.GOOGLE_SHEETS_DOCUMENT_ID` or per-node value).
- [ ] **Settings → Error Workflow → `B2B Lead Error Handler`** on every main workflow (**import does not auto-bind**): Intake, Enrichment Scoring, CRM Sync Notification, Daily/Weekly Summary, Booking Follow-up, Calendly Webhook, Slack Actions.
- [ ] Spot-check error wiring: [ERROR_HANDLING_NODES.md](ERROR_HANDLING_NODES.md).
- [ ] Activate: **Intake**, **Daily Summary**, **Weekly Summary**, **Calendly Webhook**, **Booking Follow-up**, **Slack Actions** (and Error Handler as needed). Enrichment / CRM Sync are typically invoked via Execute Workflow.
- [ ] Sheets: `config_main.mode=test`; `prompt_registry` = 6 active rows.

Sidecar URLs used inside workflows: `http://crm_python_ai:8001/enrich`, `/score`, `/sales-memo`, `/outbound-email`, `/weekly-insights`, `/manual-review`.

## 5. Configure Tally webhook

1. Create a Tally form: Name, Email, Role, Company, Message.
2. Integrations → Webhooks → URL `https://your-n8n-domain/webhook/tally-lead`.
3. Map fields / trust via `config_sources` ([FIELD_MAPPING.md](FIELD_MAPPING.md)).
4. Optional signing: [CREDENTIALS.md](CREDENTIALS.md).

## 5b. Calendly

Follow [CALENDLY_SETUP.md](CALENDLY_SETUP.md). Summary: set `CALENDLY_WEBHOOK_SIGNING_KEY`, subscribe to `invitee.created` / `invitee.canceled` at `/webhook/calendly`, activate the Calendly workflow.

## 5c. Slack Actions

Follow [SLACK_ACTIONS_SETUP.md](SLACK_ACTIONS_SETUP.md). Summary: enable Interactivity → `https://your-n8n-domain/webhook/slack-interactions`, set `SLACK_SIGNING_SECRET`, activate **B2B Lead Slack Actions**.

## 6. Test run

1. `config_main.mode=test`
2. Submit a Tally test lead
3. Confirm `leads` row + enrichment/scoring fields
4. Confirm CRM and Slack **skipped** in test mode

Walkthrough: [RUN_EXAMPLE.md](RUN_EXAMPLE.md). Observability: [OBSERVABILITY.md](OBSERVABILITY.md).

## 7. Production

Set `config_main.mode=production`. See [TEST_PRODUCTION.md](TEST_PRODUCTION.md).

## CI/CD

Push to `main` builds/pushes the Python image to GHCR and can SSH-deploy the sidecar. Workflow JSON is **not** auto-imported — re-import manually after generator changes.

```bash
python3 scripts/generate_workflows.py
```

## Troubleshooting

- **Python won’t start**: `DEEPSEEK_API_KEY` in `.env`
- **No OTEL traces**: `proxy_network` + collector running
- **Langfuse empty**: keys/host; platform inject outbound traces
- **Webhook silent**: workflow Active? production webhook URL?
- **Sidecar unreachable from n8n**: both on `n8n_platform`
- **`/weekly-insights` 404**: rebuild sidecar from current source (`docker compose ... up -d --build`)

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

## 2. Clone and configure CRM sidecar

```bash
cd ../crm-workflow
cp .env.example .env
# Edit .env with your credentials
```

## 3. Start CRM sidecar

```bash
docker compose -f docker/compose.yml up -d --build
```

| Service | URL | Notes |
|---------|-----|-------|
| n8n (platform) | http://localhost:5678 | Shared workflow editor |
| Python AI | http://localhost:8002/health | CRM LLM sidecar |

Verify Python service:

```bash
curl http://localhost:8002/health
curl http://localhost:8002/prompts
```

## 4. Import n8n workflows

Import into **shared n8n** (platform) in this order (Settings → Import from File):

1. `workflows/B2B Lead Error Handler.json`
2. `workflows/B2B Lead Enrichment Scoring.json`
3. `workflows/B2B Lead CRM Sync Notification.json`
4. `workflows/B2B Lead Intake.json`
5. `workflows/B2B Lead Daily Summary.json`
6. `workflows/B2B Lead Weekly Summary.json`
7. `workflows/B2B Lead Calendly Webhook.json`
8. `workflows/B2B Lead Booking Follow-up.json`

After import:

- Open each workflow and reconnect credentials (Google Sheets, Slack, HubSpot)
- Replace `REPLACE_WITH_SHEET_ID` in Google Sheets nodes with your document ID
- **Settings → Error Workflow → `B2B Lead Error Handler`** on each main workflow (import does not auto-bind)
- Verify error branches per [ERROR_HANDLING_NODES.md](ERROR_HANDLING_NODES.md)
- Activate **B2B Lead Intake**, **B2B Lead Daily Summary**, **B2B Lead Weekly Summary**, **B2B Lead Calendly Webhook**, and **B2B Lead Booking Follow-up** workflows

Sidecar URLs in workflows: `http://crm_python_ai:8001/enrich`, `/score`, `/sales-memo`, and `/weekly-insights`

## 5. Configure Tally webhook

1. Create a Tally form with fields: Name, Email, Role, Company, Message
2. Go to Integrations → Webhooks
3. Set URL to: `https://your-n8n-domain/webhook/tally-lead`
4. Map fields in `config_sources` sheet (see [FIELD_MAPPING.md](FIELD_MAPPING.md))

## 5b. Configure Calendly webhook

1. Set `CALENDLY_WEBHOOK_SIGNING_KEY` in n8n environment (see [CREDENTIALS.md](CREDENTIALS.md))
2. Calendly → Integrations → Webhooks → add subscription
3. URL: `https://your-n8n-domain/webhook/calendly`
4. Events: `invitee.created`, `invitee.canceled`
5. Activate **B2B Lead Calendly Webhook** in n8n

## 6. Test run

1. Ensure `config_main.mode=test` in Google Sheets
2. Submit a test form via Tally
3. Check `leads` sheet for new row
4. Verify enrichment/scoring fields populated
5. Confirm CRM and Slack were **skipped** (test mode)

## 7. Production

Set `config_main.mode=production` in Google Sheets. See [TEST_PRODUCTION.md](TEST_PRODUCTION.md).

## CI/CD

Push to `main` triggers GitHub Actions to build and push the Python image to GHCR, then SSH deploy sidecar to `/home/deploy/projects/crm-workflow`.

Requires `platform-n8n` deployed on server. See [docker/DEPLOY.md](../docker/DEPLOY.md).

n8n workflow JSON is **not** auto-deployed — import manually after changes.

## Troubleshooting

- **Python service won't start**: Check `DEEPSEEK_API_KEY` in `.env`
- **No OTEL traces**: Ensure `proxy_network` exists and otel-collector is running
- **Langfuse not linking**: Verify platform n8n has `N8N_OTEL_TRACES_INJECT_OUTBOUND=true`
- **Workflow not triggering**: Check webhook URL and that Intake workflow is active
- **Sidecar unreachable from n8n**: Ensure both are on `n8n_platform` network

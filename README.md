# B2B Lead Automation Template

Reusable n8n workflows for B2B lead processing after form submission: Tally / Google Forms intake, Google Sheets as system of record, DeepSeek enrichment & scoring, HubSpot sync, Slack notifications, Calendly meeting updates, and scheduled digests.

**Chinese documentation:** [docs/zh/](docs/zh/)

## Architecture

```text
Tally/Google Forms → Intake → Enrichment & Scoring → CRM Sync & Notification
Calendly / Slack Actions / Daily & Weekly Summary / Booking Follow-up
Error Handler → error_logs (+ Slack alert when gated)
```

Full diagram and component roles: [docs/en/ARCHITECTURE.md](docs/en/ARCHITECTURE.md).  
Workflow catalog: [docs/en/WORKFLOWS.md](docs/en/WORKFLOWS.md).

## Quick start

1. Start shared n8n — see `../platform-n8n/docs/DEPLOY.md`
2. Copy `.env.example` → `.env` and fill secrets
3. Create Sheets from templates — [docs/en/SHEETS_SETUP.md](docs/en/SHEETS_SETUP.md) (**`prompt_registry` must have 6 rows**)
4. `docker compose -f docker/compose.yml up -d --build` (CRM sidecar)
5. Import all 9 workflows from `workflows/` (port 5678) — [docs/en/INSTALL.md](docs/en/INSTALL.md)
6. Re-bind credentials; set Error Workflow → **B2B Lead Error Handler**
7. `config_main.mode=test` → submit a test Tally lead

## Project structure

| Path | Purpose |
|------|---------|
| `workflows/` | n8n JSON exports (import manually) |
| `docker/` | Sidecar compose + env example |
| `python-service/` | FastAPI: `/enrich`, `/score`, `/sales-memo`, `/outbound-email`, `/weekly-insights`, `/manual-review` |
| `prompts/` | Versioned LLM prompts |
| `schemas/` | Lead JSON Schema |
| `sheets/template/` | Spreadsheet CSV templates |
| `scripts/generate_workflows.py` | Regenerate workflow JSON |
| `scripts/sync_workflows_from_export.py` | Sync UI exports → `workflows/` |
| `docs/en/` | English docs (default) |
| `docs/zh/` | Chinese docs |

## Observability

- **Jaeger:** n8n OTEL (`n8n-platform` / `n8n-crm-ai-service`)
- **Langfuse:** LLM generations (`crm-workflow`)
- **correlation_id** at intake + `X-Correlation-Id` to sidecar

Details: [docs/en/OBSERVABILITY.md](docs/en/OBSERVABILITY.md).

## Documentation (English)

| Doc | Topic |
|-----|--------|
| [ARCHITECTURE](docs/en/ARCHITECTURE.md) | System design |
| [WORKFLOWS](docs/en/WORKFLOWS.md) | Nine workflows |
| [INSTALL](docs/en/INSTALL.md) | Install & import |
| [DEPLOY](docs/en/DEPLOY.md) | Sidecar deploy |
| [SHEETS_SETUP](docs/en/SHEETS_SETUP.md) | Google Sheets |
| [CONFIG_REFERENCE](docs/en/CONFIG_REFERENCE.md) | Config keys & effects |
| [CREDENTIALS](docs/en/CREDENTIALS.md) | API keys & OAuth |
| [TEST_PRODUCTION](docs/en/TEST_PRODUCTION.md) | test vs production gates |
| [PROMPTS](docs/en/PROMPTS.md) | Prompt files & registry |
| [FIELD_MAPPING](docs/en/FIELD_MAPPING.md) | Form → schema |
| [ERROR_HANDLING](docs/en/ERROR_HANDLING.md) / [NODES](docs/en/ERROR_HANDLING_NODES.md) | Errors |
| [CALENDLY_SETUP](docs/en/CALENDLY_SETUP.md) | Calendly webhooks |
| [SLACK_ACTIONS_SETUP](docs/en/SLACK_ACTIONS_SETUP.md) | Block Kit actions |
| [RUN_EXAMPLE](docs/en/RUN_EXAMPLE.md) | E2E walkthrough |
| [OBSERVABILITY](docs/en/OBSERVABILITY.md) | Tracing |
| [CODE_NODE_MODES](docs/en/CODE_NODE_MODES.md) | Code node modes |
| [WORKFLOW_SYNC_FROM_EXPORT](docs/en/WORKFLOW_SYNC_FROM_EXPORT.md) | UI → repo sync |

## Regenerate workflows

```bash
python3 scripts/generate_workflows.py
```

Then re-import changed JSON and re-bind credentials + Error Workflow.

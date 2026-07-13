# B2B Lead Automation Template

A reusable n8n workflow template for B2B lead processing after form submission. Supports Tally (primary) and Google Forms (secondary) as intake sources, Google Sheets for data and configuration, DeepSeek for scoring/enrichment, HubSpot CRM sync, and Slack notifications.

## Architecture

```
Tally/Google Forms → Intake → Enrichment & Scoring → CRM Sync & Notification
                              ↓
Calendly Webhook → Update meeting status → Slack notify
                              ↓
                         Error Handler → error_logs + Slack alert
```

## Quick start

1. Start shared n8n: see `../platform-n8n/docs/DEPLOY.md`
2. Copy `.env.example` to `.env` and fill in credentials
3. Follow [docs/SHEETS_SETUP.md](docs/SHEETS_SETUP.md) to create Google Sheets
4. Run `docker compose -f docker/compose.yml up -d` (sidecar only)
5. Import workflows from `workflows/` into shared n8n (port 5678)
6. Connect credentials (Google Sheets, Slack, HubSpot)
7. Set `config_main.mode=test` and submit a test Tally form

## Project structure

| Path | Purpose |
|------|---------|
| `workflows/` | n8n workflow JSON exports (import manually) |
| `docker/` | Sidecar compose, env template, deploy guide |
| `python-service/` | FastAPI sidecar: `/enrich`, `/score`, `/sales-memo`, `/manual-review`, `/outbound-email`, `/weekly-insights` |
| `prompts/` | Versioned LLM prompt files (`.md` with frontmatter) |
| `schemas/` | Unified Lead JSON Schema |
| `sheets/template/` | CSV templates for Google Sheets initialization |
| `scripts/generate_workflows.py` | Regenerate workflow JSON after code changes |
| `docs/` | Setup and operation guides |

## Observability

- **Jaeger**: n8n OTEL spans (`n8n-platform` / `n8n-crm-ai-service`)
- **Langfuse**: LLM generations (`crm-workflow` tag)
- **correlation_id**: Business ID generated at intake, passed via `X-Correlation-Id` header
- **trace_id**: W3C traceparent from n8n OTEL, links Jaeger ↔ Langfuse

## Documentation

- [INSTALL.md](docs/INSTALL.md) — Docker setup and workflow import
- [SHEETS_SETUP.md](docs/SHEETS_SETUP.md) — Google Sheets initialization
- [CREDENTIALS.md](docs/CREDENTIALS.md) — API keys and OAuth setup
- [TEST_PRODUCTION.md](docs/TEST_PRODUCTION.md) — Mode switching
- [WORKFLOW_SYNC_FROM_EXPORT.md](docs/WORKFLOW_SYNC_FROM_EXPORT.md) — Sync UI exports to `workflows/`
- [CODE_NODE_MODES.md](docs/CODE_NODE_MODES.md) — Code 节点 `runOnceForAllItems` vs `runOnceForEachItem`
- [FIELD_MAPPING.md](docs/FIELD_MAPPING.md) — Form field → Lead Schema mapping
- [ERROR_HANDLING.md](docs/ERROR_HANDLING.md) — Error workflow behavior
- [ERROR_HANDLING_NODES.md](docs/ERROR_HANDLING_NODES.md) — Per-node On Error / Retry / wiring guide
- [PROMPTS.md](docs/PROMPTS.md) — Prompt file management
- [RUN_EXAMPLE.md](docs/RUN_EXAMPLE.md) — End-to-end test walkthrough

## Regenerate workflows

After editing `scripts/generate_workflows.py`:

```bash
python3 scripts/generate_workflows.py
```

Then re-import changed workflows in n8n.

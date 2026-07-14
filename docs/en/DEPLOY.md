# CRM sidecar deployment

Deploy the CRM Python AI sidecar. Shared n8n runs in `platform-n8n`.

## Networks

| Network | Purpose |
|---------|---------|
| `n8n_platform` | n8n → `http://crm_python_ai:8001/...` |
| `proxy_network` | OTEL / Langfuse / Jaeger |

## Prerequisites

- `platform-n8n` running
- Project `.env` with `DEEPSEEK_*`, `LANGFUSE_*`, `GOOGLE_SHEETS_DOCUMENT_ID`
- Sheets configured — [SHEETS_SETUP.md](SHEETS_SETUP.md)

## Local

```bash
cd /path/to/crm-workflow
cp .env.example .env   # or docker/.env.example per your layout
docker compose -f docker/compose.yml --env-file .env up -d --build
```

Health: http://localhost:8002/health  
Prompts: http://localhost:8002/prompts

## Production

Example path: `/home/deploy/projects/crm-workflow`

```bash
../platform-n8n/scripts/ensure-networks.sh
docker pull ghcr.io/nanlindev/crm-workflow/python-ai-service:latest
docker compose -f docker/compose.yml --env-file .env up -d
```

Or build from current source if GHCR lags features (e.g. `/weekly-insights`):

```bash
docker compose -f docker/compose.yml --env-file .env up -d --build
```

## Sidecar URLs (from n8n)

- `http://crm_python_ai:8001/enrich`
- `http://crm_python_ai:8001/score`
- `http://crm_python_ai:8001/sales-memo`
- `http://crm_python_ai:8001/outbound-email`
- `http://crm_python_ai:8001/weekly-insights`
- `http://crm_python_ai:8001/manual-review`
- `http://crm_python_ai:8001/health`

## n8n workflows

Import from `workflows/` — [INSTALL.md](INSTALL.md). Workflow JSON is not auto-deployed.

## GHCR image

`ghcr.io/nanlindev/crm-workflow/python-ai-service:latest`

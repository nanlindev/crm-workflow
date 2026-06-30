# CRM Project Deployment

Deploy the CRM Python sidecar. Shared n8n runs in `platform-n8n`.

## Networks

Sidecar joins **two** external networks:

| Network | Purpose |
|---------|---------|
| `n8n_platform` | Shared n8n calls `http://crm_python_ai:8001/enrich` / `/score` |
| `proxy_network` | OTEL → `otel-collector`, Langfuse → `langfuse-web` |

## Prerequisites

- `platform-n8n` running
- Project root `.env` with `DEEPSEEK_*`, `LANGFUSE_*`, `GOOGLE_SHEETS_DOCUMENT_ID`
- Google Sheets configured (see `docs/SHEETS_SETUP.md`)

## Local

```bash
cd /home/lotey/lindev/crm-workflow
cp docker/.env.example .env
docker compose -f docker/compose.yml --env-file .env up -d --build
```

Sidecar: http://localhost:8002/health

## Production

Path: `/home/deploy/projects/crm-workflow`

Push to `main` triggers GitHub Actions.

Manual:

```bash
cd /home/deploy/projects/crm-workflow
../platform-n8n/scripts/ensure-networks.sh
docker pull ghcr.io/nanlindev/crm-workflow/python-ai-service:latest
docker compose -f docker/compose.yml --env-file .env up -d
```

## n8n workflows

Import from `workflows/` into shared n8n (see `docs/INSTALL.md`).

Sidecar URLs:
- `http://crm_python_ai:8001/enrich`
- `http://crm_python_ai:8001/score`

## GHCR image

`ghcr.io/nanlindev/crm-workflow/python-ai-service:latest`

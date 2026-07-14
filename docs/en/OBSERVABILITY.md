# Observability

End-to-end tracing for n8n executions and LLM calls.

## Stack

| Piece | Role |
|-------|------|
| OpenTelemetry Collector | Receives OTLP from n8n and sidecar |
| Jaeger | Span UI (`n8n-platform`, `n8n-crm-ai-service`) |
| Langfuse | LLM generations (`crm-workflow` tag / resource attrs) |

Deploy OBS stacks on `proxy_network` (see sibling repos `otel-collector-stack`, `jaeger-stack`, `langfuse-stack`).

## Environment checklist

**platform-n8n**

- OTEL exporter pointing at `http://otel-collector:4318` (or your collector URL)
- Prefer `N8N_OTEL_TRACES_INJECT_OUTBOUND=true` so outbound HTTP carries W3C context

**crm sidecar** (see `.env` / compose)

- `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318`
- `OTEL_SERVICE_NAME=n8n-crm-ai-service`
- `LANGFUSE_HOST=http://langfuse-web:3000` (+ public/secret keys)

**NO_PROXY / no_proxy** should include internal DNS names such as:

```text
crm_python_ai,otel-collector,langfuse-web,n8n_app
```

so Docker DNS is not forced through an external HTTP proxy.

## Correlation model

| Id | Where | Use |
|----|-------|-----|
| `correlation_id` | Generated at Intake; stored on lead; header `X-Correlation-Id` to sidecar | Business search key in Sheets / logs |
| `trace_id` | W3C Trace Context from OTEL | Join Jaeger spans |
| `lead_id` | UUID on lead row | Langfuse metadata / Sheets |

## How to verify after a test lead

1. Sheets `leads` → copy `correlation_id`.
2. Jaeger → search service `n8n-platform` or `n8n-crm-ai-service` around execution time; filter/tag by correlation if exported.
3. Langfuse → find generation with matching `correlation_id` / `lead_id`; check `prompt_version` and `prompt_hash`.
4. Sidecar health: `curl http://localhost:8002/health` and `/prompts`.

## Troubleshooting

| Symptom | Check |
|---------|-------|
| No Jaeger spans | Collector up? Both services on `proxy_network`? OTEL endpoint correct? |
| No Langfuse generations | Keys/host; sidecar logs for Langfuse auth warnings |
| Spans without LLM link | Outbound inject / shared `traceparent`; confirm enrich/score ran |
| Sidecar 404 on `/weekly-insights` | Rebuild sidecar image from current `python-service` (route must exist) |

More: [ARCHITECTURE.md](ARCHITECTURE.md), [RUN_EXAMPLE.md](RUN_EXAMPLE.md).

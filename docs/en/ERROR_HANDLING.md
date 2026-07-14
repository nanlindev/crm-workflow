# Error handling

## Two-tier model

### Tier 1: Node-level (predictable errors)

Critical external nodes use **On Error → Continue (using error output)** with dedicated handler Code nodes. Full per-node reference: [ERROR_HANDLING_NODES.md](ERROR_HANDLING_NODES.md).

| Failure | Handler | Degradation |
|---------|---------|-------------|
| Config load | Handle Config Load Error | `mode=test`, empty notification rules |
| Sheets read (dedup) | Handle Read Leads Error | Skip dedup, treat as insert |
| Sheets write (intake) | Handle Update/Append Lead Error | Continue with failed status |
| LLM enrichment / scoring | Handle Enrichment/Scoring Failure | Fallbacks + `fallback_used` where applicable |
| HubSpot | Handle HubSpot Failure | `crm_status=failed` |
| Slack notify | Log Slack Notify Error | `notification_status=failed` |
| Daily/Weekly reads | Handle Summary/Weekly Read Error | Degraded metrics; Daily skips Slack gate |
| Weekly Append | Handle Append Weekly Metrics Error | End without hanging |

Handlers return flat objects with `_metadata.processing_stage` and `severity`.

### Tier 2: Global (unpredictable errors)

Unhandled crashes go to **B2B Lead Error Handler** (Error Trigger).

## Bind Error Workflow after import

JSON `errorWorkflow` is a **name**; n8n usually does **not** bind by ID on import. Set manually:

**Workflow Settings → Error Workflow → `B2B Lead Error Handler`**

Apply to:

- B2B Lead Intake  
- B2B Lead Enrichment Scoring  
- B2B Lead CRM Sync Notification  
- B2B Lead Daily Summary  
- B2B Lead Weekly Summary  
- B2B Lead Booking Follow-up  
- B2B Lead Calendly Webhook  
- B2B Lead Slack Actions  

## Retry defaults

HTTP Request, HubSpot, Slack: Retry On Fail ON, max 3 tries, 5000 ms between tries.

## Error Handler output

Writes `error_logs` (`workflow`, `execution_id`, `node`, `message`, `stack`, `correlation_id`, `retry_suggestion`, `timestamp`) and may Slack `error_alert` when gated.

## Recovering `correlation_id`

1. `leads` by time  
2. Jaeger by execution window  
3. Langfuse by `lead_id` metadata  

Intake writes `correlation_id` early to maximize recoverability.

## Regenerate after generator edits

```bash
python3 scripts/generate_workflows.py
```

Re-import JSON and re-bind credentials + Error Workflow.

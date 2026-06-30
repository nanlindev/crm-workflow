# Error Handling

## Two-tier model

### Tier 1: Node-level (predictable errors)

Critical external nodes use `onError: continueErrorOutput` with dedicated handler Code nodes:

| Failure | Handler | Degradation |
|---------|---------|-------------|
| Config load | Handle Config Load Error | `mode=test`, empty notification rules |
| LLM enrichment | Handle Enrichment Failure | Raw content fallback, `enrichment_status=failed` |
| LLM scoring | Handle Scoring Failure | `score=0`, `manual_review`, `fallback_used=true` |
| HubSpot sync | Handle HubSpot Failure | `crm_status=failed` |
| Slack notify | Log Slack Notify Error | `notification_status=failed` |
| Validation | Validation Failed End | No downstream execution |

Handler nodes return **flat objects** with the same shape as success paths plus `_metadata.processing_stage` and `severity`.

### Tier 2: Global (unpredictable errors)

Unhandled crashes route to **B2B Lead Error Handler** via n8n Error Trigger.

Each main workflow sets:

```json
"settings": {
  "errorWorkflow": "B2B Lead Error Handler"
}
```

## Error workflow output

Written to `error_logs` sheet:

| Column | Source |
|--------|--------|
| `workflow` | Failed workflow name |
| `execution_id` | n8n execution ID |
| `node` | Failed node name |
| `message` | Error message |
| `stack` | Stack trace |
| `correlation_id` | From error context if available |
| `retry_suggestion` | `manual` (default) |
| `timestamp` | ISO timestamp |

Also sends Slack critical alert to configured channel.

## correlation_id recovery

If crash occurs before correlation_id propagates:

1. Check `leads` sheet by timestamp
2. Search Jaeger by execution time
3. Search Langfuse by `lead_id` in metadata

Intake writes `correlation_id` to Sheets immediately after generation to maximize recoverability.

## Retry guidance

| Error type | Suggestion |
|------------|------------|
| LLM timeout | Auto-retry via HTTP node (`retryOnFail: true`, 5s wait) |
| HubSpot rate limit | Manual retry after cooldown |
| Sheets API limit | Manual retry or reduce batch size |
| Unknown crash | Check error_logs, fix root cause, re-trigger manually |

## Testing error handling

1. Temporarily break Python service URL → verify enrichment fallback
2. Set invalid HubSpot credential → verify `crm_status=failed`, notification still attempts
3. Add `throw new Error('test')` in a Code node → verify error_logs row + Slack alert

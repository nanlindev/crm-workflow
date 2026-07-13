# Error Handling

## Two-tier model

### Tier 1: Node-level (predictable errors)

Critical external nodes use **On Error → Continue (using error output)** with dedicated handler Code nodes. See the full per-node reference: [ERROR_HANDLING_NODES.md](ERROR_HANDLING_NODES.md).

| Failure | Handler | Degradation |
|---------|---------|-------------|
| Config load | Handle Config Load Error | `mode=test`, empty notification rules |
| Sheets read (dedup) | Handle Read Leads Error | Skip dedup, treat as insert |
| Sheets write (intake) | Handle Update/Append Lead Error | `processing_status=failed`, continue audit |
| Audit log write | Handle Audit Log Error | Bypass audit, continue enrichment |
| LLM enrichment | Handle Enrichment Failure | Raw content fallback, `enrichment_status=failed` |
| LLM scoring | Handle Scoring Failure | `score=0`, `manual_review`, `fallback_used=true` |
| Sheets score update | Handle Sheets Score Error | Continue to CRM sync |
| HubSpot sync | Handle HubSpot Failure | `crm_status=failed` |
| Slack notify | Log Slack Notify Error | `notification_status=failed` |
| Final status write | Handle Final Status Error | End gracefully |
| error_logs write | Handle error_logs Write Failure | Still send Slack alert |
| Summary read | Handle Summary Read Error | Empty degraded summary |
| Validation | Validation Failed End | No downstream execution |

Handler nodes return **flat objects** with `_metadata.processing_stage` and `severity`.

### Tier 2: Global (unpredictable errors)

Unhandled crashes route to **B2B Lead Error Handler** via n8n Error Trigger.

## Import后必做：绑定 Error Workflow

JSON export 中的 `errorWorkflow` 是 workflow **名称**，import 后 n8n 通常不会自动绑定 ID。请对每个主 workflow 手动设置：

**Workflow Settings → Error Workflow → `B2B Lead Error Handler`**

适用 workflow：

- B2B Lead Intake
- B2B Lead Enrichment Scoring
- B2B Lead CRM Sync Notification
- B2B Lead Daily Summary
- B2B Lead Weekly Summary
- B2B Lead Booking Follow-up
- B2B Lead Calendly Webhook

## Retry settings

HTTP Request、HubSpot、Slack 节点：

- **Retry On Fail**: ON
- **Max Tries**: 3
- **Wait Between Tries**: 5000 ms

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

Also sends Slack critical alert (with retry + error handler if Slack fails).

## correlation_id recovery

If crash occurs before correlation_id propagates:

1. Check `leads` sheet by timestamp
2. Search Jaeger by execution time
3. Search Langfuse by `lead_id` in metadata

Intake writes `correlation_id` to Sheets immediately after generation to maximize recoverability.

## Regenerating workflows

After editing error handling in the generator:

```bash
python3 scripts/generate_workflows.py
```

Then re-import changed workflow JSON files in n8n and re-bind credentials + Error Workflow.

## Testing error handling

1. Temporarily break Python service URL → verify enrichment fallback
2. Set invalid HubSpot credential → verify `crm_status=failed`, notification still attempts
3. Disconnect Google Sheets credential on Intake → verify `Handle Read Leads Error` degrades
4. Add `throw new Error('test')` in a Code node → verify error_logs row + Slack alert

See [ERROR_HANDLING_NODES.md](ERROR_HANDLING_NODES.md) for the complete per-node checklist.

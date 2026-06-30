# Test / Production Mode

Mode is controlled by `config_main.mode` in Google Sheets.

## test mode (default)

```
mode=test
```

| Step | Behavior |
|------|----------|
| Intake | Writes to `leads` sheet normally |
| Enrichment | Runs domain lookup + LLM `/enrich` |
| Scoring | Runs LLM `/score` + review/routing rules |
| HubSpot CRM | **Skipped** — `crm_status=skipped_test_mode` |
| Slack notifications | **Skipped** — `notification_status=skipped_test_mode` |
| Audit logs | Written normally |
| Error handler | Active — errors still logged and alerted |

Use test mode for:

- Demo and portfolio showcase
- Validating form → Sheets → AI pipeline
- Tuning scoring thresholds without CRM noise

## production mode

```
mode=production
```

| Step | Behavior |
|------|----------|
| CRM sync | Runs when `crm_gate_passed=true` |
| Slack | Sends notifications for matching events |
| HubSpot | Upserts contact by email |

### CRM gate conditions

All must be true:

- `mode=production`
- `review_status != pending_review`
- `recommended_action` in (`crm_sync`, `notify_only`)

### Notification gate

Slack sends only when `mode=production`. High-score and review-required events use templates from `config_notifications`.

## Switching modes

1. Open Google Sheets → `config_main` tab
2. Change `mode` value to `test` or `production`
3. No workflow restart needed — config is read on each execution

## Recommended rollout

1. Deploy stack with `mode=test`
2. Submit 3-5 test leads via Tally
3. Verify Sheets data, Langfuse traces, Jaeger spans
4. Tune `config_routing` and `config_review` thresholds
5. Connect HubSpot + Slack credentials
6. Set `mode=production`
7. Submit one real lead and verify end-to-end

## Rollback

Set `mode=test` immediately to stop CRM writes and Slack notifications without stopping intake.

# Test / production mode

Mode is controlled by `config_main.mode` in Google Sheets.

## test mode (default)

```text
mode=test
```

| Step | Behavior |
|------|----------|
| Intake | Writes `leads` normally |
| Enrichment / scoring | Runs LLM and rules |
| HubSpot | **Skipped** — `crm_status=skipped_test_mode` |
| Slack notifications | **Skipped** — `notification_status=skipped_test_mode` |
| First-touch draft send path | **Skipped** — `first_touch_status=skipped_test_mode` |
| Audit logs | Written |
| Error Handler | Logs errors; Slack alert only if `error_alert.enabled` **and** `mode=production` |

Use for pipeline validation and threshold tuning without CRM/Slack noise.

## production mode

```text
mode=production
```

| Step | Behavior |
|------|----------|
| CRM sync | When `crm_gate_passed=true` |
| Slack | When the matching `config_notifications.*.enabled=true` |
| HubSpot | Contact upsert; Assign path can add email DRAFT |
| First touch | Draft in Sheets (`draft_pending_review`); HubSpot DRAFT after Assign |

### CRM gate

All must be true:

- `mode=production`
- `review_status` not `pending_review`
- `recommended_action` in (`crm_sync`, `notify_only`)

Slack **Assign** → `crm_sync`; **Nurture** → `notify_only`. Both can trigger CRM Sync with `skip_notification=true`.

### Notification gate

Slack for lead events requires production + routing that allows notify (rejects / low-score paths often skip).

**Booking Follow-up:** production + `booking_reminder.enabled=true`. Test mode does not set `booking_reminder_sent`.

### Daily / Weekly summaries

| Workflow | Slack gate | When disabled / test |
|----------|------------|----------------------|
| Daily Summary | production **and** `daily_summary.enabled` | Build summary; **Skip Daily Slack** |
| Weekly Summary | production **and** `weekly_summary.enabled` | Build metrics + AI; **Skip Weekly Slack**; still **Append** `weekly_metrics` |

**Daily window:** cron 09:00 reports **yesterday UTC 00:00–24:00** (`created_at` / error `timestamp` prefix = yesterday’s UTC date).

High-score counts use `config_main.score_threshold_high` (default `80`).

## Switching

1. Sheets → `config_main` → change `mode`
2. No workflow restart required

## Rollout / rollback

Rollout: test → tune → connect HubSpot/Slack → one production lead.  
Rollback: set `mode=test` immediately (stops CRM/Slack without stopping intake).

See [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md).

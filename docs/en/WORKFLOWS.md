# Workflows

Nine n8n workflows in `workflows/`. Import order and activation: [INSTALL.md](INSTALL.md).

## Catalog

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **B2B Lead Error Handler** | Error Trigger | Global sink: `error_logs` + Slack `error_alert` |
| **B2B Lead Intake** | Webhooks `tally-lead` / `google-forms-lead` | Normalize, dedup, append/update `leads`, start Enrichment |
| **B2B Lead Enrichment Scoring** | Execute Workflow | Domain/Hunter, LLM enrich/score/sales-memo/review, sheet updates, call CRM Sync |
| **B2B Lead CRM Sync Notification** | Execute Workflow | CRM gate → HubSpot upsert; Slack Block Kit; optional outbound email draft |
| **B2B Lead Slack Actions** | Webhook `slack-interactions` | Assign / Junk / Nurture; Assign/Nurture may re-run CRM Sync with DRAFT email |
| **B2B Lead Calendly Webhook** | Webhook `calendly` | Signature check; match email; update meeting fields; Slack notify |
| **B2B Lead Booking Follow-up** | Schedule daily ~10:00 | Reminder for high-score `not_booked` leads past `booking_reminder_hours` |
| **B2B Lead Daily Summary** | Schedule daily 09:00 | Aggregate **yesterday UTC**; Slack if production + `daily_summary.enabled` |
| **B2B Lead Weekly Summary** | Schedule Friday 17:00 | Weekly metrics + AI insights; always append `weekly_metrics`; Slack gated |

## Intake → Enrichment → CRM Sync

```text
Intake → write leads → Execute Enrichment Scoring
  → /enrich, /score, optional /sales-memo, /manual-review
  → Execute CRM Sync Notification
      → HubSpot (production + crm_gate)
      → Slack (production + notification rules)
      → First-touch draft in Sheets when eligible
```

## HubSpot behavior

- **CRM Sync:** upsert Contact (email, name, company, role) when `crm_gate_passed`.
- **Sheets remain SoT** for score, routing, review, drafts.
- **Slack Assign / Nurture:** may call CRM Sync with `skip_notification=true`; then log outbound email as HubSpot **DRAFT** from sheet draft fields.

## Daily Summary window

Cron at 09:00 aggregates leads/errors whose `created_at` / `timestamp` start with **yesterday’s UTC date** (`YYYY-MM-DD`). Title `date` is that yesterday date—not “today so far”.

## Weekly Summary

- Builds metrics for the current UTC week (Monday → run time).
- Calls `POST /weekly-insights`.
- Appends one row to `weekly_metrics` even when Slack is skipped.
- Slack only if `mode=production` and `weekly_summary.enabled=true`.

## Slack Actions

| Button | Sheet effects |
|--------|----------------|
| **Assign** | `review_status=approved`, `lead_stage=sql`, `owner_id` / `reviewer`, then HubSpot + DRAFT |
| **Junk** | `review_status=rejected`, `recommended_action=reject`, `lead_stage=junk` |
| **Nurture** | `review_status=review_later`, `lead_stage=nurture`, optional CRM notify path |

## Sidecar URLs (from n8n)

```text
http://crm_python_ai:8001/enrich
http://crm_python_ai:8001/score
http://crm_python_ai:8001/sales-memo
http://crm_python_ai:8001/outbound-email
http://crm_python_ai:8001/weekly-insights
http://crm_python_ai:8001/manual-review
```

Gate details: [TEST_PRODUCTION.md](TEST_PRODUCTION.md), [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md).

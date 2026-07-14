# Workflow node error-handling handbook

Per-node On Error, Retry, and error-output wiring. After import, verify branches in the UI against this guide.

## Global conventions

| Setting | Applies to |
|---------|------------|
| **On Error → Stop Workflow** | Code, IF, Merge, Execute Workflow, Set |
| **On Error → Continue (using error output)** | Google Sheets, HTTP Request, HubSpot, Slack |
| **Retry On Fail = ON, Max Tries = 3, Wait = 5000 ms** | HTTP Request, HubSpot, Slack |
| **Retry On Fail = ON** (some Sheets) | Intake / Enrichment config / CRM final status |

### Workflow-level (required after import)

JSON `errorWorkflow` is a **name**. n8n usually does **not** bind it automatically. Set:

**Settings → Error Workflow → `B2B Lead Error Handler`**

On: Intake, Enrichment Scoring, CRM Sync Notification, Daily Summary, Weekly Summary, Booking Follow-up, Calendly Webhook, Slack Actions.

### Credential placeholders

Repo JSON uses `GOOGLE_SHEETS_CREDENTIAL_ID` / `SLACK_CREDENTIAL_ID` / `HUBSPOT_CREDENTIAL_ID`. Exports may rewrite real IDs—re-bind after import.

### Error outputs

- **Output 0**: success → normal path  
- **Output 1**: error → `Handle * Error` → rejoin main path  

Handlers read `$input.item.error`, set `*_error_message` / `_metadata`, and preserve lead context via `$('Upstream').first()?.json`.

---

## 1. B2B Lead Intake

Key Sheets reads/writes use Continue + error handlers (`Handle Read Leads Error`, Update/Append Lead Error, Audit Log Error). Dedup uses **Run Once for All Items**. Execute Enrichment Scoring is Stop on error (fail the run).

## 2. B2B Lead Enrichment Scoring

Config reads: per-table Normalize or Handle Error wrappers → `Build Global Config` (partial degrade). HTTP Enrich / Score / Sales-memo / Manual-review: Continue + handlers. `Update Lead Scores`: Continue. Execute CRM Sync: Stop.

## 3. B2B Lead CRM Sync Notification

CRM Gate → HubSpot Continue + handler; Slack Continue + handler; outbound email HTTP Continue + handler; final status Sheets Continue + handler.

## 4. B2B Lead Error Handler

Extract details → Append `error_logs` (Continue with fallback) → optional Slack `error_alert` when gated.

## 5. B2B Lead Daily Summary

| Node | On Error | Notes |
|------|----------|-------|
| Read Leads / Errors | Continue | → Handle Summary Read Error (`daily_gate_passed=false`) |
| Read config_* | Continue + retry | Wrapper defaults disable Slack |
| Build Daily Summary | Stop | `runOnceForAllItems` + `safeNodeAll`; **yesterday UTC** window; threshold from config |
| Slack Daily Report | Continue | → Log Slack Summary Error (preserves summary) |

**Gate:** `mode=production` and `daily_summary.enabled=true`.

**Topology:**

```text
Daily 9am → Read Leads → Read Errors
  → config_main → config_notifications → Load Daily Config
  → Build Daily Summary → Should Send Daily? → Slack / Skip → End
```

## 5b. B2B Lead Weekly Summary

| Node | On Error | Notes |
|------|----------|-------|
| Read Leads / Errors / Prior metrics | Continue | → Handle Weekly Read Error (degraded metrics, gate false) |
| Read config_* | Continue + retry | |
| HTTP Weekly Insights | Continue | → Handle Weekly AI Failure (metrics-only AI text) |
| Slack Weekly Report | Continue | → Log Slack Weekly Error **preserves Merge metrics** or Restore after success |
| Append Weekly Metrics | Continue | → Handle Append Weekly Metrics Error → End |

**Gate:** `mode=production` and `weekly_summary.enabled=true` (strict boolean). Metrics still append when Slack is skipped.

## 6. Booking Follow-up / 7. Slack Actions / 8. Calendly

See generator wiring: Sheets/Slack Continue + handlers; booking reminder and Slack interactivity gates documented in [TEST_PRODUCTION.md](TEST_PRODUCTION.md) and setup guides.

## Acceptance scenarios

| Scenario | Expected |
|----------|----------|
| Daily/Weekly in test | Aggregate; Skip Slack |
| Weekly Slack fails | Metrics still Append |
| Weekly Append fails | Handle error → End (no hang) |
| LLM enrich/score fail | Fallbacks; continue pipeline where designed |
| `/weekly-insights` 404 | Rebuild sidecar image |

Regenerate:

```bash
python3 scripts/generate_workflows.py
```

Overview: [ERROR_HANDLING.md](ERROR_HANDLING.md).

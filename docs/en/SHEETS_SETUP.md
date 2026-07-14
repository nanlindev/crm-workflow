# Google Sheets Setup

Business data and configuration live in one Google Spreadsheet with **10 tabs**.

## Create the spreadsheet

1. Create a new Google Spreadsheet.
2. Create tabs with these **exact** names and import the matching CSV (File → Import → Replace current sheet):

| Tab name | Template CSV |
|----------|--------------|
| `config_main` | [config_main.csv](../../sheets/template/config_main.csv) |
| `config_notifications` | [config_notifications.csv](../../sheets/template/config_notifications.csv) |
| `config_routing` | [config_routing.csv](../../sheets/template/config_routing.csv) |
| `config_review` | [config_review.csv](../../sheets/template/config_review.csv) |
| `config_sources` | [config_sources.csv](../../sheets/template/config_sources.csv) |
| `leads` | [leads.csv](../../sheets/template/leads.csv) |
| `audit_logs` | [audit_logs.csv](../../sheets/template/audit_logs.csv) |
| `error_logs` | [error_logs.csv](../../sheets/template/error_logs.csv) |
| `prompt_registry` | [prompt_registry.csv](../../sheets/template/prompt_registry.csv) |
| `weekly_metrics` | [weekly_metrics.csv](../../sheets/template/weekly_metrics.csv) |

## Share and document ID

1. Share the spreadsheet with the Google account / service identity used by n8n (Editor).
2. Copy the ID from `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`.
3. Set `GOOGLE_SHEETS_DOCUMENT_ID=SPREADSHEET_ID` in `.env` (or per Google Sheets node).

## `prompt_registry` (required 6 rows)

The live sheet must list **all six** prompts (do not stop at scoring/summary/review only):

| prompt_key | file_path | version | notes |
|------------|-----------|---------|-------|
| `lead_scoring` | `prompts/lead_scoring.md` | `crm-lead-scoring-v1.0.0` | Scoring |
| `lead_summary` | `prompts/lead_summary.md` | `crm-lead-summary-v1.0.0` | Enrichment |
| `manual_review` | `prompts/manual_review.md` | `crm-manual-review-v1.0.0` | Review text |
| `sales_memo` | `prompts/sales_memo.md` | `crm-sales-memo-v1.0.0` | Sales memo |
| `outbound_email` | `prompts/outbound_email.md` | `crm-outbound-email-v1.0.0` | First-touch draft |
| `weekly_insights` | `prompts/weekly_insights.md` | `crm-weekly-insights-v1.0.0` | Weekly AI |

Runtime loads prompts from container files; the sheet is the ops registry. Keep versions aligned with frontmatter. Details: [PROMPTS.md](PROMPTS.md), [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md).

## `config_main` defaults

See [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md). Common keys: `mode`, score thresholds, `calendly_url`, `booking_reminder_hours`, first-touch settings.

## `leads` tab

Stores the full [Lead Schema](../../schemas/lead.schema.json). Do not rename columns—workflows map to these headers.

### Deduplication

1. `contact_email` (case-insensitive)
2. Fallback `lead_hash` = sha256(email\|company_domain)

**n8n:** Dedup Lead Code node must use **Run Once for All Items**.

### Meeting / Calendly columns

| Column | Set by |
|--------|--------|
| `meeting_status` | Intake (`not_booked`); Calendly webhook |
| `meeting_time`, `calendly_event_uri`, `calendly_invitee_email` | Calendly webhook |

### Booking reminder columns

`booking_reminder_sent`, `booking_reminder_at` — Booking Follow-up after successful Slack reminder.

### Slack action columns

`owner_id`, `lead_stage` — Slack Actions (Assign / Junk / Nurture).

## `weekly_metrics` tab

Appended by **B2B Lead Weekly Summary** (Friday). One row per reporting week for WoW comparison (`metrics_json`, `ai_summary`, `fallback_used`, …).

## Do not store in Sheets

API secrets, OAuth tokens, or high-volume raw logs. Use `.env` / n8n credentials.

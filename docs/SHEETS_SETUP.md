# Google Sheets Setup

Business data and all configuration live in a single Google Spreadsheet with 10 tabs.

## Create the spreadsheet

1. Create a new Google Spreadsheet
2. Rename or create tabs matching these exact names:

| Tab name               | Template CSV                                                            |
| ---------------------- | ----------------------------------------------------------------------- |
| `config_main`          | [config_main.csv](../sheets/template/config_main.csv)                   |
| `config_notifications` | [config_notifications.csv](../sheets/template/config_notifications.csv) |
| `config_routing`       | [config_routing.csv](../sheets/template/config_routing.csv)             |
| `config_review`        | [config_review.csv](../sheets/template/config_review.csv)               |
| `config_sources`       | [config_sources.csv](../sheets/template/config_sources.csv)             |
| `leads`                | [leads.csv](../sheets/template/leads.csv)                               |
| `audit_logs`           | [audit_logs.csv](../sheets/template/audit_logs.csv)                     |
| `error_logs`           | [error_logs.csv](../sheets/template/error_logs.csv)                     |
| `prompt_registry`      | [prompt_registry.csv](../sheets/template/prompt_registry.csv)           |
| `weekly_metrics`       | [weekly_metrics.csv](../sheets/template/weekly_metrics.csv)             |

3. Import each CSV as the header row + default data (File → Import → Replace current sheet)

## Share with service account

1. Create a Google Cloud service account with Sheets API access
2. Share the spreadsheet with the service account email (Editor)
3. Configure n8n Google Sheets OAuth credential

## Document ID

Copy the spreadsheet ID from the URL:

```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
```

Set in `.env`:

```
GOOGLE_SHEETS_DOCUMENT_ID=SPREADSHEET_ID
```

Or update each Google Sheets node in n8n workflows.

## config_main defaults

| Key                      | Default       | Description                             |
| ------------------------ | ------------- | --------------------------------------- |
| `mode`                   | `test`        | `test` or `production`                  |
| `score_threshold_high`   | `80`          | High-score threshold                    |
| `score_threshold_low`    | `40`          | Low-score threshold                     |
| `score_gray_low`         | `40`          | Manual review zone lower bound          |
| `score_gray_high`        | `79`          | Manual review zone upper bound          |
| `calendly_url`           | (your link)   | Static booking URL for high-score leads |
| `source_trust_threshold` | `50`          | Below this triggers review              |
| `freemail_domains`       | gmail.com,... | Comma-separated freemail domains        |

## leads tab

The `leads` tab stores the full [Lead Schema](../schemas/lead.schema.json). Do not rename columns — n8n workflows map to these headers.

## Deduplication

Duplicates are detected by (in order):

1. `contact_email` (case-insensitive) — one row per person
2. `lead_hash` — `sha256(email|company_domain)` fallback (same as email for normal submissions)

`company_domain` and `source_url` are stored for enrichment/attribution but **not** used to merge rows (same company may have multiple contacts; form URLs are shared across submitters).

Updates preserve `lead_id` and refresh `updated_at`. On match, `_metadata.dedup_match_key` is `contact_email` or `lead_hash`.

**n8n:** The **Dedup Lead** Code node must use **Run Once for All Items** (not *Each Item*). `Read All Leads` outputs one item per sheet row; *Each Item* mode would run dedup N times and append N duplicate rows per submission.

## Meeting / Calendly columns

| Column | Values | Set by |
|--------|--------|--------|
| `meeting_status` | `not_booked`, `booked`, `canceled`, `rescheduled` | Intake (new leads → `not_booked`); Calendly webhook |
| `meeting_time` | ISO datetime | Calendly webhook |
| `calendly_event_uri` | Calendly event URI | Calendly webhook |
| `calendly_invitee_email` | Invitee email from Calendly | Calendly webhook |

Matching uses case-insensitive `contact_email` = Calendly invitee email.

## Booking reminder columns

| Column | Values | Set by |
|--------|--------|--------|
| `booking_reminder_sent` | `true` / empty | Booking Follow-up workflow after successful Slack reminder |
| `booking_reminder_at` | ISO datetime | Booking Follow-up workflow |

Threshold: `config_main.booking_reminder_hours` (default 24). Gate: `config_notifications.booking_reminder.enabled`.

## Slack action columns

| Column | Values | Set by |
|--------|--------|--------|
| `owner_id` | Slack user ID | Slack Actions workflow on **Assign** |
| `lead_stage` | `mql`, `sql`, `nurture`, `junk` | Slack Actions workflow |

Assign sets `review_status=approved`, `lead_stage=sql`, `owner_id` and `reviewer` to the Slack user. Junk sets `review_status=rejected`, `recommended_action=reject`, `lead_stage=junk`. Nurture sets `review_status=review_later`, `lead_stage=nurture`.

## weekly_metrics tab

Appended each Friday by **B2B Lead Weekly Summary**. One row per reporting week (`week_start` Monday through `week_end` run time). Used for week-over-week comparison and audit.

| Column | Description |
|--------|-------------|
| `week_start` / `week_end` | Reporting window (ISO dates) |
| `metrics_json` | Full aggregated metrics blob |
| `ai_summary` | LLM executive summary (or fallback text) |
| `source_breakdown_json` | Leads grouped by `source_type` |
| `fallback_used` | `true` when AI insights used deterministic fallback |

## Do NOT store in Sheets

- API secrets or OAuth tokens
- n8n credentials
- Large log volumes

These belong in `.env` or n8n credential store.

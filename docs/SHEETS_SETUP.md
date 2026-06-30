# Google Sheets Setup

Business data and all configuration live in a single Google Spreadsheet with 9 tabs.

## Create the spreadsheet

1. Create a new Google Spreadsheet
2. Rename or create tabs matching these exact names:

| Tab name | Template CSV |
|----------|-------------|
| `config_main` | [config_main.csv](../sheets/template/config_main.csv) |
| `config_notifications` | [config_notifications.csv](../sheets/template/config_notifications.csv) |
| `config_routing` | [config_routing.csv](../sheets/template/config_routing.csv) |
| `config_review` | [config_review.csv](../sheets/template/config_review.csv) |
| `config_sources` | [config_sources.csv](../sheets/template/config_sources.csv) |
| `leads` | [leads.csv](../sheets/template/leads.csv) |
| `audit_logs` | [audit_logs.csv](../sheets/template/audit_logs.csv) |
| `error_logs` | [error_logs.csv](../sheets/template/error_logs.csv) |
| `prompt_registry` | [prompt_registry.csv](../sheets/template/prompt_registry.csv) |

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

| Key | Default | Description |
|-----|---------|-------------|
| `mode` | `test` | `test` or `production` |
| `score_threshold_high` | `80` | High-score threshold |
| `score_threshold_low` | `40` | Low-score threshold |
| `score_gray_low` | `40` | Manual review zone lower bound |
| `score_gray_high` | `79` | Manual review zone upper bound |
| `calendly_url` | (your link) | Static booking URL for high-score leads |
| `source_trust_threshold` | `50` | Below this triggers review |
| `freemail_domains` | gmail.com,... | Comma-separated freemail domains |

## leads tab

The `leads` tab stores the full [Lead Schema](../schemas/lead.schema.json). Do not rename columns — n8n workflows map to these headers.

## Deduplication

Duplicates are detected by (in order):

1. `contact_email`
2. `company_domain`
3. `source_url`
4. `lead_hash`

Updates preserve `lead_id` and refresh `updated_at`.

## Do NOT store in Sheets

- API secrets or OAuth tokens
- n8n credentials
- Large log volumes

These belong in `.env` or n8n credential store.

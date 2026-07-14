# Configuration reference

All runtime business config lives in Google Sheets. Workflows re-read config on each execution (no n8n restart).

Templates: [`sheets/template/`](../../sheets/template/).

## `config_main`

| Key | Default | Effect |
|-----|---------|--------|
| `mode` | `test` | `test`: skip HubSpot, Slack, first-touch send paths. `production`: enable gated side effects |
| `score_threshold_high` | `80` | High-score band; Daily/Weekly high-score counts; booking reminder min score |
| `score_threshold_low` | `40` | Low-priority band lower bound |
| `score_gray_low` / `score_gray_high` | `40` / `79` | Manual-review gray zone |
| `sales_memo_min_score` | `80` | Min score to call `/sales-memo` |
| `first_touch_min_score` | `80` | Min score for outbound email draft path |
| `first_touch_sender_name` | `Your Team` | Signature display name in email prompt |
| `calendly_url` | Calendly link | Injected into Slack / email templates |
| `booking_reminder_hours` | `24` | Age before booking reminder |
| `source_trust_threshold` | `50` | Below → review pressure |
| `freemail_domains` | gmail.com,… | Freemail detection for scoring/review |
| `default_crm` | `hubspot` | CRM identifier (documentation / routing) |
| `slack_admin_users` | empty | Mirror of env; empty = allow all (dev) |

## `config_notifications`

| `event_type` | Typical use | Gate |
|--------------|-------------|------|
| `high_score_lead` | Slack high-score card | `mode=production` and `enabled=true` |
| `review_required` | Slack review notice | same |
| `error_alert` | Error Handler Slack | same |
| `booking_reminder` | Booking Follow-up Slack | same |
| `first_touch_email` | Outbound draft eligibility channel flag | use with first-touch score gates |
| `daily_summary` | Daily Slack digest | same |
| `weekly_summary` | Weekly Slack digest | same (metrics still appended when false) |

Columns: `severity`, `channels`, `enabled` (`true`/`false` string or boolean), `template_key`.

## `config_routing`

Score bands → `recommended_action`, `notify`, `crm_sync`:

| min–max | action | notify | crm_sync |
|---------|--------|--------|----------|
| 80–100 | `crm_sync` | true | true |
| 40–79 | `manual_review` | true | false |
| 0–39 | `reject` | false | false |

## `config_review`

| `rule_key` | Meaning when enabled |
|------------|----------------------|
| `gray_zone_score` | Score in gray band → pending review |
| `enrichment_incomplete` | Enrichment not complete → review |
| `missing_role` | Empty role → review |
| `low_trust_source` | Trust below threshold → review |

## `config_sources`

Per intake source: `source_type`, `source_name`, `field_mapping_json`, `trust_level`. Defaults for `tally` and `google_forms` ship in the CSV template. Label-based Normalize in Intake covers standard Tally forms; JSON is for extensibility.

## `prompt_registry`

Operational registry of prompt versions. **Sidecar loads prompts from `prompts/*.md` files, not from this sheet.** Keep the sheet aligned for ops and future Langfuse sync.

**Required: 6 rows** (see [PROMPTS.md](PROMPTS.md)):

| prompt_key | version | API |
|------------|---------|-----|
| `lead_scoring` | `crm-lead-scoring-v1.0.0` | `POST /score` |
| `lead_summary` | `crm-lead-summary-v1.0.0` | `POST /enrich` |
| `manual_review` | `crm-manual-review-v1.0.0` | `POST /manual-review` |
| `sales_memo` | `crm-sales-memo-v1.0.0` | `POST /sales-memo` |
| `outbound_email` | `crm-outbound-email-v1.0.0` | `POST /outbound-email` |
| `weekly_insights` | `crm-weekly-insights-v1.0.0` | `POST /weekly-insights` |

| Column | Purpose |
|--------|---------|
| `prompt_key` | Matches filename stem |
| `file_path` | e.g. `prompts/lead_scoring.md` |
| `version` | Must match frontmatter `version` |
| `hash` | Optional; can leave empty |
| `active` | Registry flag only — **does not gate** `load_prompt()` today |
| `notes` | Free text |

If your live sheet only has three rows, append `sales_memo`, `outbound_email`, and `weekly_insights` from [`prompt_registry.csv`](../../sheets/template/prompt_registry.csv).

## Related

- Mode behavior: [TEST_PRODUCTION.md](TEST_PRODUCTION.md)
- Sheet creation: [SHEETS_SETUP.md](SHEETS_SETUP.md)

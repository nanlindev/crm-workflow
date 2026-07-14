# Field Mapping

All form sources normalize to the [Lead Schema](../../schemas/lead.schema.json) before enrichment.

## Tally (primary)

Webhook path: `/webhook/tally-lead`

### Default field mapping

The **Normalize Tally Payload** Code node maps Tally fields by label (case-insensitive):

| Lead field | Tally field labels (first match wins) |
|------------|--------------------------------------|
| `contact_name` | name, contact_name, full_name |
| `contact_email` | email, contact_email |
| `contact_role` | role, contact_role, job_title |
| `company_name` | company, company_name |
| `raw_content` | message, details, project_description, how_can_we_help |
| `source_url` | formUrl from payload |
| `source_name` | formName from payload |
| `source_type` | `tally` (fixed) |
| `source_trust_level` | `80` (fixed) |

### Custom mapping via config_sources

For non-standard Tally forms, update `config_sources.field_mapping_json` in Google Sheets. The intake workflow reads this for future extensibility; the Code node uses label-based matching by default.

### Tally webhook payload example

```json
{
  "eventType": "FORM_RESPONSE",
  "data": {
    "formName": "B2B Contact",
    "formUrl": "https://tally.so/r/abc123",
    "fields": [
      { "label": "Name", "value": "Jane Doe" },
      { "label": "Email", "value": "jane@acme.com" },
      { "label": "Role", "value": "VP Engineering" },
      { "label": "Company", "value": "Acme Corp" },
      { "label": "Message", "value": "We need automation help..." }
    ]
  }
}
```

## Google Forms (secondary)

Webhook path: `/webhook/google-forms-lead`

Google Forms has no native webhook. Use Apps Script:

```javascript
function onFormSubmit(e) {
  var responses = e.values;
  var payload = {
    name: responses[1],
    email: responses[2],
    role: responses[3],
    company: responses[4],
    message: responses[5],
    formName: "B2B Contact Form",
    formUrl: FormApp.getActiveForm().getPublishedUrl()
  };
  UrlFetchApp.fetch("https://your-n8n-domain/webhook/google-forms-lead", {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload)
  });
}
```

| Lead field | Google Forms payload key |
|------------|-------------------------|
| `contact_name` | name |
| `contact_email` | email |
| `contact_role` | role |
| `company_name` | company |
| `raw_content` | message |
| `source_type` | `google_forms` (fixed) |
| `source_trust_level` | `70` (fixed) |

## Generated fields (Intake workflow)

| Field | Source |
|-------|--------|
| `lead_id` | UUID v4 |
| `correlation_id` | UUID v4 (observability) |
| `lead_hash` | SHA256(email\|domain\|source_url)[:16] |
| `company_domain` | Extracted from email if not provided |
| `created_at` / `updated_at` | ISO timestamp |

## Enrichment fields

| Field | Source |
|-------|--------|
| `domain_type` | Code node (corporate/personal/unknown) |
| `content_summary` | Python `/enrich` |
| `industry`, `company_size` | Python `/enrich` |
| `intent_signals` | Python `/enrich` + `/score` |

## Scoring fields

| Field | Source |
|-------|--------|
| `score` | Python `/score` (0-100) |
| `recommended_action` | Python `/score` + routing rules |
| `review_status` | Review rules Code node |

## Sales memo fields

| Field | Source |
|-------|--------|
| `sales_memo` | Python `/sales-memo` (JSON) — only when score ≥ `sales_memo_min_score` and not rejected |
| `sales_memo_status` | `complete` \| `skipped_low_score` \| `failed` |

## Meeting / Calendly fields

| Field | Source |
|-------|--------|
| `meeting_status` | Intake sets `not_booked` on new leads; Calendly webhook updates to `booked` / `canceled` / `rescheduled` |
| `meeting_time` | Calendly `payload.event.start_time` |
| `calendly_event_uri` | Calendly `payload.event.uri` |
| `calendly_invitee_email` | Calendly `payload.invitee.email` |

Webhook path: `/webhook/calendly` — see `B2B Lead Calendly Webhook` workflow.

### Calendly webhook payload (simplified)

```json
{
  "event": "invitee.created",
  "payload": {
    "event": {
      "uri": "https://api.calendly.com/scheduled_events/...",
      "start_time": "2026-07-10T14:00:00.000000Z"
    },
    "invitee": {
      "email": "jane@acme.com",
      "uri": "https://api.calendly.com/scheduled_events/.../invitees/..."
    }
  }
}
```

Unmatched invitees (email not in `leads`) are logged to `audit_logs` as `calendly_unmatched` without raising an error.

## Booking reminder fields

| Field | Source |
|-------|--------|
| `booking_reminder_sent` | `B2B Lead Booking Follow-up` sets `true` after successful Slack reminder |
| `booking_reminder_at` | ISO timestamp when reminder was sent |

Scheduled workflow: **B2B Lead Booking Follow-up** (daily 10:00). Eligible leads: `score >= score_threshold_high`, `meeting_status=not_booked`, older than `booking_reminder_hours` (default 24), and `booking_reminder_sent` not true. Controlled by `config_notifications` row `booking_reminder` and `config_main.mode`.

## Slack action fields

| Field | Source |
|-------|--------|
| `owner_id` | Slack user ID on **Assign** button (`assign_lead`) |
| `lead_stage` | `sql` (assign), `junk` (mark junk), `nurture` (nurture) |
| `review_status` | Updated by Slack Actions: `approved`, `rejected`, or `review_later` |
| `reviewer` | Slack user ID on assign |
| `reviewed_at` | ISO timestamp when a Slack action is applied |

Webhook path: `/webhook/slack-interactions` — see `B2B Lead Slack Actions` workflow. Buttons are emitted by CRM Sync Block Kit notifications (`assign_lead`, `mark_junk`, `nurture_lead`).

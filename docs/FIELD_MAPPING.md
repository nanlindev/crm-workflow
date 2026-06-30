# Field Mapping

All form sources normalize to the [Lead Schema](../schemas/lead.schema.json) before enrichment.

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

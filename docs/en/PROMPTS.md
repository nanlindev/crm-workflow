# Prompt management

LLM prompts live in `prompts/` as markdown with YAML frontmatter. They are **not** hardcoded in n8n.

## Files

```text
prompts/
├── lead_scoring.md
├── lead_summary.md
├── manual_review.md
├── sales_memo.md
├── outbound_email.md
└── weekly_insights.md
```

## Frontmatter

```markdown
---
version: crm-lead-scoring-v1.0.0
model: deepseek-chat
output_format: json
---

Prompt body with {variable} placeholders...
```

## Endpoints

| Endpoint | Prompt file | `prompt_key` |
|----------|-------------|--------------|
| `POST /enrich` | `lead_summary.md` | `lead_summary` |
| `POST /score` | `lead_scoring.md` | `lead_scoring` |
| `POST /manual-review` | `manual_review.md` | `manual_review` |
| `POST /sales-memo` | `sales_memo.md` | `sales_memo` |
| `POST /outbound-email` | `outbound_email.md` | `outbound_email` |
| `POST /weekly-insights` | `weekly_insights.md` | `weekly_insights` |

```bash
curl http://localhost:8002/prompts
```

## Loading

`python-service/prompt_loader.py` reads **files under `prompts/`** (Docker: `./prompts:/app/prompts:ro`). Google Sheets is not consulted at runtime.

## `prompt_registry` sheet (required 6 rows)

Keep the sheet in sync for operations and future Langfuse Prompt Management:

| prompt_key | file_path | version | active | notes |
|------------|-----------|---------|--------|-------|
| `lead_scoring` | `prompts/lead_scoring.md` | `crm-lead-scoring-v1.0.0` | true | Scoring |
| `lead_summary` | `prompts/lead_summary.md` | `crm-lead-summary-v1.0.0` | true | Enrichment |
| `manual_review` | `prompts/manual_review.md` | `crm-manual-review-v1.0.0` | true | Review |
| `sales_memo` | `prompts/sales_memo.md` | `crm-sales-memo-v1.0.0` | true | Memo |
| `outbound_email` | `prompts/outbound_email.md` | `crm-outbound-email-v1.0.0` | true | Email draft |
| `weekly_insights` | `prompts/weekly_insights.md` | `crm-weekly-insights-v1.0.0` | true | Weekly AI |

- Template: [`prompt_registry.csv`](../../sheets/template/prompt_registry.csv)
- If a live sheet only has the first three rows, **append** `sales_memo`, `outbound_email`, `weekly_insights`.
- `active` is a registry flag today; it does **not** disable `load_prompt()`.

## Changing a prompt

1. Edit the `.md` file and bump `version` in frontmatter.
2. Restart sidecar: `docker compose -f docker/compose.yml restart crm_python_ai`
3. Update `prompt_registry` version to match.
4. Confirm new `prompt_version` / `prompt_hash` in Langfuse.

No n8n JSON change required.

## Placeholders (summary)

- **lead_summary:** contact/company/source/`raw_content`/`external_enrichment`
- **lead_scoring:** enrichment outputs + source trust
- **manual_review:** score + `review_triggers`
- **sales_memo:** score + enrichment + recommended action
- **outbound_email:** memo fields + `sender_name` + `calendly_url`
- **weekly_insights:** `week_start`, `week_end`, `metrics_json`, `prior_week_metrics`

# Prompt Management

All LLM prompts live in `prompts/` as markdown files with YAML frontmatter. Prompts are **not** hardcoded in n8n nodes.

## File structure

```
prompts/
├── lead_scoring.md      # B2B lead scoring (0-100)
├── lead_summary.md      # Enrichment summary generation
└── manual_review.md     # Manual review explanation
```

## Frontmatter format

```markdown
---
version: crm-lead-scoring-v1.0.0
model: deepseek-chat
output_format: json
---

Prompt body with {variable} placeholders...
```

## Versioning

- Version string: `{domain}-{task}-v{major}.{minor}.{patch}`
- Hash: SHA256 of prompt body, first 16 hex chars
- Both tracked in Langfuse generation metadata

Check current versions:

```bash
curl http://localhost:8002/prompts
```

## Variable placeholders

### lead_summary.md

`{contact_name}`, `{contact_email}`, `{contact_role}`, `{company_name}`, `{company_domain}`, `{domain_type}`, `{source_type}`, `{source_name}`, `{raw_content}`, `{external_enrichment}`

### lead_scoring.md

`{contact_name}`, `{contact_email}`, `{contact_role}`, `{company_name}`, `{company_domain}`, `{industry}`, `{company_size}`, `{source_type}`, `{source_name}`, `{source_trust_level}`, `{content_summary}`, `{intent_signals}`, `{enrichment_status}`, `{enrichment_summary}`

### manual_review.md

`{contact_name}`, `{contact_role}`, `{contact_email}`, `{company_name}`, `{company_domain}`, `{score}`, `{score_reasoning}`, `{enrichment_status}`, `{review_triggers}`

## Python loading

`python-service/prompt_loader.py`:

- Parses frontmatter + body
- `load_prompt("lead_scoring")` → `PromptTemplate`
- `prompt.render(**vars)` → final prompt string
- Mounted read-only in Docker: `./prompts:/app/prompts:ro`

## prompt_registry sheet

Optional registry in Google Sheets tracks active prompt versions. Update manually when bumping versions:

| prompt_key | file_path | version | hash | active |
|------------|-----------|---------|------|--------|

## Langfuse migration path

Current: code-managed `.md` files with version/hash in traces.

Future: sync to Langfuse Prompt Management UI using matching version strings (`crm-lead-scoring-v1.0.0`). The `prompt_registry` sheet and Langfuse metadata fields are designed for this migration.

## Changing a prompt

1. Edit the `.md` file
2. Bump `version` in frontmatter
3. Restart Python service: `docker compose -f docker/compose.yml restart crm_python_ai`
4. Update `prompt_registry` sheet (optional)
5. Verify in Langfuse that new `prompt_version` and `prompt_hash` appear

No n8n workflow changes needed.

## Endpoints using prompts

| Endpoint | Prompt file |
|----------|-------------|
| `POST /enrich` | lead_summary.md |
| `POST /score` | lead_scoring.md |
| `POST /manual-review` | manual_review.md |

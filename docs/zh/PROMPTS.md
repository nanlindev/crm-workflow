# Prompt 管理

LLM prompt 以带 YAML frontmatter 的 markdown 形式存放在 `prompts/`。**不会**硬编码在 n8n 中。

## 文件

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

## 端点

| Endpoint | Prompt 文件 | `prompt_key` |
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

## 加载方式

`python-service/prompt_loader.py` 读取 **`prompts/` 下的文件**（Docker：`./prompts:/app/prompts:ro`）。运行时**不会**查询 Google Sheets。

## `prompt_registry` 表（必须 6 行）

保持表格同步，便于运维与未来 Langfuse Prompt Management：

| prompt_key | file_path | version | active | notes |
|------------|-----------|---------|--------|-------|
| `lead_scoring` | `prompts/lead_scoring.md` | `crm-lead-scoring-v1.0.0` | true | Scoring |
| `lead_summary` | `prompts/lead_summary.md` | `crm-lead-summary-v1.0.0` | true | Enrichment |
| `manual_review` | `prompts/manual_review.md` | `crm-manual-review-v1.0.0` | true | Review |
| `sales_memo` | `prompts/sales_memo.md` | `crm-sales-memo-v1.0.0` | true | Memo |
| `outbound_email` | `prompts/outbound_email.md` | `crm-outbound-email-v1.0.0` | true | Email draft |
| `weekly_insights` | `prompts/weekly_insights.md` | `crm-weekly-insights-v1.0.0` | true | Weekly AI |

- 模板：[`prompt_registry.csv`](../../sheets/template/prompt_registry.csv)
- 若线上表格只有前三行，请**追加** `sales_memo`、`outbound_email`、`weekly_insights`。
- `active` 目前仅为注册表标志；**不会**禁用 `load_prompt()`。

## 修改 prompt

1. 编辑 `.md` 文件并提升 frontmatter 中的 `version`。
2. 重启 sidecar：`docker compose -f docker/compose.yml restart crm_python_ai`
3. 将 `prompt_registry` 的 version 更新为一致。
4. 在 Langfuse 中确认新的 `prompt_version` / `prompt_hash`。

无需修改 n8n JSON。

## 占位符（摘要）

- **lead_summary：** contact/company/source/`raw_content`/`external_enrichment`
- **lead_scoring：** enrichment 输出 + source trust
- **manual_review：** score + `review_triggers`
- **sales_memo：** score + enrichment + recommended action
- **outbound_email：** memo 字段 + `sender_name` + `calendly_url`
- **weekly_insights：** `week_start`、`week_end`、`metrics_json`、`prior_week_metrics`

# Google Sheets 设置

业务数据与配置集中在一个 Google Spreadsheet，共 **10 个工作表（tab）**。

## 创建电子表格

1. 新建一个 Google Spreadsheet。
2. 创建名称**完全一致**的 tab，并导入对应 CSV（File → Import → Replace current sheet）：

| Tab 名称 | 模板 CSV |
|----------|----------|
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

## 共享与文档 ID

1. 将电子表格共享给 n8n 使用的 Google 账号 / 服务身份（Editor）。
2. 从 `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit` 复制 ID。
3. 在 `.env`（或各 Google Sheets 节点）中设置 `GOOGLE_SHEETS_DOCUMENT_ID=SPREADSHEET_ID`。

## `prompt_registry`（必须 6 行）

线上表格必须列出**全部六个** prompt（不要只停在 scoring/summary/review）：

| prompt_key | file_path | version | notes |
|------------|-----------|---------|-------|
| `lead_scoring` | `prompts/lead_scoring.md` | `crm-lead-scoring-v1.0.0` | Scoring |
| `lead_summary` | `prompts/lead_summary.md` | `crm-lead-summary-v1.0.0` | Enrichment |
| `manual_review` | `prompts/manual_review.md` | `crm-manual-review-v1.0.0` | Review text |
| `sales_memo` | `prompts/sales_memo.md` | `crm-sales-memo-v1.0.0` | Sales memo |
| `outbound_email` | `prompts/outbound_email.md` | `crm-outbound-email-v1.0.0` | First-touch draft |
| `weekly_insights` | `prompts/weekly_insights.md` | `crm-weekly-insights-v1.0.0` | Weekly AI |

运行时从容器内文件加载 prompt；表格是运维注册表。请保持 version 与 frontmatter 对齐。细节：[PROMPTS.md](PROMPTS.md)、[CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)。

## `config_main` 默认值

见 [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)。常用 key：`mode`、分数阈值、`calendly_url`、`booking_reminder_hours`、首触相关设置。

## `leads` tab

存储完整 [Lead Schema](../../schemas/lead.schema.json)。不要重命名列——工作流按这些表头映射。

### 去重

1. `contact_email`（不区分大小写）
2. 回退 `lead_hash` = sha256(email\|company_domain)

**n8n：** Dedup Lead Code 节点必须使用 **Run Once for All Items**。

### 会议 / Calendly 列

| 列 | 写入方 |
|----|--------|
| `meeting_status` | Intake（`not_booked`）；Calendly webhook |
| `meeting_time`、`calendly_event_uri`、`calendly_invitee_email` | Calendly webhook |

### 预约提醒列

`booking_reminder_sent`、`booking_reminder_at` — Booking Follow-up 在 Slack 提醒成功后写入。

### Slack 动作列

`owner_id`、`lead_stage` — Slack Actions（Assign / Junk / Nurture）。

## `weekly_metrics` tab

由 **B2B Lead Weekly Summary**（周五）追加。每周一行，用于 WoW 对比（`metrics_json`、`ai_summary`、`fallback_used` 等）。

## 不要存入 Sheets

API 密钥、OAuth token 或高频原始日志。请使用 `.env` / n8n credentials。

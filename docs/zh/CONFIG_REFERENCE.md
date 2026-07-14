# 配置参考

全部运行时业务配置保存在 Google Sheets。工作流每次执行都会重新读取配置（无需重启 n8n）。

模板：[`sheets/template/`](../../sheets/template/)。

## `config_main`

| Key | 默认值 | 效果 |
|-----|--------|------|
| `mode` | `test` | `test`：跳过 HubSpot、Slack、首触发送路径。`production`：启用经门控的副作用 |
| `score_threshold_high` | `80` | 高分区间；Daily/Weekly 高分计数；预约提醒最低分 |
| `score_threshold_low` | `40` | 低优先级区间下界 |
| `score_gray_low` / `score_gray_high` | `40` / `79` | 人工审核灰区 |
| `sales_memo_min_score` | `80` | 调用 `/sales-memo` 的最低分 |
| `first_touch_min_score` | `80` | 外发邮件草稿路径的最低分 |
| `first_touch_sender_name` | `Your Team` | 邮件 prompt 中的签名显示名 |
| `calendly_url` | Calendly 链接 | 注入 Slack / 邮件模板 |
| `booking_reminder_hours` | `24` | 发送预约提醒前的等待时长 |
| `source_trust_threshold` | `50` | 低于此值 → 审核压力 |
| `freemail_domains` | gmail.com,… | 评分/审核用的免费邮箱识别 |
| `default_crm` | `hubspot` | CRM 标识（文档/路由） |
| `slack_admin_users` | 空 | 环境变量镜像；空 = 允许全部（开发） |

## `config_notifications`

| `event_type` | 典型用途 | 门控 |
|--------------|----------|------|
| `high_score_lead` | Slack 高分卡片 | `mode=production` 且 `enabled=true` |
| `review_required` | Slack 审核通知 | 同上 |
| `error_alert` | Error Handler Slack | 同上 |
| `booking_reminder` | Booking Follow-up Slack | 同上 |
| `first_touch_email` | 外发草稿资格频道标志 | 与首触分数门控联用 |
| `daily_summary` | 日报 Slack 摘要 | 同上 |
| `weekly_summary` | 周报 Slack 摘要 | 同上（为 false 时仍会追加指标） |

列：`severity`、`channels`、`enabled`（`true`/`false` 字符串或布尔）、`template_key`。

## `config_routing`

分数区间 → `recommended_action`、`notify`、`crm_sync`：

| min–max | action | notify | crm_sync |
|---------|--------|--------|----------|
| 80–100 | `crm_sync` | true | true |
| 40–79 | `manual_review` | true | false |
| 0–39 | `reject` | false | false |

## `config_review`

| `rule_key` | 启用时的含义 |
|------------|--------------|
| `gray_zone_score` | 分数落在灰区 → 待审 |
| `enrichment_incomplete` | 富化未完成 → 待审 |
| `missing_role` | 职位为空 → 待审 |
| `low_trust_source` | 信任度低于阈值 → 待审 |

## `config_sources`

按入库来源：`source_type`、`source_name`、`field_mapping_json`、`trust_level`。CSV 模板中预置 `tally` 与 `google_forms`。Intake 中基于标签的 Normalize 覆盖标准 Tally 表单；JSON 用于扩展。

## `prompt_registry`

Prompt 版本的运维注册表。**Sidecar 从 `prompts/*.md` 文件加载 prompt，不从本表加载。** 请保持表格与文件对齐，便于运维与未来 Langfuse 同步。

**必须 6 行**（见 [PROMPTS.md](PROMPTS.md)）：

| prompt_key | version | API |
|------------|---------|-----|
| `lead_scoring` | `crm-lead-scoring-v1.0.0` | `POST /score` |
| `lead_summary` | `crm-lead-summary-v1.0.0` | `POST /enrich` |
| `manual_review` | `crm-manual-review-v1.0.0` | `POST /manual-review` |
| `sales_memo` | `crm-sales-memo-v1.0.0` | `POST /sales-memo` |
| `outbound_email` | `crm-outbound-email-v1.0.0` | `POST /outbound-email` |
| `weekly_insights` | `crm-weekly-insights-v1.0.0` | `POST /weekly-insights` |

| 列 | 用途 |
|----|------|
| `prompt_key` | 与文件名主名一致 |
| `file_path` | 例如 `prompts/lead_scoring.md` |
| `version` | 须与 frontmatter `version` 一致 |
| `hash` | 可选；可留空 |
| `active` | 仅注册表标志 — **当前不会**门控 `load_prompt()` |
| `notes` | 自由文本 |

若线上表格只有三行，请从 [`prompt_registry.csv`](../../sheets/template/prompt_registry.csv) 追加 `sales_memo`、`outbound_email`、`weekly_insights`。

## 相关

- 模式行为：[TEST_PRODUCTION.md](TEST_PRODUCTION.md)
- 表格创建：[SHEETS_SETUP.md](SHEETS_SETUP.md)

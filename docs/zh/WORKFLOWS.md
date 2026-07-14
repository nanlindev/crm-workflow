# 工作流

`workflows/` 下共有九个 n8n 工作流。导入顺序与激活说明见 [INSTALL.md](INSTALL.md)。

## 目录

| 工作流 | 触发 | 用途 |
|--------|------|------|
| **B2B Lead Error Handler** | Error Trigger | 全局下沉：`error_logs` + Slack `error_alert` |
| **B2B Lead Intake** | Webhook `tally-lead` / `google-forms-lead` | 归一化、去重、追加/更新 `leads`，启动 Enrichment |
| **B2B Lead Enrichment Scoring** | Execute Workflow | Domain/Hunter、LLM enrich/score/sales-memo/review、更新表格、调用 CRM Sync |
| **B2B Lead CRM Sync Notification** | Execute Workflow | CRM 门控 → HubSpot upsert；Slack Block Kit；可选外发邮件草稿 |
| **B2B Lead Slack Actions** | Webhook `slack-interactions` | Assign / Junk / Nurture；Assign/Nurture 可带着 DRAFT 邮件重跑 CRM Sync |
| **B2B Lead Calendly Webhook** | Webhook `calendly` | 签名校验；按邮箱匹配；更新会议字段；Slack 通知 |
| **B2B Lead Booking Follow-up** | 每日定时约 10:00 | 对超过 `booking_reminder_hours` 的高分 `not_booked` 线索发提醒 |
| **B2B Lead Daily Summary** | 每日定时 09:00 | 汇总**昨日 UTC**；生产环境且 `daily_summary.enabled` 时发 Slack |
| **B2B Lead Weekly Summary** | 周五定时 17:00 | 周指标 + AI 洞察；始终追加 `weekly_metrics`；Slack 门控 |

## Intake → Enrichment → CRM Sync

```text
Intake → write leads → Execute Enrichment Scoring
  → /enrich, /score, optional /sales-memo, /manual-review
  → Execute CRM Sync Notification
      → HubSpot (production + crm_gate)
      → Slack (production + notification rules)
      → First-touch draft in Sheets when eligible
```

## HubSpot 行为

- **CRM Sync：** 当 `crm_gate_passed` 时 upsert Contact（email、name、company、role）。
- **Sheets 仍为 SoT**（评分、路由、审核、草稿）。
- **Slack Assign / Nurture：** 可调用 CRM Sync 且 `skip_notification=true`；随后根据表格草稿字段将外发邮件记为 HubSpot **DRAFT**。

## Daily Summary 时间窗口

09:00 Cron 汇总 `created_at` / `timestamp` 前缀为**昨日 UTC 日期**（`YYYY-MM-DD`）的线索/错误。标题中的 `date` 是该昨日日期——不是「今天到目前为止」。

## Weekly Summary

- 统计当前 UTC 周（周一 → 运行时刻）的指标。
- 调用 `POST /weekly-insights`。
- 即使跳过 Slack，也会向 `weekly_metrics` 追加一行。
- 仅当 `mode=production` 且 `weekly_summary.enabled=true` 时发 Slack。

## Slack Actions

| 按钮 | 表格效果 |
|------|----------|
| **Assign** | `review_status=approved`，`lead_stage=sql`，`owner_id` / `reviewer`，然后 HubSpot + DRAFT |
| **Junk** | `review_status=rejected`，`recommended_action=reject`，`lead_stage=junk` |
| **Nurture** | `review_status=review_later`，`lead_stage=nurture`，可选 CRM 通知路径 |

## Sidecar URL（从 n8n 调用）

```text
http://crm_python_ai:8001/enrich
http://crm_python_ai:8001/score
http://crm_python_ai:8001/sales-memo
http://crm_python_ai:8001/outbound-email
http://crm_python_ai:8001/weekly-insights
http://crm_python_ai:8001/manual-review
```

门控细节：[TEST_PRODUCTION.md](TEST_PRODUCTION.md)、[CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)。

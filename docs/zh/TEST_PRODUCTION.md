# 测试 / 生产模式

模式由 Google Sheets 中的 `config_main.mode` 控制。

## test 模式（默认）

```text
mode=test
```

| 步骤 | 行为 |
|------|------|
| Intake | 正常写入 `leads` |
| Enrichment / scoring | 运行 LLM 与规则 |
| HubSpot | **跳过** — `crm_status=skipped_test_mode` |
| Slack 通知 | **跳过** — `notification_status=skipped_test_mode` |
| 首触草稿发送路径 | **跳过** — `first_touch_status=skipped_test_mode` |
| Audit logs | 写入 |
| Error Handler | 记录错误；仅当 `error_alert.enabled` **且** `mode=production` 时发 Slack 告警 |

用于在无 CRM/Slack 噪音的情况下验证流水线并调阈值。

## production 模式

```text
mode=production
```

| 步骤 | 行为 |
|------|------|
| CRM sync | 当 `crm_gate_passed=true` |
| Slack | 当对应 `config_notifications.*.enabled=true` |
| HubSpot | Contact upsert；Assign 路径可追加邮件 DRAFT |
| First touch | Sheets 中的草稿（`draft_pending_review`）；Assign 后写 HubSpot DRAFT |

### CRM 门控

须全部为真：

- `mode=production`
- `review_status` 不是 `pending_review`
- `recommended_action` 属于（`crm_sync`、`notify_only`）

Slack **Assign** → `crm_sync`；**Nurture** → `notify_only`。两者都可以带着 `skip_notification=true` 触发 CRM Sync。

### 通知门控

线索事件的 Slack 需要 production，且路由允许 notify（reject / 低分路径通常跳过）。

**Booking Follow-up：** production + `booking_reminder.enabled=true`。Test 模式不会设置 `booking_reminder_sent`。

### Daily / Weekly 摘要

| 工作流 | Slack 门控 | 禁用 / test 时 |
|--------|------------|----------------|
| Daily Summary | production **且** `daily_summary.enabled` | 构建 summary；**Skip Daily Slack** |
| Weekly Summary | production **且** `weekly_summary.enabled` | 构建 metrics + AI；**Skip Weekly Slack**；仍会 **Append** `weekly_metrics` |

**Daily 窗口：** Cron 09:00 报告**昨日 UTC 00:00–24:00**（`created_at` / 错误 `timestamp` 前缀 = 昨日 UTC 日期）。

高分计数使用 `config_main.score_threshold_high`（默认 `80`）。

## 切换

1. Sheets → `config_main` → 修改 `mode`
2. 无需重启工作流

## 上线 / 回滚

上线：test → 调参 → 连接 HubSpot/Slack → 一条生产线索。  
回滚：立即设 `mode=test`（停止 CRM/Slack，不停止入库）。

见 [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md)。

# Workflow 节点错误处理手册

逐节点说明 On Error、Retry On Fail 与 error output 连线。import 后若 UI 未显示错误分支，请按本手册核对。

## 全局约定

| UI 设置                                               | 适用节点                                    |
| ----------------------------------------------------- | ------------------------------------------- |
| **On Error → Stop Workflow**                          | Code、IF、Merge、Execute Workflow、Set      |
| **On Error → Continue (using error output)**          | Google Sheets、HTTP Request、HubSpot、Slack |
| **Retry On Fail = ON, Max Tries = 3, Wait = 5000 ms** | HTTP Request、HubSpot、Slack                |
| **Retry On Fail = ON, Wait = 5000 ms**（部分 Sheets） | Intake / Enrichment config / CRM final status |

### Workflow 级设置（import 后必做）

JSON 中的 `errorWorkflow` 为名称字符串，**import 后 n8n 通常不会自动绑定**。请对每个主 workflow 手动设置：

**Settings → Error Workflow → `B2B Lead Error Handler`**

适用：`B2B Lead Intake`、`B2B Lead Enrichment Scoring`、`B2B Lead CRM Sync Notification`、`B2B Lead Daily Summary`、`B2B Lead Weekly Summary`、`B2B Lead Booking Follow-up`、`B2B Lead Calendly Webhook`、`B2B Lead Slack Actions`

### Credential 占位符

仓库内 Google Sheets 节点使用 `GOOGLE_SHEETS_CREDENTIAL_ID` 占位符。**n8n export 会将 credential 解析为真实 ID**（如 `ITJp5Xyp9z6SOvYV`），属正常行为；重新 import 后需重新绑定凭证。

### Error output 连线

- **Output 0**：成功 → 正常下游
- **Output 1**：错误 → `Handle * Error` 节点 → 接回主链路

### 跨工作流契约（workflowInputs）

| 调用方 | 节点 | 接收方 trigger | 字段数 |
| ------ | ---- | -------------- | ------ |
| Intake | **Execute Enrichment Scoring** | Enrichment `When Executed by Another Workflow` | 17（含 lineage 可选字段） |
| Enrichment | **Execute CRM Sync** | CRM `When Executed by Another Workflow` | 24（11 核心 + 13 可选） |

Execute 节点使用 `mappingMode: defineBelow` + `??` 默认值；下游 trigger 声明 schema（含 `boolean` / `number` / `object` 类型）。

---

所有 `Handle * Error` Code 节点从 `$input.item.error` 解析 `errorMessage`，并写入对应的 `*_error_message` 字段与 `_metadata.error_message`。Handler 通过 `$('上游节点').first()?.json` 保留 lead 上下文，避免 Sheets/HTTP 响应覆盖业务对象。

---

## 1. B2B Lead Intake

| 节点                                         | On Error                | Retry | 错误分支 / 输出字段                              |
| -------------------------------------------- | ----------------------- | ----- | ------------------------------------------------ |
| Tally / Google Forms Webhook                 | Stop                    | OFF   | —                                                |
| Normalize \* / Generate IDs                  | Stop                    | OFF   | —（无 Merge Sources，双 webhook 直连 Generate）  |
| Validate Lead / Validation Passed?           | Stop                    | OFF   | false → Validation Failed End                    |
| **Read All Leads**                           | Continue (error output) | ON, 5s | → Handle Read Leads Error → `read_error_message` |
| Dedup Lead / Is Update?                      | Stop                    | OFF   | —                                                |
| **Update Lead**                              | Continue (error output) | ON, 5s | → Handle Update Lead Error → `sheets_error_message` |
| **Append Lead**                              | Continue (error output) | ON, 5s | → Handle Append Lead Error → `sheets_error_message` |
| **Set Normalize Lead**                       | Stop                    | OFF   | 四路 fan-in（无 Merge Upsert Result）            |
| **Write Audit Log**                          | Continue (error output) | ON, 5s | → Handle Audit Log Error → `audit_log_error_message` |
| Pass Lead To Enrichment                      | Stop                    | OFF   | Code 投影 17 字段                                |
| **Execute Enrichment Scoring**               | Stop                    | OFF   | workflowInputs 手动映射 → Enrichment trigger     |

**Sheets 写入：** `Update Lead` 使用 `operation: update` + `matchingColumns: ["lead_id"]`；仅新 lead 走 `Append Lead`。

---

## 2. B2B Lead Enrichment Scoring

| 节点                                                | On Error                | Retry      | 错误分支 / 输出字段                                      |
| --------------------------------------------------- | ----------------------- | ---------- | -------------------------------------------------------- |
| Read config_main / routing / notifications / review | Continue (error output) | ON, 5s（routing 3x） | `alwaysOutputData: false`；失败走 error output → Handle config_* Error |
| **Hold Lead**                                       | Stop                    | OFF        | 固定 lead 引用；`Build Global Config` 从 `$('Hold Lead')` 取数 |
| **Normalize config_***                            | Stop                    | OFF        | 成功路径 wrapper：`{ config_table, rows, load_failed, load_error_message }` |
| **Handle config_* Error**                           | Stop                    | OFF        | 解析 `$input.item.error`；wrapper 同上结构，`load_failed: true` |
| **Build Global Config**                             | Stop                    | OFF        | 读 4 个 wrapper + Hold Lead；partial degrade + `config_load_error_message` |
| **HTTP Enrich Lead**                                | Continue (error output) | ON, 3x, 5s | → Handle Enrichment Failure → `enrichment_error_message` |
| **HTTP Score Lead**                                 | Continue (error output) | ON, 3x, 5s | → Handle Scoring Failure → `scoring_error_message`       |
| Apply Review / Routing Rules                        | Stop                    | OFF        | —                                                        |
| **Update Lead Scores**                              | Continue (error output) | OFF        | → Handle Sheets Score Error → `sheets_error_message`     |
| **Normalize Enriched Lead** (Code)                  | Stop                    | OFF        | CRM 契约投影 + 降级 lineage 条件透传                   |
| **Execute CRM Sync**                                | Stop                    | OFF        | workflowInputs 手动映射（24 字段）→ CRM trigger        |

**Sheets 写入：** `Update Lead Scores` 使用 `operation: update` + `matchingColumns: ["lead_id"]`（不再 append 重复行）。

**Config 读取拓扑（串行 + per-table wrapper）：**

```text
Trigger → Hold Lead → Read main → (Norm|Handle) → Read routing → ... → Build Global Config → Domain
```

每路 read 成功/失败均输出统一 wrapper schema，error handler 与 Intake 一致从 `$input.item.error` 解析 `errorMessage`。

---

## 3. B2B Lead CRM Sync Notification

| 节点                           | On Error                | Retry      | 错误分支 / 输出字段                                    |
| ------------------------------ | ----------------------- | ---------- | ------------------------------------------------------ |
| **When Executed by Another Workflow** | Stop             | OFF        | workflowInputs schema（24 字段，含 `global_config` object） |
| CRM Gate / Code 逻辑           | Stop                    | OFF        | —                                                      |
| **Should Sync CRM?**           | Stop                    | OFF        | boolean `crm_gate_passed` 判断（strict）               |
| **Should Notify?**             | Stop                    | OFF        | `notification_mode === production`（strict）           |
| **HubSpot Upsert Contact**     | Continue (error output) | ON, 3x, 5s | → Handle HubSpot Failure → `crm_error_message`         |
| **Set Normalize CRM Result**   | Stop                    | OFF        | 三路 fan-in（拓扑汇合，无字段投影）                    |
| **Slack Notify**               | Continue (error output) | ON, 3x, 5s | → Log Slack Notify Error → `slack_error_message`       |
| **Set Normalize Notification Result** | Stop             | OFF        | 通知三路 fan-in → Update Final Status                  |
| **Update Final Status**        | Continue (error output) | ON, 5s     | → Handle Final Status Error → `sheets_error_message`   |

**Sheets 写入：** `Update Final Status` 使用 `operation: update` + `matchingColumns: ["lead_id"]`。

---

## 4. B2B Lead Error Handler

| 节点                                  | On Error                | Retry      | 错误分支 / 输出字段                                      |
| ------------------------------------- | ----------------------- | ---------- | -------------------------------------------------------- |
| Error Trigger / Extract Error Details | Stop                    | OFF        | —                                                        |
| **Write error_logs**                  | Continue (error output) | OFF        | → Handle error_logs Write Failure → `error_logs_error_message` |
| **Slack Error Alert**                 | Continue (error output) | ON, 3x, 5s | → Log Slack Error → `slack_error_message`                |

`Handle error_logs Write Failure` fallback：`$('Extract Error Details')`，确保 Slack 告警仍能发出。

---

## 5. B2B Lead Daily Summary

| 节点                          | On Error                | Retry      | 错误分支 / 输出字段                                      |
| ----------------------------- | ----------------------- | ---------- | -------------------------------------------------------- |
| Daily 9am                     | Stop                    | OFF        | —                                                        |
| **Read Leads For Summary**    | Continue (error output) | OFF        | → Handle Summary Read Error（`alwaysOutputData: true`）  |
| **Read Errors For Summary**   | Continue (error output) | OFF        | → Handle Summary Read Error（`alwaysOutputData: true`）  |
| **Handle Summary Read Error** | Stop                    | OFF        | → `summary_read_error_message`；保留已读 leads 数据    |
| Build Daily Summary           | Stop                    | OFF        | —                                                        |
| **Slack Daily Report**        | Continue (error output) | ON, 3x, 5s | → Log Slack Summary Error → `slack_error_message`        |

**拓扑变更：** 去掉 `Merge Summary Data`，改为串行 read：

```text
Daily 9am → Read Leads For Summary → Read Errors For Summary → Build Daily Summary
```

任一 read 失败时 `Handle Summary Read Error` 用 `$('Read Leads For Summary').all()` 保留已成功读取的 leads，避免整表归零或分支挂起。

---

## 5b. B2B Lead Weekly Summary

| 节点                              | On Error                | Retry      | 错误分支 / 输出字段                                              |
| --------------------------------- | ----------------------- | ---------- | ---------------------------------------------------------------- |
| Friday 5pm                        | Stop                    | OFF        | —                                                                |
| **Read Leads For Weekly**         | Continue (error output) | OFF        | → Handle Weekly Read Error（`alwaysOutputData: true`）           |
| **Read Errors For Weekly**        | Continue (error output) | OFF        | → Handle Weekly Read Error                                       |
| **Read Prior Weekly Metrics**     | Continue (error output) | OFF        | → Handle Weekly Read Error                                       |
| **Read config_main**              | Continue (error output) | ON, 3x, 5s | → Handle config_main Read Error（降级默认阈值）                  |
| **Read config_notifications**     | Continue (error output) | ON, 3x, 5s | → Handle config_notifications Read Error（默认禁用周报 Slack）   |
| **Handle Weekly Read Error**      | Stop                    | OFF        | → `weekly_read_error_message`；降级 metrics → HTTP Weekly Insights |
| Build Weekly Metrics              | Stop                    | OFF        | —                                                                |
| **HTTP Weekly Insights**          | Continue (error output) | ON, 3x, 5s | → Handle Weekly AI Failure → metrics-only `ai_summary` fallback  |
| **Slack Weekly Report**           | Continue (error output) | ON, 3x, 5s | → Log Slack Weekly Error；仍 Append weekly_metrics               |
| Append Weekly Metrics             | Stop                    | ON, 3x, 5s | 历史行供下周 WoW 对比                                            |

**门控：** 仅当 `config_main.mode=production` 且 `config_notifications.weekly_summary.enabled=true` 时发送 Slack；test/disabled 仍聚合指标并写入 `weekly_metrics`。

**拓扑：**

```text
Friday 5pm → Read Leads → Read Errors → Read Prior weekly_metrics
  → Read config_main → Read config_notifications → Load Weekly Config
      → Build Weekly Metrics → HTTP Weekly Insights → Merge Weekly Report
          → Should Send Weekly? → Slack / Skip → Append weekly_metrics
```

Read 失败时：`Handle Weekly Read Error` 跳过 Build Weekly Metrics，直接调用 HTTP Weekly Insights（AI 失败则 metrics-only fallback）。

---

## 6. B2B Lead Booking Follow-up

| 节点                              | On Error                | Retry      | 错误分支 / 输出字段                                           |
| --------------------------------- | ----------------------- | ---------- | ------------------------------------------------------------- |
| Daily 10am                        | Stop                    | OFF        | —                                                             |
| **Read Leads For Reminder**       | Continue (error output) | ON, 3x, 5s | → Handle Booking Read Error → `read_error_message`            |
| **Read config_main**              | Continue (error output) | ON, 3x, 5s | → Handle config_main Read Error（降级默认阈值）               |
| **Read config_notifications**     | Continue (error output) | ON, 3x, 5s | → Handle config_notifications Read Error（默认禁用提醒）    |
| Filter Due Booking Reminders      | Stop                    | OFF        | —                                                             |
| **Slack Booking Reminder**        | Continue (error output) | ON, 3x, 5s | → Log Slack Reminder Error → `reminder_status=failed`         |
| **Update Lead Reminder Status**   | Continue (error output) | ON, 3x, 5s | → Handle Update Reminder Error → `sheets_error_message`       |
| Write Booking Reminder Audit      | Stop                    | OFF        | `event_type=booking_reminder*`                                |

**筛选条件：** `score >= score_threshold_high`、`meeting_status=not_booked`、`created_at` 超过 `booking_reminder_hours`（默认 24h）、`booking_reminder_sent` 不为 true。

**门控：** 仅当 `config_main.mode=production` 且 `config_notifications.booking_reminder.enabled=true` 时发送 Slack；test/disabled 写 audit 但不更新 `booking_reminder_sent`。

**拓扑：**

```text
Daily 10am → Read Leads → Read config_main → Read config_notifications
  → Load Booking Config → Filter Due → Has Due?
      → Expand Due Leads → Build Text → Should Send? → Slack / Skip
      → Prepare Audit → Should Update? → Sheets update (success only) → audit_logs
```

---

## 7. B2B Lead Slack Actions

| 节点                              | On Error                | Retry      | 错误分支 / 输出字段                                           |
| --------------------------------- | ----------------------- | ---------- | ------------------------------------------------------------- |
| **Slack Interactions Webhook**    | Stop                    | OFF        | —                                                             |
| **Verify Slack Signature**        | Stop                    | OFF        | 空 `SLACK_SIGNING_SECRET` 时跳过验签（dev）                   |
| **Write Invalid Signature Audit** | Stop                    | OFF        | → Respond 401                                                 |
| **Read All Leads For Slack**      | Continue (error output) | ON, 3x, 5s | → Handle Slack Read Error → ephemeral 回复 + audit            |
| **Update Lead Review**            | Continue (error output) | ON, 3x, 5s | → Handle Update Review Error → error_logs + ephemeral 回复    |
| **Post Slack Response**           | Continue (error output) | ON, 3x, 5s | → Log Slack Response Error（非阻塞，仍写 audit）              |
| Write Slack Action Audit Log      | Continue (error output) | ON, 3x, 5s | 非阻塞                                                        |

**动作映射：** `assign_lead` → `review_status=approved`, `lead_stage=sql`, `owner_id`/`reviewer`; `mark_junk` → `rejected` + `reject` + `junk`; `nurture_lead` → `review_later` + `nurture`.

**门控：** `SLACK_ADMIN_USERS` 非空时仅 listed Slack user ID 可执行；空则 dev 模式允许全部。

**拓扑：**

```text
POST /slack-interactions → Verify Signature → Parse → Admin? → Resolve Action
  → Read Leads → Match lead_id → Update Sheets → response_url 回复 → audit_logs → 200
```

---

## 快速自检（5 分钟）

1. 四个主 workflow 已设置 Error Workflow
2. 所有 Sheets / HTTP / HubSpot / Slack 节点 On Error = Continue (using error output)
3. 每条 error output 都接到 Handler，Handler 接回主链路
4. HTTP Enrich、HTTP Score、HubSpot、Slack 已开启 Retry
5. 断开 Sheets 凭证跑一次 Intake → 应降级而非整 workflow 崩溃
6. 确认无错误的 `combineAll` fan-in（Enrichment config merge 除外）

## 验收场景

| 场景               | 预期                                                         |
| ------------------ | ------------------------------------------------------------ |
| LLM `/enrich` 超时 | Retry → Handle Enrichment Failure → `enrichment_error_message` → 继续 scoring |
| LLM `/score` 失败  | Handle Scoring Failure → `scoring_error_message` → manual_review |
| LLM `/sales-memo` 失败 | Retry → Handle Sales Memo Failure → `sales_memo_status=failed` + content_summary fallback → 继续 review/routing |
| config 读取失败    | Handle Config Load Error → mode=test                         |
| HubSpot 限流       | Retry → `crm_error_message` → crm_status=failed，通知仍尝试  |
| Slack 不可用       | `slack_error_message` → notification_status=failed           |
| error_logs 写失败  | `error_logs_error_message` → Slack 告警仍发出                |
| Daily Summary read 失败 | `summary_read_error_message` → 降级 summary，leads 数据保留 |
| Weekly Summary read 失败 | `weekly_read_error_message` → 降级 metrics，仍写 weekly_metrics |
| Weekly AI `/weekly-insights` 失败 | `weekly_ai_error_message` → metrics-only Slack + `fallback_used=true` |
| Booking reminder read 失败 | `read_error_message` → error_logs，不发送提醒 |
| Booking reminder Slack 失败 | `reminder_status=failed` → 不写 `booking_reminder_sent`，下次重试 |
| Slack 按钮 lead 不存在 | ephemeral `Lead not found` + `audit_logs.slack_action_lead_not_found` |
| Slack 按钮 Sheets 写失败 | ephemeral `Action failed, please retry` + `error_logs` |
| Slack 签名校验失败 | Respond 401 + `audit_logs.slack_action_signature_invalid` |
| Code throw         | 全局 Error Handler → error_logs + Slack                      |

重新生成 workflow JSON：`python3 scripts/generate_workflows.py`

从 UI 导出的 New 文件同步到仓库：`python3 scripts/sync_new_workflows.py`（一次性；会规范化 credential / workflowId 占位符）


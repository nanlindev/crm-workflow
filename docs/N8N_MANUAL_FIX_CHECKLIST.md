# n8n 本地手动修复清单

对照 `workflows/workflows-new/`（n8n 导出）与 `workflows/*.json`（仓库 canonical）的差异，修复不合理项。

> **仓库 JSON 已可通过** `scripts/sync_workflows_from_export.py` **同步**；n8n 手动步骤见本文第 0–11 节。

---

## 0. 在本地 n8n 上立即修复（不重导入也可做）

以下 4 项为 `workflows-new` 中的已知退步，建议**先在当前运行的 n8n** 里改掉。

### 0.1 删除冗余 End 节点

**工作流：** `B2B Lead CRM Sync Notification`

1. 找到 `Final Status Write Failed End1`（与 `Final Status Write Failed End` 重复）
2. 将 `Handle Final Status Error` 的错误输出改连到 `Final Status Write Failed End`
3. 删除 `Final Status Write Failed End1` → Save

### 0.2 恢复 Hunter 错误 lineage

**工作流：** `B2B Lead Enrichment Scoring` → `Attach Hunter Data`

在 return 中增加：

- `hunter_error_message`（`$input.item.error` 时写入）
- `_metadata.processing_stage`: `hunter_enrichment_failed` / `hunter_company_enriched` / `hunter_skipped`

### 0.3 恢复 Slack 线程 message_ts

**工作流：** `B2B Lead Slack Actions` → `Parse Slack Payload`

```javascript
// 改前
message_ts: payload.message?.ts || '',
// 改后
message_ts: payload.message?.ts || payload.container?.message_ts || '',
```

### 0.4 Normalize Enriched Lead 默认值

**工作流：** `B2B Lead Enrichment Scoring` → `Normalize Enriched Lead`

`industry`、`company_size`、`content_summary`、`intent_signals`、`enrichment_summary`、`enrichment_status` 均使用 `lead.<field> ?? ''`。

### 0.5 保持不动（合理）

| 项 | 说明 |
|----|------|
| Hunter `companies/find` + `Attach Hunter Data` | 比旧 `domain-search` 更优，保留 |
| HubSpot Service Key | 生产正确；仓库同步后需重绑凭证 |
| `Resolve Lead Action` 的 `slack_reply` | 合理，保留 |

---

## 1. 同步仓库后重新导入（可选）

```bash
cd /home/lotey/lindev/crm-workflow
python3 scripts/sync_workflows_from_export.py
```

---

## 2. 重新导入工作流（若用文件覆盖）

1. n8n → **Workflows** → 对每个 CRM 工作流：**⋯ → Import from File**，选择 `workflows/` 下对应 JSON（或 Delete 后 Import）。
2. 确认 **9 个工作流**均已更新：
   - B2B Lead Intake
   - B2B Lead Enrichment Scoring
   - B2B Lead CRM Sync Notification
   - B2B Lead Error Handler
   - B2B Lead Calendly Webhook
   - B2B Lead Booking Follow-up
   - B2B Lead Slack Actions
   - B2B Lead Daily Summary
   - B2B Lead Weekly Summary

---

## 3. 凭证重新绑定（必须）

仓库 JSON 使用占位符，导入后节点会显示 Credential missing。

| 节点类型 | 工作流 | 生产环境推荐 |
|----------|--------|--------------|
| Google Sheets | 所有 Read/Update/Append | 你的 Google Sheets OAuth |
| HubSpot Upsert + Log Outbound Email | CRM Sync | **HubSpot Service Key**（Private App） |
| Slack Notify / Alert / Block Kit | CRM、Error、Calendly、Booking、Daily、Weekly、Slack Actions | Slack OAuth 或 Bot Token |
| HTTP Request | Enrichment（Hunter） | 无需凭证；确认 `$env.HUNTER_API_KEY` 可读 |

**HubSpot 手动步骤：**

1. 打开 `B2B Lead CRM Sync Notification`
2. `HubSpot Upsert Contact` → Credential → 选 **HubSpot Service Key account**
3. `HubSpot Log Outbound Email` → 同上
4. Save

---

## 4. Error Workflow 绑定（必须）

同步脚本已将 `settings.errorWorkflow` 写回工作流名称 `B2B Lead Error Handler`。导入后请验证：

1. 打开每个主工作流 → **Settings**（齿轮）
2. **Error Workflow** = `B2B Lead Error Handler`
3. 若显示 ID 而非名称，手动改选名称
4. Save

涉及工作流：Intake、Enrichment、CRM Sync、Calendly、Booking Follow-up、Slack Actions、Daily/Weekly Summary。

---

## 5. Execute Workflow 子流程映射（必须抽查）

1. **Intake** → `Execute Enrichment Scoring`：workflow = `B2B Lead Enrichment Scoring`
2. **Enrichment** → `Execute CRM Sync`：workflow = `B2B Lead CRM Sync Notification`，**workflowInputs 字段映射完整**（约 40 个字段，含 enrichment、sales_memo、company_region）
3. **Slack Actions** → `Execute Post-Assign CRM Sync`：workflow = `B2B Lead CRM Sync Notification`

打开 `Execute CRM Sync` → 确认 **Define Below** 映射存在（非空）。

---

## 6. 同步脚本自动修复项（导入后验证）

以下项已由 `sync_workflows_from_export.py` 写入 canonical JSON，**无需在 n8n 再改逻辑**（仅验证执行结果）：

| 问题 | 修复 |
|------|------|
| 冗余 `Final Status Write Failed End1` | 已删除，错误分支指向 `Final Status Write Failed End` |
| Hunter 失败无 `hunter_error_message` | `Attach Hunter Data` 已补错误 lineage |
| Slack 线程 `message_ts` 丢失 | `Parse Slack Payload` 已恢复 `payload.container?.message_ts` 回退 |
| Normalize 字段可能 undefined | `Normalize Enriched Lead` 已恢复 `?? ''` 默认值 |

**验证：** 用 corporate 测试 lead 跑 Enrichment，Hunter 失败时在 item 上应能看到 `hunter_error_message`。

---

## 7. 激活工作流 + Webhook URL（上线前）

仓库中 `active: false`；生产需手动 Activate：

| 工作流 | 激活 | 外部配置 |
|--------|------|----------|
| B2B Lead Intake | Yes | Tally webhook → Production URL |
| B2B Lead Enrichment Scoring | 子流程，无需 webhook | — |
| B2B Lead CRM Sync Notification | 子流程 | — |
| B2B Lead Error Handler | Yes | — |
| B2B Lead Calendly Webhook | Yes | Calendly → Webhook URL |
| B2B Lead Booking Follow-up | Yes | Schedule 已配置 |
| B2B Lead Slack Actions | Yes | Slack Interactivity URL |
| B2B Lead Daily Summary | 按需 | Cron 9am |
| B2B Lead Weekly Summary | 按需 | Cron 周五 17:00 |

**Slack App Interactivity URL：** 指向 `B2B Lead Slack Actions` 的 Production Webhook URL。

**Calendly Webhook：** 指向 `B2B Lead Calendly Webhook` 的 Production URL，订阅 `invitee.created` / `invitee.canceled`。

---

## 8. 环境变量（platform-n8n / crm-workflow）

确认 n8n 容器可读：

```text
GOOGLE_SHEETS_DOCUMENT_ID
HUNTER_API_KEY
SLACK_CHANNEL_ID
SLACK_SIGNING_SECRET
SLACK_ADMIN_USERS          # 可选，逗号分隔 Slack user ID
CALENDLY_WEBHOOK_SIGNING_KEY
DEEPSEEK_*                 # Python sidecar
```

**代理：** 确保 `NO_PROXY` 含 `crm_python_ai,rss_python_ai,otel-collector,langfuse-web`；重建 n8n 容器后 `docker exec platform-n8n-n8n_app-1 sh -c 'echo $NO_PROXY'` 验证。

---

## 9. config_main（Google Sheets）

| key | 说明 |
|-----|------|
| `mode` | `test` 跳过 HubSpot/Slack 真发；上线改 `production` |
| `calendly_url` | 高分 lead Slack 消息中的预约链接 |
| `sales_memo_min_score` | 默认 80 |
| `first_touch_min_score` | 首轮邮件门控 |
| `first_touch_sender_name` | 邮件署名 |

---

## 10. 冒烟测试顺序

1. `curl` 或 Tally 提交 → Intake 成功
2. Enrichment：corporate 域名走 Hunter → LLM enrich/score → Sheets 更新
3. CRM Sync（`mode=test`）：跳过 HubSpot/Slack，无报错
4. `mode=production` 单条：HubSpot contact + Slack Block Kit
5. Calendly 测试预约 → `meeting_status=booked`
6. Slack 按钮 assign/junk/nurture → Sheets 更新 + 线程回复

---

## 11. 勿提交到仓库的内容

- 真实 Credential ID
- `pinData` 测试数据
- `errorWorkflow` 的 n8n 内部 UUID（应使用工作流名称）
- `active: true`（仓库保持 `false`，由部署环境决定）

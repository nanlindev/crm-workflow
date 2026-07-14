# Slack Actions 设置

适用于 **B2B Lead Slack Actions**（Block Kit Assign / Junk / Nurture）。

Slack 要求约 **3 秒内返回 HTTP 200**。先快速 Ack，再更新 Sheets，并用 `chat.update` 刷新消息。

## 流程

```text
User clicks button
  → Verify Slack signature + parse payload
  → Respond 200 Ack immediately
  → Optional interim update (“Processing…”)
  → Update Google Sheets leads + audit
  → Assign / Nurture may Execute CRM Sync (HubSpot, skip duplicate Slack)
  → chat.update final card (channel_id + message_ts)
```

优先使用 **Slack → Message → Update**，并用交互 payload 中的 `channel_id` + `message_ts`（含 `container.message_ts` 回退）。避免再发第二条消息，导致旧按钮仍可见。

## 配置 Slack app

1. [api.slack.com](https://api.slack.com/apps) → 你的 app → **Interactivity & Shortcuts** → On  
2. Request URL：`https://<public-n8n-host>/webhook/slack-interactions`  
3. **Basic Information** → Signing Secret → n8n 环境中的 `SLACK_SIGNING_SECRET`  
4. 可选：`SLACK_ADMIN_USERS` = 逗号分隔的 Slack user ID（空 = 开发环境允许全部）  
5. Bot 必须在 `SLACK_CHANNEL_ID` 频道中；工作流已绑定 OAuth 凭证  

## 导入 / 激活

1. 导入 `workflows/B2B Lead Slack Actions.json`  
2. 绑定 Google Sheets + Slack 凭证  
3. Settings → Error Workflow → **B2B Lead Error Handler**  
4. **Activate** 该工作流  
5. 确认 CRM Sync Notification 在通知路径上会发出 Block Kit 按钮  

## 按钮 → 表格映射

| Action | 表格更新 |
|--------|----------|
| `assign_lead` | `review_status=approved`，`lead_stage=sql`，`owner_id` / `reviewer`，然后在配置允许时 CRM Sync + DRAFT 邮件 |
| `mark_junk` | `review_status=rejected`，`recommended_action=reject`，`lead_stage=junk` |
| `nurture_lead` | `review_status=review_later`，`lead_stage=nurture`，可选 CRM 通知路径 |

## 排障

| 问题 | 检查 |
|------|------|
| Slack 中黄色超时 | Ack 节点过晚 / 路径阻塞 |
| 卡片重复 | 用了 `response_url` post 而非 `chat.update` |
| 签名无效 | `SLACK_SIGNING_SECRET`；签名基串需用 raw body |
| 按钮无效果 | 工作流未激活；Interactivity URL 错误 |

见 [CREDENTIALS.md](CREDENTIALS.md)、[WORKFLOWS.md](WORKFLOWS.md)、[TEST_PRODUCTION.md](TEST_PRODUCTION.md)。

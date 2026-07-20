# Calendly webhook 设置

适用于 **B2B Lead Calendly Webhook**。  
前置条件：`leads` 列含 `meeting_status`、`meeting_time`、`calendly_event_uri`、`calendly_invitee_email`；工作流已导入并 Active；公开的 Production webhook URL 可用。

## PAT 与 signing key

| | Personal Access Token (PAT) | Webhook signing key |
|--|----------------------------|---------------------|
| 用途 | Calendly REST API（创建/列出/删除订阅） | n8n 校验每次 webhook POST |
| 放置位置 | 仅本地 `curl` / API 客户端 | platform-n8n / n8n 环境中的 `CALENDLY_WEBHOOK_SIGNING_KEY` |
| 常见错误 | 把 PAT 放进 `CALENDLY_WEBHOOK_SIGNING_KEY` | 期望 Calendly 稍后返回该 key（通常不会） |

创建订阅时**在请求体中自带 `signing_key`**。若丢失，删除订阅后重建。

## Webhook URL

```text
https://<public-n8n-host>/webhook/calendly
```

确保 platform-n8n 的 `WEBHOOK_URL` 与你的公网 base URL 一致。Calendly 只会调用 **Active** 工作流的 **Production** URL。

Calendly webhook 需要 **付费** Calendly 套餐。

## 创建订阅（API 概要）

1. 从 Calendly 获取 PAT。
2. 生成一串足够长的随机 signing key；在 n8n 环境中设为 `CALENDLY_WEBHOOK_SIGNING_KEY`。
3. 为 organization/user 作用域创建订阅，事件包括：
   - `invitee.created`
   - `invitee.canceled`
4. 在创建 payload 中传入同一 `signing_key` 与上述 URL。

具体 API 字段随 Calendly API 版本变化——请遵循 Calendly 当前的 webhook 订阅文档，且除非你有意为管理脚本添加 HTTP credential，否则不要把 PAT 存进 n8n 凭证库。

## n8n 工作流行为

1. 校验签名（仅当 key 为空时跳过 — **仅开发**）。
2. 归一化 payload；按 invitee email 匹配 `leads.contact_email`（不区分大小写）。
3. 更新会议字段；可选 Slack 通知；按连线写入 audit / error logs。

## 验证

1. 用已存在于线索行的邮箱预约一个测试事件。
2. 执行成功；`meeting_status` / `meeting_time` 更新。
3. 取消事件 → 状态反映 canceled 路径。

## 排障

| 问题 | 检查 |
|------|------|
| 401 / 签名无效 | Key 不匹配；raw body 已启用；key 不是 PAT |
| 200 但未匹配 | Email 与 Sheets 不一致；线索缺失 |
| 未投递 | 工作流未激活；URL 错误；免费 Calendly 套餐 |
| **一条预约刷出多条 Slack booked** | `Match Lead By Email` 必须是 `runOnceForAllItems`（Sheets 有 N 行时 `EachItem` 会扇出 N 次）。重新导入修复后的 `B2B Lead Calendly Webhook.json` |

凭证总览：[CREDENTIALS.md](CREDENTIALS.md)。字段列表：[SHEETS_SETUP.md](SHEETS_SETUP.md)。

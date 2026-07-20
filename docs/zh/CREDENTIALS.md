# 凭证配置

## 必需

### DeepSeek

```bash
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash
```

由 Python sidecar 用于全部 LLM 端点。

### Google Sheets（n8n OAuth）

1. n8n → Credentials → Google Sheets OAuth2
2. 授权可编辑 CRM 电子表格的账号
3. 分配给所有 Google Sheets 节点

### Langfuse

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://langfuse-web:3000
ENVIRONMENT=development
```

Sidecar 启动时连接；认证失败会记为警告，服务仍继续运行。

## 生产必需

### HubSpot（n8n OAuth — 仓库默认）

1. n8n → Credentials → HubSpot OAuth2
2. 分配给 **HubSpot Upsert Contact**（以及使用该凭证的任何 HubSpot 邮件 HTTP 节点）

仓库 JSON 使用占位符 `HUBSPOT_CREDENTIAL_ID`（`hubspotOAuth2Api`，upsert）。导入后需重新绑定。

**可选变体：** HubSpot Private App token — 不要提交真实凭证 ID。

**数据策略：** Google Sheets 是评分、路由、审核与邮件草稿的**事实来源（SoT）**。HubSpot 接收基础 Contact 字段（email、name、company、role），并在人工 **Assign** 后写入一封邮件 **DRAFT** 活动。默认不写入评分相关的自定义 HubSpot 属性。

### Slack（n8n OAuth — 仓库默认）

1. n8n → Credentials → Slack OAuth2
2. 邀请 bot 进入目标频道
3. 设置 `SLACK_CHANNEL_ID`（环境变量或节点）

占位符：`SLACK_CREDENTIAL_ID`。

用于高分 / 审核 / 错误 / 日报 / 周报 / Calendly / 预约提醒消息。

**交互（Block Kit 按钮）：**

1. api.slack.com → App → **Interactivity & Shortcuts** → ON
2. Request URL：`https://<n8n-host>/webhook/slack-interactions`
3. Signing Secret → n8n 环境中的 `SLACK_SIGNING_SECRET`
4. 可选 `SLACK_ADMIN_USERS`（逗号分隔的 Slack user ID；空 = 开发环境允许全部）
5. 导入并激活 **B2B Lead Slack Actions**

见 [SLACK_ACTIONS_SETUP.md](SLACK_ACTIONS_SETUP.md)。

## 可选

### Tally 签名

1. Tally 表单 → Webhooks → 启用 signing secret
2. 在 n8n 环境中设置 `TALLY_WEBHOOK_SIGNING_KEY=<secret>`
3. Intake 使用 `rawBody`。密钥为空时 **跳过** 验签（仅开发/演示）。配置了密钥后，缺签或验签失败为 **fail-closed**（401）。

### Hunter.io

可选域名富化：`HUNTER_API_KEY`，以及 Enrichment 工作流中带 `onError: continueErrorOutput` 的 HTTP 节点。

### Calendly

- 静态预约链接：`config_main.calendly_url`
- Webhook：`CALENDLY_WEBHOOK_SIGNING_KEY` — 见 [CALENDLY_SETUP.md](CALENDLY_SETUP.md)

Signing key 为空时跳过验证（**仅用于开发**）。

## 安全

切勿提交 `.env`。切勿把 API key 写入 Google Sheets。

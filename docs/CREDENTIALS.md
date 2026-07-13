# Credentials Configuration

## Required

### DeepSeek

```
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash
```

Used by Python sidecar for enrichment and scoring.

### Google Sheets (n8n OAuth)

1. n8n → Credentials → Google Sheets OAuth2
2. Authorize with Google account that owns or can edit the spreadsheet
3. Assign to all Google Sheets nodes in workflows

### Langfuse

```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://langfuse-web:3000
ENVIRONMENT=development
```

Python service connects on startup; warns if auth fails but continues.

## Production required

### HubSpot (n8n OAuth — 仓库默认)

1. n8n → Credentials → HubSpot OAuth2
2. Assign to **HubSpot Upsert Contact** node in CRM Sync workflow

仓库 JSON 使用占位符 `HUBSPOT_CREDENTIAL_ID`（`hubspotOAuth2Api` + `operation: upsert`）。重新 import 后需绑定真实凭证。

**可选部署变体：** HubSpot Private App Token（`hubspotAppToken` + `authentication: appToken`）。若在 UI 中使用此方式，请勿将真实 credential ID 提交进仓库。

**数据策略：** Google Sheets 为评分、路由、review、邮件草稿等 intelligence 的**唯一真相源**。HubSpot 仅同步基础 Contact 字段（email、name、company、role），并在人工 Assign 后写入 email DRAFT 活动记录。n8n HubSpot 节点**不同步**自定义评分列（`lead_score` 等）；若需在 HubSpot 查看评分，请手动查阅 Sheets 或后续接专用集成。

**Custom properties**（可选，当前工作流未写入）：

| Property             | Type   | Purpose           |
| -------------------- | ------ | ----------------- |
| `lead_score`         | Number | AI score          |
| `correlation_id`     | Text   | Trace correlation |
| `recommended_action` | Text   | Routing decision  |

### Slack (n8n OAuth — 仓库默认)

1. n8n → Credentials → Slack OAuth2
2. Invite bot to target channel
3. Set channel ID in nodes or `SLACK_CHANNEL_ID` env var

仓库 JSON 使用占位符 `SLACK_CREDENTIAL_ID`（`slackOAuth2Api`）。

**可选部署变体：** Slack API Token（`slackApi`）。若在 UI 中使用此方式，请勿将真实 credential ID 提交进仓库。

Used for: high-score alerts, review reminders, error alerts, daily summary, Calendly updates, booking reminders.

**Slack interactivity (Block Kit buttons):**

1. [api.slack.com](https://api.slack.com/apps) → your App → **Interactivity & Shortcuts** → ON
2. Request URL = `https://<n8n-host>/webhook/slack-interactions`
3. Copy **Signing Secret** from **Basic Information** → set `SLACK_SIGNING_SECRET` in n8n env
4. Optional: restrict who can click buttons via `SLACK_ADMIN_USERS` (comma-separated Slack user IDs; empty allows all in dev)
5. Import and activate **B2B Lead Slack Actions** workflow

Button actions (`assign_lead`, `mark_junk`, `nurture_lead`) update `leads` in Google Sheets and reply in-thread via `response_url`.

## Optional

### Tally

1. Tally 表单 → Integrations → Webhooks → 开启 **Signing secret**
2. n8n 环境变量：`TALLY_WEBHOOK_SIGNING_KEY=<secret>`
3. Intake 工作流 `Tally Webhook` 已开启 `rawBody`，`Verify Tally Signature` 在密钥缺失时 **fail-closed**

### Google Forms

Requires Apps Script webhook bridge (see [FIELD_MAPPING.md](FIELD_MAPPING.md)). Posts to `/webhook/google-forms-lead`.

### Clearbit / Hunter.io (domain enrichment)

Optional HTTP enrichment APIs. To enable:

1. Add API key to `.env`: `HUNTER_API_KEY=...`
2. Add HTTP Request node after **Domain Enrichment** in Enrichment Scoring workflow
3. Set `onError: continueErrorOutput` — failures degrade to `enrichment_status=partial`

Example Hunter companies/find (current workflow):

```
GET https://api.hunter.io/v2/companies/find?domain={{ $json.company_domain }}&api_key=YOUR_KEY
```

### Calendly

Static booking URL comes from `config_main.calendly_url` (used in Slack notifications).

For **Calendly webhooks** (`B2B Lead Calendly Webhook` workflow):

1. Calendly → Integrations → Webhooks → create subscription for `invitee.created` and `invitee.canceled`
2. Set URL to `https://your-n8n-domain/webhook/calendly`
3. Copy the **signing key** into `.env`:

```
CALENDLY_WEBHOOK_SIGNING_KEY=your_signing_key
```

4. Expose the key to n8n (platform-n8n `.env` or n8n environment variables)

If the signing key is empty, signature verification is skipped (development only).

### Discord / Telegram

Not wired in default CRM notification workflow. **Booking Follow-up** reads `config_notifications` row `booking_reminder` (`enabled`, `channels`, `template_key`) to gate scheduled reminders.

## n8n internal Postgres

```
POSTGRES_USER=n8n_user
POSTGRES_PASSWORD=change_me
POSTGRES_DB=n8n_db
```

Used only for n8n runtime state — not for business leads.

## Security

Never commit `.env` files. Never store API keys in Google Sheets.

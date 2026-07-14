# 字段映射

所有表单来源在富化前都会归一到 [Lead Schema](../../schemas/lead.schema.json)。

## Tally（主来源）

Webhook 路径：`/webhook/tally-lead`

### 默认字段映射

**Normalize Tally Payload** Code 节点按标签映射 Tally 字段（不区分大小写）：

| Lead 字段 | Tally 字段标签（先匹配者优先） |
|-----------|--------------------------------|
| `contact_name` | name, contact_name, full_name |
| `contact_email` | email, contact_email |
| `contact_role` | role, contact_role, job_title |
| `company_name` | company, company_name |
| `raw_content` | message, details, project_description, how_can_we_help |
| `source_url` | formUrl from payload |
| `source_name` | formName from payload |
| `source_type` | `tally`（固定） |
| `source_trust_level` | `80`（固定） |

### 通过 config_sources 自定义映射

对非标准 Tally 表单，更新 Google Sheets 中的 `config_sources.field_mapping_json`。Intake 工作流会读取该配置以便后续扩展；Code 节点默认仍使用基于标签的匹配。

### Tally webhook payload 示例

```json
{
  "eventType": "FORM_RESPONSE",
  "data": {
    "formName": "B2B Contact",
    "formUrl": "https://tally.so/r/abc123",
    "fields": [
      { "label": "Name", "value": "Jane Doe" },
      { "label": "Email", "value": "jane@acme.com" },
      { "label": "Role", "value": "VP Engineering" },
      { "label": "Company", "value": "Acme Corp" },
      { "label": "Message", "value": "We need automation help..." }
    ]
  }
}
```

## Google Forms（次来源）

Webhook 路径：`/webhook/google-forms-lead`

Google Forms 无原生 webhook。请使用 Apps Script：

```javascript
function onFormSubmit(e) {
  var responses = e.values;
  var payload = {
    name: responses[1],
    email: responses[2],
    role: responses[3],
    company: responses[4],
    message: responses[5],
    formName: "B2B Contact Form",
    formUrl: FormApp.getActiveForm().getPublishedUrl()
  };
  UrlFetchApp.fetch("https://your-n8n-domain/webhook/google-forms-lead", {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload)
  });
}
```

| Lead 字段 | Google Forms payload key |
|-----------|--------------------------|
| `contact_name` | name |
| `contact_email` | email |
| `contact_role` | role |
| `company_name` | company |
| `raw_content` | message |
| `source_type` | `google_forms`（固定） |
| `source_trust_level` | `70`（固定） |

## 生成字段（Intake 工作流）

| 字段 | 来源 |
|------|------|
| `lead_id` | UUID v4 |
| `correlation_id` | UUID v4（可观测性） |
| `lead_hash` | SHA256(email\|domain\|source_url)[:16] |
| `company_domain` | 未提供时从 email 提取 |
| `created_at` / `updated_at` | ISO 时间戳 |

## Enrichment 字段

| 字段 | 来源 |
|------|------|
| `domain_type` | Code 节点（corporate/personal/unknown） |
| `content_summary` | Python `/enrich` |
| `industry`、`company_size` | Python `/enrich` |
| `intent_signals` | Python `/enrich` + `/score` |

## Scoring 字段

| 字段 | 来源 |
|------|------|
| `score` | Python `/score`（0-100） |
| `recommended_action` | Python `/score` + 路由规则 |
| `review_status` | Review rules Code 节点 |

## Sales memo 字段

| 字段 | 来源 |
|------|------|
| `sales_memo` | Python `/sales-memo`（JSON）— 仅当 score ≥ `sales_memo_min_score` 且未被 reject |
| `sales_memo_status` | `complete` \| `skipped_low_score` \| `failed` |

## 会议 / Calendly 字段

| 字段 | 来源 |
|------|------|
| `meeting_status` | Intake 对新线索设为 `not_booked`；Calendly webhook 更新为 `booked` / `canceled` / `rescheduled` |
| `meeting_time` | Calendly `payload.event.start_time` |
| `calendly_event_uri` | Calendly `payload.event.uri` |
| `calendly_invitee_email` | Calendly `payload.invitee.email` |

Webhook 路径：`/webhook/calendly` — 见 `B2B Lead Calendly Webhook` 工作流。

### Calendly webhook payload（简化）

```json
{
  "event": "invitee.created",
  "payload": {
    "event": {
      "uri": "https://api.calendly.com/scheduled_events/...",
      "start_time": "2026-07-10T14:00:00.000000Z"
    },
    "invitee": {
      "email": "jane@acme.com",
      "uri": "https://api.calendly.com/scheduled_events/.../invitees/..."
    }
  }
}
```

未匹配的 invitee（email 不在 `leads`）会写入 `audit_logs` 为 `calendly_unmatched`，不抛错。

## 预约提醒字段

| 字段 | 来源 |
|------|------|
| `booking_reminder_sent` | `B2B Lead Booking Follow-up` 在 Slack 提醒成功后设为 `true` |
| `booking_reminder_at` | 发送提醒时的 ISO 时间戳 |

定时工作流：**B2B Lead Booking Follow-up**（每日 10:00）。合格线索：`score >= score_threshold_high`、`meeting_status=not_booked`、早于 `booking_reminder_hours`（默认 24），且 `booking_reminder_sent` 不为 true。由 `config_notifications` 行 `booking_reminder` 与 `config_main.mode` 控制。

## Slack 动作字段

| 字段 | 来源 |
|------|------|
| `owner_id` | **Assign** 按钮上的 Slack user ID（`assign_lead`） |
| `lead_stage` | `sql`（assign）、`junk`（mark junk）、`nurture`（nurture） |
| `review_status` | 由 Slack Actions 更新：`approved`、`rejected` 或 `review_later` |
| `reviewer` | Assign 时的 Slack user ID |
| `reviewed_at` | 应用 Slack 动作时的 ISO 时间戳 |

Webhook 路径：`/webhook/slack-interactions` — 见 `B2B Lead Slack Actions` 工作流。按钮由 CRM Sync Block Kit 通知发出（`assign_lead`、`mark_junk`、`nurture_lead`）。

# Slack Actions setup

Applies to **B2B Lead Slack Actions** (Block Kit Assign / Junk / Nurture).

Slack requires an HTTP **200 within ~3 seconds**. Ack fast, then update Sheets and refresh the message via `chat.update`.

## Flow

```text
User clicks button
  → Verify Slack signature + parse payload
  → Respond 200 Ack immediately
  → Optional interim update (“Processing…”)
  → Update Google Sheets leads + audit
  → Assign / Nurture may Execute CRM Sync (HubSpot, skip duplicate Slack)
  → chat.update final card (channel_id + message_ts)
```

Prefer **Slack → Message → Update** with `channel_id` + `message_ts` from the interaction payload (including `container.message_ts` fallback). Avoid posting a second message that leaves old buttons visible.

## Configure Slack app

1. [api.slack.com](https://api.slack.com/apps) → your app → **Interactivity & Shortcuts** → On  
2. Request URL: `https://<public-n8n-host>/webhook/slack-interactions`  
3. **Basic Information** → Signing Secret → `SLACK_SIGNING_SECRET` in n8n env  
4. Optional: `SLACK_ADMIN_USERS` = comma-separated Slack user IDs (empty = allow all in development)  
5. Bot must be in `SLACK_CHANNEL_ID` channel; OAuth credential bound in workflows  

## Import / activate

1. Import `workflows/B2B Lead Slack Actions.json`  
2. Bind Google Sheets + Slack credentials  
3. Settings → Error Workflow → **B2B Lead Error Handler**  
4. **Activate** the workflow  
5. Confirm CRM Sync Notification posts Block Kit buttons on notify path  

## Button → sheet mapping

| Action | Sheet updates |
|--------|----------------|
| `assign_lead` | `review_status=approved`, `lead_stage=sql`, `owner_id` / `reviewer`, then CRM Sync + DRAFT email when configured |
| `mark_junk` | `review_status=rejected`, `recommended_action=reject`, `lead_stage=junk` |
| `nurture_lead` | `review_status=review_later`, `lead_stage=nurture`, optional CRM notify path |

## Troubleshoot

| Issue | Check |
|-------|-------|
| Yellow timeout in Slack | Ack node too late / path blocked |
| Duplicate cards | Used `response_url` post instead of `chat.update` |
| Invalid signature | `SLACK_SIGNING_SECRET`; raw body for signing base string |
| Buttons no-op | Workflow inactive; Interactivity URL wrong |

See [CREDENTIALS.md](CREDENTIALS.md), [WORKFLOWS.md](WORKFLOWS.md), [TEST_PRODUCTION.md](TEST_PRODUCTION.md).

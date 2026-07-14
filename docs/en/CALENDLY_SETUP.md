# Calendly webhook setup

Applies to **B2B Lead Calendly Webhook**.  
Prerequisites: `leads` columns `meeting_status`, `meeting_time`, `calendly_event_uri`, `calendly_invitee_email`; workflow imported and Active; public Production webhook URL.

## PAT vs signing key

| | Personal Access Token (PAT) | Webhook signing key |
|--|----------------------------|---------------------|
| Purpose | Calendly REST API (create/list/delete subscriptions) | n8n verifies each webhook POST |
| Where | Local `curl` / API client only | `CALENDLY_WEBHOOK_SIGNING_KEY` in platform-n8n / n8n env |
| Mistake | Putting PAT into `CALENDLY_WEBHOOK_SIGNING_KEY` | Expecting Calendly to return the key later (it usually will not) |

Create the subscription **with your own `signing_key` in the request body**. If lost, delete the subscription and recreate.

## Webhook URL

```text
https://<public-n8n-host>/webhook/calendly
```

Ensure `WEBHOOK_URL` on platform-n8n matches your public base URL. Calendly only calls the **Production** URL of an **Active** workflow.

Calendly webhooks require a **paid** Calendly plan.

## Create subscription (API sketch)

1. Obtain a PAT from Calendly.
2. Generate a long random signing key; set it in n8n env as `CALENDLY_WEBHOOK_SIGNING_KEY`.
3. Create subscription for organization/user scope with events:
   - `invitee.created`
   - `invitee.canceled`
4. Pass the same `signing_key` in the create payload and the URL above.

Exact API fields change with Calendly API versions—follow Calendly’s current webhook subscription docs and keep PAT out of n8n credentials store unless you intentionally add an HTTP credential for admin scripts.

## n8n workflow behavior

1. Verify signature (skipped only if key empty — **dev only**).
2. Normalize payload; match invitee email to `leads.contact_email` (case-insensitive).
3. Update meeting fields; optional Slack notify; write audit / error logs as wired.

## Verify

1. Book a test event with an email that exists on a lead row.
2. Execution succeeds; `meeting_status` / `meeting_time` update.
3. Cancel event → status reflects canceled path.

## Troubleshoot

| Issue | Check |
|-------|-------|
| 401 / invalid signature | Key mismatch; raw body enabled; key not PAT |
| 200 but unmatched | Email differs from Sheets; lead missing |
| No delivery | Workflow inactive; wrong URL; free Calendly plan |

Credentials overview: [CREDENTIALS.md](CREDENTIALS.md). Field list: [SHEETS_SETUP.md](SHEETS_SETUP.md).

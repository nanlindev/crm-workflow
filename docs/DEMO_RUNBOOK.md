# Production Demo Runbook

Step-by-step script for a **production-mode** full-chain demo on the remote n8n + CRM stack. Use this while recording screenshots / Loom (see material checklist at the end).

**中文完整手动清单（含每处录像/截图提示）：** [zh/DEMO_RUNBOOK.md](zh/DEMO_RUNBOOK.md)

Related docs: [TEST_PRODUCTION](en/TEST_PRODUCTION.md) · [INSTALL](en/INSTALL.md) · [OBSERVABILITY](en/OBSERVABILITY.md) · [RUN_EXAMPLE](en/RUN_EXAMPLE.md) · [WORKFLOWS](en/WORKFLOWS.md)

**Priority for portfolio:** Scenarios **A, B, E, J** are required. Complete at least **two** of C / D / G / H. Scenario H should use the **gated Daily / Weekly** flows (post-debug: config load + `Should Send *` + Skip Slack in test).

---

## 0. Pre-flight

### 0.1 Isolation (required for production)

| Resource | Demo isolation |
|----------|----------------|
| Google Sheets | Dedicated spreadsheet (not client prod data) |
| Slack | Dedicated channel (e.g. `#crm-automation-demo`); bot invited |
| HubSpot | Free portal / sandbox; use `@demo+alias@…` emails |
| Tally | Dedicated demo form → `https://<domain>/webhook/tally-lead` |
| Calendly | Test event type; signing key in n8n env |

### 0.2 Stack health

- [ ] n8n UI reachable (HTTPS or SSH tunnel)
- [ ] Sidecar: `curl` → `/health` OK; `/prompts` lists **6** keys (incl. `weekly_insights`, `outbound_email`)
- [ ] Nine workflows imported; credentials rebound (Sheets / Slack / HubSpot)
- [ ] Error Workflow → **B2B Lead Error Handler** on all main workflows
- [ ] Active: Intake, Calendly Webhook, Booking Follow-up, Daily Summary, Weekly Summary, Slack Actions
- [ ] OBS: otel-collector + Jaeger + Langfuse up; `NO_PROXY` includes `crm_python_ai,otel-collector,langfuse-web`

### 0.3 Sheets config for demo

**`config_main`**

```text
mode=production
```

Keep defaults unless you need easier triggers (e.g. slightly lower `first_touch_min_score` / `score_threshold_high` for a thinner demo lead).

**`config_notifications`** — all `enabled=true` for a full run:

| event_type | Demo role |
|------------|-----------|
| `high_score_lead` | Slack Block Kit on high-score path |
| `review_required` | Manual review Slack |
| `first_touch_email` | Outbound draft → `draft_pending_review` |
| `booking_reminder` | Booking Follow-up Slack |
| `daily_summary` | Daily Slack digest |
| `weekly_summary` | Weekly Slack digest |
| `error_alert` | Optional Scenario I |

### 0.4 Recommended order

1. **H0** — Daily / Weekly in `mode=test` (prove Skip Slack + metrics append)
2. Flip `mode=production` + enable notification rows
3. **A → B** (high-score + Assign / HubSpot DRAFT)
4. **E** (Calendly)
5. **C / D / G** as time allows
6. **H1** — Daily / Weekly with Slack
7. **J** + **I** (optional)
8. Capture OBS screenshots from A / H

---

## H0. Daily / Weekly gate check (test mode first)

Do this **before** production Slack digests. Confirms post-debug Daily/Weekly behavior.

### Prep

- [ ] Set `config_main.mode=test`
- [ ] Leave `daily_summary` / `weekly_summary` enabled or disabled — Slack must still be **skipped** in test
- [ ] Prefer having at least one lead with `created_at` on **yesterday UTC** (Daily window) and some leads in the **current UTC week** (Weekly)

### Daily (test)

1. [ ] Open **B2B Lead Daily Summary** → **Execute Workflow**
2. [ ] Execution path: config load → **Build Daily Summary** → **Should Send Daily?** → **Skip Daily Slack** → End
3. [ ] **No** message in Slack demo channel
4. [ ] Build item shows `daily_gate_passed=false`, `mode=test`, `score_threshold_high` from config (not a hard-coded orphan)
5. [ ] One summary path only (`runOnceForAllItems` — not one Slack-shaped item per lead/error row)

### Weekly (test)

1. [ ] Open **B2B Lead Weekly Summary** → **Execute Workflow**
2. [ ] Path: metrics → optional `/weekly-insights` → **Should Send Weekly?** → **Skip Weekly Slack** → **Append Weekly Metrics**
3. [ ] **No** Slack message
4. [ ] New row on sheet **`weekly_metrics`**
5. [ ] Langfuse may show a `weekly-insights` / `crm-workflow` generation if AI ran

**Pass criteria:** aggregates + (Weekly) metrics append; Slack skipped.

Then set `mode=production` and continue with Scenario A.

---

## Scenario A — High-score lead main path (required)

**Trigger:** Submit a Tally (or webhook) lead with strong intent (budget / demo / automation language).

Sample webhook (adjust URL / signing as needed):

```bash
curl -X POST https://<your-n8n-domain>/webhook/tally-lead \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "FORM_RESPONSE",
    "data": {
      "formName": "B2B Contact Demo",
      "formUrl": "https://tally.so/r/demo",
      "fields": [
        {"label": "Name", "value": "Sarah Chen"},
        {"label": "Email", "value": "sarah.chen+demo@techscale.io"},
        {"label": "Role", "value": "Head of Operations"},
        {"label": "Company", "value": "TechScale Inc"},
        {"label": "Message", "value": "We need workflow automation for sales. Budget approved for Q3. Need a demo this week."}
      ]
    }
  }'
```

**Expected chain:**

```text
Intake → Enrichment → Scoring → CRM Sync
  → HubSpot Contact upsert (if crm_gate passed)
  → Slack high_score Block Kit
  → First Touch: outbound draft → first_touch_status ≈ draft_pending_review
```

### Checklist

- [ ] `leads` new/updated row: `score` high, `recommended_action` toward `crm_sync`, `enrichment_status=complete`
- [ ] `crm_status=synced` (or equivalent success); HubSpot Contact exists
- [ ] Slack high-score card in demo channel (Assign / Junk / Nurture buttons)
- [ ] First-touch draft fields present; `first_touch_status=draft_pending_review` when first-touch gate passes
- [ ] Copy `correlation_id` / `lead_id` for OBS

### Screenshot slots

| # | Capture |
|---|--------|
| A1 | Sheets `leads` row (score, statuses, `correlation_id`) |
| A2 | Slack Block Kit notification |
| A3 | Langfuse generation for `/score` or `/enrich` (prompt version) |
| A4 | Jaeger trace spanning n8n + sidecar (`correlation_id` / timing) |

**Status:** [ ] Done

---

## Scenario B — Slack Assign + HubSpot DRAFT (required)

**Trigger:** On the Scenario A Slack card, click **Assign**.

**Expected:**

```text
Slack Actions → Execute Post-Assign CRM Sync
  → HubSpot Upsert Contact
  → Load Draft From Lead → HubSpot Log Outbound Email (DRAFT)
  → Sheets review / first_touch fields updated
```

### Checklist

- [ ] Sheets: `review_status=approved`, `lead_stage=sql`, owner/reviewer set
- [ ] HubSpot Contact page shows demo contact
- [ ] HubSpot timeline / engagements: outbound email as **DRAFT** (not auto-sent)
- [ ] Sheets `crm_contact_id` populated
- [ ] Slack message updated (chat.update — not a second stale card)

### Screenshot slots

| # | Capture |
|---|--------|
| B1 | HubSpot Contact |
| B2 | HubSpot DRAFT email on timeline |
| B3 | Sheets `crm_contact_id` + review fields |

**Status:** [ ] Done

---

## Scenario C — Slack Nurture / Junk (recommended)

**Trigger:** Submit another lead (or reuse a second notification) → click **Nurture** or **Junk**.

### Checklist

- [ ] **Junk:** `review_status=rejected`, `recommended_action=reject`, `lead_stage=junk`
- [ ] **Nurture:** `review_status=review_later`, `lead_stage=nurture` (optional CRM notify path)
- [ ] Slack card updated

### Screenshot slots

| # | Capture |
|---|--------|
| C1 | Sheets status fields after Nurture or Junk |

**Status:** [ ] Done

---

## Scenario D — Manual Review path (recommended)

**Trigger:** Lead that lands in gray-zone / `review_required` (weaker message, freemail, or score between `score_gray_low`–`score_gray_high`), or a path that hits `/manual-review`.

### Checklist

- [ ] Slack `review_required` notification (if enabled + production)
- [ ] Sheets `review_status=pending_review` (or equivalent pending state)
- [ ] Pipeline did not treat as silent high-score CRM without review when triggers apply

### Screenshot slots

| # | Capture |
|---|--------|
| D1 | Slack review notification |
| D2 | Sheets `review_status=pending_review` |

**Status:** [ ] Done

---

## Scenario E — Calendly booking (required)

**Paid Calendly is optional.** Free plans often cannot push webhooks. Prefer a **signed mock POST** to `/webhook/calendly` (same shape as `invitee.created`); email must match a lead `contact_email`. Full curl + HMAC steps: [zh/DEMO_RUNBOOK.md](zh/DEMO_RUNBOOK.md#场景-e--calendly-预约必做可用模拟).

**Trigger (real):** Book a Calendly test event whose invitee email **matches** a lead `contact_email` (`invitee.created`).

### Checklist

- [ ] **B2B Lead Calendly Webhook** execution succeeds (signature OK or key empty skip for local demo only)
- [ ] Sheets: `meeting_status` / `meeting_time` / Calendly URI fields updated
- [ ] Optional Slack meeting notify if wired + enabled

### Screenshot slots

| # | Capture |
|---|--------|
| E1 | Sheets meeting fields |
| E2 | n8n Calendly execution success |

**Status:** [ ] Done

---

## Scenario F — Calendly cancel (optional)

**Trigger:** Cancel the same event (`invitee.canceled`).

### Checklist

- [ ] Meeting fields reflect canceled path
- [ ] Execution succeeds

**Status:** [ ] Done

---

## Scenario G — Booking Follow-up (recommended)

**Prep (Sheets):** At least one lead with:

- `score >= score_threshold_high`
- `meeting_status=not_booked`
- `created_at` older than `booking_reminder_hours` (default 24)
- `booking_reminder_sent` not true

**Trigger:** Manually **Execute** **B2B Lead Booking Follow-up** (or wait for cron ~10:00).

### Checklist

- [ ] Slack booking reminder in demo channel (`mode=production` + `booking_reminder.enabled=true`)
- [ ] Audit log / sheet: reminder success; `booking_reminder_sent` / `booking_reminder_at` set on success
- [ ] Re-run does not spam the same lead after sent flag is set

### Screenshot slots

| # | Capture |
|---|--------|
| G1 | Slack booking reminder |
| G2 | Sheets booking reminder columns / audit |

**Status:** [ ] Done

---

## Scenario H — Daily / Weekly Summary (recommended; post-debug)

Requires **H0** passed. Now with **`mode=production`** and `daily_summary` / `weekly_summary` **`enabled=true`**.

### Daily (production)

**Window:** Cron/manual run aggregates **yesterday UTC** (`created_at` / error `timestamp` prefix = yesterday’s `YYYY-MM-DD`). Leads created “today only” will not appear in Daily counts.

1. [ ] Ensure yesterday-UTC leads exist (or temporarily set a demo row’s `created_at` to yesterday for the recording)
2. [ ] Execute **B2B Lead Daily Summary**
3. [ ] Path: **Should Send Daily?** → **Slack Daily Report** (not Skip)
4. [ ] Slack digest: new leads, high-score count (threshold from `score_threshold_high`), CRM/Slack/review KPIs
5. [ ] Single Slack message for the run (aggregate, not per-row spam)

### Weekly (production)

1. [ ] Execute **B2B Lead Weekly Summary**
2. [ ] `/weekly-insights` succeeds or degrades gracefully; Merge report present
3. [ ] Path: **Should Send Weekly?** → **Slack Weekly Report**
4. [ ] **Append Weekly Metrics** still runs after Slack (or after Skip in other modes)
5. [ ] If Slack node fails: metrics preserved and still Append (error handler keeps upstream report)
6. [ ] Langfuse: weekly insights generation

### Screenshot slots

| # | Capture |
|---|--------|
| H1 | Slack Daily digest |
| H2 | Slack Weekly digest |
| H3 | `weekly_metrics` new row |
| H4 | Langfuse `/weekly-insights` |

**Status:** [ ] Done

---

## Scenario I — Error Handler (optional)

**Trigger:** Controllable fault (e.g. briefly wrong `GOOGLE_SHEETS_DOCUMENT_ID` on one node, or force a failing branch), then restore.

### Checklist

- [ ] Row in `error_logs`
- [ ] Slack `error_alert` only if `error_alert.enabled=true` **and** `mode=production`
- [ ] Fix config; next lead succeeds

### Screenshot slots

| # | Capture |
|---|--------|
| I1 | `error_logs` row |
| I2 | Optional Slack error_alert |

**Status:** [ ] Done

---

## Scenario J — Workflow panorama (required)

### Checklist

- [ ] n8n: list / overview of all **9** workflows
- [ ] Canvas: **Enrichment Scoring** (HTTP to sidecar visible)
- [ ] Canvas: **CRM Sync Notification** (HubSpot + Slack)

### Screenshot slots

| # | Capture |
|---|--------|
| J1 | Nine workflows list |
| J2 | Enrichment canvas |
| J3 | CRM Sync canvas (optional extra) |

**Status:** [ ] Done

---

## Observability quick pass (during A or H)

| Check | How |
|-------|-----|
| Langfuse | Search by `correlation_id` / `lead_id`; confirm prompt version on enrich/score |
| Jaeger | Services `n8n-platform` / `n8n-crm-ai-service` around execution time |
| Sidecar | `/health`, `/prompts` still healthy after demo load |

Details: [OBSERVABILITY.md](en/OBSERVABILITY.md).

---

## Material checklist (for Phase 4 capture)

Target ~10–12 stills + one 2–3 min English walkthrough (SSH tunnel + local Loom/OBS recommended).

**Live tracker + filenames:** [assets/MANIFEST.md](../assets/MANIFEST.md) · [assets/README.md](../assets/README.md) · narration [assets/demo-video-script.md](../assets/demo-video-script.md)

Tunnel helper: `REMOTE_HOST=user@host ./scripts/ssh_tunnel_demo.sh`

| # | Asset | Filename | Source |
|---|--------|----------|--------|
| 1 | Architecture diagram | `assets/architecture.png` | Pre-made SVG |
| 2 | Nine workflows list | `assets/screenshots/01-n8n-workflows-list.png` | J |
| 3 | Enrichment canvas | `assets/screenshots/02-enrichment-canvas.png` | J |
| 4 | Tally → Sheets row | `assets/screenshots/03-sheets-new-lead.png` | A |
| 5 | Slack Block Kit | `assets/screenshots/04-slack-high-score.png` | A |
| 6 | Langfuse (prompt version) | `assets/screenshots/05-langfuse-score-trace.png` | A / H |
| 7 | Jaeger (`correlation_id`) | `assets/screenshots/06-jaeger-correlation.png` | A |
| 8 | HubSpot Contact | `assets/screenshots/07-hubspot-contact.png` | B |
| 9 | HubSpot DRAFT email | `assets/screenshots/08-hubspot-draft-email.png` | B |
| 10 | Calendly → meeting fields | `assets/screenshots/09-calendly-meeting-fields.png` | E |
| 11 | Daily / Weekly Slack | `assets/screenshots/10-daily-weekly-slack.png` | H |
| 12 | Booking reminder Slack | `assets/screenshots/11-booking-reminder-slack.png` | G |

Suggested video outline: problem + architecture → Tally → Slack + Langfuse → Assign / HubSpot DRAFT → Calendly → Jaeger CTA (full script in `assets/demo-video-script.md`).

Store curated stills under `assets/screenshots/`; unmasked originals under `assets/raw/` (gitignored). **Do not commit** real PII.

---

## Post-demo cleanup

- [ ] `config_main.mode` → `test` (or leave production only if intentionally keeping a live demo env)
- [ ] Delete HubSpot demo contacts
- [ ] Optional: clear Slack demo channel history
- [ ] Restore any temporary sheet edits (e.g. backdated `created_at` for Daily)

---

## Gate reference (Daily / Weekly)

| Workflow | Sends Slack when | Still does when Slack skipped |
|----------|------------------|-------------------------------|
| Daily Summary | `mode=production` **and** `daily_summary.enabled=true` | Builds yesterday-UTC summary → **Skip Daily Slack** |
| Weekly Summary | `mode=production` **and** `weekly_summary.enabled=true` (strict) | Metrics + AI → **Skip Weekly Slack** → still **Append** `weekly_metrics` |

High-score counts in digests use `config_main.score_threshold_high`.

See [TEST_PRODUCTION.md](en/TEST_PRODUCTION.md) and [ERROR_HANDLING_NODES.md](en/ERROR_HANDLING_NODES.md).

---

## Run progress summary

| Scenario | Required? | Done |
|----------|-----------|------|
| H0 Daily/Weekly test gate | Strongly recommended | [ ] |
| A High-score path | Required | [ ] |
| B Assign + HubSpot DRAFT | Required | [ ] |
| C Nurture / Junk | Recommended | [ ] |
| D Manual review | Recommended | [ ] |
| E Calendly book | Required | [ ] |
| F Calendly cancel | Optional | [ ] |
| G Booking follow-up | Recommended | [ ] |
| H Daily/Weekly Slack | Recommended | [ ] |
| I Error Handler | Optional | [ ] |
| J Workflow panorama | Required | [ ] |

**Success bar (portfolio):** A + B + E + J complete; ≥2 of C/D/G/H; ≥1 Langfuse + ≥1 Jaeger still; Daily/Weekly proven via H0 and preferably H.

# Demo video narration (EN, ~2–3 min)

Record with SSH tunnel + local Loom/OBS. Split screen when useful: n8n execution left, Sheets/Slack right.

## 0:00–0:20 — Problem + architecture

> B2B inbound leads often stall between form submit, scoring, CRM, and human follow-up. This stack runs production-mode automation on n8n: intake from Tally, AI enrichment and scoring, HubSpot sync, Slack human-in-the-loop, Calendly updates — with Jaeger and Langfuse for full-path observability. Here’s the architecture.

**On screen:** `architecture.png` (3–5s), then n8n workflows list.

## 0:20–0:50 — Tally → Sheets + score

> A high-intent lead submits the demo form. Intake writes the row, enrichment and scoring run through the Python sidecar, and the lead lands in Sheets with score, recommended action, and a correlation id.

**On screen:** Tally submit → Sheets new row → Enrichment execution (optional).

## 0:50–1:20 — Slack + Langfuse

> High-score leads trigger a Slack Block Kit card so sales can Assign, Nurture, or Junk. In Langfuse we see the scoring generation with prompt version — not a black box.

**On screen:** Slack card → Langfuse trace.

## 1:20–1:50 — Assign → HubSpot DRAFT

> On Assign, the workflow upserts the HubSpot contact and logs the AI outbound email as a DRAFT on the timeline — human-approved, not auto-sent.

**On screen:** Slack Assign click → HubSpot contact → DRAFT email.

## 1:50–2:10 — Calendly

> When the invitee books, the Calendly webhook updates meeting fields on the same lead row — one system of record.

**On screen:** Calendly book (or simulated webhook) → Sheets meeting fields.

## 2:10–2:30 — Jaeger + CTA

> In Jaeger, the same correlation id ties n8n and the AI sidecar. Ready for client deploy: start in test mode, flip to production when gates and credentials are ready.

**On screen:** Jaeger trace → short CTA (repo / contact).

---

Optional cutaways (if time): Daily/Weekly Slack digest, booking reminder.

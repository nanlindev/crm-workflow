# Portfolio copy drafts

Short drafts for Upwork / Fiverr / LinkedIn. Pair with [SHOWCASE](SHOWCASE.md) stills and [CASE_STUDY](CASE_STUDY.md).

**Public repo:** `https://github.com/nanlindev/crm-workflow`  
Replace `(demo video URL)` after publishing Loom / MP4.

---

## Backfill GitHub link (after repo is public)

| Platform | Where to paste |
|----------|----------------|
| **Upwork** portfolio | Add content → **Link** → repo URL |
| **Fiverr** Gig / portfolio | Gallery link or portfolio project link |
| **Codementor** project | **Project Link** field |
| **LinkedIn** post | Include repo URL in the post body |

---

## Upwork portfolio project

**Title:** Production B2B Lead Automation — n8n + AI + HubSpot + Slack + Observability

**Summary**

End-to-end B2B inbound pipeline on n8n (production mode): Tally form → DeepSeek enrichment & scoring → Google Sheets as system of record → Slack Assign / Junk / Nurture → HubSpot Contact + human-approved email DRAFT → Calendly meeting sync → daily/weekly digests. Every lead carries a `correlation_id` joined in Jaeger and Langfuse.

**What I built**

- 9 n8n workflows (intake, enrichment/scoring, CRM sync, Slack actions, Calendly, booking follow-up, daily/weekly summary, error handler)
- FastAPI AI sidecar (`/enrich`, `/score`, `/outbound-email`, `/weekly-insights`, …) with versioned prompts
- test → production gates so Slack/HubSpot stay off until ready
- OpenTelemetry → Jaeger + Langfuse for LLM provenance

**Proof**

- GitHub: https://github.com/nanlindev/crm-workflow
- Demo video: `(demo video URL)`
- Architecture + screenshots: repo `docs/SHOWCASE.md` / `assets/`
- Case narrative: `docs/CASE_STUDY.md`

**Stack:** n8n, Python/FastAPI, DeepSeek, Google Sheets, HubSpot, Slack, Calendly, OTEL, Jaeger, Langfuse

---

## LinkedIn — Featured / Media (作品集位)

- **Title:** Production B2B Lead Automation (n8n + AI + HubSpot)
- **Media:** `assets/raw/b2b-begin.png` or `assets/architecture.png` + short demo video
- **Link:** `https://github.com/nanlindev/crm-workflow`

## LinkedIn post (production full-chain angle)

Most “AI lead scoring” demos stop at a pretty Slack message.

I ran this stack in **production mode** on a remote host: form submit → score → Slack human-in-the-loop → HubSpot **DRAFT** email (not auto-sent) → Calendly fields on the same Sheets row — with **Jaeger + Langfuse** on the same `correlation_id`.

Human control stays in Slack (Assign / Junk / Nurture). Clients can wire everything in `test`, then flip one config cell to go live.

Open-source template + screenshots: https://github.com/nanlindev/crm-workflow  
Demo: `(demo video URL)`

#n8n #HubSpot #B2B #observability #automation #LLMOps

---

## Fiverr gig (three packages)

**Gig title:** I will build a production-ready n8n B2B lead automation with AI scoring and HubSpot

**Intro**

I deploy a gated lead pipeline: form → AI score → Slack review → HubSpot Contact + DRAFT email → calendar sync → digests, with optional Jaeger/Langfuse. You get workflows, a Python sidecar, Sheets templates, and a runbook — not a one-off Zap.

### Basic — Pipeline core

- Intake + enrichment/scoring + CRM sync + Slack notify
- Google Sheets templates + `test` mode gates
- Install notes + one test-lead walkthrough

### Standard — Human-in-the-loop + CRM

Everything in Basic, plus:

- Slack Assign / Junk / Nurture
- HubSpot Contact upsert + post-Assign email DRAFT
- Calendly webhook meeting fields
- Error handler → error_logs

### Premium — Ops + observability

Everything in Standard, plus:

- Booking follow-up + Daily / Weekly Summary digests
- Langfuse prompt tracing + Jaeger / OTEL wiring guidance
- Production demo runbook + screenshot checklist
- Remote deploy assist (n8n + sidecar networks)

**FAQ note:** Production Slack/HubSpot only fire when `mode=production` and notification flags allow — safe to install in test first.

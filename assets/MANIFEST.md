# Asset capture manifest

Track Phase 4 stills + video. Mark **Captured** when the file exists under the path below (demo identities only, or masked).

| # | Path | Scenario | Captured | Notes |
|---|------|----------|----------|-------|
| 1 | `assets/architecture.png` | Pre-made | [x] | Rendered from `architecture.svg` |
| 2 | `assets/screenshots/01-n8n-workflows-list.png` | J | [ ] | Nine workflows list in n8n |
| 3 | `assets/screenshots/02-enrichment-canvas.png` | J | [ ] | Enrichment & Scoring canvas |
| 4 | `assets/screenshots/03-sheets-new-lead.png` | A | [ ] | New leads row after Tally |
| 5 | `assets/screenshots/04-slack-high-score.png` | A | [ ] | Block Kit high_score card |
| 6 | `assets/screenshots/05-langfuse-score-trace.png` | A / H | [ ] | Show prompt version |
| 7 | `assets/screenshots/06-jaeger-correlation.png` | A | [ ] | `correlation_id` / `n8n-platform` |
| 8 | `assets/screenshots/07-hubspot-contact.png` | B | [ ] | Contact after Assign |
| 9 | `assets/screenshots/08-hubspot-draft-email.png` | B | [ ] | Timeline DRAFT email |
| 10 | `assets/screenshots/09-calendly-meeting-fields.png` | E | [ ] | Sheets meeting fields |
| 11 | `assets/screenshots/10-daily-weekly-slack.png` | H | [ ] | Digest message(s) |
| 12 | `assets/screenshots/11-booking-reminder-slack.png` | G | [ ] | Booking reminder |

## Video

| Asset | Status | Location |
|-------|--------|----------|
| 2–3 min English walkthrough | [ ] | `assets/demo-video.mp4` **or** Loom URL below |
| Narration script | [x] | `assets/demo-video-script.md` |

**Loom / video URL:** _(paste after recording)_

```text

```

## Capture session checklist

- [ ] `REMOTE_HOST` tunnel up (`scripts/ssh_tunnel_demo.sh`)
- [ ] Sheets `mode=production`; notifications `enabled=true` for events you will film
- [ ] Demo Slack channel / HubSpot sandbox / demo emails only
- [ ] Run DEMO_RUNBOOK A → B → E → J (plus ≥2 of C/D/G/H)
- [ ] Drop stills into `screenshots/` with exact names above
- [ ] Post-demo cleanup (mode→test, delete HubSpot demo contacts)

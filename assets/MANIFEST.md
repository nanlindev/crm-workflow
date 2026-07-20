# Asset capture manifest

Track Phase 4 stills + video. Mark **Captured** when the file exists under the path below (demo identities only, or masked).

| # | Path | Scenario | Captured | Notes |
|---|------|----------|----------|-------|
| 1 | `assets/architecture.png` | Pre-made | [x] | Rendered from `architecture.svg` |
| 2 | `assets/screenshots/01-n8n-workflows-list.png` | J | [x] | Nine workflows list in n8n |
| 3 | `assets/screenshots/02-enrichment-canvas.png` | J | [x] | Enrichment & Scoring canvas |
| 4 | `assets/screenshots/03-sheets-new-lead.png` | A | [x] | New leads row after Tally |
| 5 | `assets/screenshots/04-slack-high-score.png` | A | [x] | Block Kit high_score card |
| 6 | `assets/screenshots/05-langfuse-score-trace.png` | A / H | [x] | Show prompt version |
| 7 | `assets/screenshots/06-jaeger-correlation.png` | A | [x] | `correlation_id` / `n8n-platform` |
| 8 | `assets/screenshots/07-hubspot-contact.png` | B | [x] | Contact **and** timeline DRAFT email (single still; no `08`) |
| 9 | _(merged into 07)_ | B | [x] | Was `08-hubspot-draft-email.png` — covered by `07` |
| 10 | `assets/screenshots/09-calendly-meeting-fields.png` | E | [x] | Sheets meeting fields |
| 11 | `assets/screenshots/10-daily-weekly-slack.png` | H | [x] | Digest message(s) |
| 12 | `assets/screenshots/11-booking-reminder-slack.png` | G | [x] | Booking reminder |

## Video

| Asset | Status | Location |
|-------|--------|----------|
| 2–3 min English walkthrough | [ ] | `assets/demo-video.mp4` **or** Loom URL below |
| Fiverr Gallery short (≤75s, titles only) | [ ] | keep under 50MB |
| Narration script | [x] | `assets/demo-video-script.md` |

**Loom / video URL:** _(paste after recording)_

```text

```

## Capture session checklist

- [x] Drop stills into `screenshots/` with exact names above
- [ ] `REMOTE_HOST` tunnel up (`scripts/ssh_tunnel_demo.sh`) when re-recording
- [ ] Post-demo cleanup (mode→test, delete HubSpot demo contacts) if still on production

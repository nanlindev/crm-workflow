# Portfolio assets

Curated stills and architecture for the public showcase. Capture status: [MANIFEST.md](MANIFEST.md).  
Full demo steps: [DEMO_RUNBOOK](../docs/DEMO_RUNBOOK.md) · [中文版](../docs/zh/DEMO_RUNBOOK.md).

## Layout

```text
assets/
  architecture.svg          # editable source
  architecture.png          # rendered for README / SHOWCASE
  demo-video-script.md      # English narration outline
  MANIFEST.md               # filenames ↔ scenarios ↔ status (+ YouTube URL)
  screenshots/              # curated stills (no real PII)
  raw/                      # unmasked originals (gitignored)
```

**Demo video:** https://youtu.be/xr4y7ulGIV8 (listed in MANIFEST; not stored as mp4 in git)

## Render architecture

```bash
chmod +x scripts/render_architecture.sh
./scripts/render_architecture.sh
```

## Screenshot filenames

| # | File | Scenario |
|---|------|----------|
| 1 | `architecture.png` | Pre-made |
| 2 | `screenshots/01-n8n-workflows-list.png` | J |
| 3 | `screenshots/02-enrichment-canvas.png` | J |
| 4 | `screenshots/03-sheets-new-lead.png` | A |
| 5 | `screenshots/04-slack-high-score.png` | A |
| 6 | `screenshots/05-langfuse-score-trace.png` | A / H |
| 7 | `screenshots/06-jaeger-correlation.png` | A |
| 8 | `screenshots/07-hubspot-contact.png` | B (Contact + DRAFT; no separate `08`) |
| 9 | — | merged into `07` |
| 10 | `screenshots/09-calendly-meeting-fields.png` | E |
| 11 | `screenshots/10-daily-weekly-slack.png` | H |
| 12 | `screenshots/11-booking-reminder-slack.png` | G |

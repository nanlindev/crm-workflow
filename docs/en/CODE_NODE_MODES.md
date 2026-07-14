# Code node modes

n8n Code node v2 has two execution modes:

| Mode | Meaning | Use when |
|------|---------|----------|
| `runOnceForAllItems` | Runs once; use `$input.all()` / `$('Node').all()` | Dedup, aggregating config sheet rows, expand 1→N |
| `runOnceForEachItem` | Runs per inbound item; use `$input.item` | Per-lead transforms, error handlers, gates |

## Conventions in this project

### Must use `runOnceForAllItems`

| Node | Workflow | Why |
|------|----------|-----|
| `Dedup Lead` | Intake | Full-sheet `$('Read All Leads').all()` |
| `Normalize config_*` | Enrichment / Booking / Slack / Summaries | Collapse sheet rows to `{ rows: [...] }` |
| `Build Global Config` | Enrichment | Merge config wrappers |
| `Filter Due Booking Reminders` / `Expand Due Leads` / `Load Booking Config` | Booking Follow-up | Multi-row filter / expand |
| `Load Daily Config` / `Build Daily Summary` | Daily Summary | Config + aggregate yesterday UTC |
| `Load Weekly Config` / `Build Weekly Metrics` / `Merge Weekly Report` | Weekly Summary | Config + week aggregate |
| `Check Error Alert Enabled` | Error Handler | Read config rows |

### Must use `runOnceForEachItem`

| Node | Workflow | Why |
|------|----------|-----|
| All `Handle * Error` / Slack error loggers | Most workflows | Single error item + `$input.item` |
| `Attach Hunter Data` | Enrichment | Pair HTTP item with domain enrichment |
| Review / routing gates | Enrichment | Per-lead |
| `Mark Draft Pending Review` / `Build Notification Payload` | CRM Sync | Per lead |
| `Prepare Slack CRM Payload` | Slack Actions | One interaction (may still call `$('Read All Leads…').all()`) |

### Pitfalls

1. **`Mark Draft Pending Review`** must use `$input.item.json`, not `$('Merge Outbound Email').item`, or the LLM failure path breaks.
2. Calling `$('Some Sheets Read').all()` inside `runOnceForEachItem` is valid for cross-node reads.
3. Generator default in `code_node()` is `runOnceForEachItem`; batch nodes pass `mode="runOnceForAllItems"` explicitly.
4. `scripts/sync_workflows_from_export.py` can force EachItem for listed node names after UI export.

See [WORKFLOWS.md](WORKFLOWS.md).

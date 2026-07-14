# 代码节点 mode 说明

n8n Code 节点 v2 有两种执行模式：

| mode | 含义 | 适用场景 |
|------|------|----------|
| `runOnceForAllItems` | 整个节点执行一次；用 `$input.all()` / `$('Node').all()` | 去重、聚合 config 表、1→N 展开 |
| `runOnceForEachItem` | 每个入站 item 各执行一次；用 `$input.item` | 单条 lead 变换、错误处理、门控 |

## 本项目约定

### 必须用 `runOnceForAllItems`

| 节点 | 工作流 | 原因 |
|------|--------|------|
| `Dedup Lead` | Intake | `$('Read All Leads').all()` 全表去重 |
| `Normalize config_*` | Enrichment / Booking / Slack / Summaries | 将 Sheets 多行收成 `{ rows: [...] }` |
| `Build Global Config` | Enrichment | 聚合 config wrapper |
| `Filter Due Booking Reminders` / `Expand Due Leads` / `Load Booking Config` | Booking Follow-up | 多行过滤 / 展开 |
| `Load Daily Config` / `Build Daily Summary` | Daily Summary | 配置 + 聚合昨天 UTC |
| `Load Weekly Config` / `Build Weekly Metrics` / `Merge Weekly Report` | Weekly Summary | 配置 + 周聚合 |
| `Check Error Alert Enabled` | Error Handler | 读 config 行 |

### 必须用 `runOnceForEachItem`

| 节点 | 工作流 | 原因 |
|------|--------|------|
| 所有 `Handle * Error` / Slack 错误日志节点 | 多数工作流 | 单条错误 item + `$input.item` |
| `Attach Hunter Data` | Enrichment | HTTP item 与 enrichment 配对 |
| Review / routing 门控 | Enrichment | 单 lead |
| `Mark Draft Pending Review` / `Build Notification Payload` | CRM Sync | 单 lead |
| `Prepare Slack CRM Payload` | Slack Actions | 单次交互（内部仍可 `$('Read All Leads…').all()`） |

### 注意点

1. **`Mark Draft Pending Review`** 必须用 `$input.item.json`，不能用 `$('Merge Outbound Email').item`，否则 LLM 失败路径会报错。
2. 在 `runOnceForEachItem` 下调用 `$('Some Sheets Read').all()` 做跨节点读表是合法的。
3. 生成器 `code_node()` 默认 `runOnceForEachItem`；批量节点显式传 `mode="runOnceForAllItems"`。
4. `scripts/sync_workflows_from_export.py` 可对导出 JSON 强制部分节点为 EachItem。

详见 [WORKFLOWS.md](WORKFLOWS.md)。

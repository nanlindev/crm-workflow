# Code 节点 mode 说明

n8n Code 节点 v2 有两种执行模式：

| mode | 含义 | 适用场景 |
|------|------|----------|
| `runOnceForAllItems`（默认） | 整个节点只执行一次，用 `$input.all()` / `$('Node').all()` 处理批量 | 去重、聚合 config 表、展开多行 |
| `runOnceForEachItem` | 每个入站 item 各执行一次，用 `$input.item` / `$('Node').item` | 单条 lead 变换、错误处理、门控 |

## 当前约定

### 必须用 `runOnceForAllItems`

| 节点 | 工作流 | 原因 |
|------|--------|------|
| `Dedup Lead` | Intake | `$('Read All Leads').all()` 全表去重 |
| `Normalize config_*` | Enrichment / Booking / Slack | 将 Sheets 多行收成 `{ rows: [...] }` |
| `Build Global Config` | Enrichment | 聚合多张 config 表（若上游为单 item 也可用 EachItem） |
| `Filter Due Booking Reminders` | Booking Follow-up | 过滤多行 leads |
| `Expand Due Leads` | Booking Follow-up | 1→N 展开 |
| `Load Booking Config` | Booking Follow-up | 读 config 行聚合 |
| `Check Error Alert Enabled` | Error Handler | `$('Read config_*').all()` 读配置 |

### 必须用 `runOnceForEachItem`

| 节点 | 工作流 | 原因 |
|------|--------|------|
| 所有 `Handle * Error` | 各工作流 | 单条错误 item + `$input.item` |
| `Attach Hunter Data` | Enrichment | `$input.item` + `$('Domain Enrichment').item` |
| `Apply Review Rules` / `Apply Routing Rules` | Enrichment | 单 lead 门控 |
| `Mark Draft Pending Review` | CRM Sync | `$input.item.json`（兼容 success / fallback 两路） |
| `Build Notification Payload` | CRM Sync | 单 lead Slack 卡片 |
| `Prepare Slack CRM Payload` | Slack Actions | 单次按钮交互（内部 `$('Read All Leads').all()` 跨节点读表，仍用 EachItem） |

### 已知注意点

1. **`Mark Draft Pending Review`** 必须用 `$input.item.json`，不能用 `$('Merge Outbound Email').item`，否则 LLM 失败路径（`Handle Outbound Email Failure`）会因未执行 Merge 节点而报错。
2. **`Prepare Slack CRM Payload`** 在 `runOnceForEachItem` 下调用 `$('Read All Leads For Slack').all()` 是合法模式：当前 item 是 Slack 交互，跨节点读取 Sheets 全表做 lead 匹配。
3. **Normalize config 节点** 在 Enrichment 中默认为 `runOnceForAllItems`（未显式写 mode 时）：因上游 Sheets Read 返回多行，需一次聚合。

## 生成器与同步

- `scripts/generate_workflows.py` 中 `code_node()` 默认 `runOnceForEachItem`；批量节点显式传 `mode="runOnceForAllItems"`。
- `scripts/sync_workflows_from_export.py` 在同步时为列在 `CODE_NODE_EACH_ITEM` 中的节点强制 `runOnceForEachItem`。

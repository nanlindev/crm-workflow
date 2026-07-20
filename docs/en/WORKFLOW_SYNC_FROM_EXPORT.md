# 从 workflows-new 同步到 canonical JSON

将 `workflows/workflows-new/*.json`（n8n UI 导出）合并进 `workflows/*.json`，并应用仓库卫生规则与已知修复。

## 脚本

```bash
cd /path/to/crm-workflow
python3 scripts/sync_workflows_from_export.py
```

## 同步时自动处理

| 项 | 说明 |
|----|------|
| 凭证 | → 占位符（`GOOGLE_SHEETS_CREDENTIAL_ID` 等） |
| `errorWorkflow` | 主工作流 → `B2B Lead Error Handler`；Error Handler 自身清空 |
| `active` | → `false`；删除 `pinData` |
| `Final Status Write Failed End1` | 删除并重连 |
| `Attach Hunter Data` | `hunter_error_message` + `company_region` |
| `Parse Slack Payload` | `container?.message_ts` |
| `Normalize Enriched Lead` | `?? ''` 默认值 |
| `Mark Draft Pending Review` | `$input.item.json`（兼容 fallback 路径） |
| Code 节点 mode | 见 `docs/CODE_NODE_MODES.md` 中 `CODE_NODE_EACH_ITEM` 列表 |
| Webhook rawBody | Tally / Calendly 开启 `rawBody: true` |

## 数据源策略

- **Google Sheets**：评分、路由、review、邮件草稿等 intelligence 的**唯一真相源**
- **HubSpot**：仅基础 Contact（email/name/company/role）+ Assign 后 email DRAFT 日志；不同步自定义评分列

## 与 generate_workflows.py 的关系

1. **线上改 UI** → 导出到 `workflows-new/` → `sync_workflows_from_export.py`
2. **改生成逻辑** → 编辑 `generate_workflows.py` → `python3 scripts/generate_workflows.py`

两者应保持一致；大改后建议先 sync 再对照更新 generator。

## 当前功能（2026-06）

- Tally webhook 签名校验（fail-closed）
- `/manual-review` 接线（Enrichment）
- First Touch：`draft_pending_review` → Slack Assign → HubSpot DRAFT
- `config_notifications.enabled` 控制 Slack / error_alert
- Hunter `companies/find` + `company_region`

## 执行顺序

```bash
python3 scripts/sync_workflows_from_export.py   # UI 导出 → workflows/
# 或
python3 scripts/generate_workflows.py           # 从代码生成 workflows/
```

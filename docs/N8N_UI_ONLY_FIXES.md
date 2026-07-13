# n8n 手动修复清单（不重新导入）

> **状态：** 2026-06 线上 UI 修改已完成。请以 `workflows/workflows-new/` 导出 + `scripts/sync_workflows_from_export.py` 同步到 `workflows/`。本文档保留作历史参考。

在**当前已运行的 n8n** 里逐项修改，**不要** Import from File。

每步改完点 **Save**。建议按顺序做，做完一项可 Pin 测试数据或跑一条 execution 验证。

---

## 修复 1：删除冗余 End 节点

**工作流：** `B2B Lead CRM Sync Notification`

1. 打开工作流，搜索节点 `Final Status Write Failed End1`
2. 若不存在 → **跳过本项**
3. 点击 `Handle Final Status Error` 节点
4. 把 **错误输出**（下方第二根线）从 `Final Status Write Failed End1` 拖到 `Final Status Write Failed End`
5. 选中 `Final Status Write Failed End1` → Delete
6. **Save**

---

## 修复 2：`Attach Hunter Data` 补错误记录

**工作流：** `B2B Lead Enrichment Scoring`  
**节点：** `Attach Hunter Data`（Code）

1. 双击节点，**全选替换**为下面代码
2. **Save**

```javascript
const lead = $('Domain Enrichment').item.json;
const resp = $input.item.json || {};
const hasError = $input.item.error;
const errorObj = hasError || {};
const errorMessage =
  errorObj.message ||
  errorObj.description ||
  (typeof errorObj === 'string' ? errorObj : null) ||
  '';
const co = resp.data;

const hasData = !hasError && co && (co.name || co.category?.industry);
const external = hasData
  ? JSON.stringify({
      source: 'hunter',
      name: co.name,
      domain: co.domain,
      industry: co.category?.industry || co.category?.sector || '',
      company_size: co.metrics?.employees || '',
      description: co.description || '',
      location: co.location || '',
      founded: co.foundedYear,
      tags: co.tags || [],
    })
  : '';

return {
  ...lead,
  external_enrichment: external,
  hunter_error_message: hasError ? String(errorMessage || 'Hunter Company Lookup failed') : '',
  _metadata: {
    ...(lead._metadata || {}),
    processing_stage: hasError
      ? 'hunter_enrichment_failed'
      : hasData
        ? 'hunter_company_enriched'
        : 'hunter_skipped',
    ...(hasError
      ? { severity: 'low', error_message: errorMessage, failed_node: 'Hunter Company Lookup' }
      : {}),
  },
};
```

**验证：** corporate 测试 lead 跑 Enrichment；Hunter 失败时 execution 里应有 `hunter_error_message`。

---

## 修复 3：`Parse Slack Payload` 恢复线程 timestamp

**工作流：** `B2B Lead Slack Actions`  
**节点：** `Parse Slack Payload`（Code）

1. 找到 return 对象里的 `message_ts` 行
2. 若为 `payload.message?.ts || ''`，改为：

```javascript
message_ts: payload.message?.ts || payload.container?.message_ts || '',
```

3. **Save**

**验证：** 点 Slack 卡片按钮后，原消息应能更新（按钮移除 / 状态变更）。

---

## 修复 4：`Normalize Enriched Lead` 字段默认值

**工作流：** `B2B Lead Enrichment Scoring`  
**节点：** `Normalize Enriched Lead`（Code）

在 `const payload = { ... }` 里确认以下字段带 `?? ''`（不是裸 `lead.industry`）：

```javascript
industry: lead.industry ?? '',
company_size: lead.company_size ?? '',
content_summary: lead.content_summary ?? '',
intent_signals: lead.intent_signals ?? '',
enrichment_summary: lead.enrichment_summary ?? '',
enrichment_status: lead.enrichment_status ?? '',
```

其余字段（`contact_name`、`sales_memo` 等）保持现有写法即可。  
**Save**

---

## 检查 5：Error Workflow 名称（Settings，非导入）

对以下每个工作流：右上角 **⋯ → Settings**（或工作流设置）：

- B2B Lead Intake
- B2B Lead Enrichment Scoring
- B2B Lead CRM Sync Notification
- B2B Lead Calendly Webhook
- B2B Lead Booking Follow-up
- B2B Lead Slack Actions
- B2B Lead Daily Summary
- B2B Lead Weekly Summary

确认 **Error Workflow** = `B2B Lead Error Handler`（显示名称，不是一串 UUID）。  
若是 UUID → 下拉改选 `B2B Lead Error Handler` → Save。

---

## 检查 6：`Execute CRM Sync` 字段映射

**工作流：** `B2B Lead Enrichment Scoring`  
**节点：** `Execute CRM Sync`

1. 打开节点
2. **Workflow** = `B2B Lead CRM Sync Notification`
3. **Workflow Inputs** = Define Below，且映射非空（约 40 项，含 `industry`、`sales_memo`、`company_region` 等）
4. 若映射为空 → 对照仓库 JSON 或让同事导出一份补全（仍无需整工作流导入）

---

## 检查 7：HubSpot 凭证（保持你现在的 Service Key）

**工作流：** `B2B Lead CRM Sync Notification`

确认以下节点仍绑定 **HubSpot Service Key account**（不要改成 OAuth 占位符）：

- `HubSpot Upsert Contact`
- `HubSpot Log Outbound Email`

无需改动若已正确。

---

## 检查 8：代理 / Python 502（终端，非 n8n 节点）

若 `HTTP Enrich Lead` 仍 502：

```bash
# 确认 n8n 容器 NO_PROXY 含 crm_python_ai
docker exec platform-n8n-n8n_app-1 sh -c 'echo $NO_PROXY'

# 若只有 localhost,127.0.0.1,::1 → 在 platform-n8n 目录重建 n8n（勿 source 精简 NO_PROXY 的 bashrc）
unset NO_PROXY
cd /home/lotey/lindev/platform-n8n
docker compose up -d --force-recreate n8n_app
```

---

## 不必改（保持现状）

| 项 | 原因 |
|----|------|
| Hunter `companies/find` API | 已比 domain-search 更合适 |
| HubSpot Service Key | 生产配置正确 |
| `Resolve Lead Action` 的 `slack_reply` | 体验改进，保留 |
| 工作流 `active: true` | 保持激活 |

---

## 改完后冒烟测试（5 分钟）

1. Tally / curl 提交一条 corporate lead
2. Enrichment：Hunter → Enrich → Score 无报错
3. CRM Sync：`mode=test` 时 `skipped_test_mode` 正常
4. Slack 按钮：assign 一次，看线程是否更新
5. （可选）Calendly 测试预约 → `meeting_status=booked`

---

## 改动了什么（对照表）

| # | 工作流 | 节点 | 改什么 |
|---|--------|------|--------|
| 1 | CRM Sync Notification | End1 | 删冗余节点 |
| 2 | Enrichment Scoring | Attach Hunter Data | 全量替换 JS |
| 3 | Slack Actions | Parse Slack Payload | 一行 message_ts |
| 4 | Enrichment Scoring | Normalize Enriched Lead | 6 个 `?? ''` |
| 5–7 | 多个 | Settings / Execute / HubSpot | 仅检查 |

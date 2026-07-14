# 错误处理

## 两层模型

### 第一层：节点级（可预期错误）

关键外部节点使用 **On Error → Continue (using error output)**，并配有专用 handler Code 节点。逐节点说明见 [ERROR_HANDLING_NODES.md](ERROR_HANDLING_NODES.md)。

| 失败 | Handler | 降级 |
|------|---------|------|
| Config load | Handle Config Load Error | `mode=test`，空通知规则 |
| Sheets read（去重） | Handle Read Leads Error | 跳过去重，视为插入 |
| Sheets write（入库） | Handle Update/Append Lead Error | 带着失败状态继续 |
| LLM enrichment / scoring | Handle Enrichment/Scoring Failure | 回退 + 适用处写入 `fallback_used` |
| HubSpot | Handle HubSpot Failure | `crm_status=failed` |
| Slack notify | Log Slack Notify Error | `notification_status=failed` |
| Daily/Weekly reads | Handle Summary/Weekly Read Error | 降级指标；Daily 跳过 Slack 门控 |
| Weekly Append | Handle Append Weekly Metrics Error | 结束后不挂起 |

Handler 返回扁平对象，含 `_metadata.processing_stage` 与 `severity`。

### 第二层：全局（不可预期错误）

未处理崩溃进入 **B2B Lead Error Handler**（Error Trigger）。

## 导入后绑定 Error Workflow

JSON 中的 `errorWorkflow` 是**名称**；n8n 导入时通常**不会**按 ID 绑定。请手动设置：

**Workflow Settings → Error Workflow → `B2B Lead Error Handler`**

应用到：

- B2B Lead Intake  
- B2B Lead Enrichment Scoring  
- B2B Lead CRM Sync Notification  
- B2B Lead Daily Summary  
- B2B Lead Weekly Summary  
- B2B Lead Booking Follow-up  
- B2B Lead Calendly Webhook  
- B2B Lead Slack Actions  

## 重试默认值

HTTP Request、HubSpot、Slack：Retry On Fail ON，最多 3 次，间隔 5000 ms。

## Error Handler 输出

写入 `error_logs`（`workflow`、`execution_id`、`node`、`message`、`stack`、`correlation_id`、`retry_suggestion`、`timestamp`），并在门控通过时可能发送 Slack `error_alert`。

## 找回 `correlation_id`

1. 按时间查 `leads`  
2. 按执行窗口查 Jaeger  
3. 按 `lead_id` metadata 查 Langfuse  

Intake 尽早写入 `correlation_id`，以最大化可恢复性。

## 生成器修改后重新生成

```bash
python3 scripts/generate_workflows.py
```

重新导入 JSON，并重新绑定凭证与 Error Workflow。

# 可观测性

覆盖 n8n 执行与 LLM 调用的端到端追踪。

## 技术栈

| 组件 | 职责 |
|------|------|
| OpenTelemetry Collector | 接收来自 n8n 与 sidecar 的 OTLP |
| Jaeger | Span UI（`n8n-platform`、`n8n-crm-ai-service`） |
| Langfuse | LLM generation（`crm-workflow` 标签 / resource attrs） |

OBS 栈部署在 `proxy_network`（见兄弟仓库 `otel-collector-stack`、`jaeger-stack`、`langfuse-stack`）。

## 环境检查清单

**platform-n8n**

- OTEL exporter 指向 `http://otel-collector:4318`（或你的 collector URL）
- 建议 `N8N_OTEL_TRACES_INJECT_OUTBOUND=true`，使出站 HTTP 携带 W3C 上下文

**crm sidecar**（见 `.env` / compose）

- `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318`
- `OTEL_SERVICE_NAME=n8n-crm-ai-service`
- `LANGFUSE_HOST=http://langfuse-web:3000`（+ public/secret keys）

**NO_PROXY / no_proxy** 应包含内部 DNS 名，例如：

```text
crm_python_ai,otel-collector,langfuse-web,n8n_app
```

以免 Docker DNS 被强制走外部 HTTP 代理。

## 关联模型

| Id | 位置 | 用途 |
|----|------|------|
| `correlation_id` | Intake 生成；存在线索上；请求头 `X-Correlation-Id` 发给 sidecar | Sheets / 日志中的业务检索键 |
| `trace_id` | OTEL 的 W3C Trace Context | 关联 Jaeger span |
| `lead_id` | 线索行上的 UUID | Langfuse metadata / Sheets |

## 测试线索后如何验证

1. Sheets `leads` → 复制 `correlation_id`。
2. Jaeger → 按执行时间搜索服务 `n8n-platform` 或 `n8n-crm-ai-service`；若已导出可按 correlation 过滤/打标。
3. Langfuse → 查找匹配 `correlation_id` / `lead_id` 的 generation；检查 `prompt_version` 与 `prompt_hash`。
4. Sidecar 健康：`curl http://localhost:8002/health` 与 `/prompts`。

## 排障

| 现象 | 检查 |
|------|------|
| Jaeger 无 span | Collector 是否在跑？两服务是否都在 `proxy_network`？OTEL endpoint 是否正确？ |
| Langfuse 无 generation | keys/host；sidecar 日志中的 Langfuse 认证警告 |
| Span 无法与 LLM 关联 | 出站 inject / 共享 `traceparent`；确认 enrich/score 已执行 |
| Sidecar 对 `/weekly-insights` 返回 404 | 用当前 `python-service` 重建 sidecar 镜像（路由必须存在） |

更多：[ARCHITECTURE.md](ARCHITECTURE.md)、[RUN_EXAMPLE.md](RUN_EXAMPLE.md)。

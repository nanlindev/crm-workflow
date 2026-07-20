# 安装指南

## 前置条件

- Docker 与 Docker Compose v2.20+
- 可访问 CRM sidecar 的 **n8n**（自建推荐）。可选兄弟仓库 `platform-n8n`（共享 n8n + Docker 网络）
- 外部 Docker 网络 `proxy_network` 与 `n8n_platform`（可手动创建，或用 platform 脚本）
- 已启用 Sheets API 的 Google Cloud 项目
- DeepSeek API key
- Tally 账号（免费档即可）用于表单入库

## 1. 启动共享 platform n8n

若使用同级目录下的 `platform-n8n`：

```bash
cd ../platform-n8n
cp .env.example .env
./scripts/ensure-networks.sh
docker compose -f docker/compose.yml up -d
```

否则自行启动 n8n，按需加入 `n8n_platform` / `proxy_network`，然后从步骤 2 继续。n8n UI 一般为 http://localhost:5678

## 2. 配置 CRM 项目

```bash
cd ../crm-workflow   # 或：cd /path/to/crm-workflow
cp .env.example .env
# 编辑 .env — DeepSeek、Langfuse、GOOGLE_SHEETS_DOCUMENT_ID 等
```

创建并共享电子表格：[SHEETS_SETUP.md](SHEETS_SETUP.md)。  
确认 **`prompt_registry` 含全部 6 行 prompt**（模板 CSV）；若线上表格较旧，请补齐缺失行。

## 3. 启动 CRM sidecar

```bash
docker compose -f docker/compose.yml up -d --build
```

| 服务 | URL | 说明 |
|------|-----|------|
| n8n (platform) | http://localhost:5678 | 共享编辑器 |
| Python AI | http://localhost:8002/health | CRM LLM sidecar |

```bash
curl http://localhost:8002/health
curl http://localhost:8002/prompts
```

`/prompts` 应列出六个 key，包括 `sales_memo`、`outbound_email`、`weekly_insights`。

Sidecar 部署细节：[DEPLOY.md](DEPLOY.md)。

## 4. 导入 n8n 工作流

导入到**共享 n8n**（Settings → Import from File），建议按此顺序：

1. `workflows/B2B Lead Error Handler.json`
2. `workflows/B2B Lead Enrichment Scoring.json`
3. `workflows/B2B Lead CRM Sync Notification.json`
4. `workflows/B2B Lead Intake.json`
5. `workflows/B2B Lead Daily Summary.json`
6. `workflows/B2B Lead Weekly Summary.json`
7. `workflows/B2B Lead Calendly Webhook.json`
8. `workflows/B2B Lead Booking Follow-up.json`
9. `workflows/B2B Lead Slack Actions.json`

### 导入后检查清单

- [ ] 在每个需要凭证的节点上重新连接 **Google Sheets**、**Slack**、**HubSpot**（JSON 使用占位符，如 `GOOGLE_SHEETS_CREDENTIAL_ID` / `SLACK_CREDENTIAL_ID` / `HUBSPOT_CREDENTIAL_ID`）。
- [ ] 确认电子表格文档 id（`$env.GOOGLE_SHEETS_DOCUMENT_ID` 或节点级取值）。
- [ ] 在每个主工作流上设置 **Settings → Error Workflow → `B2B Lead Error Handler`**（**导入不会自动绑定**）：Intake、Enrichment Scoring、CRM Sync Notification、Daily/Weekly Summary、Booking Follow-up、Calendly Webhook、Slack Actions。
- [ ] 抽查错误连线：[ERROR_HANDLING_NODES.md](ERROR_HANDLING_NODES.md)。
- [ ] 激活：**Intake**、**Daily Summary**、**Weekly Summary**、**Calendly Webhook**、**Booking Follow-up**、**Slack Actions**（以及按需的 Error Handler）。Enrichment / CRM Sync 通常由 Execute Workflow 调用。
- [ ] Sheets：`config_main.mode=test`；`prompt_registry` = 6 行有效记录。

工作流内使用的 Sidecar URL：`http://crm_python_ai:8001/enrich`、`/score`、`/sales-memo`、`/outbound-email`、`/weekly-insights`、`/manual-review`。

## 5. 配置 Tally webhook

1. 创建 Tally 表单：Name、Email、Role、Company、Message。
2. Integrations → Webhooks → URL `https://your-n8n-domain/webhook/tally-lead`。
3. 通过 `config_sources` 映射字段 / 信任度（[FIELD_MAPPING.md](FIELD_MAPPING.md)）。
4. 可选签名：[CREDENTIALS.md](CREDENTIALS.md)。

## 5b. Calendly

按 [CALENDLY_SETUP.md](CALENDLY_SETUP.md) 操作。摘要：设置 `CALENDLY_WEBHOOK_SIGNING_KEY`，订阅 `invitee.created` / `invitee.canceled` 到 `/webhook/calendly`，并激活 Calendly 工作流。

## 5c. Slack Actions

按 [SLACK_ACTIONS_SETUP.md](SLACK_ACTIONS_SETUP.md) 操作。摘要：启用 Interactivity → `https://your-n8n-domain/webhook/slack-interactions`，设置 `SLACK_SIGNING_SECRET`，激活 **B2B Lead Slack Actions**。

## 6. 测试运行

1. `config_main.mode=test`
2. 提交一条 Tally 测试线索
3. 确认 `leads` 行 + enrichment/scoring 字段
4. 确认 CRM 与 Slack 在 test 模式下**被跳过**

演练：[RUN_EXAMPLE.md](RUN_EXAMPLE.md)。可观测性：[OBSERVABILITY.md](OBSERVABILITY.md)。

## 7. 生产

设置 `config_main.mode=production`。见 [TEST_PRODUCTION.md](TEST_PRODUCTION.md)。

## CI/CD

推送到 `main` 会构建/推送 Python 镜像到 GHCR，并可 SSH 部署 sidecar。Workflow JSON **不会**自动导入 — 生成器变更后需手动重新导入。

```bash
python3 scripts/generate_workflows.py
```

## 排障

- **Python 起不来**：`.env` 中的 `DEEPSEEK_API_KEY`
- **无 OTEL traces**：`proxy_network` + collector 在运行
- **Langfuse 为空**：keys/host；platform 注入出站 traces
- **Webhook 无响应**：工作流是否 Active？生产 webhook URL？
- **n8n 访问不到 sidecar**：两者是否都在 `n8n_platform`
- **`/weekly-insights` 404**：用当前源码重建 sidecar（`docker compose ... up -d --build`）

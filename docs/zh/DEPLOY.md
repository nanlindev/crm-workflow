# CRM sidecar 部署

部署 CRM Python AI sidecar。共享 n8n 运行在 `platform-n8n`。

## 网络

| 网络 | 用途 |
|------|------|
| `n8n_platform` | n8n → `http://crm_python_ai:8001/...` |
| `proxy_network` | OTEL / Langfuse / Jaeger |

## 前置条件

- `platform-n8n` 已运行
- 项目 `.env` 含 `DEEPSEEK_*`、`LANGFUSE_*`、`GOOGLE_SHEETS_DOCUMENT_ID`
- Sheets 已配置 — [SHEETS_SETUP.md](SHEETS_SETUP.md)

## 本地

```bash
cd /path/to/crm-workflow
cp .env.example .env   # or docker/.env.example per your layout
docker compose -f docker/compose.yml --env-file .env up -d --build
```

健康检查：http://localhost:8002/health  
Prompts：http://localhost:8002/prompts

## 生产

示例路径：`/home/deploy/projects/crm-workflow`

```bash
../platform-n8n/scripts/ensure-networks.sh
docker pull ghcr.io/nanlindev/crm-workflow/python-ai-service:latest
docker compose -f docker/compose.yml --env-file .env up -d
```

若 GHCR 落后于功能（例如 `/weekly-insights`），也可从当前源码构建：

```bash
docker compose -f docker/compose.yml --env-file .env up -d --build
```

## Sidecar URL（从 n8n 调用）

- `http://crm_python_ai:8001/enrich`
- `http://crm_python_ai:8001/score`
- `http://crm_python_ai:8001/sales-memo`
- `http://crm_python_ai:8001/outbound-email`
- `http://crm_python_ai:8001/weekly-insights`
- `http://crm_python_ai:8001/manual-review`
- `http://crm_python_ai:8001/health`

## n8n 工作流

从 `workflows/` 导入 — [INSTALL.md](INSTALL.md)。Workflow JSON 不会自动部署。

## GHCR 镜像

`ghcr.io/nanlindev/crm-workflow/python-ai-service:latest`

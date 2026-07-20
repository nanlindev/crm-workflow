# Portfolio assets（作品集素材）

Phase 4 素材存放处。

**手动录屏：**

- 勾选总表：[CAPTURE_CHECKLIST.zh.md](CAPTURE_CHECKLIST.zh.md)
- **分镜逐步指南（推荐）：** [RECORDING_SHOTLIST.zh.md](RECORDING_SHOTLIST.zh.md)（含多段 Take、停留秒数、分屏 Assign）

完整触发步骤见 [DEMO_RUNBOOK](../docs/DEMO_RUNBOOK.md) / [中文版](../docs/zh/DEMO_RUNBOOK.md)。采完后把静图与成片放进本目录。

## 目录

```text
assets/
  architecture.svg          # 源图（可编辑）
  architecture.png          # 作品集用 PNG（脚本渲染）
  demo-video.mp4            # 或只在 MANIFEST 填 Loom URL
  demo-video-script.md      # 2–3 分钟英文旁白稿
  MANIFEST.md               # 文件名 ↔ 场景 ↔ 采集状态
  screenshots/              # 精选静图（可进 git；须无真实 PII）
  raw/                      # 未打码原图（默认 gitignore）
```

## 推荐采集方式

1. 远程已部署 n8n + sidecar + OBS（Phase 1–2）
2. 开隧道：`REMOTE_HOST=user@host ./scripts/ssh_tunnel_demo.sh`
3. 本地浏览器打开隧道端口，按 DEMO_RUNBOOK 场景 A/B/E/J… 操作
4. **本地 Loom / OBS** 录屏；静图另存为下表文件名
5. 含真实邮箱/公司名的原图放 `raw/`，发布前打码后复制到 `screenshots/`

## 渲染架构图

```bash
chmod +x scripts/render_architecture.sh
./scripts/render_architecture.sh
```

## 静图目标文件名（12）

| # | 文件 | 场景 |
|---|------|------|
| 1 | `architecture.png` | 预制作 |
| 2 | `screenshots/01-n8n-workflows-list.png` | J |
| 3 | `screenshots/02-enrichment-canvas.png` | J |
| 4 | `screenshots/03-sheets-new-lead.png` | A |
| 5 | `screenshots/04-slack-high-score.png` | A |
| 6 | `screenshots/05-langfuse-score-trace.png` | A / H |
| 7 | `screenshots/06-jaeger-correlation.png` | A |
| 8 | `screenshots/07-hubspot-contact.png` | B（Contact + DRAFT，无单独 `08`） |
| 9 | — | 已并入 `07` |
| 10 | `screenshots/09-calendly-meeting-fields.png` | E |
| 11 | `screenshots/10-daily-weekly-slack.png` | H |
| 12 | `screenshots/11-booking-reminder-slack.png` | G |

状态勾选见 [MANIFEST.md](MANIFEST.md)。

# 手动录屏 / 截图操作清单（边做边勾）

专给 Phase 4 采素材用。

**按点击顺序的详细分镜（多段录制）：** [RECORDING_SHOTLIST.zh.md](RECORDING_SHOTLIST.zh.md)

触发细节见完整 [DEMO_RUNBOOK 中文版](../docs/zh/DEMO_RUNBOOK.md)；文件名状态见 [MANIFEST.md](MANIFEST.md)；旁白稿见 [demo-video-script.md](demo-video-script.md)。

**达标：** 必做 A + B + E + J；再从 C/D/G/H 里至少做 **2** 个；Langfuse、Jaeger 各 ≥1 张；成片 1 条（2–3 分钟英文）。

**存图：** 打码/demo 假数据 → `assets/screenshots/`（用下表文件名）。含真实 PII 的原图 → `assets/raw/`（勿提交）。

---

## 开录前（约 10–15 分钟，不录像）

- [ ] 远程 n8n / sidecar / Jaeger / Langfuse 可访问（HTTPS 或隧道）
- [ ] 隧道（可选）：`REMOTE_HOST=user@host ./scripts/ssh_tunnel_demo.sh`
- [ ] Demo 隔离：专用 Sheets、Slack 频道、HubSpot sandbox、`+demo` 邮箱
- [ ] 9 个工作流已 Activate；凭证已绑；Error Workflow 已设
- [ ] （建议）先 `mode=test` 跑 seed，再改 production：
  ```bash
  python3 scripts/seed_demo_leads.py --url https://<域名>/webhook/tally-lead
  ```
- [ ] Sheets：`config_main.mode=production`
- [ ] Sheets：`config_notifications` 里要用到的 event 均为 `enabled=true`
- [ ] 浏览器分屏准备好：左 n8n，右 Sheets 或 Slack
- [ ] Loom / OBS 已装好；麦克风测过（英文旁白）
- [ ] 架构图已有：`assets/architecture.png`（可直接进成片片头）

---

## 建议录制顺序（一条成片 + 穿插截图）

| 时段 | 成片内容 | 开 🎥？ | 同时 📷 |
|------|----------|--------|---------|
| 0:00–0:20 | 问题 + 架构图 + 工作流列表 | ✅ | J1、J2 可先截再录 |
| 0:20–0:50 | Tally 提交 → Sheets 新行 / 分数 | ✅ | A1 |
| 0:50–1:20 | Slack 高分卡片 → Langfuse | ✅ | A2、A3 |
| 1:20–1:50 | Slack Assign → HubSpot Contact + DRAFT | ✅ | B1、B2 |
| 1:50–2:10 | Calendly（或模拟 webhook）→ meeting 字段 | ✅ 短 | E1 |
| 2:10–2:30 | Jaeger correlation → CTA | ✅ | A4 |
| 另段或补镜 | Daily/Weekly Slack、Booking reminder | 可选 | H1、G1 |

旁白英文稿直接念 [demo-video-script.md](demo-video-script.md)。

---

## 静图逐张勾选（保存到 `assets/screenshots/`）

### 必做

| 勾 | # | 操作（你做什么） | 保存为 |
|----|---|------------------|--------|
| [ ] | J1 | n8n → Workflows，露出 **9 个 B2B Lead** 工作流 | `01-n8n-workflows-list.png` |
| [ ] | J2 | 打开 **B2B Lead Enrichment Scoring** canvas，缩放到节点可读 | `02-enrichment-canvas.png` |
| [ ] | A1 | 用 demo 高分表单提交 Tally → Sheets `leads` 新行（分数 / `correlation_id` 可见） | `03-sheets-new-lead.png` |
| [ ] | A2 | Slack demo 频道：高分 Block Kit 卡片（含 Assign / Junk / Nurture） | `04-slack-high-score.png` |
| [ ] | A3 | Langfuse：该次 `/score`（或 enrich）generation，**prompt version** 可见 | `05-langfuse-score-trace.png` |
| [ ] | A4 | Jaeger：`n8n-platform` / sidecar span，能对上同一 `correlation_id` | `06-jaeger-correlation.png` |
| [ ] | B1 | Slack 点 **Assign** 后 → HubSpot Contact 页（含 Timeline **DRAFT** email，一张图即可） | `07-hubspot-contact.png` |
| [ ] | E1 | Calendly 预约或模拟 `invitee.created` → Sheets meeting 相关字段已更新 | `09-calendly-meeting-fields.png` |

### 建议（至少再完成 2 项）

| 勾 | # | 操作 | 保存为 |
|----|---|------|--------|
| [ ] | H1 | production 下手动 Execute **Daily** 和/或 **Weekly Summary** → Slack digest | `10-daily-weekly-slack.png` |
| [ ] | G1 | 手动 Execute **Booking Follow-up**（或等 cron）→ Slack booking reminder | `11-booking-reminder-slack.png` |
| [ ] | C | （可选加镜）Slack **Nurture** 或 **Junk** → Sheets `recommended_action` / `review_status` | 自命名放 `raw/` 或另存 |
| [ ] | D | （可选）`review_required` 路径 → Slack review 通知 | 同上 |

### 已完成（不必再截）

| # | 文件 | 说明 |
|---|------|------|
| 1 | `assets/architecture.png` | 已生成 |

---

## 场景操作速查（录的时候看这几行就够）

### A — 高分主路径（🎥 + 📷）

1. 确认 `mode=production`，`high_score_lead` / `first_touch_email` 已 enabled  
2. **开录** → 提交高分 demo Tally（Message 含 budget/demo 等意图词）  
3. 等 Intake → Enrichment → CRM Sync 跑完  
4. **暂停或切窗截图：** Sheets(A1) → Slack(A2) → Langfuse(A3) → Jaeger(A4)

### B — Assign → HubSpot DRAFT（🎥 + 📷）

1. 在 A2 那张 Slack 卡片点 **Assign**  
2. 看 n8n **Slack Actions** / Post-Assign 执行成功  
3. **截图：** HubSpot Contact(B1) + Timeline DRAFT(B2)

### E — Calendly（📷，可短 🎥）

1. 真实预约 **或** 按 DEMO_RUNBOOK 发模拟 `invitee.created`（不必 Calendly 会员）  
2. Sheets meeting 字段更新后截 E1

### J — 全景（📷，可片头用）

1. 工作流列表 J1；Enrichment canvas J2（可在开录前先截好）

### H / G — 建议补镜

1. **H：** Execute Daily + Weekly → Slack；可顺带截 Weekly 的 Langfuse `/weekly-insights`  
2. **G：** 准备一条高分、`meeting_status=not_booked`、且超过 `booking_reminder_hours` 的 lead → Execute Booking Follow-up → 截 G1

---

## 成片导出

- [ ] Loom/OBS 导出 2–3 分钟英文成片  
- [ ] 保存为 `assets/demo-video.mp4` **或** 把 URL 贴进 [MANIFEST.md](MANIFEST.md) 的 Loom 栏  
- [ ] 对照旁白稿检查：架构 → Tally → Slack+Langfuse → Assign/HubSpot → Calendly → Jaeger

---

## 录完清理

- [ ] `config_main.mode` 改回 `test`（除非刻意保留 live demo）  
- [ ] 删除 HubSpot demo contacts  
- [ ] （可选）清空 Slack demo 频道历史  
- [ ] 恢复临时改过的 Sheets 字段（如 backdated `created_at`）  
- [ ] 把 `screenshots/` 文件名与上表对齐；勾 [MANIFEST.md](MANIFEST.md)

---

## 一页纸优先级（贴显示器）

```text
必做截图：J1 J2 | A1 A2 A3 A4 | B1 B2 | E1
建议至少 2：H1 / G1 / C / D
成片：架构 → A → Slack+Langfuse → B → E → Jaeger
假数据 only；原图进 raw/；精选进 screenshots/
```

# 分镜录制指南（按点击顺序）

适合：**先录多段无旁白屏幕视频 → 后期剪辑 + AI 英文配音 → 再从成片/原片截静图**。

配套：

- 勾选总表：[CAPTURE_CHECKLIST.zh.md](CAPTURE_CHECKLIST.zh.md)
- 触发细节：[docs/zh/DEMO_RUNBOOK.md](../docs/zh/DEMO_RUNBOOK.md)
- 旁白稿（后期 AI 念）：[demo-video-script.md](demo-video-script.md)
- 镜头 A 表单数据：`scripts/demo_seed_leads.json` → `live_hero_do_not_seed`

**约定：**

| 标记 | 含义 |
|------|------|
| ⏱ | 画面停留建议时间（方便后期截帧） |
| 🎥 Take N | 可单独开一段录制，后期拼 |
| 📷 | 该镜事后可导出静图的文件名 |
| 分屏 | 左右两个窗口同时入画 |

每个关键画面尽量 **停 3–5 秒、别晃鼠标**。

---

## 多段录制怎么拆（推荐）

你完全可以录 **多段**，后期拼成 2–3 分钟：

| Take | 内容 | 难度 | 成片位置 |
|------|------|------|----------|
| **Take 0** | 开录前准备（不录，或极短） | — | — |
| **Take 1** | n8n 全景 + Enrichment canvas | 易 | 片头 |
| **Take 2** | Tally/提交 → Sheets → Slack 高分卡 | 中 | 主戏前半 |
| **Take 3** | Slack Assign 分屏 + HubSpot Contact/DRAFT | 中 | 主戏后半 |
| **Take 4** | Calendly 模拟 → Sheets meeting | 易/中 | 中后 |
| **Take 5** | Langfuse（单独） | 易 | 插在 Slack 后 |
| **Take 6** | Jaeger（单独） | 易 | 片尾 |
| **Take 7** | Daily/Weekly Slack（可选） | 易 | 补镜 |
| **Take 8** | Booking reminder（可选） | 易 | 补镜 |

OBS（Langfuse / Jaeger）**单独录完全 OK**，剪的时候接到对应旁白段落即可。

原始长视频建议命名：

```text
assets/raw/take1-n8n-overview.mp4
assets/raw/take2-tally-sheets-slack.mp4
assets/raw/take3-assign-hubspot.mp4
assets/raw/take4-calendly.mp4
assets/raw/take5-langfuse.mp4
assets/raw/take6-jaeger.mp4
assets/raw/take7-daily-weekly.mp4
assets/raw/take8-booking.mp4
```

---

## Take 0 — 开录前（不录像）

按顺序做完再开 Take 1：

1. [ ] 远程 n8n / Sheets / Slack / HubSpot / Langfuse / Jaeger 都能打开  
2. [ ] （建议）`mode=test` 先 seed 7 条背景数据：
   ```bash
   python3 scripts/seed_demo_leads.py --url https://<你的n8n>/webhook/tally-lead
   ```
3. [ ] 等 enrichment 跑完；按终端提示改部分行的 `created_at`（Daily / Booking 用）  
4. [ ] **不要** seed Sarah Chen（留给镜头）  
5. [ ] Sheets：`config_main.mode=production`  
6. [ ] 需要的通知行 `enabled=true`（至少：`high_score_lead`、`first_touch_email`；做 H/G 再开对应项）  
7. [ ] 浏览器标签页预先排好：n8n、Tally（或终端）、Sheets `leads`、Slack demo 频道、HubSpot、Langfuse、Jaeger  
8. [ ] 记下一会儿要用的窗口布局（Take 3 要分屏）

---

## Take 1 — n8n 工作流全景（🎥 易）

**目标静图：** `01-n8n-workflows-list.png`、`02-enrichment-canvas.png`

1. [ ] 打开 n8n → **Workflows**（列表视图）  
2. [ ] 筛选/滚动，让屏幕上清楚露出 **9 个 B2B Lead…** 工作流  
3. [ ] ⏱ **停留 3–5 秒**（别动鼠标）→ 📷 可截 `01-…`  
4. [ ] 点击进入 **B2B Lead Enrichment Scoring**  
5. [ ] 缩放到主链路节点可读（Intake 调用侧 / HTTP / Code 大致可见即可）  
6. [ ] ⏱ **停留 3–5 秒** → 📷 `02-enrichment-canvas.png`  
7. [ ] （可选）再快速点开 **B2B Lead CRM Sync Notification** canvas，⏱ 2–3 秒（加戏，非必须）  
8. [ ] **停止本段录制**

---

## Take 2 — 明星 Lead：提交 → Sheets → Slack（🎥 主戏）

**镜头表单（只在录像时提交，勿提前 seed）：**

| 字段 | 值 |
|------|-----|
| Name | Sarah Chen |
| Email | `sarah.chen+demo@techscale.io` |
| Role | Head of Operations |
| Company | TechScale Inc |
| Message | We need workflow automation for sales. Budget approved for Q3. Need a demo this week. |

### 2A — 提交

任选一种（录像里只做一种即可）：

**方式 1：Tally 网页（更适合出镜）**

1. [ ] 打开 demo Tally 表单  
2. [ ] 按上表填写（可提前填好，开录后再点 Submit）  
3. [ ] **开录** → 鼠标点到 Submit → ⏱ 提交成功页停 2 秒  

**方式 2：curl / webhook（更快，可分屏：左终端右 n8n Executions）**

用 DEMO_RUNBOOK 场景 A 的 curl（字段与上表相同）。

### 2B — n8n 执行过程

1. [ ] 切到 n8n **Executions**（或 Intake / Enrichment 正在跑的画布）  
2. [ ] ⏱ 等 Intake → Enrichment → CRM Sync 变绿，**停 3 秒**看成功态  

### 2C — Google Sheets

1. [ ] 打开 Sheets → `leads`  
2. [ ] 滚到 **Sarah Chen / techscale** 新行  
3. [ ] 横向露出：`score`、`recommended_action`、`enrichment_status`、`correlation_id`、`first_touch_status`（有则更好）  
4. [ ] ⏱ **停留 4–5 秒** → 📷 `03-sheets-new-lead.png`  
5. [ ] **抄下 `correlation_id`**（Take 5/6 要用）

### 2D — Slack 高分提醒

1. [ ] 打开 Slack demo 频道  
2. [ ] 找到 Sarah / TechScale 的高分 Block Kit 卡（含 **Assign / Junk / Nurture**）  
3. [ ] ⏱ **停留 4–5 秒**，滚到按钮区清晰可见 → 📷 `04-slack-high-score.png`  
4. [ ] **本段先停**（不要点 Assign——留给 Take 3）

---

## Take 3 — Assign 分屏 + HubSpot DRAFT（🎥 主戏）

**布局建议（开录前摆好）：**

```text
┌─────────────────┬─────────────────┐
│  左：Slack 卡片  │ 右：HubSpot     │
│  （按钮区域）    │ Contact 搜索页  │
└─────────────────┴─────────────────┘
```

若分屏不好做：先录 Slack 点 Assign → 再切 HubSpot（后期硬切也行）。

1. [ ] 右窗：HubSpot → Contacts，搜 `sarah.chen+demo@techscale.io`（可先打开 Contact，若 CRM Sync 已 upsert）  
2. [ ] 左窗：Slack 同一张高分卡，按钮清晰  
3. [ ] **开录** → ⏱ 分屏静止 **2 秒**  
4. [ ] 在 Slack 点击 **Assign**  
5. [ ] ⏱ 等 Slack 卡 **chat.update**（同一条卡变化，不是新刷一条）停 **3 秒**  
6. [ ] 右窗刷新 / 打开 Contact → 滚到 **Timeline**，露出 **DRAFT** outbound email  
7. [ ] ⏱ Contact + DRAFT 同屏停 **4–5 秒** → 📷 `07-hubspot-contact.png`（**无单独 `08`**）  
8. [ ] （可选）再切 Sheets 看 `crm_contact_id`、`review_status=approved`，⏱ 2–3 秒  
9. [ ] **停录**

---

## Take 4 — Calendly / meeting 字段（🎥 可短）

**推荐：模拟 webhook**（不必 Calendly 会员）。邮箱必须与 Sarah 一致：`sarah.chen+demo@techscale.io`。

1. [ ] 左：终端（curl）；右：Sheets `leads` 的 Sarah 行（meeting 列可见）  
2. [ ] **开录** → 执行 DEMO_RUNBOOK「场景 E」模拟 curl  
3. [ ] 切 n8n：**B2B Lead Calendly Webhook** 执行成功，⏱ 2 秒  
4. [ ] 回 Sheets：看 `meeting_status` / `meeting_time` 等更新  
5. [ ] ⏱ **停留 4 秒** → 📷 `09-calendly-meeting-fields.png`  
6. [ ] **停录**

---

## Take 5 — Langfuse（🎥 单独录，后期插入）

1. [ ] 打开 Langfuse → 找最近 `crm-workflow` / `/score` 或 `/enrich`  
2. [ ] 用 Take 2 记下的 `correlation_id` 或时间戳对齐 Sarah 那次  
3. [ ] 展开 generation，露出 **prompt version** / model  
4. [ ] ⏱ **停留 4–5 秒** → 📷 `05-langfuse-score-trace.png`  
5. [ ] **停录**

剪辑：接到「Slack 高分卡」旁白段落后即可。

---

## Take 6 — Jaeger（🎥 单独录，后期片尾）

1. [ ] 打开 Jaeger → service 选 `n8n-platform`（或你们部署名）  
2. [ ] 用时间窗 / `correlation_id` 找到 Sarah 那次链路  
3. [ ] 展开 span：n8n → sidecar 可见  
4. [ ] ⏱ **停留 4–5 秒** → 📷 `06-jaeger-correlation.png`  
5. [ ] **停录**

剪辑：接到片尾 CTA 旁白。

---

## Take 7 — Daily / Weekly Slack（可选补镜）

1. [ ] 确认 `mode=production`，`daily_summary` / `weekly_summary` = enabled  
2. [ ] n8n 手动 **Execute** `B2B Lead Daily Summary` → 切 Slack 看 digest，⏱ 3 秒  
3. [ ] 再 **Execute** `B2B Lead Weekly Summary` → Slack +（可选）Sheets `weekly_metrics` 新行  
4. [ ] ⏱ Slack digest 停 **4 秒** → 📷 `10-daily-weekly-slack.png`  
5. [ ] **停录**

---

## Take 8 — Booking reminder（可选补镜）

前置：有一条高分、`meeting_status=not_booked`、`created_at` 早于提醒阈值（可用 seed-03 Marcus，或临时改行）。

1. [ ] **Execute** `B2B Lead Booking Follow-up`  
2. [ ] Slack 出现 booking reminder，⏱ **4 秒** → 📷 `11-booking-reminder-slack.png`  
3. [ ] **停录**

---

## 后期剪辑建议（AI 旁白）

1. 按旁白稿时间轴拼接 Take：`1 → 2 → 5 → 3 → 4 → 6`（7/8 可选插入）  
2. 架构图 `architecture.png` 可静帧 3–5 秒垫在最前  
3. 用剪辑软件 AI 语音读 [demo-video-script.md](demo-video-script.md)  
4. 从各 Take 导出静图，改名进 `assets/screenshots/`  
5. 成片导出 `demo-video.mp4` 或 Loom URL 写入 [MANIFEST.md](MANIFEST.md)

成片目标顺序：

```text
架构图 → n8n 全景 → Tally/提交 → Sheets → Slack
→ Langfuse → Assign + HubSpot DRAFT → Calendly/meeting → Jaeger CTA
```

---

## 一页纸（贴显示器）

```text
Take1  n8n列表3s → Enrichment canvas 3s
Take2  Sarah提交 → Executions → Sheets 4s → Slack卡 4s（先别点Assign）
Take3  分屏：点Assign → Slack卡变 → HubSpot Contact → Timeline DRAFT 4s
Take4  Calendly模拟 → Sheets meeting 4s
Take5  Langfuse（单独）
Take6  Jaeger（单独）
Take7/8  Daily·Weekly / Booking（可选）

Hero: Sarah Chen / sarah.chen+demo@techscale.io / TechScale Inc
截帧停够3–5秒；OBS可分段；后期AI英文旁白
```

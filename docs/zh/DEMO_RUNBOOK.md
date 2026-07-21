# 全链路演示手动清单（中文）

远程 **production** 环境逐步操作清单。边跑边勾；需要出片的步骤用 **🎥 录像** / **📷 截图** 标出。

**素材勾选与文件名：** [assets/MANIFEST.md](../../assets/MANIFEST.md)

英文版：[DEMO_RUNBOOK.md](../DEMO_RUNBOOK.md)  
相关：[TEST_PRODUCTION](TEST_PRODUCTION.md) · [INSTALL](INSTALL.md) · [OBSERVABILITY](OBSERVABILITY.md) · [CALENDLY_SETUP](CALENDLY_SETUP.md)

---

## 图例（哪里要录像）

| 标记 | 含义 |
|------|------|
| **🎥 录像** | 开 Loom/OBS，保留操作过程（建议进成片） |
| **📷 截图** | 定格一张静图进作品集 |
| **⏸️ 可不录** | 仅验证，不必出镜 |
| **必做 / 建议 / 可选** | 作品集优先级 |

**成片建议（2–3 分钟英文旁白）：** 架构 → 场景 A → Slack+Langfuse → 场景 B HubSpot → 场景 E（或模拟）→ Jaeger CTA。  
**静图目标：** 约 10–12 张（文末总表）。

**不进 git：** 含真实邮箱/公司名的原图；用 demo 假数据或打码。

---

## 优先级一览

| 场景 | 优先级 | 🎥 / 📷 |
|------|--------|---------|
| 0 预检 | 必做 | ⏸️ |
| H0 Daily/Weekly test 门控 | 强烈建议 | ⏸️（可截 n8n 路径） |
| **A 高分 Lead 主路径** | **必做** | **🎥 + 📷** |
| **B Slack Assign → HubSpot DRAFT** | **必做** | **🎥 + 📷** |
| C Nurture / Junk | 建议 | 📷 |
| D Manual Review | 建议 | 📷 |
| **E Calendly 预约** | **必做**（可用模拟 webhook，**不必充会员**） | **📷**（可选短 🎥） |
| F Calendly 取消 | 可选 | ⏸️ |
| G Booking Follow-up | 建议 | 📷 |
| H Daily/Weekly 发 Slack | 建议 | 📷（可选 🎥） |
| I Error Handler | 可选 | 📷 |
| **J 九个工作流全景** | **必做** | **📷** |

作品集达标：**A + B + E + J**；C/D/G/H 至少再完成 **2** 个；Langfuse、Jaeger 各 ≥1 张；Daily/Weekly 至少做过 H0，最好再做 H。

---

## 0. 预检（⏸️ 可不录）

### 0.1 Demo 隔离

- [ ] Google Sheets：专用演示表（与客户数据隔离）
- [ ] Slack：专用频道（如 `#crm-automation-demo`），bot 已进频道
- [ ] HubSpot：sandbox / Free；邮箱用 `xxx+demo@…`
- [ ] Tally：专用表单 → `https://<域名>/webhook/tally-lead`
- [ ] Calendly：**可不订会员**；场景 E 用下方「模拟 webhook」即可

### 0.2 栈健康

- [ ] n8n UI 可访问（HTTPS 或 SSH 隧道）
- [ ] Sidecar：`/health` OK；`/prompts` 有 **6** 个 key（含 `weekly_insights`、`outbound_email`）
- [ ] 9 个工作流已导入；Sheets / Slack / HubSpot 凭证已重绑
- [ ] 各主工作流 Settings → Error Workflow → **B2B Lead Error Handler**
- [ ] 已 Activate：Intake、Calendly Webhook、Booking Follow-up、Daily Summary、Weekly Summary、Slack Actions
- [ ] OBS：otel + Jaeger + Langfuse 正常；`NO_PROXY` 含 `crm_python_ai,otel-collector,langfuse-web`

### 0.3 Sheets 配置（跑 A 之前）

先做 **H0** 时请保持：

```text
config_main.mode = test
```

H0 通过后改为：

```text
config_main.mode = production
```

`config_notifications` 演示时建议全部 `enabled=true`：

| event_type | 用途 |
|------------|------|
| `high_score_lead` | 高分 Slack Block Kit |
| `review_required` | 人工审核通知 |
| `first_touch_email` | 草稿 → `draft_pending_review` |
| `booking_reminder` | 预约提醒 |
| `daily_summary` | 日报 Slack |
| `weekly_summary` | 周报 Slack |
| `error_alert` | 可选场景 I |

### 0.4 推荐操作顺序

1. H0（test 门控）  
2. **预埋 seed（见 0.5）** → 等 enrichment 完 → 按脚本提示改 `created_at`  
3. `mode=production`  
4. **🎥 开录** → A → B  
5. E（模拟即可）→ J（可穿插或最后截）  
6. C / D / G 择做  
7. H（production 日报/周报 Slack）  
8. I 可选  
9. 从 A/H 补 OBS 截图  

### 0.5 预埋数据（建议录前做）

仓库已备 **7 条** demo seed（不含镜头上的明星 lead）：

| 文件 | 说明 |
|------|------|
| [`scripts/demo_seed_leads.json`](../../scripts/demo_seed_leads.json) | 载荷 + 用途标注 |
| [`scripts/seed_demo_leads.py`](../../scripts/seed_demo_leads.py) | POST 到 Tally webhook |

```bash
# 建议先 mode=test，少打扰 Slack；跑完再改 production 开录
python3 scripts/seed_demo_leads.py --url https://<你的n8n>/webhook/tally-lead

# 只看内容不提交
python3 scripts/seed_demo_leads.py --url https://.../webhook/tally-lead --dry-run
```

默认间隔 15s。全部跑完后按终端打印表，在 Sheets 改：

- **2 条高分** → `created_at` = **昨天 UTC**（Daily）
- **1 条高分 booking** → `created_at` = **两天前**，保持 `meeting_status=not_booked`
- **其余** 留本周（Weekly 好看）
- **镜头 A** 的 `sarah.chen+demo@techscale.io`：**不要 seed**，录像时再交

---


## H0. Daily / Weekly 门控（test，强烈建议）

**⏸️ 可不录**；出问题再截 n8n 执行路径。

### 准备

- [ ] `config_main.mode=test`
- [ ] 最好有一条 `created_at` 为 **昨天 UTC** 的 lead（Daily 窗口）；本周有若干 lead（Weekly）

### Daily（test）

1. [ ] 打开 **B2B Lead Daily Summary** → **Execute Workflow**
2. [ ] 路径：读 config → **Build Daily Summary** → **Should Send Daily?** → **Skip Daily Slack** → End
3. [ ] Slack **没有**新消息
4. [ ] 输出含 `daily_gate_passed=false`、`mode=test`；阈值来自 `score_threshold_high`
5. [ ] 整次只聚合 **一条** summary（不是每行 lead 打一次）

### Weekly（test）

1. [ ] 打开 **B2B Lead Weekly Summary** → **Execute Workflow**
2. [ ] 路径：metrics → `/weekly-insights`（可失败降级）→ **Should Send Weekly?** → **Skip Weekly Slack** → **Append Weekly Metrics**
3. [ ] Slack **没有**新消息
4. [ ] 表 **`weekly_metrics`** 新增一行

**通过标准：** 聚合成功；Weekly 写表；Slack 跳过。  
然后设 `mode=production`，进入场景 A。

---

## 场景 A — 高分 Lead 主路径（必做）

**🎥 录像（主戏）：** 从提交表单/执行 webhook 起，到 Slack 卡片出现；可切屏 Sheets。  
**📷 截图：** A1–A4（见下）。

### 操作步骤

1. [ ] 确认 `mode=production`，相关 `config_notifications` 已启用  
2. [ ] **🎥 开始录像**  
3. [ ] 用 Tally 提交，或：

```bash
curl -X POST https://<你的n8n域名>/webhook/tally-lead \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "FORM_RESPONSE",
    "data": {
      "formName": "B2B Contact Demo",
      "formUrl": "https://tally.so/r/demo",
      "fields": [
        {"label": "Name", "value": "Sarah Chen"},
        {"label": "Email", "value": "sarah.chen+demo@techscale.io"},
        {"label": "Role", "value": "Head of Operations"},
        {"label": "Company", "value": "TechScale Inc"},
        {"label": "Message", "value": "We need workflow automation for sales. Budget approved for Q3. Need a demo this week."}
      ]
    }
  }'
```

4. [ ] 等 Intake → Enrichment → Scoring → CRM Sync 跑完  
5. [ ] 看 Sheets / Slack /（稍后）OBS  

**预期链路：**

```text
Intake → Enrichment → Scoring → CRM Sync
  → HubSpot Contact upsert（crm_gate 通过时）
  → Slack high_score（Block Kit + Assign/Junk/Nurture）
  → First Touch 草稿 → first_touch_status ≈ draft_pending_review
```

### 验收勾选

- [ ] `leads`：高分、`enrichment_status=complete`、`recommended_action` 偏 `crm_sync`
- [ ] `crm_status=synced`（或成功态）；HubSpot 有 Contact
- [ ] Slack demo 频道有高分卡片
- [ ] 有 outbound 草稿字段；符合首触门控时 `first_touch_status=draft_pending_review`
- [ ] 记下 `correlation_id` / `lead_id`（给 Langfuse/Jaeger）

### 📷 本场景必拍

| 编号 | 拍什么 | 进成片？ |
|------|--------|----------|
| **A1** | Sheets `leads` 行（score、状态、`correlation_id`） | ✅ 静图 #4 |
| **A2** | Slack Block Kit 通知全文 | ✅ 静图 #5；视频高潮 |
| **A3** | Langfuse：`/enrich` 或 `/score`（含 prompt version） | ✅ 静图 #6 |
| **A4** | Jaeger：n8n + sidecar 链路 | ✅ 静图 #7；视频收尾 |

建议：A2 出现后可 **⏸️ 暂停录像**，切到 Langfuse/Jaeger 再 **📷 截图**（或续录 OBS 段）。

**本场景完成：** [ ]

---

## 场景 B — Slack Assign → HubSpot DRAFT（必做）

**🎥 录像：** 点 Assign → Slack 卡更新 → 切到 HubSpot Contact / Timeline DRAFT → 回 Sheets。  
**📷：** B1–B3。

### 操作步骤

1. [ ] **🎥 开录**（或接在 A 同一条视频里）  
2. [ ] 在场景 A 的 Slack 卡片上点 **Assign**  
3. [ ] 等待 Slack Actions → CRM Sync（`skip_notification`）→ HubSpot DRAFT  

**预期：**

```text
Slack Actions → Post-Assign CRM Sync
  → HubSpot Upsert
  → 从 Lead 加载草稿 → HubSpot Log Outbound Email（DRAFT）
  → Sheets review / first_touch 更新
```

### 验收勾选

- [ ] Sheets：`review_status=approved`，`lead_stage=sql`，owner/reviewer 有值  
- [ ] HubSpot Contact 页可见 demo 联系人  
- [ ] Timeline：**DRAFT** 邮件（不是自动发出）  
- [ ] Sheets 有 `crm_contact_id`  
- [ ] Slack 是 **chat.update** 同一条卡，不是又刷一条新卡  

### 📷 本场景必拍

| 编号 | 拍什么 | 进成片？ |
|------|--------|----------|
| **B1** | HubSpot Contact 页 | ✅ 静图 #8 |
| **B2** | HubSpot Timeline 上的 DRAFT email | ✅ 静图 #9；视频重点 |
| **B3** | Sheets：`crm_contact_id` + review 字段 | 建议 |

**本场景完成：** [ ]

---

## 场景 C — Nurture / Junk（建议）

**📷 截图即可**（一般不必单独录像）。

1. [ ] 再提交一条 lead，或用第二张 Slack 卡  
2. [ ] 点 **Nurture** 或 **Junk**  

验收：

- [ ] Junk：`review_status=rejected`，`recommended_action=reject`，`lead_stage=junk`  
- [ ] Nurture：`review_status=review_later`，`lead_stage=nurture`  
- [ ] Slack 卡已更新  

| 编号 | 📷 |
|------|-----|
| **C1** | Sheets 状态字段变化 |

**本场景完成：** [ ]

---

## 场景 D — Manual Review（建议）

**📷 截图即可。**

1. [ ] 提交弱意向 / 灰区分数 / freemail 等易触发 `review_required` 的 lead  
2. [ ] 确认审核路径（含 `/manual-review` 若走到）  

验收：

- [ ] Slack `review_required`（production + enabled）  
- [ ] Sheets `review_status=pending_review`（或等价待审）  

| 编号 | 📷 |
|------|-----|
| **D1** | Slack 审核通知 |
| **D2** | Sheets `pending_review` |

**本场景完成：** [ ]

---

## 场景 E — Calendly 预约（必做，可用模拟）

**不必为展示充 Calendly $12/mo。** 免费计划通常不能向你推送 webhook；用下方 **自己 POST 模拟包** 即可。

**📷 必拍 E1、E2**；若旁白要讲 meeting 链路，可加 **🎥 短镜**（终端 curl → n8n 成功 → Sheets）。

### 方式 A：模拟 webhook（推荐）

前置：

- [ ] **B2B Lead Calendly Webhook** 已 Active  
- [ ] Sheets 里已有 lead，`contact_email` 与模拟包邮箱 **完全一致**（建议用场景 A 的邮箱）  
- [ ] 若配置了 `CALENDLY_WEBHOOK_SIGNING_KEY`：签名必须对；或临时清空 key（仅 demo，验签会 skip，用完记得加回）  

签名算法（与工作流一致）：header  
`Calendly-Webhook-Signature: t=<unix>,v1=<hmac_sha256_hex(key, "t.rawBody")>`  

示例（`signing_key` 与 n8n 环境变量相同；邮箱改成你的 lead）：

```bash
# 把 KEY、URL、EMAIL 换成你的
KEY="$CALENDLY_WEBHOOK_SIGNING_KEY"
URL="https://<你的n8n域名>/webhook/calendly"
EMAIL="sarah.chen+demo@techscale.io"
BODY=$(cat <<EOF
{"event":"invitee.created","payload":{"email":"$EMAIL","scheduled_event":{"uri":"https://api.calendly.com/scheduled_events/DEMO","start_time":"2026-07-16T10:00:00.000000Z"},"invitee":{"email":"$EMAIL"}}}
EOF
)
T=$(date +%s)
V1=$(printf '%s' "${T}.${BODY}" | openssl dgst -sha256 -hmac "$KEY" | awk '{print $2}')
curl -sS -X POST "$URL" \
  -H "Content-Type: application/json" \
  -H "Calendly-Webhook-Signature: t=${T},v1=${V1}" \
  -d "$BODY"
```

若暂时 **清空** 了 signing key，可省略签名 header（仅本地/演示）。

### 方式 B：真实 Calendly（可选）

付费会员 + 真实预约，邮箱匹配 lead。非必须。

### 验收勾选

- [ ] n8n **B2B Lead Calendly Webhook** 执行成功  
- [ ] Sheets：`meeting_status` / `meeting_time` / Calendly URI 等已更新  
- [ ] （可选）会议相关 Slack  

| 编号 | 📷 | 进成片？ |
|------|-----|----------|
| **E1** | Sheets meeting 字段 | ✅ 静图 #10 |
| **E2** | n8n 该次执行成功 | 建议 |

**本场景完成：** [ ]

---

## 场景 F — Calendly 取消（可选，⏸️）

模拟 `invitee.canceled` 或真实取消。验收 meeting 字段为取消态。可不录。

**本场景完成：** [ ]

---

## 场景 G — Booking Follow-up（建议）

**📷 截图** G1、G2。一般不必长录像。

### Sheets 准备

至少一行：

- `score >= score_threshold_high`
- `meeting_status=not_booked`
- `created_at` 早于 `booking_reminder_hours`（默认 24h）
- `booking_reminder_sent` 不为 true  

可用场景 A 的 lead：把 `created_at` 临时改成 2 天前（录完恢复）。

### 操作

1. [ ] `mode=production` 且 `booking_reminder.enabled=true`  
2. [ ] **Execute** **B2B Lead Booking Follow-up**（或等约 10:00 cron）  

### 验收

- [ ] Slack 预约提醒  
- [ ] `booking_reminder_sent` / `booking_reminder_at` 写入  
- [ ] 再跑不会对同一 lead 重复轰炸  

| 编号 | 📷 | 进成片？ |
|------|-----|----------|
| **G1** | Slack booking reminder | ✅ 静图 #12 |
| **G2** | Sheets 提醒字段 / audit | 建议 |

**本场景完成：** [ ]

---

## 场景 H — Daily / Weekly Summary（建议；须先过 H0）

**📷 截图** H1–H4；可选 **🎥** 手动 Execute → Slack 弹出。

条件：`mode=production`，`daily_summary` / `weekly_summary` 均为 `enabled=true`。

### Daily（production）

> 窗口是 **昨天 UTC**，不是「今天到现在」。若今天刚造的 lead，需把某行 `created_at` 临时改成昨天 UTC 日期前缀。

1. [ ] 确认有「昨天 UTC」数据  
2. [ ] Execute **B2B Lead Daily Summary**  
3. [ ] 路径：**Should Send Daily?** → **Slack Daily Report**（不是 Skip）  
4. [ ] 一条聚合 digest（非多条刷屏）  

### Weekly（production）

1. [ ] Execute **B2B Lead Weekly Summary**  
2. [ ] `/weekly-insights` 成功或降级；随后 **Slack Weekly Report**  
3. [ ] **Append Weekly Metrics** 仍有新行（Slack 失败时也应保留 metrics 再 Append）  

| 编号 | 📷 | 进成片？ |
|------|-----|----------|
| **H1** | Slack 日报 | ✅ 静图 #11 |
| **H2** | Slack 周报 | ✅ 静图 #11 |
| **H3** | `weekly_metrics` 新行 | 建议 |
| **H4** | Langfuse weekly-insights | 可与 A3 二选一加强 |

**本场景完成：** [ ]

---

## 场景 I — Error Handler（可选）

**📷** 即可。可控制造错误（如临时改错 Sheets ID）→ 看 `error_logs` → 恢复。

- [ ] `error_logs` 有行  
- [ ] `error_alert` 仅在 production + enabled 时发 Slack  

| 编号 | 📷 |
|------|-----|
| **I1** | `error_logs` |
| **I2** | （可选）Slack error_alert |

**本场景完成：** [ ]

---

## 场景 J — 工作流全景（必做）

**📷 必拍**（成片开头或中段也可 🎥 扫一眼列表）。

1. [ ] n8n 列出全部 **9** 个工作流  
2. [ ] 打开 **Enrichment Scoring** canvas（看到调 sidecar 的 HTTP）  
3. [ ] （建议）打开 **CRM Sync Notification** canvas  

| 编号 | 📷 | 进成片？ |
|------|-----|----------|
| **J1** | 九个工作流列表 | ✅ 静图 #2 |
| **J2** | Enrichment canvas | ✅ 静图 #3 |
| **J3** | CRM Sync canvas | 建议 |

**本场景完成：** [ ]

---

## 录像时间线（建议一条 2–3 分钟英文片）

| 时间 | 画面 | 对应场景 | 标记 |
|------|------|----------|------|
| 0:00–0:20 | 架构图 / 问题一句话 | — | 📷 架构图先备好 |
| 0:20–0:50 | 提交 lead → Sheets 出分 | A | 🎥 |
| 0:50–1:20 | Slack 卡 + 切 Langfuse | A | 🎥 + 📷 A2/A3 |
| 1:20–1:50 | Assign → HubSpot DRAFT | B | 🎥 + 📷 B1/B2 |
| 1:50–2:10 | Calendly 模拟 → meeting 字段 | E | 🎥 短 / 📷 E1 |
| 2:10–2:30 | Jaeger + CTA | A4 | 🎥 / 📷 |

**录制方式：** SSH 隧道开远程 n8n/Jaeger/Langfuse → **本地** Loom/OBS。  
**分屏推荐：** 左 n8n execution，右 Sheets 或 Slack。

---

## 静图总清单（Phase 4）

**状态与文件名：** [assets/MANIFEST.md](../../assets/MANIFEST.md) · [assets/README.md](../../assets/README.md) · 旁白稿 [assets/demo-video-script.md](../../assets/demo-video-script.md)

隧道：`REMOTE_HOST=user@host ./scripts/ssh_tunnel_demo.sh`

| # | 素材 | 文件名 | 场景 | 📷 |
|---|------|--------|------|-----|
| 1 | 架构图 PNG | `assets/architecture.png` | 预制作 | — |
| 2 | 九个工作流列表 | `assets/screenshots/01-n8n-workflows-list.png` | J | J1 |
| 3 | Enrichment canvas | `assets/screenshots/02-enrichment-canvas.png` | J | J2 |
| 4 | Tally/提交 → Sheets 行 | `assets/screenshots/03-sheets-new-lead.png` | A | A1 |
| 5 | Slack Block Kit | `assets/screenshots/04-slack-high-score.png` | A | A2 |
| 6 | Langfuse（prompt version） | `assets/screenshots/05-langfuse-score-trace.png` | A / H | A3 |
| 7 | Jaeger（correlation） | `assets/screenshots/06-jaeger-correlation.png` | A | A4 |
| 8 | HubSpot Contact + DRAFT | `assets/screenshots/07-hubspot-contact.png` | B | B1（无单独 `08`） |
| 9 | （已并入上栏） | — | B | — |
| 10 | Meeting 字段更新 | `assets/screenshots/09-calendly-meeting-fields.png` | E | E1 |
| 11 | Daily/Weekly Slack | `assets/screenshots/10-daily-weekly-slack.png` | H | H1 |
| 12 | Booking reminder Slack | `assets/screenshots/11-booking-reminder-slack.png` | G | G1 |

精选图进 `screenshots/`；未打码原图进 `raw/`（默认不进 git）。

---

## 演示后清理

- [ ] `config_main.mode` 改回 `test`（除非刻意保留 live demo）  
- [ ] 删除 HubSpot demo contacts  
- [ ] （可选）清空 Slack demo 频道  
- [ ] 恢复临时改过的 `created_at` 等字段  
- [ ] 若为演示清空过 `CALENDLY_WEBHOOK_SIGNING_KEY`，加回  

---

## Daily / Weekly 门控速查

| 工作流 | 何时发 Slack | 跳过 Slack 时仍做 |
|--------|--------------|-------------------|
| Daily | `mode=production` **且** `daily_summary.enabled=true` | 聚合昨天 UTC → **Skip Daily Slack** |
| Weekly | `mode=production` **且** `weekly_summary.enabled=true` | metrics + AI → **Skip Weekly Slack** → 仍 **Append** `weekly_metrics` |

高分统计阈值：`config_main.score_threshold_high`。

---

## 进度总表

| 场景 | 优先级 | 🎥/📷 | 完成 |
|------|--------|-------|------|
| 0 预检 | 必做 | ⏸️ | [ ] |
| H0 test 门控 | 强烈建议 | ⏸️ | [ ] |
| A 高分主路径 | 必做 | 🎥📷 | [ ] |
| B Assign + DRAFT | 必做 | 🎥📷 | [ ] |
| C Nurture/Junk | 建议 | 📷 | [ ] |
| D Manual Review | 建议 | 📷 | [ ] |
| E Calendly（可模拟） | 必做 | 📷 | [ ] |
| F 取消 | 可选 | ⏸️ | [ ] |
| G Booking | 建议 | 📷 | [ ] |
| H Daily/Weekly Slack | 建议 | 📷 | [ ] |
| I Error | 可选 | 📷 | [ ] |
| J 全景 | 必做 | 📷 | [ ] |

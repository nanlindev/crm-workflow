# Slack Block Kit 交互操作指南

> 适用：`crm-workflow` 的 **B2B Lead Slack Actions**（新工作流，可直接 import）  
> 以及 **现有工作流的手动修改**（CRM 通知发 Block Kit 按钮、Enrichment 传 enrichment 字段）  
> 前提：Slack OAuth 凭证、Google Sheets `leads` 表、`SLACK_CHANNEL_ID` 已配置

---

## 一、架构与职责（必读）

Slack 按钮交互必须在 **3 秒内**收到 HTTP 200。耗时业务（读 Sheets、写 CRM）必须异步完成，通过 `response_url` 更新原消息。

```text
Slack 点击按钮
  → n8n 验签 + 解析 (<1s)
  → 立即 Respond 200 Ack（空 200，消除黄色超时）
  → response_url #1：replace_original 为「⏳ Processing…」（去掉按钮）
  → Sheets 更新 + audit（后台，不限时）
  → chat.update #2：用 channel_id + message_ts 原地更新为「✅ 结果卡片」（去掉按钮）
```

> **重要：** 不要用 `response_url` + `JSON.stringify` 更新原消息——容易在原卡片下方 **新发一条**，按钮仍保留。应使用 Slack 节点的 **Message → Update**（`chat.update`），传入 `channel_id` + `message_ts`（来自 Parse Slack Payload）。

```text
Enrichment Scoring
  └─ Execute CRM Sync ──► CRM Sync Notification
                              └─ Slack Notify (Block Kit 按钮)
                                    │
                     用户点击 Assign / Junk / Nurture
                                    ▼
                         Slack Actions Webhook（新工作流）
                              ├─ 验签
                              ├─ 更新 Google Sheets leads
                              ├─ Assign / Nurture → Execute CRM Sync（HubSpot，不发第二条 Slack）
                              ├─ chat.update 原地更新结果卡片
                              └─ audit_logs
```

| 组件 | 是否可 import 覆盖 | 说明 |
|------|-------------------|------|
| **B2B Lead Slack Actions** | ✅ 直接 import | 接收 Slack 交互，写 Sheets，Assign/Nurture 触发 HubSpot |
| **B2B Lead CRM Sync Notification** | ⚠️ 仅手动改 | Block Kit 按钮 + `skip_notification` 门禁（见 7.4） |
| **B2B Lead Enrichment Scoring** | ⚠️ 仅手动改 | `Execute CRM Sync` 需传入 enrichment 字段（画像区块） |
| 其余工作流（Intake / Daily / Calendly 等） | ❌ 无需改动 | — |

**按钮与 action_id 对应关系（必须与 Slack Actions 工作流一致）：**

| 按钮文案 | action_id | Sheets 写入 | HubSpot（`mode=production`） |
|----------|-----------|-------------|------------------------------|
| Assign | `assign_lead` | `review_status=approved`, `recommended_action=crm_sync`, `lead_stage=sql`, `owner_id` + `reviewer` = Slack 用户 ID | ✅ Upsert 联系人（SQL） |
| Mark Junk | `mark_junk` | `review_status=rejected`, `recommended_action=reject`, `lead_stage=junk` | ❌ 不同步（拒绝线索不进 CRM） |
| Nurture | `nurture_lead` | `review_status=review_later`, `recommended_action=notify_only`, `lead_stage=nurture` | ✅ Upsert 联系人（培育池，非 SQL） |

> **Mark Junk 说明：** 若该联系人此前已同步到 HubSpot（高分自动入库），点 Junk **不会**自动删除或标记 HubSpot 记录，需在 HubSpot 手动归档。Sheets 侧会正确标记为 `junk`。

> **Nurture 说明：** 同步使用 `notify_only` 动作（通过 CRM 门禁），仅写入 HubSpot 联系人供培育序列使用，**不会**再发一条 Slack 通知（`skip_notification=true`）。

按钮 `value` 为 JSON 字符串（≤2000 字符）：

```json
{"lead_id":"<uuid>","correlation_id":"<uuid>"}
```

---

## 二、前置条件检查清单

- [ ] n8n 公网可访问（ngrok / 正式域名），且 `WEBHOOK_URL` 已配置
- [ ] `platform-n8n/.env` 已有：

```bash
WEBHOOK_URL=https://<你的公网域名>
N8N_BLOCK_ENV_ACCESS_IN_NODE=false
NODE_FUNCTION_ALLOW_BUILTIN=crypto
GOOGLE_SHEETS_DOCUMENT_ID=<你的 Sheet ID>
SLACK_CHANNEL_ID=<频道 ID>
```

- [ ] Slack App 已安装到 workspace，Bot 已加入通知频道
- [ ] Google Sheets `leads` 表已追加 **`owner_id`**、**`lead_stage`** 两列（见第三节）
- [ ] CRM 通知已是 Block Kit 卡片且含三个按钮（若仍是纯文本，见第五节）
- [ ] `config_main.mode=production` 时才会发 Slack 通知（test 模式不发，无法测按钮）

---

## 三、Google Sheets 变更

在 **`leads`** 表头追加（建议放在 `reviewed_at` 之后）：

| 列名 | 示例值 | 说明 |
|------|--------|------|
| `owner_id` | `U01234567` | Assign 时写入 Slack 用户 ID |
| `lead_stage` | `sql` / `nurture` / `junk` / `mql` | 漏斗阶段 |

模板参考：`sheets/template/leads.csv`

可选：在 **`config_main`** 表增加一行（文档用途，实际权限由 env 控制）：

| key | value | description |
|-----|-------|-------------|
| `slack_admin_users` | `U01234567,U89ABCDEF` | 允许点击按钮的 Slack 用户 ID，逗号分隔 |

---

## 四、platform-n8n/.env 新增变量

在 `platform-n8n/.env` 追加：

```bash
# Slack 交互验签（Slack App → Basic Information → Signing Secret）
SLACK_SIGNING_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 可选：限制谁可以点击 Block Kit 按钮（逗号分隔 Slack 用户 ID）
# 留空 = 开发模式，允许所有人点击
SLACK_ADMIN_USERS=U01234567,U89ABCDEF
```

**获取 Signing Secret：**

1. 打开 [api.slack.com/apps](https://api.slack.com/apps) → 选择你的 App  
2. **Basic Information** → **App Credentials** → **Signing Secret** → Show → 复制  

**获取 Slack 用户 ID（用于 SLACK_ADMIN_USERS）：**

1. Slack 客户端 → 点击用户头像 → **View full profile**  
2. **⋯** → **Copy member ID**（形如 `U01234567`）

修改 env 后 **重启 n8n**：

```bash
cd ../platform-n8n
docker compose -f docker/compose.yml up -d
```

---

## 五、Slack App 配置

### 5.1 开启 Interactivity（必做）

1. [api.slack.com/apps](https://api.slack.com/apps) → 你的 App  
2. **Interactivity & Shortcuts** → **Interactivity** → **ON**  
3. **Request URL** 填：

```
https://<你的公网域名>/webhook/slack-interactions
```

4. 保存后 Slack 会发验证请求；需先完成 **第八节** 导入并 **Activate** `B2B Lead Slack Actions`，否则验证失败。

### 5.2 OAuth Scopes（核对）

在 **OAuth & Permissions** → **Bot Token Scopes** 至少包含：

| Scope | 用途 |
|-------|------|
| `chat:write` | 发 Block Kit 通知 |
| `chat:write.public` | 可选，Bot 未邀请也能发公开频道 |

交互回复走 `response_url`（HTTP POST），**不额外需要** `chat:write` 权限，但发通知仍需要。

### 5.3 重装 App（若改了 Scopes）

**Install App** → **Reinstall to Workspace**

---

## 六、新工作流：导入 B2B Lead Slack Actions

### 6.1 Import

1. n8n → **Workflows** → **Import from File**  
2. 选择 `workflows/B2B Lead Slack Actions.json`  
3. 打开工作流，绑定凭证：  
   - 所有 **Google Sheets** 节点 → 你的 Google Sheets OAuth  
4. **Settings**（工作流级）→ **Error Workflow** → 选 **B2B Lead Error Handler**  
5. **Activate** 工作流（必须 Active，Slack 只调 Production URL）

### 6.2 节点速查（import 后自检）

| 节点 | 作用 |
|------|------|
| Slack Interactions Webhook | `POST /webhook/slack-interactions`；**Options → Raw Body = ON**（必须） |
| Verify Slack Signature | 读 `binary.data` 原始 body 做 HMAC；空 secret 时跳过（dev） |
| Parse Slack Payload | 解析 `body.payload`，提取 action / user / response_url / message_ts |
| Resolve Lead Action | 映射 assign / junk / nurture，并设置 `recommended_action` |
| Update Lead Review | 按 `lead_id` 更新 Sheets |
| Should Trigger CRM? | Assign / Nurture 为 true → 触发 HubSpot |
| Prepare Slack CRM Payload | 组装 CRM 子流程入参，`skip_notification=true` |
| Execute Post-Assign CRM Sync | 调用 **B2B Lead CRM Sync Notification** |
| Slack Update Final | `chat.update` 原地更新结果卡片 |
| Write Slack Action Audit Log | 写 `audit_logs` |

### 6.3 无需绑定的节点

- **Post Slack Response** 使用 HTTP Request 调 Slack `response_url`，**不需要** Slack OAuth 凭证。

### 6.4 已 import 工作流的手动补丁（不 re-import 时）

1. **Slack Interactions Webhook** → **Options** → 打开 **Raw Body**
2. **Verify Slack Signature** → 用仓库 `workflows/B2B Lead Slack Actions.json` 里该节点的 `jsCode` 整段替换
3. 重启 n8n 使 env 生效

---

## 七、现有工作流手动修改

> ⚠️ 以下步骤在 n8n UI 中操作，**不要** re-import 覆盖你已接好的 Hunter 等节点。

### 7.1 判断：CRM 通知是否已有 Block Kit 按钮？

打开 **B2B Lead CRM Sync Notification** → 节点 **Build Notification Payload** → 查看 Code 是否包含：

```javascript
action_id: 'assign_lead'
action_id: 'mark_junk'
action_id: 'nurture_lead'
```

- **已有** → 跳到 [7.3](#73-b2b-lead-enrichment-scoringexecute-crm-sync-字段映射)  
- **没有（仍是纯文本 Slack）** → 继续 7.2

### 7.2 B2B Lead CRM Sync Notification — 升级 Block Kit

#### A. 修改 `Build Notification Payload` Code 节点

对照仓库最新版整段替换 Code（来源：`scripts/generate_workflows.py` 中 `NOTIFICATION_PAYLOAD_JS`）。

核心逻辑必须包含：

1. `buildSlackBlocks()` 构建 blocks  
2. `actions` 区块三个按钮，`action_id` 分别为 `assign_lead` / `mark_junk` / `nurture_lead`  
3. 按钮 `value`：

```javascript
JSON.stringify({ lead_id: item.lead_id, correlation_id: item.correlation_id })
```

4. 输出字段：`notification.slack_blocks`、`notification.slack_blocks_valid`

> 完整 JS 约 400+ 行，建议从生成的 `workflows/B2B Lead CRM Sync Notification.json` 里复制 **Build Notification Payload** 节点的 `jsCode`，粘贴到 UI 同名节点。

#### B. 增加分支：Block Kit vs 纯文本降级

在 **Should Notify?** 之后、原 **Slack Notify** 之前：

1. 新增 **IF** 节点 **Use Slack Blocks?**  
   - 条件：`{{ $json.notification.slack_blocks_valid }}` is true  

2. 新增 **Slack** 节点 **Slack Notify**（Block Kit 版）  
   - Resource: Message  
   - Operation: Post  
   - Message Type: **Blocks**  
   - Channel: `{{ $env.SLACK_CHANNEL_ID }}`  
   - Blocks: `{{ JSON.stringify($json.notification.slack_blocks) }}`  
   - Notification Text（fallback）: `{{ $json.notification.message }}`  
   - On Error: **Continue (using error output)**  
   - Retry: ON, 3 tries, 5s  

3. 原纯文本 Slack 节点改名为 **Slack Notify Text**（降级路径）  

4. 连线：

```text
Should Notify? (true)
  → Use Slack Blocks? (true)  → Slack Notify (blocks)      ─┐
  → Use Slack Blocks? (false) → Slack Notify Text (plain)  ─┼→ Mark Notification Sent
```

5. 两个 Slack 节点的 error output → **Log Slack Notify Error**（已有则复用）

#### C. 扩展 Trigger 输入字段（When Executed by Another Workflow）

打开 CRM Sync 的 **When Executed by Another Workflow**，确保 **Workflow Input Schema** 包含以下字段（画像 + Sales Memo 用，缺了 Block Kit 仍可用但区块显示 N/A）：

| 字段名 | 类型 |
|--------|------|
| `industry` | string |
| `company_size` | string |
| `company_region` | string |
| `content_summary` | string |
| `intent_signals` | string |
| `enrichment_summary` | string |
| `enrichment_status` | string |
| `sales_memo` | string |
| `sales_memo_status` | string |
| `source_type` | string |
| `source_name` | string |

基础字段（`lead_id`, `correlation_id`, `score` 等）应已存在。

---

### 7.3 B2B Lead Enrichment Scoring — Execute CRM Sync 字段映射

打开 **B2B Lead Enrichment Scoring** → **Execute CRM Sync** 节点 → **Workflow Inputs**，确认以下映射存在（缺则手动添加）：

| Input 名 | Expression |
|----------|------------|
| `industry` | `{{ $json.industry ?? "" }}` |
| `company_size` | `{{ $json.company_size ?? "" }}` |
| `company_region` | `{{ $json.company_region ?? "" }}` |
| `content_summary` | `{{ $json.content_summary ?? "" }}` |
| `intent_signals` | `{{ $json.intent_signals ?? "" }}` |
| `enrichment_summary` | `{{ $json.enrichment_summary ?? "" }}` |
| `enrichment_status` | `{{ $json.enrichment_status ?? "" }}` |
| `sales_memo` | `{{ $json.sales_memo ?? "" }}` |
| `sales_memo_status` | `{{ $json.sales_memo_status ?? "" }}` |
| `source_type` | `{{ $json.source_type ?? "" }}` |
| `source_name` | `{{ $json.source_name ?? "" }}` |

**按钮交互本身只依赖 `lead_id` + `correlation_id`**，上述 enrichment 字段仅影响 Slack 卡片内容，不影响 Slack Actions 写 Sheets。

---

### 7.4 B2B Lead CRM Sync Notification — Slack 触发同步（必做）

Slack 点 **Assign** / **Nurture** 后会调用本子流程写 HubSpot。需手动改两处，避免 **重复发 Slack 通知**。

#### A. 扩展 Trigger 输入字段

在 **When Executed by Another Workflow** → **Workflow Input Schema** 追加：

| 字段名 | 类型 |
|--------|------|
| `skip_notification` | boolean |
| `trigger_source` | string |

#### B. 修改 `CRM Gate` Code 节点

对照 `workflows/B2B Lead CRM Sync Notification.json` 中 **CRM Gate** 的 `jsCode` 整段替换。核心逻辑：

```javascript
const skipNotification = item.skip_notification === true || item.trigger_source === 'slack_action';
// ...
skip_notification: skipNotification,
```

#### C. 修改 `Build Notification Payload` 与 `Should Notify?`

在 **Build Notification Payload** 末尾统一计算门禁（`skip_notification` 保留在**根级**，`notification` 只放消息内容）：

```javascript
const skipNotification = item.skip_notification === true;
const shouldSendSlack = mode === 'production' && !skipNotification;
return {
  ...item,
  skip_notification: skipNotification,
  should_send_slack: shouldSendSlack,
  notification: payload,
};
```

**Should Notify?** 改为单一 Boolean（读根级 `should_send_slack`）：

```text
{{ $json.should_send_slack }}
```

- `true` → 走 Slack Notify（Enrichment 自动高分/待审路径）
- `false` → Skip Notification Test（test 模式、或 Slack 按钮触发的 CRM 同步）

> 不要用 `$json.notification.skip_notification`——`notification` 里没有这个字段。

#### D. 验证

1. `config_main.mode=production`，HubSpot 凭证已绑  
2. 提交一条 40–79 分 lead → Slack 收到待审卡片  
3. 点 **Assign** → Sheets：`review_status=approved`，`crm_status=synced`，`crm_contact_id` 有值  
4. Slack **不应**再收到第二条「New high-score lead」通知  
5. 点 **Nurture** → HubSpot 有联系人，`lead_stage=nurture`，同样无第二条 Slack  

---

## 八、推荐操作顺序（一次性上线）

按顺序执行，避免 Slack Interactivity 验证失败：

| 步骤 | 操作 |
|------|------|
| 1 | Sheets 追加 `owner_id`、`lead_stage` 列 |
| 2 | `platform-n8n/.env` 写入 `SLACK_SIGNING_SECRET`（及可选 `SLACK_ADMIN_USERS`）→ 重启 n8n |
| 3 | Import + Activate **B2B Lead Slack Actions**，绑定 Sheets 凭证，设 Error Workflow |
| 4 | 手动改 **CRM Sync Notification**（Block Kit + 7.4 `skip_notification` 门禁） |
| 5 | 手动改 **Enrichment Scoring** 的 Execute CRM Sync 映射（若缺 enrichment 字段） |
| 6 | Re-import 或手动补丁 **B2B Lead Slack Actions**（含 CRM 触发分支） |
| 7 | Slack App → Interactivity → 填 Request URL → Save |
| 8 | `config_main.mode=production` → 提交测试 lead → 点按钮验收 HubSpot |

---

## 九、测试与验收

### 9.1 端到端测试

1. Google Sheets `config_main.mode` 设为 **`production`**  
2. 提交一条能触发高分/复核通知的测试 lead（Tally 表单）  
3. Slack 频道应收到 **Block Kit 卡片**，底部有 Assign / Mark Junk / Nurture  
4. 点击 **Assign**  
   - Slack 卡片原地更新为「Assigned」  
   - Sheets 该行：`review_status=approved`, `lead_stage=sql`, `recommended_action=crm_sync`, `owner_id` = 你的 Slack UID  
   - `crm_status=synced`，`crm_contact_id` 有值（production + HubSpot 已绑）  
   - `audit_logs` 新增 `slack_action_assign`  
5. 对另一条 lead 分别测试 Junk、Nurture（Nurture 应同步 HubSpot，无第二条 Slack）  

### 9.2 验收表

| 场景 | 预期 |
|------|------|
| 点击 Assign | Sheets + HubSpot 同步 + Slack 卡片更新 + audit |
| 点击 Mark Junk | `review_status=rejected`, `lead_stage=junk`；**不进** HubSpot |
| 点击 Nurture | `lead_stage=nurture`；HubSpot upsert；无第二条 Slack |
| lead_id 不存在 | ephemeral「Lead not found」，不报错 |
| 非授权用户（配置了 SLACK_ADMIN_USERS） | ephemeral「You are not authorized…」 |
| 错误 Signing Secret | Slack Interactivity 保存失败；或请求 401 |
| test 模式 | 不发 Slack，无法测按钮；CRM 同步也会 `skipped_test_mode` |

### 9.3 查看 n8n 执行记录

**Executions** → 筛选 **B2B Lead Slack Actions** → 确认节点：

- `Verify Slack Signature` → `signature_valid: true`  
- `Match Lead By ID` → `lead_found: true`  
- `Update Lead Review` → 成功  
- `Execute Post-Assign CRM Sync` → 成功（Assign/Nurture）  
- `Slack Update Final` → 成功  

---

## 十、故障排查

### Slack 保存 Interactivity URL 时报错

| 原因 | 处理 |
|------|------|
| 工作流未 Active | Activate **B2B Lead Slack Actions** |
| URL 不可公网访问 | 检查 ngrok / 防火墙 |
| Signing Secret 未配且验签失败 | 先配 secret 或临时留空 secret（dev 跳过验签） |
| n8n 未重启读 env | `docker compose up -d` 重启 |

### 点击按钮无反应

| 原因 | 处理 |
|------|------|
| Interactivity URL 未配或配错 | 核对 `/webhook/slack-interactions` |
| 通知是纯文本，无按钮 | 完成第七节 CRM Sync 升级 |
| 工作流未 Active | Activate Slack Actions |
| 3 秒内未返回 200 | 查 Executions 是否超时；Sheets 读慢会延迟 |

### 按钮有反应但 Sheets 未更新

| 原因 | 处理 |
|------|------|
| 缺 `owner_id` / `lead_stage` 列 | 补列 |
| Google Sheets 凭证失效 | 重新授权 |
| lead_id 不匹配 | 检查按钮 value 里 JSON 是否含正确 UUID |

### 线程无回复但 Sheets 已更新

| 原因 | 处理 |
|------|------|
| `Post Slack Response` 失败 | 看 Executions error output |
| `response_url` 过期（30 分钟） | 正常；Slack 限制，重新发通知再测 |

### 签名校验 401 / timestamp_expired

| 原因 | 处理 |
|------|------|
| **在 n8n 里重放旧 Execution** | Slack 时间戳超过 5 分钟 → `timestamp_expired`。请 **live 点击按钮** 测试，不要 Replay 20 分钟前的执行 |
| 想调试旧 Execution | 临时设 `SLACK_SKIP_TIMESTAMP_CHECK=true`（仅 dev，生产勿开） |
| `invalid_signature` | 检查 `SLACK_SIGNING_SECRET` 是否与 Slack App 一致；Webhook 必须开启 **Raw Body** |
| 验签节点 `raw_body_source` | 应为 `binary.data`；若是 `payload_reencoded` 说明 Raw Body 未开，可能验签失败 |

**Verify Slack Signature 输出字段说明：**

| 字段 | 含义 |
|------|------|
| `signature_error=timestamp_expired` | 时间戳超时，但 `signature_match=true` 表示 secret/body 正确 |
| `signature_error=invalid_signature` | secret 或 raw body 不对 |
| `signature_age_seconds` | 请求时间与 n8n 当前时间的差值（秒） |
| `raw_body_source` | `binary.data`（推荐） / `payload_reencoded`（降级，不可靠） |

确认 `platform-n8n/.env` 已有：

```bash
N8N_BLOCK_ENV_ACCESS_IN_NODE=false
NODE_FUNCTION_ALLOW_BUILTIN=crypto
SLACK_SIGNING_SECRET=<Signing Secret>
# 调试重放时可临时开启：
# SLACK_SKIP_TIMESTAMP_CHECK=true
```

---

## 十一、安全清单

- [ ] 生产环境务必配置 `SLACK_SIGNING_SECRET`（不要依赖 dev 跳过验签）
- [ ] 生产环境配置 `SLACK_ADMIN_USERS` 限制可操作人员
- [ ] Signing Secret 不进 Git（只放 `platform-n8n/.env`）
- [ ] Interactivity URL 使用 HTTPS
- [ ] 定期轮换 Signing Secret（Slack App 可 Regenerate，同步更新 env）

---

## 十二、快速命令速查

```bash
# 1. 重启 n8n 使 env 生效
cd ../platform-n8n
docker compose -f docker/compose.yml up -d

# 2. 重新生成 workflow JSON（仅新工作流需要 import 时）
cd ../crm-workflow
python3 scripts/generate_workflows.py

# 3. 确认 Webhook 可达（应返回 4xx/405，说明路由存在）
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://<域名>/webhook/slack-interactions"
```

---

## 相关文档

- [CREDENTIALS.md](CREDENTIALS.md) — Slack OAuth、Signing Secret、Admin 用户  
- [FIELD_MAPPING.md](FIELD_MAPPING.md) — `owner_id` / `lead_stage` 字段说明  
- [SHEETS_SETUP.md](SHEETS_SETUP.md) — leads 列定义  
- [ERROR_HANDLING_NODES.md](ERROR_HANDLING_NODES.md) — Slack Actions 错误分支  
- [TEST_PRODUCTION.md](TEST_PRODUCTION.md) — production 门控与 Slack 发送条件  

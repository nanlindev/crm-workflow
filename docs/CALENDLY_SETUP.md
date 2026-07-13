# Calendly Webhook 接入操作指南

> 适用：`crm-workflow` 的 **B2B Lead Calendly Webhook** 工作流  
> 前提：Google Sheets `leads` 表已添加 `meeting_status` / `meeting_time` / `calendly_event_uri` / `calendly_invitee_email` 四列

---

## 一、概念区分（必读）

| 名称 | 是什么 | 用途 | 写进哪里 |
|------|--------|------|----------|
| **Personal Access Token（PAT）** | Calendly 个人访问令牌（JWT 形态） | 调用 Calendly API（创建/查询/删除 webhook 订阅） | **仅 curl 时用**，不写进 n8n |
| **Webhook Signing Key** | 你自己生成的随机密钥 | n8n 验签 Calendly 推送的请求 | `platform-n8n/.env` → `CALENDLY_WEBHOOK_SIGNING_KEY` |

**常见误区：**

- PAT ≠ Signing Key，不能把 PAT 填进 `CALENDLY_WEBHOOK_SIGNING_KEY`
- Calendly **新版 API 创建订阅的响应里通常不返回** `signing_key`
- 正确做法：**创建 webhook 订阅时，在请求体里自己传入 `signing_key`**
- Signing Key **创建后无法通过 GET 再取回**；丢了只能删订阅重建

---

## 二、前置条件

- [ ] Calendly **付费计划**（Webhook 订阅为付费功能）
- [ ] n8n 已部署且 **B2B Lead Calendly Webhook** 工作流已导入
- [ ] 公网可访问的 n8n Webhook URL（如 ngrok）
- [ ] n8n 工作流已 **Active**（Calendly 只能调 Production URL）

**Webhook URL 格式：**

```
https://<你的公网域名>/webhook/calendly
```

**platform-n8n/.env 需具备：**

```bash
WEBHOOK_URL=https://<你的公网域名>
N8N_BLOCK_ENV_ACCESS_IN_NODE=false
NODE_FUNCTION_ALLOW_BUILTIN=crypto
```

---

## 三、步骤 1：创建 Personal Access Token

1. 登录 [Calendly Developer](https://developer.calendly.com/)
2. 进入 **Personal Access Tokens**
3. 点击 **Generate new token**
4. 勾选至少以下 scope：

| Scope | 用途 |
|-------|------|
| `users:read` | 查询 `/users/me` 拿 user URI |
| `organizations:read` | 拿 organization URI |
| `webhooks:read` | 列出/查询 webhook 订阅 |
| `webhooks:write` | 创建/删除 webhook 订阅 |

5. 创建后立即 **Copy token**（只显示一次，无法找回）

**安全建议：** 用环境变量引用，不要写进 shell 历史：

```bash
export CALENDLY_PAT='粘贴你的token'
```

---

## 四、步骤 2：查询 User / Organization URI

```bash
curl -s https://api.calendly.com/users/me \
  -H "Authorization: Bearer $CALENDLY_PAT" | jq .
```

从响应中记录：

| 字段 | 示例 | 用途 |
|------|------|------|
| `resource.uri` | `https://api.calendly.com/users/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` | user scope 时用 |
| `resource.current_organization` | `https://api.calendly.com/organizations/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` | organization scope 时用 |

**若报 `Insufficient scope`，需重新生成带 `users:read` 的 PAT。**

---

## 五、步骤 3：自己生成 Signing Key

```bash
openssl rand -hex 32
```

输出示例（64 位十六进制）：

```
a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

**保存到密码管理器。** 此值将同时用于：

1. 创建 webhook 订阅时的 API 请求体
2. `platform-n8n/.env` 的 `CALENDLY_WEBHOOK_SIGNING_KEY`

---

## 六、步骤 4：创建 Webhook 订阅

### 6.1 组织级订阅（推荐，团队所有成员预约都能收到）

```bash
export CALENDLY_SIGNING_KEY='步骤3生成的随机字符串'
export N8N_WEBHOOK_URL='https://<你的公网域名>/webhook/calendly'
export CALENDLY_ORG_URI='https://api.calendly.com/organizations/<你的ORG_UUID>'

curl -s -X POST https://api.calendly.com/webhook_subscriptions \
  -H "Authorization: Bearer $CALENDLY_PAT" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"$N8N_WEBHOOK_URL\",
    \"events\": [\"invitee.created\", \"invitee.canceled\"],
    \"organization\": \"$CALENDLY_ORG_URI\",
    \"scope\": \"organization\",
    \"signing_key\": \"$CALENDLY_SIGNING_KEY\"
  }" | jq .
```

### 6.2 个人级订阅（仅自己的日历）

> 在组织计划下，即使 `scope: user`，也**必须同时传 `organization`**

```bash
export CALENDLY_USER_URI='https://api.calendly.com/users/<你的USER_UUID>'

curl -s -X POST https://api.calendly.com/webhook_subscriptions \
  -H "Authorization: Bearer $CALENDLY_PAT" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"$N8N_WEBHOOK_URL\",
    \"events\": [\"invitee.created\", \"invitee.canceled\"],
    \"organization\": \"$CALENDLY_ORG_URI\",
    \"user\": \"$CALENDLY_USER_URI\",
    \"scope\": \"user\",
    \"signing_key\": \"$CALENDLY_SIGNING_KEY\"
  }" | jq .
```

### 6.3 成功响应示例

```json
{
  "resource": {
    "callback_url": "https://xxx.ngrok-free.dev/webhook/calendly",
    "state": "active",
    "events": ["invitee.created", "invitee.canceled"],
    "scope": "organization",
    "uri": "https://api.calendly.com/webhook_subscriptions/<SUBSCRIPTION_UUID>"
  }
}
```

**注意：** 响应里可能没有 `signing_key` 字段——正常。你步骤 3 生成的字符串就是 signing key。

---

## 七、步骤 5：管理已有订阅（可选）

### 列出所有订阅

```bash
curl -s "https://api.calendly.com/webhook_subscriptions?organization=$CALENDLY_ORG_URI&scope=organization" \
  -H "Authorization: Bearer $CALENDLY_PAT" | jq .
```

### 查看单个订阅

```bash
curl -s "https://api.calendly.com/webhook_subscriptions/<SUBSCRIPTION_UUID>" \
  -H "Authorization: Bearer $CALENDLY_PAT" | jq .
```

> GET 响应**不会**包含 signing_key

### 删除订阅（Signing Key 丢失时重建前必做）

```bash
curl -X DELETE \
  "https://api.calendly.com/webhook_subscriptions/<SUBSCRIPTION_UUID>" \
  -H "Authorization: Bearer $CALENDLY_PAT"
```

---

## 八、步骤 6：配置 n8n 环境变量

编辑 `platform-n8n/.env`：

```bash
# 填步骤 3 生成的随机字符串，不是 PAT！
CALENDLY_WEBHOOK_SIGNING_KEY=<你的signing_key>
```

重启 n8n：

```bash
cd platform-n8n
docker compose -f docker/compose.yml up -d
```

**开发期跳过验签（可选）：** 留空或注释掉该行，工作流会跳过签名校验。但 webhook 订阅仍必须存在。

---

## 九、步骤 7：n8n 工作流配置

1. 导入 `workflows/B2B Lead Calendly Webhook.json`（若尚未导入）
2. 绑定凭证：Google Sheets、Slack
3. **Settings → Error Workflow → B2B Lead Error Handler**
4. 右上角 **Active** 工作流
5. 点开 **Calendly Webhook** 节点，确认 Production URL：
   ```
   https://<你的公网域名>/webhook/calendly
   ```

**Intake 手动补字段（UI 维护，勿 re-import）：**  
`Append Lead` 节点增加列映射 `meeting_status` = `not_booked`

详见 [INSTALL.md](INSTALL.md) 与 [ERROR_HANDLING_NODES.md](ERROR_HANDLING_NODES.md)。

---

## 十、步骤 8：验证

### 10.1 预约测试

1. 确保 `leads` 表中有测试行，`contact_email` 与 Calendly 预约邮箱一致
2. 用该邮箱在 Calendly 预约一次会议
3. 检查 n8n **Executions** → `B2B Lead Calendly Webhook` 是否成功
4. 检查 Sheets：

| 字段 | 预期 |
|------|------|
| `meeting_status` | `booked` |
| `meeting_time` | ISO 时间 |
| `calendly_event_uri` | Calendly URI |
| `calendly_invitee_email` | 预约邮箱 |

5. Slack 应收到 `📅 Meeting booked` 通知
6. `audit_logs` 应有 `calendly_booked`

### 10.2 取消测试

取消会议 → `meeting_status` = `canceled`，audit = `calendly_canceled`

### 10.3 未匹配测试

用 leads 表里没有的邮箱预约 → audit = `calendly_unmatched`，不报错

---

## 十一、故障排查

| 现象 | 原因 | 处理 |
|------|------|------|
| `/users/me` 报 `Insufficient scope` | PAT 缺 `users:read` | 重新生成 token |
| user scope 报 `organization is missing` | 组织计划下必须传 organization | 请求体加 `organization` |
| 创建成功但无 signing_key | 新版 API 正常行为 | 自己生成并在 POST 时传入 |
| n8n 一直 401 | `.env` 填了 PAT 而非 signing key | 换成步骤 3 的随机字符串 |
| Calendly 不推送 | 工作流未 Active / ngrok 挂了 / URL 不对 | 检查 Production URL 和隧道 |
| 匹配不到 lead | 邮箱不一致 | 核对 `contact_email` 大小写无关但需相同 |
| 改期 | Calendly 先发 cancel 再 create | 工作流会识别为 `rescheduled` |

---

## 十二、Signing Key 丢失后的恢复流程

1. `openssl rand -hex 32` 生成新 key
2. `DELETE` 旧 webhook 订阅
3. `POST` 重建，请求体带新 `signing_key`
4. 更新 `platform-n8n/.env` → 重启 n8n

---

## 十三、安全清单

- [ ] PAT 只用于 API 调用，不进 n8n 环境变量
- [ ] Signing Key 与 PAT 分开保管
- [ ] Token 泄露后立即在 Calendly 撤销并重新生成
- [ ] 生产环境务必配置 `CALENDLY_WEBHOOK_SIGNING_KEY`
- [ ] 不要把 PAT / Signing Key 提交进 Git

---

## 十四、快速命令速查

```bash
# 1. 设置变量
export CALENDLY_PAT='你的PAT'
export CALENDLY_SIGNING_KEY=$(openssl rand -hex 32)
echo "Signing Key: $CALENDLY_SIGNING_KEY"   # 保存此值！

# 2. 查 URI
curl -s https://api.calendly.com/users/me \
  -H "Authorization: Bearer $CALENDLY_PAT" | jq '.resource | {uri, current_organization}'

# 3. 创建订阅（替换 ORG_URI 和 WEBHOOK_URL）
curl -s -X POST https://api.calendly.com/webhook_subscriptions \
  -H "Authorization: Bearer $CALENDLY_PAT" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://<域名>/webhook/calendly\",
    \"events\": [\"invitee.created\", \"invitee.canceled\"],
    \"organization\": \"https://api.calendly.com/organizations/<ORG_UUID>\",
    \"scope\": \"organization\",
    \"signing_key\": \"$CALENDLY_SIGNING_KEY\"
  }" | jq .

# 4. 写入 platform-n8n/.env 后重启
# CALENDLY_WEBHOOK_SIGNING_KEY=<同上signing_key>
# cd platform-n8n && docker compose -f docker/compose.yml up -d
```

---

## 相关文档

- [CREDENTIALS.md](CREDENTIALS.md) — 环境变量总览
- [INSTALL.md](INSTALL.md) — 工作流导入顺序
- [FIELD_MAPPING.md](FIELD_MAPPING.md) — Calendly 字段映射
- [SHEETS_SETUP.md](SHEETS_SETUP.md) — leads 预约列说明

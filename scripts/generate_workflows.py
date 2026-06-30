#!/usr/bin/env python3
"""Generate n8n workflow JSON exports for the CRM lead automation template."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / "workflows"


def nid(name: str = "") -> str:
    return str(uuid.uuid4())


def code_node(name: str, js: str, position: list[int], mode: str = "runOnceForEachItem") -> dict:
    return {
        "parameters": {"mode": mode, "jsCode": js},
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": position,
        "id": nid(name),
        "name": name,
    }


def sheets_read(name: str, position: list[int], sheet_name: str) -> dict:
    return {
        "parameters": {
            "documentId": {
                "__rl": True,
                "mode": "id",
                "value": "={{ $env.GOOGLE_SHEETS_DOCUMENT_ID || 'REPLACE_WITH_SHEET_ID' }}"
            },
            "sheetName": {"__rl": True, "mode": "name", "value": sheet_name},
            "options": {},
        },
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.5,
        "position": position,
        "id": nid(name),
        "name": name,
        "onError": "continueErrorOutput",
        "credentials": {
            "googleSheetsOAuth2Api": {"id": "GOOGLE_SHEETS_CREDENTIAL_ID", "name": "Google Sheets account"}
        },
    }


def sheets_append(name: str, position: list[int], sheet_name: str, columns_expr: str) -> dict:
    return {
        "parameters": {
            "operation": "append",
            "documentId": {
                "__rl": True,
                "mode": "id",
                "value": "={{ $env.GOOGLE_SHEETS_DOCUMENT_ID || 'REPLACE_WITH_SHEET_ID' }}"
            },
            "sheetName": {"__rl": True, "mode": "name", "value": sheet_name},
            "columns": {
                "mappingMode": "defineBelow",
                "value": columns_expr,
            },
            "options": {},
        },
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.5,
        "position": position,
        "id": nid(name),
        "name": name,
        "onError": "continueErrorOutput",
        "credentials": {
            "googleSheetsOAuth2Api": {"id": "GOOGLE_SHEETS_CREDENTIAL_ID", "name": "Google Sheets account"}
        },
    }


def sheets_update(name: str, position: list[int], sheet_name: str, match_column: str, columns: dict) -> dict:
    return {
        "parameters": {
            "operation": "update",
            "documentId": {
                "__rl": True,
                "mode": "id",
                "value": "={{ $env.GOOGLE_SHEETS_DOCUMENT_ID || 'REPLACE_WITH_SHEET_ID' }}"
            },
            "sheetName": {"__rl": True, "mode": "name", "value": sheet_name},
            "columns": {
                "mappingMode": "defineBelow",
                "value": columns,
                "matchingColumns": [match_column],
            },
            "options": {},
        },
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.5,
        "position": position,
        "id": nid(name),
        "name": name,
        "onError": "continueErrorOutput",
        "credentials": {
            "googleSheetsOAuth2Api": {"id": "GOOGLE_SHEETS_CREDENTIAL_ID", "name": "Google Sheets account"}
        },
    }


def merge_node(name: str, position: list[int], inputs: int = 2) -> dict:
    return {
        "parameters": {"mode": "combine", "combineBy": "combineAll", "options": {}},
        "type": "n8n-nodes-base.merge",
        "typeVersion": 3,
        "position": position,
        "id": nid(name),
        "name": name,
    }


def if_node(name: str, position: list[int], condition_left: str, condition_right: str = "true") -> dict:
    return {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
                "conditions": [
                    {
                        "id": nid(),
                        "leftValue": condition_left,
                        "rightValue": condition_right,
                        "operator": {"type": "string", "operation": "equals"},
                    }
                ],
                "combinator": "and",
            },
            "options": {},
        },
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": position,
        "id": nid(name),
        "name": name,
    }


def execute_workflow(name: str, position: list[int], target_workflow: str) -> dict:
    return {
        "parameters": {
            "workflowId": {"__rl": True, "mode": "name", "value": target_workflow},
            "options": {},
        },
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": 1.2,
        "position": position,
        "id": nid(name),
        "name": name,
    }


def webhook_node(name: str, position: list[int], path: str) -> dict:
    return {
        "parameters": {"path": path, "options": {}},
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": position,
        "id": nid(name),
        "name": name,
        "webhookId": nid(path),
    }


def http_request_node(name: str, position: list[int], method: str, url: str, body_fields: list[dict]) -> dict:
    return {
        "parameters": {
            "method": method,
            "url": url,
            "sendBody": True,
            "bodyParameters": {"parameters": body_fields},
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "X-Correlation-Id", "value": "={{ $json.correlation_id }}"},
                ]
            },
            "options": {
                "batching": {"batch": {"batchSize": 1, "batchInterval": 2000}},
                "timeout": 45000,
            },
        },
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.4,
        "position": position,
        "id": nid(name),
        "name": name,
        "retryOnFail": True,
        "waitBetweenTries": 5000,
        "onError": "continueErrorOutput",
    }


def noop(name: str, position: list[int]) -> dict:
    return {
        "parameters": {},
        "type": "n8n-nodes-base.noOp",
        "typeVersion": 1,
        "position": position,
        "id": nid(name),
        "name": name,
    }


def connect(connections: dict, src: str, dst: str, src_output: int = 0, dst_input: int = 0) -> None:
    connections.setdefault(src, {"main": []})
    while len(connections[src]["main"]) <= src_output:
        connections[src]["main"].append([])
    connections[src]["main"][src_output].append({"node": dst, "type": "main", "index": dst_input})


def save_workflow(filename: str, name: str, nodes: list, connections: dict, error_workflow: str | None = None) -> None:
    settings = {"executionOrder": "v1", "callerPolicy": "workflowsFromSameOwner"}
    if error_workflow:
        settings["errorWorkflow"] = error_workflow
    payload = {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": settings,
        "versionId": nid(),
        "meta": {"templateCredsSetupCompleted": False},
        "tags": [{"name": "crm-workflow"}],
    }
    path = WORKFLOWS_DIR / filename
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {path}")


# --- Shared JavaScript snippets ---

BUILD_GLOBAL_CONFIG_JS = r"""
const lead = $('When Executed by Another Workflow').item.json;
const mainRows = $('Read config_main').all().map(i => i.json);
const routingRows = $('Read config_routing').all().map(i => i.json);
const notificationRows = $('Read config_notifications').all().map(i => i.json);
const reviewRows = $('Read config_review').all().map(i => i.json);

const kv = {};
for (const row of mainRows) {
  if (row.key) kv[row.key] = row.value;
}

const scoreHigh = parseInt(kv.score_threshold_high || '80', 10);
const scoreLow = parseInt(kv.score_threshold_low || '40', 10);
const grayLow = parseInt(kv.score_gray_low || '40', 10);
const grayHigh = parseInt(kv.score_gray_high || '79', 10);

const global_config = {
  mode: (kv.mode || 'test').toLowerCase(),
  score_thresholds: { high: scoreHigh, low: scoreLow, gray_low: grayLow, gray_high: grayHigh },
  calendly_url: kv.calendly_url || '',
  source_trust_threshold: parseInt(kv.source_trust_threshold || '50', 10),
  freemail_domains: (kv.freemail_domains || 'gmail.com,outlook.com,yahoo.com,hotmail.com,icloud.com').split(',').map(s => s.trim()),
  routing_rules: routingRows.filter(r => r.min_score !== undefined),
  notification_rules: notificationRows.filter(r => r.enabled === true || r.enabled === 'true'),
  review_rules: reviewRows.filter(r => r.enabled === true || r.enabled === 'true'),
  _metadata: { processing_stage: 'config_loaded', config_load_failed: false },
};

return { ...lead, global_config };
"""

HANDLE_CONFIG_ERROR_JS = r"""
return {
  global_config: {
    mode: 'test',
    score_thresholds: { high: 80, low: 40, gray_low: 40, gray_high: 79 },
    calendly_url: '',
    source_trust_threshold: 50,
    freemail_domains: ['gmail.com','outlook.com','yahoo.com','hotmail.com','icloud.com'],
    routing_rules: [],
    notification_rules: [],
    review_rules: [],
    _metadata: { processing_stage: 'config_load_failed', config_load_failed: true, severity: 'high' },
  },
  ...($input.item.json || {}),
};
"""

NORMALIZE_TALLY_JS = r"""
const body = $input.item.json.body || $input.item.json;
const data = body.data || body;
const fields = data.fields || [];
const fieldMap = {};
for (const f of fields) {
  const key = (f.label || f.key || '').toLowerCase().replace(/\s+/g, '_');
  fieldMap[key] = f.value;
}
const getField = (...keys) => {
  for (const k of keys) {
    if (fieldMap[k]) return fieldMap[k];
  }
  return '';
};
const now = new Date().toISOString();
return {
  source_type: 'tally',
  source_name: data.formName || 'Tally Form',
  source_url: data.formUrl || body.formUrl || '',
  source_trust_level: 80,
  contact_name: getField('name', 'contact_name', 'full_name'),
  contact_email: getField('email', 'contact_email').toLowerCase().trim(),
  contact_role: getField('role', 'contact_role', 'job_title'),
  company_name: getField('company', 'company_name'),
  raw_content: getField('message', 'details', 'project_description', 'how_can_we_help'),
  processing_status: 'intake',
  created_at: now,
  updated_at: now,
  _metadata: { processing_stage: 'normalized_tally' },
};
"""

NORMALIZE_GFORMS_JS = r"""
const body = $input.item.json.body || $input.item.json;
const now = new Date().toISOString();
return {
  source_type: 'google_forms',
  source_name: body.formName || 'Google Form',
  source_url: body.formUrl || body.source_url || '',
  source_trust_level: 70,
  contact_name: body.name || body.contact_name || '',
  contact_email: (body.email || body.contact_email || '').toLowerCase().trim(),
  contact_role: body.role || body.contact_role || '',
  company_name: body.company || body.company_name || '',
  raw_content: body.message || body.raw_content || JSON.stringify(body),
  processing_status: 'intake',
  created_at: now,
  updated_at: now,
  _metadata: { processing_stage: 'normalized_google_forms' },
};
"""

GENERATE_IDS_JS = r"""
const crypto = require('crypto');
const item = $input.item.json;
const email = item.contact_email || '';
const domain = item.company_domain || (email.includes('@') ? email.split('@')[1] : '');
const sourceUrl = item.source_url || '';
const hashInput = `${email}|${domain}|${sourceUrl}`;
const lead_hash = crypto.createHash('sha256').update(hashInput).digest('hex').slice(0, 16);
return {
  ...item,
  lead_id: crypto.randomUUID(),
  correlation_id: crypto.randomUUID(),
  lead_hash,
  company_domain: domain,
  updated_at: new Date().toISOString(),
  _metadata: { processing_stage: 'ids_generated' },
};
"""

VALIDATE_LEAD_JS = r"""
const item = $input.item.json;
const email = item.contact_email || '';
const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
if (!emailOk) {
  return {
    ...item,
    validation_passed: false,
    validation_error: 'invalid_email',
    _metadata: { processing_stage: 'validation_failed', severity: 'low' },
  };
}
return {
  ...item,
  validation_passed: true,
  _metadata: { processing_stage: 'validation_passed' },
};
"""

DEDUP_LEAD_JS = r"""
const item = $input.item.json;
const existingRows = $('Read All Leads').all().map(r => r.json);
const findMatch = (rows, predicate) => rows.find(predicate);

let existing = null;
if (item.contact_email) {
  existing = findMatch(existingRows, r => (r.contact_email || '').toLowerCase() === item.contact_email);
}
if (!existing && item.company_domain) {
  existing = findMatch(existingRows, r => r.company_domain === item.company_domain);
}
if (!existing && item.source_url) {
  existing = findMatch(existingRows, r => r.source_url === item.source_url);
}
if (!existing && item.lead_hash) {
  existing = findMatch(existingRows, r => r.lead_hash === item.lead_hash);
}

if (existing && existing.lead_id) {
  return {
    ...item,
    lead_id: existing.lead_id,
    correlation_id: item.correlation_id,
    is_update: true,
    updated_at: new Date().toISOString(),
    _metadata: { processing_stage: 'dedup_update' },
  };
}
return {
  ...item,
  is_update: false,
  _metadata: { processing_stage: 'dedup_insert' },
};
"""

DOMAIN_ENRICHMENT_JS = r"""
const item = $input.item.json;
const config = item.global_config || {};
const freemail = config.freemail_domains || [];
const email = item.contact_email || '';
let domain = item.company_domain || '';
if (!domain && email.includes('@')) domain = email.split('@')[1].toLowerCase();
const isFreemail = freemail.includes(domain);
const domain_type = isFreemail ? 'personal' : (domain ? 'corporate' : 'unknown');
return {
  ...item,
  company_domain: domain,
  domain_type,
  enrichment_status: domain && !isFreemail ? 'partial' : 'limited',
  processing_status: 'enriching',
  updated_at: new Date().toISOString(),
  _metadata: { processing_stage: 'domain_enriched' },
};
"""

MERGE_ENRICHMENT_JS = r"""
const lead = $('Domain Enrichment').item.json;
const aiData = $input.item.json;
return {
  ...lead,
  content_summary: aiData.content_summary || lead.content_summary || '',
  industry: aiData.industry || lead.industry || '',
  company_size: aiData.company_size || lead.company_size || '',
  intent_signals: JSON.stringify(aiData.intent_signals || []),
  enrichment_summary: aiData.enrichment_summary || lead.enrichment_summary || '',
  enrichment_status: aiData.content_summary ? 'complete' : (lead.enrichment_status || 'partial'),
  processing_status: 'enriched',
  updated_at: new Date().toISOString(),
  _metadata: { processing_stage: 'enrichment_merged' },
};
"""

HANDLE_AI_ENRICH_FAILURE_JS = r"""
const item = $('Domain Enrichment').item.json;
return {
  ...item,
  content_summary: (item.raw_content || '').slice(0, 300),
  enrichment_status: 'failed',
  enrichment_summary: 'LLM enrichment failed; using raw content fallback',
  processing_status: 'enriched',
  _metadata: { processing_stage: 'enrichment_fallback', severity: 'medium' },
};
"""

MERGE_SCORING_JS = r"""
const lead = $('Domain Enrichment').item.json;
const ai = $input.item.json;
const scoreData = ai.score !== undefined ? ai : ($('HTTP Score Lead').item?.json || {});
return {
  ...lead,
  score: scoreData.score ?? 0,
  score_reasoning: scoreData.score_reasoning || '',
  confidence: scoreData.confidence || 'low',
  recommended_action: scoreData.recommended_action || 'manual_review',
  routing_decision: scoreData.routing_decision || '',
  fallback_used: scoreData.fallback_used || false,
  intent_signals: JSON.stringify(scoreData.intent_signals || []),
  processing_status: 'scoring',
  updated_at: new Date().toISOString(),
  _metadata: { processing_stage: 'scoring_merged' },
};
"""

HANDLE_AI_SCORE_FAILURE_JS = r"""
const item = $('Domain Enrichment').item.json;
return {
  ...item,
  score: 0,
  score_reasoning: 'AI scoring failed',
  confidence: 'low',
  recommended_action: 'manual_review',
  routing_decision: 'fallback_manual_review',
  fallback_used: true,
  processing_status: 'scoring',
  _metadata: { processing_stage: 'scoring_fallback', severity: 'high' },
};
"""

APPLY_REVIEW_RULES_JS = r"""
const item = $input.item.json;
const config = item.global_config || {};
const thresholds = config.score_thresholds || { gray_low: 40, gray_high: 79 };
const triggers = [];
const score = Number(item.score || 0);

if (score >= thresholds.gray_low && score <= thresholds.gray_high) triggers.push('gray_zone_score');
if (item.enrichment_status !== 'complete') triggers.push('enrichment_incomplete');
if (!item.contact_role) triggers.push('missing_role');
if ((item.source_trust_level || 0) < (config.source_trust_threshold || 50)) triggers.push('low_trust_source');

let review_status = 'none';
let recommended_action = item.recommended_action;

if (triggers.length > 0 || recommended_action === 'manual_review') {
  review_status = 'pending_review';
  recommended_action = 'manual_review';
}

return {
  ...item,
  review_status,
  recommended_action,
  review_triggers: triggers.join(','),
  processing_status: review_status === 'pending_review' ? 'review_pending' : item.processing_status,
  updated_at: new Date().toISOString(),
  _metadata: { processing_stage: 'review_rules_applied' },
};
"""

APPLY_ROUTING_RULES_JS = r"""
const item = $input.item.json;
const rules = (item.global_config || {}).routing_rules || [];
const score = Number(item.score || 0);
let matched = null;
for (const rule of rules) {
  const min = Number(rule.min_score || 0);
  const max = Number(rule.max_score || 100);
  if (score >= min && score <= max) { matched = rule; break; }
}
const result = { ...item };
if (matched && item.review_status !== 'pending_review') {
  result.recommended_action = matched.recommended_action || item.recommended_action;
  result.routing_decision = `matched_rule_${matched.min_score}_${matched.max_score}`;
}
return {
  ...result,
  updated_at: new Date().toISOString(),
  _metadata: { processing_stage: 'routing_rules_applied' },
};
"""

CRM_GATE_JS = r"""
const item = $input.item.json;
const mode = (item.global_config || {}).mode || 'test';
const canSync = mode === 'production'
  && item.review_status !== 'pending_review'
  && ['crm_sync', 'notify_only'].includes(item.recommended_action);
return {
  ...item,
  crm_gate_passed: canSync,
  crm_status: canSync ? 'pending' : 'skipped_test_mode',
  _metadata: { processing_stage: 'crm_gate' },
};
"""

NOTIFICATION_PAYLOAD_JS = r"""
const item = $input.item.json;
const mode = (item.global_config || {}).mode || 'test';
const score = Number(item.score || 0);
const thresholds = (item.global_config || {}).score_thresholds || { high: 80 };

let event_type = 'high_score_lead';
if (item.review_status === 'pending_review') event_type = 'review_required';
if (item.recommended_action === 'reject') event_type = 'low_score';

const payload = {
  event_type,
  severity: event_type === 'review_required' ? 'warning' : 'info',
  title: event_type === 'review_required' ? 'Lead needs manual review' : 'New high-score B2B lead',
  message: `${item.company_name || 'Unknown'} — ${item.contact_name || ''} (${item.contact_email}) — Score: ${score}`,
  lead_id: item.lead_id,
  correlation_id: item.correlation_id,
  channels: ['slack'],
  metadata: {
    score,
    company_name: item.company_name,
    recommended_action: item.recommended_action,
    calendly_url: (item.global_config || {}).calendly_url || '',
  },
  notification_mode: mode,
  _metadata: { processing_stage: 'notification_payload_built' },
};
return { ...item, notification: payload };
"""

SKIP_NOTIFICATION_TEST_JS = r"""
const item = $input.item.json;
return {
  ...item,
  notification_status: 'skipped_test_mode',
  _metadata: { processing_stage: 'notification_skipped_test' },
};
"""

ERROR_EXTRACT_JS = r"""
const err = $input.item.json;
const execution = err.execution || {};
const error = err.error || {};
return {
  workflow: err.workflow?.name || 'unknown',
  execution_id: execution.id || '',
  node: error.node?.name || 'unknown',
  message: error.message || JSON.stringify(error),
  stack: error.stack || '',
  correlation_id: error.context?.correlation_id || execution.customData?.correlation_id || '',
  retry_suggestion: 'manual',
  timestamp: new Date().toISOString(),
  _metadata: { processing_stage: 'global_error_logged', severity: 'critical' },
};
"""

DAILY_SUMMARY_JS = r"""
const leads = $('Read Leads For Summary').all().map(i => i.json);
const errors = $('Read Errors For Summary').all().map(i => i.json);
const today = new Date().toISOString().slice(0, 10);

const todayLeads = leads.filter(l => (l.created_at || '').startsWith(today));
const highScore = todayLeads.filter(l => Number(l.score || 0) >= 80);
const crmSynced = todayLeads.filter(l => l.crm_status === 'synced');
const crmFailed = todayLeads.filter(l => l.crm_status === 'failed');
const notified = todayLeads.filter(l => l.notification_status === 'sent');
const reviewPending = todayLeads.filter(l => l.review_status === 'pending_review');
const reviewApproved = todayLeads.filter(l => l.review_status === 'approved');

const errorTypes = {};
for (const e of errors.filter(e => (e.timestamp || '').startsWith(today))) {
  const key = (e.message || 'unknown').slice(0, 40);
  errorTypes[key] = (errorTypes[key] || 0) + 1;
}

const summary = {
  date: today,
  new_leads: todayLeads.length,
  high_score_leads: highScore.length,
  crm_success_rate: todayLeads.length ? (crmSynced.length / todayLeads.length * 100).toFixed(1) + '%' : 'N/A',
  slack_success_count: notified.length,
  review_pending: reviewPending.length,
  review_approved: reviewApproved.length,
  error_count: Object.values(errorTypes).reduce((a,b)=>a+b,0),
  error_types: errorTypes,
  _metadata: { processing_stage: 'daily_summary_built' },
};

return summary;
"""


def build_error_handler() -> None:
    nodes = [
        {
            "parameters": {},
            "type": "n8n-nodes-base.errorTrigger",
            "typeVersion": 1,
            "position": [0, 0],
            "id": nid("error"),
            "name": "Error Trigger",
        },
        code_node("Extract Error Details", ERROR_EXTRACT_JS, [220, 0]),
        sheets_append("Write error_logs", [440, 0], "error_logs", {
            "workflow": "={{ $json.workflow }}",
            "execution_id": "={{ $json.execution_id }}",
            "node": "={{ $json.node }}",
            "message": "={{ $json.message }}",
            "stack": "={{ $json.stack }}",
            "correlation_id": "={{ $json.correlation_id }}",
            "retry_suggestion": "={{ $json.retry_suggestion }}",
            "timestamp": "={{ $json.timestamp }}",
        }),
        {
            "parameters": {
                "select": "channel",
                "channelId": {"__rl": True, "mode": "id", "value": "={{ $env.SLACK_CHANNEL_ID || 'SLACK_CHANNEL_ID' }}"},
                "text": "=🚨 CRM Workflow Error\nWorkflow: {{ $('Extract Error Details').item.json.workflow }}\nNode: {{ $('Extract Error Details').item.json.node }}\nMessage: {{ $('Extract Error Details').item.json.message }}\nCorrelation: {{ $('Extract Error Details').item.json.correlation_id }}",
            },
            "type": "n8n-nodes-base.slack",
            "typeVersion": 2.2,
            "position": [660, 0],
            "id": nid("slack"),
            "name": "Slack Error Alert",
            "onError": "continueErrorOutput",
            "credentials": {"slackOAuth2Api": {"id": "SLACK_CREDENTIAL_ID", "name": "Slack account"}},
        },
        code_node("Log Slack Error", "return { error_type: 'slack_notification_failed', _metadata: { processing_stage: 'slack_error_handled', severity: 'low' } };", [880, 120]),
    ]
    conn = {}
    connect(conn, "Error Trigger", "Extract Error Details")
    connect(conn, "Extract Error Details", "Write error_logs")
    connect(conn, "Write error_logs", "Slack Error Alert")
    connect(conn, "Slack Error Alert", "Log Slack Error", src_output=1)
    save_workflow("B2B Lead Error Handler.json", "B2B Lead Error Handler", nodes, conn)


def build_intake() -> None:
    nodes = [
        webhook_node("Tally Webhook", [0, 0], "tally-lead"),
        webhook_node("Google Forms Webhook", [0, 200], "google-forms-lead"),
        code_node("Normalize Tally Payload", NORMALIZE_TALLY_JS, [240, 0]),
        code_node("Normalize Google Forms Payload", NORMALIZE_GFORMS_JS, [240, 200]),
        merge_node("Merge Sources", [480, 100]),
        code_node("Generate Lead IDs", GENERATE_IDS_JS, [700, 100]),
        code_node("Validate Lead", VALIDATE_LEAD_JS, [920, 100]),
        if_node("Validation Passed?", [1140, 100], "={{ $json.validation_passed }}", "true"),
        sheets_read("Read All Leads", [1140, 300], "leads"),
        code_node("Dedup Lead", DEDUP_LEAD_JS, [1360, 100]),
        if_node("Is Update?", [1580, 100], "={{ $json.is_update }}", "true"),
        sheets_update("Update Lead", [1800, 0], "leads", "lead_id", {
            "lead_id": "={{ $json.lead_id }}",
            "correlation_id": "={{ $json.correlation_id }}",
            "lead_hash": "={{ $json.lead_hash }}",
            "source_type": "={{ $json.source_type }}",
            "source_name": "={{ $json.source_name }}",
            "source_url": "={{ $json.source_url }}",
            "source_trust_level": "={{ $json.source_trust_level }}",
            "company_name": "={{ $json.company_name }}",
            "company_domain": "={{ $json.company_domain }}",
            "contact_name": "={{ $json.contact_name }}",
            "contact_role": "={{ $json.contact_role }}",
            "contact_email": "={{ $json.contact_email }}",
            "raw_content": "={{ $json.raw_content }}",
            "processing_status": "={{ $json.processing_status }}",
            "updated_at": "={{ $json.updated_at }}",
        }),
        sheets_append("Append Lead", [1800, 200], "leads", {
            "lead_id": "={{ $json.lead_id }}",
            "correlation_id": "={{ $json.correlation_id }}",
            "lead_hash": "={{ $json.lead_hash }}",
            "source_type": "={{ $json.source_type }}",
            "source_name": "={{ $json.source_name }}",
            "source_url": "={{ $json.source_url }}",
            "source_trust_level": "={{ $json.source_trust_level }}",
            "company_name": "={{ $json.company_name }}",
            "company_domain": "={{ $json.company_domain }}",
            "contact_name": "={{ $json.contact_name }}",
            "contact_role": "={{ $json.contact_role }}",
            "contact_email": "={{ $json.contact_email }}",
            "raw_content": "={{ $json.raw_content }}",
            "processing_status": "={{ $json.processing_status }}",
            "created_at": "={{ $json.created_at }}",
            "updated_at": "={{ $json.updated_at }}",
        }),
        merge_node("Merge Upsert Result", [2020, 100]),
        sheets_append("Write Audit Log", [2240, 100], "audit_logs", {
            "lead_id": "={{ $('Dedup Lead').item.json.lead_id }}",
            "correlation_id": "={{ $('Dedup Lead').item.json.correlation_id }}",
            "event": "={{ $('Dedup Lead').item.json.is_update ? 'lead_updated' : 'lead_created' }}",
            "old_value": "",
            "new_value": "={{ $('Dedup Lead').item.json.processing_status }}",
            "workflow": "B2B Lead Intake",
            "timestamp": "={{ $('Dedup Lead').item.json.updated_at }}",
        }),
        code_node("Pass Lead To Enrichment", "return $('Dedup Lead').item.json;", [2460, 100]),
        execute_workflow("Execute Enrichment Scoring", [2680, 100], "B2B Lead Enrichment Scoring"),
        noop("Validation Failed End", [1360, 300]),
    ]
    conn = {}
    connect(conn, "Tally Webhook", "Normalize Tally Payload")
    connect(conn, "Google Forms Webhook", "Normalize Google Forms Payload")
    connect(conn, "Normalize Tally Payload", "Merge Sources")
    connect(conn, "Normalize Google Forms Payload", "Merge Sources", dst_input=1)
    connect(conn, "Merge Sources", "Generate Lead IDs")
    connect(conn, "Generate Lead IDs", "Validate Lead")
    connect(conn, "Validate Lead", "Validation Passed?")
    connect(conn, "Validation Passed?", "Read All Leads", src_output=0)
    connect(conn, "Read All Leads", "Dedup Lead")
    connect(conn, "Dedup Lead", "Is Update?")
    connect(conn, "Is Update?", "Update Lead", src_output=0)
    connect(conn, "Is Update?", "Append Lead", src_output=1)
    connect(conn, "Update Lead", "Merge Upsert Result")
    connect(conn, "Append Lead", "Merge Upsert Result", dst_input=1)
    connect(conn, "Merge Upsert Result", "Write Audit Log")
    connect(conn, "Write Audit Log", "Pass Lead To Enrichment")
    connect(conn, "Pass Lead To Enrichment", "Execute Enrichment Scoring")
    connect(conn, "Validation Passed?", "Validation Failed End", src_output=1)
    save_workflow("B2B Lead Intake.json", "B2B Lead Intake", nodes, conn, error_workflow="B2B Lead Error Handler")


def build_enrichment_scoring() -> None:
    nodes = [
        {
            "parameters": {},
            "type": "n8n-nodes-base.executeWorkflowTrigger",
            "typeVersion": 1.1,
            "position": [0, 200],
            "id": nid("trigger"),
            "name": "When Executed by Another Workflow",
        },
        sheets_read("Read config_main", [0, 0], "config_main"),
        sheets_read("Read config_routing", [0, 120], "config_routing"),
        sheets_read("Read config_notifications", [0, 240], "config_notifications"),
        sheets_read("Read config_review", [0, 360], "config_review"),
        merge_node("Merge Config 1", [220, 60]),
        merge_node("Merge Config 2", [440, 120]),
        merge_node("Merge Config 3", [660, 180]),
        code_node("Build Global Config", BUILD_GLOBAL_CONFIG_JS, [880, 200]),
        code_node("Handle Config Load Error", HANDLE_CONFIG_ERROR_JS, [880, 400]),
        code_node("Domain Enrichment", DOMAIN_ENRICHMENT_JS, [1100, 200]),
        http_request_node("HTTP Enrich Lead", [1320, 200], "POST", "http://crm_python_ai:8001/enrich", [
            {"name": "lead_id", "value": "={{ $json.lead_id }}"},
            {"name": "correlation_id", "value": "={{ $json.correlation_id }}"},
            {"name": "source_type", "value": "={{ $json.source_type }}"},
            {"name": "source_name", "value": "={{ $json.source_name }}"},
            {"name": "contact_name", "value": "={{ $json.contact_name }}"},
            {"name": "contact_email", "value": "={{ $json.contact_email }}"},
            {"name": "contact_role", "value": "={{ $json.contact_role }}"},
            {"name": "company_name", "value": "={{ $json.company_name }}"},
            {"name": "company_domain", "value": "={{ $json.company_domain }}"},
            {"name": "domain_type", "value": "={{ $json.domain_type }}"},
            {"name": "raw_content", "value": "={{ ($json.raw_content || '').substring(0, 3000) }}"},
            {"name": "external_enrichment", "value": "={{ $json.external_enrichment || '' }}"},
        ]),
        code_node("Merge Enrichment Result", MERGE_ENRICHMENT_JS, [1540, 200]),
        code_node("Handle Enrichment Failure", HANDLE_AI_ENRICH_FAILURE_JS, [1540, 400]),
        http_request_node("HTTP Score Lead", [1760, 200], "POST", "http://crm_python_ai:8001/score", [
            {"name": "lead_id", "value": "={{ $json.lead_id }}"},
            {"name": "correlation_id", "value": "={{ $json.correlation_id }}"},
            {"name": "source_type", "value": "={{ $json.source_type }}"},
            {"name": "source_name", "value": "={{ $json.source_name }}"},
            {"name": "source_trust_level", "value": "={{ $json.source_trust_level }}"},
            {"name": "contact_name", "value": "={{ $json.contact_name }}"},
            {"name": "contact_email", "value": "={{ $json.contact_email }}"},
            {"name": "contact_role", "value": "={{ $json.contact_role }}"},
            {"name": "company_name", "value": "={{ $json.company_name }}"},
            {"name": "company_domain", "value": "={{ $json.company_domain }}"},
            {"name": "industry", "value": "={{ $json.industry }}"},
            {"name": "company_size", "value": "={{ $json.company_size }}"},
            {"name": "content_summary", "value": "={{ $json.content_summary }}"},
            {"name": "intent_signals", "value": "={{ typeof $json.intent_signals === 'string' ? JSON.parse($json.intent_signals || '[]') : ($json.intent_signals || []) }}"},
            {"name": "enrichment_status", "value": "={{ $json.enrichment_status }}"},
            {"name": "enrichment_summary", "value": "={{ $json.enrichment_summary }}"},
        ]),
        code_node("Merge Scoring Result", MERGE_SCORING_JS, [1980, 200]),
        code_node("Handle Scoring Failure", HANDLE_AI_SCORE_FAILURE_JS, [1980, 400]),
        code_node("Apply Review Rules", APPLY_REVIEW_RULES_JS, [2200, 200]),
        code_node("Apply Routing Rules", APPLY_ROUTING_RULES_JS, [2420, 200]),
        sheets_append("Update Lead Scores", [2640, 200], "leads", {
            "lead_id": "={{ $json.lead_id }}",
            "content_summary": "={{ $json.content_summary }}",
            "industry": "={{ $json.industry }}",
            "company_size": "={{ $json.company_size }}",
            "intent_signals": "={{ $json.intent_signals }}",
            "enrichment_status": "={{ $json.enrichment_status }}",
            "enrichment_summary": "={{ $json.enrichment_summary }}",
            "score": "={{ $json.score }}",
            "score_reasoning": "={{ $json.score_reasoning }}",
            "confidence": "={{ $json.confidence }}",
            "recommended_action": "={{ $json.recommended_action }}",
            "routing_decision": "={{ $json.routing_decision }}",
            "fallback_used": "={{ $json.fallback_used }}",
            "review_status": "={{ $json.review_status }}",
            "processing_status": "={{ $json.processing_status }}",
            "updated_at": "={{ $json.updated_at }}",
        }),
        execute_workflow("Execute CRM Sync", [2860, 200], "B2B Lead CRM Sync Notification"),
    ]
    conn = {}
    connect(conn, "When Executed by Another Workflow", "Read config_main")
    connect(conn, "When Executed by Another Workflow", "Read config_routing", dst_input=0)
    connect(conn, "When Executed by Another Workflow", "Read config_notifications", dst_input=0)
    connect(conn, "When Executed by Another Workflow", "Read config_review", dst_input=0)
    connect(conn, "Read config_main", "Merge Config 1")
    connect(conn, "Read config_routing", "Merge Config 1", dst_input=1)
    connect(conn, "Merge Config 1", "Merge Config 2")
    connect(conn, "Read config_notifications", "Merge Config 2", dst_input=1)
    connect(conn, "Merge Config 2", "Merge Config 3")
    connect(conn, "Read config_review", "Merge Config 3", dst_input=1)
    connect(conn, "Merge Config 3", "Build Global Config")
    connect(conn, "Build Global Config", "Domain Enrichment")
    connect(conn, "Domain Enrichment", "HTTP Enrich Lead")
    connect(conn, "HTTP Enrich Lead", "Merge Enrichment Result", src_output=0)
    connect(conn, "HTTP Enrich Lead", "Handle Enrichment Failure", src_output=1)
    connect(conn, "Handle Enrichment Failure", "HTTP Score Lead")
    connect(conn, "Merge Enrichment Result", "HTTP Score Lead")
    connect(conn, "HTTP Score Lead", "Merge Scoring Result", src_output=0)
    connect(conn, "HTTP Score Lead", "Handle Scoring Failure", src_output=1)
    connect(conn, "Handle Scoring Failure", "Apply Review Rules")
    connect(conn, "Merge Scoring Result", "Apply Review Rules")
    connect(conn, "Apply Review Rules", "Apply Routing Rules")
    connect(conn, "Apply Routing Rules", "Update Lead Scores")
    connect(conn, "Update Lead Scores", "Execute CRM Sync")
    save_workflow("B2B Lead Enrichment Scoring.json", "B2B Lead Enrichment Scoring", nodes, conn, error_workflow="B2B Lead Error Handler")


def build_crm_sync_notification() -> None:
    nodes = [
        {
            "parameters": {},
            "type": "n8n-nodes-base.executeWorkflowTrigger",
            "typeVersion": 1.1,
            "position": [0, 200],
            "id": nid("trigger"),
            "name": "When Executed by Another Workflow",
        },
        code_node("CRM Gate", CRM_GATE_JS, [220, 200]),
        if_node("Should Sync CRM?", [440, 200], "={{ $json.crm_gate_passed }}", "true"),
        {
            "parameters": {
                "resource": "contact",
                "operation": "upsert",
                "email": "={{ $json.contact_email }}",
                "additionalFields": {
                    "firstName": "={{ ($json.contact_name || '').split(' ')[0] }}",
                    "lastName": "={{ ($json.contact_name || '').split(' ').slice(1).join(' ') }}",
                    "companyName": "={{ $json.company_name }}",
                    "jobTitle": "={{ $json.contact_role }}",
                },
            },
            "type": "n8n-nodes-base.hubspot",
            "typeVersion": 2.1,
            "position": [660, 100],
            "id": nid("hubspot"),
            "name": "HubSpot Upsert Contact",
            "onError": "continueErrorOutput",
            "credentials": {"hubspotOAuth2Api": {"id": "HUBSPOT_CREDENTIAL_ID", "name": "HubSpot account"}},
        },
        code_node("Handle HubSpot Failure", "return { ...($('CRM Gate').item.json), crm_status: 'failed', _metadata: { processing_stage: 'crm_failed', severity: 'high' } };", [880, 260]),
        code_node("Mark CRM Synced", "return { ...($('CRM Gate').item.json), crm_status: 'synced', crm_contact_id: $input.item.json.id || '', processing_status: 'completed', _metadata: { processing_stage: 'crm_synced' } };", [880, 100]),
        code_node("Skip CRM Test Mode", "return { ...$input.item.json, crm_status: 'skipped_test_mode', _metadata: { processing_stage: 'crm_skipped' } };", [660, 300]),
        merge_node("Merge CRM Result", [1100, 200]),
        code_node("Build Notification Payload", NOTIFICATION_PAYLOAD_JS, [1320, 200]),
        if_node("Should Notify?", [1540, 200], "={{ $json.notification.notification_mode }}", "production"),
        {
            "parameters": {
                "select": "channel",
                "channelId": {"__rl": True, "mode": "id", "value": "={{ $env.SLACK_CHANNEL_ID || 'SLACK_CHANNEL_ID' }}"},
                "text": "=📋 {{ $json.notification.title }}\n{{ $json.notification.message }}\nAction: {{ $json.notification.metadata.recommended_action }}\nScore: {{ $json.notification.metadata.score }}\nCorrelation: {{ $json.correlation_id }}\n{{ $json.notification.metadata.calendly_url ? 'Book: ' + $json.notification.metadata.calendly_url : '' }}",
            },
            "type": "n8n-nodes-base.slack",
            "typeVersion": 2.2,
            "position": [1760, 100],
            "id": nid("slack"),
            "name": "Slack Notify",
            "onError": "continueErrorOutput",
            "credentials": {"slackOAuth2Api": {"id": "SLACK_CREDENTIAL_ID", "name": "Slack account"}},
        },
        code_node("Mark Notification Sent", "return { ...$input.item.json, notification_status: 'sent', _metadata: { processing_stage: 'notification_sent' } };", [1980, 100]),
        code_node("Skip Notification Test", SKIP_NOTIFICATION_TEST_JS, [1760, 300]),
        code_node("Log Slack Notify Error", "return { ...($('Build Notification Payload').item.json), notification_status: 'failed', _metadata: { processing_stage: 'notification_failed', severity: 'medium' } };", [1980, 260]),
        sheets_append("Update Final Status", [2200, 200], "leads", {
            "lead_id": "={{ $json.lead_id }}",
            "crm_status": "={{ $json.crm_status }}",
            "crm_contact_id": "={{ $json.crm_contact_id || '' }}",
            "notification_status": "={{ $json.notification_status || 'pending' }}",
            "processing_status": "={{ $json.processing_status || 'completed' }}",
            "updated_at": "={{ new Date().toISOString() }}",
        }),
    ]
    conn = {}
    connect(conn, "When Executed by Another Workflow", "CRM Gate")
    connect(conn, "CRM Gate", "Should Sync CRM?")
    connect(conn, "Should Sync CRM?", "HubSpot Upsert Contact", src_output=0)
    connect(conn, "Should Sync CRM?", "Skip CRM Test Mode", src_output=1)
    connect(conn, "HubSpot Upsert Contact", "Mark CRM Synced", src_output=0)
    connect(conn, "HubSpot Upsert Contact", "Handle HubSpot Failure", src_output=1)
    connect(conn, "Mark CRM Synced", "Merge CRM Result")
    connect(conn, "Handle HubSpot Failure", "Merge CRM Result", dst_input=1)
    connect(conn, "Skip CRM Test Mode", "Merge CRM Result", dst_input=1)
    connect(conn, "Merge CRM Result", "Build Notification Payload")
    connect(conn, "Build Notification Payload", "Should Notify?")
    connect(conn, "Should Notify?", "Slack Notify", src_output=0)
    connect(conn, "Should Notify?", "Skip Notification Test", src_output=1)
    connect(conn, "Slack Notify", "Mark Notification Sent", src_output=0)
    connect(conn, "Slack Notify", "Log Slack Notify Error", src_output=1)
    connect(conn, "Mark Notification Sent", "Update Final Status")
    connect(conn, "Skip Notification Test", "Update Final Status")
    connect(conn, "Log Slack Notify Error", "Update Final Status")
    save_workflow("B2B Lead CRM Sync Notification.json", "B2B Lead CRM Sync Notification", nodes, conn, error_workflow="B2B Lead Error Handler")


def build_daily_summary() -> None:
    nodes = [
        {
            "parameters": {"rule": {"interval": [{"field": "days", "triggerAtHour": 9}]}},
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [0, 200],
            "id": nid("schedule"),
            "name": "Daily 9am",
        },
        sheets_read("Read Leads For Summary", [220, 100], "leads"),
        sheets_read("Read Errors For Summary", [220, 300], "error_logs"),
        merge_node("Merge Summary Data", [440, 200]),
        code_node("Build Daily Summary", DAILY_SUMMARY_JS, [660, 200]),
        {
            "parameters": {
                "select": "channel",
                "channelId": {"__rl": True, "mode": "id", "value": "={{ $env.SLACK_CHANNEL_ID || 'SLACK_CHANNEL_ID' }}"},
                "text": "=📊 CRM Daily Summary ({{ $json.date }})\nNew leads: {{ $json.new_leads }}\nHigh score: {{ $json.high_score_leads }}\nCRM success rate: {{ $json.crm_success_rate }}\nSlack sent: {{ $json.slack_success_count }}\nReview pending: {{ $json.review_pending }}\nErrors: {{ $json.error_count }}",
            },
            "type": "n8n-nodes-base.slack",
            "typeVersion": 2.2,
            "position": [880, 200],
            "id": nid("slack"),
            "name": "Slack Daily Report",
            "onError": "continueErrorOutput",
            "credentials": {"slackOAuth2Api": {"id": "SLACK_CREDENTIAL_ID", "name": "Slack account"}},
        },
    ]
    conn = {}
    connect(conn, "Daily 9am", "Read Leads For Summary")
    connect(conn, "Daily 9am", "Read Errors For Summary")
    connect(conn, "Read Leads For Summary", "Merge Summary Data")
    connect(conn, "Read Errors For Summary", "Merge Summary Data", dst_input=1)
    connect(conn, "Merge Summary Data", "Build Daily Summary")
    connect(conn, "Build Daily Summary", "Slack Daily Report")
    save_workflow("B2B Lead Daily Summary.json", "B2B Lead Daily Summary", nodes, conn, error_workflow="B2B Lead Error Handler")


def main() -> None:
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    build_error_handler()
    build_intake()
    build_enrichment_scoring()
    build_crm_sync_notification()
    build_daily_summary()


if __name__ == "__main__":
    main()

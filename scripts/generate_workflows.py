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


def sheets_read(
    name: str,
    position: list[int],
    sheet_name: str,
    *,
    always_output_data: bool = False,
    retry: bool = False,
    max_tries: int | None = None,
) -> dict:
    node = {
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
    if always_output_data:
        node["alwaysOutputData"] = True
    if retry:
        node["retryOnFail"] = True
        node["waitBetweenTries"] = 5000
        if max_tries is not None:
            node["maxTries"] = max_tries
    return node


def sheets_column_schema(columns: dict) -> list[dict]:
    """n8n Google Sheets v4+ requires columns.schema when mappingMode=defineBelow."""
    return [
        {
            "id": key,
            "displayName": key,
            "required": False,
            "defaultMatch": False,
            "display": True,
            "type": "string",
            "canBeUsedToMatch": True,
            "removed": False,
        }
        for key in columns
    ]


def sheets_append(name: str, position: list[int], sheet_name: str, columns_expr: str, *, retry: bool = False) -> dict:
    node = {
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
                "matchingColumns": [],
                "schema": sheets_column_schema(columns_expr),
                "attemptToConvertTypes": False,
                "convertFieldsToString": False,
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
    if retry:
        node["retryOnFail"] = True
        node["waitBetweenTries"] = 5000
    return node


def sheets_update(
    name: str,
    position: list[int],
    sheet_name: str,
    match_column: str,
    columns: dict,
    *,
    retry: bool = False,
) -> dict:
    node = {
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
                "schema": sheets_column_schema(columns),
                "attemptToConvertTypes": False,
                "convertFieldsToString": False,
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
    if retry:
        node["retryOnFail"] = True
        node["waitBetweenTries"] = 5000
    return node


def merge_node(name: str, position: list[int], inputs: int = 2, mode: str = "combineAll") -> dict:
    if mode == "append":
        parameters = {"mode": "append", "options": {}}
    else:
        parameters = {"mode": "combine", "combineBy": mode, "options": {}}
    return {
        "parameters": parameters,
        "type": "n8n-nodes-base.merge",
        "typeVersion": 3,
        "position": position,
        "id": nid(name),
        "name": name,
    }


def set_node(name: str, position: list[int]) -> dict:
    return {
        "parameters": {"includeOtherFields": True, "options": {}},
        "type": "n8n-nodes-base.set",
        "typeVersion": 3.4,
        "position": position,
        "id": nid(name),
        "name": name,
    }


def if_bool_node(name: str, position: list[int], condition_left: str) -> dict:
    return {
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 2,
                },
                "conditions": [
                    {
                        "id": nid(),
                        "leftValue": condition_left,
                        "rightValue": "true",
                        "operator": {"type": "boolean", "operation": "true", "singleValue": True},
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


def if_node(
    name: str,
    position: list[int],
    condition_left: str,
    condition_right: str = "true",
    *,
    strict: bool = False,
) -> dict:
    options: dict = {"caseSensitive": True, "leftValue": "", "typeValidation": "strict" if strict else "loose"}
    if strict:
        options["version"] = 2
    return {
        "parameters": {
            "conditions": {
                "options": options,
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


def if_string_or_node(name: str, position: list[int], left: str, values: list[str]) -> dict:
    """IF node: leftValue equals any value (OR combinator)."""
    return {
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 3,
                },
                "conditions": [
                    {
                        "id": nid(),
                        "leftValue": left,
                        "rightValue": value,
                        "operator": {
                            "type": "string",
                            "operation": "equals",
                            "name": "filter.operator.equals",
                        },
                    }
                    for value in values
                ],
                "combinator": "or",
            },
            "options": {},
        },
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.3,
        "position": position,
        "id": nid(name),
        "name": name,
    }


def execute_workflow(
    name: str,
    position: list[int],
    target_workflow: str,
    *,
    inputs: dict[str, str] | None = None,
    on_error: str | None = None,
) -> dict:
    parameters: dict = {
        "workflowId": {"__rl": True, "mode": "name", "value": target_workflow},
        "options": {},
    }
    if inputs is not None:
        parameters["workflowInputs"] = {
            "mappingMode": "defineBelow",
            "value": inputs,
            "matchingColumns": [],
            "attemptToConvertTypes": False,
            "convertFieldsToString": True,
        }
    node = {
        "parameters": parameters,
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": 1.2,
        "position": position,
        "id": nid(name),
        "name": name,
    }
    if on_error:
        node["onError"] = on_error
    return node


def webhook_node(
    name: str,
    position: list[int],
    path: str,
    *,
    http_method: str | None = None,
    response_mode: str | None = None,
    raw_body: bool = False,
) -> dict:
    params: dict = {"path": path, "options": {}}
    if http_method:
        params["httpMethod"] = http_method
    if response_mode:
        params["responseMode"] = response_mode
    if raw_body:
        params["options"]["rawBody"] = True
    return {
        "parameters": params,
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": position,
        "id": nid(name),
        "name": name,
        "webhookId": nid(path),
    }


def respond_to_webhook_node(
    name: str,
    position: list[int],
    *,
    response_code: int = 200,
    response_body: str = '={{ { "ok": true } }}',
) -> dict:
    return {
        "parameters": {
            "respondWith": "json",
            "responseBody": response_body,
            "options": {"responseCode": response_code},
        },
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": position,
        "id": nid(name),
        "name": name,
    }


def error_message_prelude(default_message: str) -> str:
    return f"""const item = $input.item;
const errJson = item.json || {{}};
const errorObj = item.error || errJson.error || {{}};
const errorMessage =
  errorObj.message ||
  errorObj.description ||
  errJson.message ||
  errJson.description ||
  (typeof errJson.error === 'string' ? errJson.error : null) ||
  '{default_message}';
"""


def _retry_settings() -> dict:
    return {"retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000}


def _io_error_settings(retry: bool = False) -> dict:
    settings: dict = {"onError": "continueErrorOutput"}
    if retry:
        settings.update(_retry_settings())
    return settings


def http_json_request_node(
    name: str,
    position: list[int],
    method: str,
    url: str,
    json_body: str,
    *,
    timeout: int = 45000,
) -> dict:
    return {
        "parameters": {
            "method": method,
            "url": url,
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": json_body,
            "options": {"timeout": timeout},
        },
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.4,
        "position": position,
        "id": nid(name),
        "name": name,
        **_retry_settings(),
        "onError": "continueErrorOutput",
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
        **_retry_settings(),
        "onError": "continueErrorOutput",
    }


def http_get_request_node(
    name: str,
    position: list[int],
    url: str,
    query_fields: list[dict],
    *,
    timeout: int = 30000,
) -> dict:
    return {
        "parameters": {
            "method": "GET",
            "url": url,
            "sendQuery": True,
            "queryParameters": {"parameters": query_fields},
            "options": {"timeout": timeout},
        },
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.4,
        "position": position,
        "id": nid(name),
        "name": name,
        **_retry_settings(),
        "onError": "continueErrorOutput",
    }


def http_json_post_node(
    name: str,
    position: list[int],
    url_expr: str,
    json_body_expr: str,
    *,
    timeout: int = 45000,
    correlation_id_header: bool = False,
) -> dict:
    parameters: dict = {
        "method": "POST",
        "url": url_expr,
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": json_body_expr,
        "options": {"timeout": timeout},
    }
    if correlation_id_header:
        parameters["sendHeaders"] = True
        parameters["headerParameters"] = {
            "parameters": [
                {"name": "X-Correlation-Id", "value": "={{ $json.correlation_id }}"},
            ]
        }
    return {
        "parameters": parameters,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.4,
        "position": position,
        "id": nid(name),
        "name": name,
        **_retry_settings(),
        "onError": "continueErrorOutput",
    }


def slack_node(name: str, position: list[int], text: str) -> dict:
    return {
        "parameters": {
            "select": "channel",
            "channelId": {"__rl": True, "mode": "id", "value": "={{ $env.SLACK_CHANNEL_ID || 'SLACK_CHANNEL_ID' }}"},
            "text": text,
        },
        "type": "n8n-nodes-base.slack",
        "typeVersion": 2.2,
        "position": position,
        "id": nid(name),
        "name": name,
        **_retry_settings(),
        "onError": "continueErrorOutput",
        "credentials": {"slackOAuth2Api": {"id": "SLACK_CREDENTIAL_ID", "name": "Slack account"}},
    }


def slack_blocks_node(name: str, position: list[int]) -> dict:
    return {
        "parameters": {
            "resource": "message",
            "operation": "post",
            "select": "channel",
            "channelId": {"__rl": True, "mode": "id", "value": "={{ $env.SLACK_CHANNEL_ID || 'SLACK_CHANNEL_ID' }}"},
            "messageType": "block",
            "blocksUi": "={{ JSON.stringify($json.notification.slack_blocks) }}",
            "text": "={{ $json.notification.message }}",
            "otherOptions": {"includeLinkToWorkflow": False},
        },
        "type": "n8n-nodes-base.slack",
        "typeVersion": 2.2,
        "position": position,
        "id": nid(name),
        "name": name,
        **_retry_settings(),
        "onError": "continueErrorOutput",
        "credentials": {"slackOAuth2Api": {"id": "SLACK_CREDENTIAL_ID", "name": "Slack account"}},
    }


def slack_update_blocks_node(name: str, position: list[int]) -> dict:
    return {
        "parameters": {
            "resource": "message",
            "operation": "update",
            "select": "channel",
            "channelId": {
                "__rl": True,
                "mode": "id",
                "value": "={{ $json.channel_id || $env.SLACK_CHANNEL_ID || 'SLACK_CHANNEL_ID' }}",
            },
            "ts": "={{ $json.message_ts }}",
            "messageType": "block",
            "blocksUi": "={{ JSON.stringify({ blocks: $json.slack_message_body.blocks }) }}",
            "text": "={{ $json.slack_message_body.text }}",
            "otherOptions": {},
        },
        "type": "n8n-nodes-base.slack",
        "typeVersion": 2.2,
        "position": position,
        "id": nid(name),
        "name": name,
        **_retry_settings(),
        "onError": "continueErrorOutput",
        "credentials": {"slackOAuth2Api": {"id": "SLACK_CREDENTIAL_ID", "name": "Slack account"}},
    }


def hubspot_upsert_node(name: str, position: list[int]) -> dict:
    return {
        "parameters": {
            "resource": "contact",
            "operation": "upsert",
            "email": "={{ $json.contact_email }}",
            "additionalFields": {
                "firstName": "={{ ($json.contact_name || '').trim().split(/\\s+/)[0] || '' }}",
                "lastName": "={{ ($json.contact_name || '').trim().split(/\\s+/).slice(1).join(' ') || '' }}",
                # HubSpot contact property is `company` (n8n maps companyName → company).
                # Always send a non-empty string when known — empty string can clear the UI to "--".
                "companyName": "={{ ($json.company_name || '').trim() }}",
                "jobTitle": "={{ $json.contact_role || '' }}",
            },
        },
        "type": "n8n-nodes-base.hubspot",
        "typeVersion": 2.1,
        "position": position,
        "id": nid(name),
        "name": name,
        **_retry_settings(),
        "onError": "continueErrorOutput",
        "credentials": {"hubspotOAuth2Api": {"id": "HUBSPOT_CREDENTIAL_ID", "name": "HubSpot account"}},
    }


def hubspot_crm_email_node(name: str, position: list[int]) -> dict:
    json_body = (
        "={{ JSON.stringify({ properties: { hs_timestamp: new Date().toISOString(), "
        "hs_email_direction: 'EMAIL', hs_email_status: 'DRAFT', "
        "hs_email_subject: $json.outbound_email_subject || 'Following up', "
        "hs_email_text: $json.outbound_email_body || '' }, associations: "
        "[{ to: { id: String($json.crm_contact_id) }, types: "
        "[{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 198 }] }] }) }}"
    )
    return {
        "parameters": {
            "method": "POST",
            "url": "https://api.hubapi.com/crm/v3/objects/emails",
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "hubspotOAuth2Api",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": json_body,
            "options": {"timeout": 30000},
        },
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.4,
        "position": position,
        "id": nid(name),
        "name": name,
        **_retry_settings(),
        "onError": "continueErrorOutput",
        "credentials": {"hubspotOAuth2Api": {"id": "HUBSPOT_CREDENTIAL_ID", "name": "HubSpot account"}},
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


def connect_error(connections: dict, src: str, dst: str, dst_input: int = 0) -> None:
    connect(connections, src, dst, src_output=1, dst_input=dst_input)


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
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

function loadWrapper(normalizeName, handleName, table) {
  const ok = safeNodeJson(normalizeName);
  if (ok) return ok;
  const err = safeNodeJson(handleName);
  if (err) return err;
  return {
    config_table: table,
    rows: [],
    load_failed: true,
    load_error_message: 'Config wrapper not executed',
  };
}

const lead = safeNodeJson('Hold Lead') ?? {};

const mainWrap = loadWrapper('Normalize config_main', 'Handle config_main Error', 'config_main');
const routingWrap = loadWrapper('Normalize config_routing', 'Handle config_routing Error', 'config_routing');
const notificationWrap = loadWrapper(
  'Normalize config_notifications',
  'Handle config_notifications Error',
  'config_notifications',
);
const reviewWrap = loadWrapper('Normalize config_review', 'Handle config_review Error', 'config_review');

const wrappers = [mainWrap, routingWrap, notificationWrap, reviewWrap];
const mainRows = (mainWrap.rows || []).filter(r => r.key);
const routingRows = (routingWrap.rows || []).filter(r => r.min_score !== undefined);
const notificationRows = (notificationWrap.rows || []).filter(
  r => r.enabled === true || r.enabled === 'true',
);
const reviewRows = (reviewWrap.rows || []).filter(r => r.enabled === true || r.enabled === 'true');

const kv = {};
for (const row of mainRows) {
  if (row.key) kv[row.key] = row.value;
}

const scoreHigh = parseInt(kv.score_threshold_high || '80', 10);
const scoreLow = parseInt(kv.score_threshold_low || '40', 10);
const grayLow = parseInt(kv.score_gray_low || '40', 10);
const grayHigh = parseInt(kv.score_gray_high || '79', 10);

const failedTables = wrappers.filter(w => w.load_failed).map(w => w.config_table);
const errorMessages = wrappers
  .filter(w => w.load_failed && w.load_error_message)
  .map(w => `${w.config_table}: ${w.load_error_message}`);

const global_config = {
  mode: (kv.mode || 'test').toLowerCase(),
  score_thresholds: { high: scoreHigh, low: scoreLow, gray_low: grayLow, gray_high: grayHigh },
  sales_memo_min_score: parseInt(kv.sales_memo_min_score || kv.score_threshold_high || '80', 10),
  first_touch_min_score: parseInt(kv.first_touch_min_score || kv.sales_memo_min_score || kv.score_threshold_high || '80', 10),
  first_touch_sender_name: kv.first_touch_sender_name || 'Your Team',
  calendly_url: kv.calendly_url || '',
  source_trust_threshold: parseInt(kv.source_trust_threshold || '50', 10),
  freemail_domains: (kv.freemail_domains || 'gmail.com,outlook.com,yahoo.com,hotmail.com,icloud.com')
    .split(',')
    .map(s => s.trim()),
  routing_rules: routingRows,
  notification_rules: notificationRows,
  review_rules: reviewRows,
  _metadata: {
    processing_stage: failedTables.length ? 'config_load_degraded' : 'config_loaded',
    config_load_failed: failedTables.length > 0,
    config_load_partial: failedTables.length > 0 && failedTables.length < 4,
    failed_tables: failedTables.join(','),
  },
};

const result = { ...lead, global_config };
if (errorMessages.length) {
  result.config_load_error_message = errorMessages.join('; ');
}
return result;
"""

CONFIG_TABLES = (
    ("config_main", "Read config_main"),
    ("config_routing", "Read config_routing"),
    ("config_notifications", "Read config_notifications"),
    ("config_review", "Read config_review"),
)


def normalize_config_js(table: str) -> str:
    return f"""const rows = $input.all().map(i => i.json).filter(r => r && !r.config_table);
return {{
  config_table: '{table}',
  rows,
  load_failed: false,
  load_error_message: '',
}};
"""


def handle_config_read_error_js(table: str, read_node: str) -> str:
    return error_message_prelude(f"Unknown {read_node} error") + f"""
return {{
  config_table: '{table}',
  rows: [],
  load_failed: true,
  load_error_message: errorMessage,
  _metadata: {{
    processing_stage: '{table}_read_failed',
    severity: 'medium',
    error_message: errorMessage,
    error_description: errorObj.description || '',
    failed_node: '{read_node}',
  }},
}};
"""


ENRICHMENT_WORKFLOW_INPUTS = [
    {"name": "lead_id"},
    {"name": "correlation_id"},
    {"name": "source_type"},
    {"name": "source_name"},
    {"name": "source_trust_level", "type": "number"},
    {"name": "company_name"},
    {"name": "company_domain"},
    {"name": "contact_name"},
    {"name": "contact_role"},
    {"name": "contact_email"},
    {"name": "raw_content"},
    {"name": "sheets_write_failed", "type": "boolean"},
    {"name": "sheets_error_message"},
    {"name": "dedup_skipped", "type": "boolean"},
    {"name": "read_error_message"},
    {"name": "audit_log_failed", "type": "boolean"},
    {"name": "audit_log_error_message"},
]

INTAKE_TO_ENRICHMENT_INPUTS = {
    "lead_id": "={{ $json.lead_id }}",
    "correlation_id": "={{ $json.correlation_id }}",
    "source_type": "={{ $json.source_type }}",
    "source_name": "={{ $json.source_name }}",
    "source_trust_level": "={{ $json.source_trust_level }}",
    "company_name": "={{ $json.company_name }}",
    "company_domain": "={{ $json.company_domain }}",
    "contact_name": "={{ $json.contact_name }}",
    "contact_role": "={{ $json.contact_role }}",
    "contact_email": "={{ $json.contact_email }}",
    "raw_content": "={{ $json.raw_content }}",
    "sheets_write_failed": "={{ $json.sheets_write_failed ?? false }}",
    "sheets_error_message": "={{ $json.sheets_error_message ?? \"\" }}",
    "dedup_skipped": "={{ $json.dedup_skipped ?? false }}",
    "read_error_message": "={{ $json.read_error_message ?? \"\" }}",
    "audit_log_failed": "={{ $json.audit_log_failed ?? false }}",
    "audit_log_error_message": "={{ $json.audit_log_error_message ?? \"\" }}",
}

ENRICHMENT_TO_CRM_INPUTS = {
    "lead_id": "={{ $json.lead_id }}",
    "correlation_id": "={{ $json.correlation_id }}",
    "contact_email": "={{ $json.contact_email }}",
    "contact_name": "={{ $json.contact_name }}",
    "contact_role": "={{ $json.contact_role }}",
    "company_name": "={{ $json.company_name }}",
    "score": "={{ $json.score }}",
    "review_status": "={{ $json.review_status }}",
    "recommended_action": "={{ $json.recommended_action }}",
    "processing_status": "={{ $json.processing_status }}",
    "global_config": "={{ $json.global_config }}",
    "company_domain": "={{ $json.company_domain }}",
    "confidence": "={{ $json.confidence }}",
    "routing_decision": "={{ $json.routing_decision }}",
    "dedup_skipped": "={{ $json.dedup_skipped ?? false }}",
    "sheets_write_failed": "={{ $json.sheets_write_failed ?? false }}",
    "sheets_error_message": "={{ $json.sheets_error_message ?? \"\" }}",
    "sheets_update_failed": "={{ $json.sheets_update_failed ?? false }}",
    "read_error_message": "={{ $json.read_error_message ?? \"\" }}",
    "audit_log_failed": "={{ $json.audit_log_failed ?? false }}",
    "audit_log_error_message": "={{ $json.audit_log_error_message ?? \"\" }}",
    "config_load_error_message": "={{ $json.config_load_error_message ?? \"\" }}",
    "enrichment_error_message": "={{ $json.enrichment_error_message ?? \"\" }}",
    "scoring_error_message": "={{ $json.scoring_error_message ?? \"\" }}",
    "industry": "={{ $json.industry ?? \"\" }}",
    "company_size": "={{ $json.company_size ?? \"\" }}",
    "content_summary": "={{ $json.content_summary ?? \"\" }}",
    "intent_signals": "={{ $json.intent_signals ?? \"\" }}",
    "enrichment_summary": "={{ $json.enrichment_summary ?? \"\" }}",
    "enrichment_status": "={{ $json.enrichment_status ?? \"\" }}",
    "sales_memo": "={{ $json.sales_memo ?? \"\" }}",
    "sales_memo_status": "={{ $json.sales_memo_status ?? \"\" }}",
    "domain_type": "={{ $json.domain_type ?? \"\" }}",
    "score_reasoning": "={{ $json.score_reasoning ?? \"\" }}",
    "first_touch_status": "={{ $json.first_touch_status ?? \"\" }}",
    "crm_status": "={{ $json.crm_status != null && $json.crm_status !== '' ? String($json.crm_status) : \"\" }}",
    "crm_contact_id": "={{ $json.crm_contact_id != null && $json.crm_contact_id !== '' ? String($json.crm_contact_id) : \"\" }}",
    "source_type": "={{ $json.source_type ?? \"\" }}",
    "source_name": "={{ $json.source_name ?? \"\" }}",
    "company_region": "={{ $json.company_region ?? \"\" }}",
    "skip_notification": "={{ $json.skip_notification ?? false }}",
    "trigger_source": "={{ $json.trigger_source ?? \"\" }}",
    "outbound_email_subject": "={{ $json.outbound_email_subject ?? \"\" }}",
    "outbound_email_body": "={{ $json.outbound_email_body ?? \"\" }}",
    "notification_status": "={{ $json.notification_status ?? \"\" }}",
}

SLACK_TO_CRM_INPUTS = dict(ENRICHMENT_TO_CRM_INPUTS)

CRM_WORKFLOW_INPUTS = [
    {"name": "lead_id"},
    {"name": "correlation_id"},
    {"name": "contact_email"},
    {"name": "contact_name"},
    {"name": "contact_role"},
    {"name": "company_name"},
    {"name": "score", "type": "number"},
    {"name": "review_status"},
    {"name": "recommended_action"},
    {"name": "processing_status"},
    {"name": "global_config", "type": "object"},
    {"name": "company_domain"},
    {"name": "confidence"},
    {"name": "routing_decision"},
    {"name": "dedup_skipped", "type": "boolean"},
    {"name": "sheets_write_failed", "type": "boolean"},
    {"name": "sheets_error_message"},
    {"name": "sheets_update_failed", "type": "boolean"},
    {"name": "read_error_message"},
    {"name": "audit_log_failed", "type": "boolean"},
    {"name": "audit_log_error_message"},
    {"name": "config_load_error_message"},
    {"name": "enrichment_error_message"},
    {"name": "scoring_error_message"},
    {"name": "industry"},
    {"name": "company_size"},
    {"name": "content_summary"},
    {"name": "intent_signals"},
    {"name": "enrichment_summary"},
    {"name": "enrichment_status"},
    {"name": "sales_memo"},
    {"name": "sales_memo_status"},
    {"name": "domain_type"},
    {"name": "score_reasoning"},
    {"name": "first_touch_status"},
    {"name": "crm_status"},
    {"name": "crm_contact_id"},
    {"name": "source_type"},
    {"name": "source_name"},
    {"name": "company_region"},
    {"name": "skip_notification", "type": "boolean"},
    {"name": "trigger_source"},
    {"name": "outbound_email_subject"},
    {"name": "outbound_email_body"},
    {"name": "notification_status"},
]

HOLD_LEAD_JS = r"""return $input.item.json;"""

HANDLE_READ_LEADS_ERROR_JS = error_message_prelude("Unknown Read All Leads error") + r"""

const lead = $('Validate Lead').item.json;

return {
  ...lead,
  is_update: false,
  _dedup_skipped: true,
  read_error_message: errorMessage,
  _metadata: {
    processing_stage: 'dedup_read_failed',
    severity: 'medium',
    error_message: errorMessage,
    error_description: errorObj.description || '',
    failed_node: 'Read All Leads',
  },
};
"""

HANDLE_UPDATE_LEAD_ERROR_JS = error_message_prelude("Unknown Update Lead error") + r"""

const lead =
  $('Dedup Lead').first()?.json ??
  $('Validate Lead').first()?.json;

return {
  ...lead,
  sheets_write_failed: true,
  processing_status: 'failed',
  sheets_error_message: errorMessage,
  _metadata: {
    processing_stage: 'update_lead_failed',
    severity: 'high',
    error_message: errorMessage,
    error_description: errorObj.description || '',
    failed_node: 'Update Lead',
  },
};
"""

HANDLE_APPEND_LEAD_ERROR_JS = error_message_prelude("Unknown Append Lead error") + r"""

const lead =
  $('Dedup Lead').first()?.json ??
  $('Handle Read Leads Error').first()?.json ??
  $('Validate Lead').first()?.json;

return {
  ...lead,
  sheets_write_failed: true,
  processing_status: 'failed',
  sheets_error_message: errorMessage,
  _metadata: {
    processing_stage: 'append_lead_failed',
    severity: 'high',
    error_message: errorMessage,
    error_description: errorObj.description || '',
    failed_node: 'Append Lead',
  },
};
"""

HANDLE_AUDIT_LOG_ERROR_JS = r"""const item = $input.item;
const errJson = item.json || {};
const errorObj = item.error || errJson.error || {};
const auditErrorMessage =
  errorObj.message ||
  errorObj.description ||
  errJson.message ||
  errJson.description ||
  (typeof errJson.error === 'string' ? errJson.error : null) ||
  'Unknown Write Audit Log error';

const lead = $('Normalize Lead').first()?.json

return {
  ...lead,
  audit_log_failed: true,
  audit_log_error_message: auditErrorMessage,
  _metadata: {
    ...(lead._metadata || {}),
    processing_stage: 'audit_log_failed',
    severity: 'low',
    error_message: auditErrorMessage,
    failed_node: 'Write Audit Log',
  },
};
"""

HANDLE_SHEETS_SCORE_ERROR_JS = error_message_prelude("Unknown Update Lead Scores error") + r"""

const lead =
  $('Apply Routing Rules').first()?.json ??
  $('Domain Enrichment').first()?.json;

return {
  ...lead,
  sheets_update_failed: true,
  sheets_error_message: errorMessage,
  _metadata: {
    processing_stage: 'score_sheet_update_failed',
    severity: 'high',
    error_message: errorMessage,
    error_description: errorObj.description || '',
    failed_node: 'Update Lead Scores',
  },
};
"""

HANDLE_FINAL_STATUS_ERROR_JS = error_message_prelude("Unknown Update Final Status error") + r"""

const lead =
  $('Normalize Notification Result').first()?.json ??
  $('Normalize CRM Result').first()?.json ??
  $('Build Notification Payload').first()?.json;

return {
  ...lead,
  sheets_write_failed: true,
  sheets_error_message: errorMessage,
  _metadata: {
    processing_stage: 'final_status_write_failed',
    severity: 'medium',
    error_message: errorMessage,
    error_description: errorObj.description || '',
    failed_node: 'Update Final Status',
  },
};
"""

HANDLE_ERROR_LOGS_WRITE_FAILURE_JS = error_message_prelude("Unknown Write error_logs error") + r"""

const details = $('Extract Error Details').first()?.json ?? errJson;

return {
  ...details,
  error_logs_write_failed: true,
  error_logs_error_message: errorMessage,
  _metadata: {
    processing_stage: 'error_logs_write_failed',
    severity: 'high',
    error_message: errorMessage,
    failed_node: 'Write error_logs',
  },
};
"""

HANDLE_SUMMARY_READ_ERROR_JS = error_message_prelude("Unknown Daily Summary read error") + r"""
function safeNodeAll(name) {
  try {
    return $(name).all().map(i => i.json);
  } catch {
    return [];
  }
}

const leads = safeNodeAll('Read Leads For Summary').filter(r => r.lead_id);
const yesterday = new Date();
yesterday.setUTCDate(yesterday.getUTCDate() - 1);
const reportDate = yesterday.toISOString().slice(0, 10);
const dayLeads = leads.filter(l => (l.created_at || '').startsWith(reportDate));

return {
  date: reportDate,
  new_leads: dayLeads.length,
  high_score_leads: dayLeads.filter(l => Number(l.score || 0) >= 80).length,
  crm_success_rate: dayLeads.length ? 'partial' : 'N/A',
  slack_success_count: dayLeads.filter(l => l.notification_status === 'sent').length,
  review_pending: dayLeads.filter(l => l.review_status === 'pending_review').length,
  review_approved: dayLeads.filter(l => l.review_status === 'approved').length,
  error_count: 0,
  error_types: {},
  mode: 'test',
  daily_summary_enabled: false,
  daily_gate_passed: false,
  _summary_degraded: true,
  summary_read_error_message: errorMessage,
  _metadata: {
    processing_stage: 'summary_read_failed',
    severity: 'medium',
    error_message: errorMessage,
    failed_node: 'Read Leads/Errors For Summary',
  },
};
"""

LOG_SLACK_SUMMARY_ERROR_JS = error_message_prelude("Unknown Slack Daily Report error") + r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const summary = safeNodeJson('Build Daily Summary') || safeNodeJson('Handle Summary Read Error') || {};
return {
  ...summary,
  error_type: 'slack_summary_failed',
  slack_error_message: errorMessage,
  _metadata: { processing_stage: 'slack_summary_error_handled', severity: 'low', error_message: errorMessage },
};
"""

HANDLE_HUBSPOT_FAILURE_JS = error_message_prelude("Unknown HubSpot Upsert error") + r"""
const lead = $('CRM Gate').item.json;
return {
  ...lead,
  crm_status: 'failed',
  crm_error_message: errorMessage,
  _metadata: {
    processing_stage: 'crm_failed',
    severity: 'high',
    error_message: errorMessage,
    failed_node: 'HubSpot Upsert Contact',
  },
};
"""

MARK_CRM_SYNCED_JS = r"""
const lead = $('CRM Gate').item.json;
const hs = $input.item.json || {};
// OAuth upsert (CRM v3) returns `id`; Private App / legacy API returns `vid`
const contactId =
  hs.id ||
  hs.vid ||
  hs['canonical-vid'] ||
  (hs.properties && hs.properties.hs_object_id && hs.properties.hs_object_id.value) ||
  lead.crm_contact_id ||
  '';
return {
  ...lead,
  crm_status: 'synced',
  crm_contact_id: String(contactId || ''),
  processing_status: 'completed',
  _metadata: { processing_stage: 'crm_synced' },
};
"""

LOG_SLACK_NOTIFY_ERROR_JS = error_message_prelude("Unknown Slack Notify error") + r"""
const lead = $('Build Notification Payload').item.json;
return {
  ...lead,
  notification_status: 'failed',
  slack_error_message: errorMessage,
  _metadata: {
    processing_stage: 'notification_failed',
    severity: 'medium',
    error_message: errorMessage,
    failed_node: 'Slack Notify',
  },
};
"""

LOG_SLACK_ERROR_JS = error_message_prelude("Unknown Slack Error Alert error") + r"""
return {
  error_type: 'slack_notification_failed',
  slack_error_message: errorMessage,
  _metadata: { processing_stage: 'slack_error_handled', severity: 'low', error_message: errorMessage },
};
"""

PASS_LEAD_TO_ENRICHMENT_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const dedup =
  safeNodeJson('Dedup Lead') ??
  safeNodeJson('Handle Read Leads Error') ??
  {};

const updateErr = safeNodeJson('Handle Update Lead Error');
const appendErr = safeNodeJson('Handle Append Lead Error');
const auditErr = safeNodeJson('Handle Audit Log Error');

const sheetErr =
  updateErr?.sheets_write_failed ? updateErr :
  appendErr?.sheets_write_failed ? appendErr :
  null;

const email = (dedup.contact_email ?? '').toLowerCase().trim();
let company_domain = dedup.company_domain ?? '';
if (!company_domain && email.includes('@')) {
  company_domain = email.split('@')[1].toLowerCase();
}

const payload = {
  lead_id: dedup.lead_id,
  correlation_id: dedup.correlation_id,
  source_type: dedup.source_type ?? '',
  source_name: dedup.source_name ?? '',
  source_trust_level: Number(dedup.source_trust_level ?? 0),
  contact_name: dedup.contact_name ?? '',
  contact_email: email,
  contact_role: dedup.contact_role ?? '',
  company_name: dedup.company_name ?? '',
  company_domain,
  raw_content: dedup.raw_content ?? '',
};

if (sheetErr) {
  payload.sheets_write_failed = true;
  payload.sheets_error_message = sheetErr.sheets_error_message ?? '';
}

if (dedup._dedup_skipped) {
  payload.dedup_skipped = true;
  payload.read_error_message = dedup.read_error_message ?? '';
}

if (auditErr?.audit_log_failed) {
  payload.audit_log_failed = true;
  payload.audit_log_error_message = auditErr.audit_log_error_message ?? '';
}

return payload;
"""

NORMALIZE_ENRICHED_LEAD_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const lead = safeNodeJson('Apply Routing Rules') ?? {};
const sheetErr = safeNodeJson('Handle Sheets Score Error');

const payload = {
  lead_id: lead.lead_id,
  correlation_id: lead.correlation_id,
  contact_email: (lead.contact_email ?? '').toLowerCase().trim(),
  contact_name: lead.contact_name ?? '',
  contact_role: lead.contact_role ?? '',
  company_name: lead.company_name ?? '',
  company_domain: lead.company_domain ?? '',
  score: lead.score,
  review_status: lead.review_status ?? '',
  recommended_action: lead.recommended_action ?? '',
  routing_decision: lead.routing_decision ?? '',
  processing_status: lead.processing_status ?? '',
  global_config: lead.global_config,
  industry: lead.industry ?? '',
  company_size: lead.company_size ?? '',
  content_summary: lead.content_summary ?? '',
  intent_signals: lead.intent_signals ?? '',
  enrichment_summary: lead.enrichment_summary ?? '',
  enrichment_status: lead.enrichment_status ?? '',
  sales_memo: lead.sales_memo ?? '',
  sales_memo_status: lead.sales_memo_status ?? '',
  domain_type: lead.domain_type ?? '',
  score_reasoning: lead.score_reasoning ?? '',
  first_touch_status: lead.first_touch_status ?? '',
  source_type: lead.source_type ?? '',
  source_name: lead.source_name ?? '',
  company_region: lead.company_region ?? '',
};

if (lead.confidence != null && lead.confidence !== '') {
  payload.confidence = lead.confidence;
}

const optionalKeys = [
  'sheets_write_failed',
  'sheets_error_message',
  'dedup_skipped',
  'read_error_message',
  'audit_log_failed',
  'audit_log_error_message',
  'config_load_error_message',
  'enrichment_error_message',
  'scoring_error_message',
];

for (const key of optionalKeys) {
  const value = lead[key];
  if (value != null && value !== '') {
    payload[key] = value;
  }
}

if (sheetErr?.sheets_update_failed) {
  payload.sheets_update_failed = true;
  if (sheetErr.sheets_error_message) {
    payload.sheets_error_message = sheetErr.sheets_error_message;
  }
}

return payload;
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
  source_url: data.formId ? ('https://tally.so/r/' + data.formId) : '',
  source_trust_level: 80,
  contact_name: getField('name', 'contact_name', 'full_name'),
  contact_email: getField('email', 'contact_email').toLowerCase().trim(),
  contact_role: getField('role', 'contact_role', 'job_title'),
  company_name: getField('company', 'company_name'),
  raw_content: getField('message', 'details', 'project_description', 'how_can_we_help?'),
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
const email = (item.contact_email || '').toLowerCase().trim();
const domain = (item.company_domain || (email.includes('@') ? email.split('@')[1] : '')).toLowerCase().trim();
const hashInput = `${email}|${domain}`;
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
const item = $('Validate Lead').item.json;
const existingRows = $('Read All Leads').all().map(r => r.json);
const findMatch = (rows, predicate) => rows.find(predicate);

let existing = null;
let dedupMatchKey = '';

if (item.contact_email) {
  const email = item.contact_email.toLowerCase().trim();
  existing = findMatch(
    existingRows,
    (row) => (row.contact_email || '').toLowerCase().trim() === email,
  );
  if (existing) dedupMatchKey = 'contact_email';
}

if (!existing && item.lead_hash) {
  existing = findMatch(existingRows, (row) => row.lead_hash === item.lead_hash);
  if (existing) dedupMatchKey = 'lead_hash';
}

if (existing && existing.lead_id) {
  return {
    ...item,
    lead_id: existing.lead_id,
    correlation_id: item.correlation_id,
    is_update: true,
    dedup_match_key: dedupMatchKey,
    updated_at: new Date().toISOString(),
    _metadata: { processing_stage: 'dedup_update', dedup_match_key: dedupMatchKey },
  };
}

return {
  ...item,
  is_update: false,
  dedup_match_key: '',
  _metadata: { processing_stage: 'dedup_insert' },
};
"""

VERIFY_CALENDLY_SIGNATURE_JS = r"""
const crypto = require('crypto');

const item = $input.item;
const json = item.json || {};
const headers = json.headers || {};
const body = json.body ?? json;
const signingKey = $env.CALENDLY_WEBHOOK_SIGNING_KEY || '';

const signatureHeader =
  headers['calendly-webhook-signature'] ||
  headers['Calendly-Webhook-Signature'] ||
  '';

const rawBody =
  json.rawBody ||
  (typeof body === 'string' ? body : JSON.stringify(body));

function verifySignature(key, header, payload) {
  if (!key) return { valid: true, skipped: true, reason: 'verification_skipped' };
  if (!header) return { valid: false, skipped: false, reason: 'missing_signature' };

  const parts = {};
  for (const part of header.split(',')) {
    const eq = part.indexOf('=');
    if (eq === -1) continue;
    parts[part.slice(0, eq).trim()] = part.slice(eq + 1).trim();
  }

  const t = parts.t;
  const v1 = parts.v1;
  if (!t || !v1) return { valid: false, skipped: false, reason: 'malformed_signature' };

  const signedPayload = `${t}.${payload}`;
  const expected = crypto.createHmac('sha256', key).update(signedPayload).digest('hex');

  let valid = false;
  try {
    valid =
      v1.length === expected.length &&
      crypto.timingSafeEqual(Buffer.from(v1), Buffer.from(expected));
  } catch {
    valid = false;
  }

  return {
    valid,
    skipped: false,
    reason: valid ? 'ok' : 'invalid_signature',
  };
}

const result = verifySignature(signingKey, signatureHeader, rawBody);
const parsedBody = typeof body === 'string' ? JSON.parse(body) : body;

return {
  headers,
  body: parsedBody,
  rawBody,
  signature_valid: result.valid,
  signature_skipped: result.skipped || false,
  signature_error: result.reason,
  _metadata: {
    processing_stage: result.valid ? 'calendly_signature_verified' : 'calendly_signature_failed',
    severity: result.valid ? 'info' : 'medium',
  },
};
"""

NORMALIZE_CALENDLY_JS = r"""
const crypto = require('crypto');
const body = $input.item.json.body || $input.item.json;
const event = body.event || '';
const payload = body.payload || {};
const scheduledEvent = payload.scheduled_event || {};
const eventField = payload.event;
const invitee = payload.invitee || {};

const inviteeEmail = (
  payload.email ||
  invitee.email ||
  ''
).toLowerCase().trim();

const eventUri =
  scheduledEvent.uri ||
  (typeof eventField === 'string' ? eventField : eventField?.uri) ||
  '';

const meetingTime = scheduledEvent.start_time || '';

let meetingStatus = 'not_booked';
if (event === 'invitee.created') {
  meetingStatus = 'booked';
} else if (event === 'invitee.canceled') {
  meetingStatus = 'canceled';
}

const correlationId = crypto.randomUUID();
const now = new Date().toISOString();

return {
  calendly_event: event,
  invitee_email: inviteeEmail,
  calendly_event_uri: eventUri,
  meeting_time: meetingTime,
  meeting_status: meetingStatus,
  calendly_invitee_email: inviteeEmail,
  correlation_id: correlationId,
  updated_at: now,
  _metadata: { processing_stage: 'calendly_normalized' },
};
"""

MATCH_LEAD_BY_EMAIL_JS = r"""
// Must runOnceForAllItems: Sheets returns one item per row; forEachItem would
// fan-out Match → Update → Slack Notify (N booked messages for N leads).
const normalized = $('Normalize Calendly Payload').first()?.json ?? {};

function rowsFrom(name) {
  try {
    return $(name).all().map((row) => row.json).filter((row) => row && row.lead_id);
  } catch {
    return [];
  }
}

let existingRows = [];
try {
  existingRows = $input.all().map((row) => row.json).filter((row) => row && row.lead_id);
} catch {
  existingRows = [];
}
if (!existingRows.length) {
  existingRows = rowsFrom('Read All Leads');
}

const email = (normalized.invitee_email || '').toLowerCase().trim();
const lead = existingRows.find(
  (row) => (row.contact_email || '').toLowerCase().trim() === email,
);

let meetingStatus = normalized.meeting_status;
if (lead && normalized.calendly_event === 'invitee.created') {
  const prev = (lead.meeting_status || '').toLowerCase();
  if (
    prev === 'booked' &&
    lead.meeting_time &&
    normalized.meeting_time &&
    lead.meeting_time !== normalized.meeting_time
  ) {
    meetingStatus = 'rescheduled';
  }
}

const auditEventByStatus = {
  booked: 'calendly_booked',
  canceled: 'calendly_canceled',
  rescheduled: 'calendly_rescheduled',
};

return {
  ...normalized,
  lead_found: !!lead,
  lead_id: lead?.lead_id || '',
  correlation_id: lead?.correlation_id || normalized.correlation_id,
  contact_name: lead?.contact_name || '',
  contact_email: lead?.contact_email || email,
  company_name: lead?.company_name || '',
  score: lead?.score || 0,
  previous_meeting_status: lead?.meeting_status || '',
  meeting_status: meetingStatus,
  calendly_invitee_email: email,
  audit_event: lead ? (auditEventByStatus[meetingStatus] || 'calendly_updated') : 'calendly_unmatched',
  sheets_row_count: existingRows.length,
  _metadata: {
    processing_stage: lead ? 'calendly_lead_matched' : 'calendly_lead_not_found',
  },
};
"""

HANDLE_CALENDLY_READ_ERROR_JS = error_message_prelude("Unknown Read All Leads error") + r"""
const normalized = $('Normalize Calendly Payload').first()?.json ?? {};

return {
  ...normalized,
  lead_found: false,
  read_error_message: errorMessage,
  audit_event: 'calendly_read_failed',
  _metadata: {
    processing_stage: 'calendly_read_failed',
    severity: 'medium',
    error_message: errorMessage,
    failed_node: 'Read All Leads',
  },
};
"""

HANDLE_UPDATE_MEETING_ERROR_JS = error_message_prelude("Unknown Update Lead Meeting error") + r"""
const lead = $('Match Lead By Email').first()?.json ?? {};

return {
  ...lead,
  sheets_update_failed: true,
  sheets_error_message: errorMessage,
  audit_event: 'calendly_update_failed',
  _metadata: {
    processing_stage: 'calendly_update_failed',
    severity: 'high',
    error_message: errorMessage,
    failed_node: 'Update Lead Meeting',
  },
};
"""

BUILD_CALENDLY_SLACK_TEXT_JS = r"""
const lead = $('Match Lead By Email').first()?.json ?? $input.item.json;
const status = lead.meeting_status || 'updated';
const name = lead.contact_name || 'Unknown';
const email = lead.contact_email || lead.invitee_email || lead.calendly_invitee_email || '';
const when = lead.meeting_time || 'N/A';
const score = lead.score != null && lead.score !== '' ? lead.score : 'N/A';

const titles = {
  booked: '📅 Meeting booked',
  canceled: '❌ Meeting canceled',
  rescheduled: '🔄 Meeting rescheduled',
};
const title = titles[status] || '📅 Calendly update';

return {
  ...lead,
  slack_text: `${title}\nLead: ${name} (${email})\nScore: ${score}\nTime: ${when}\nStatus: ${status}\nCorrelation: ${lead.correlation_id || 'N/A'}`,
  _metadata: { processing_stage: 'calendly_slack_prepared' },
};
"""

LOG_CALENDLY_SLACK_ERROR_JS = error_message_prelude("Unknown Slack Calendly Notify error") + r"""
const lead =
  $('Build Calendly Slack Text').first()?.json ??
  $('Match Lead By Email').first()?.json ??
  {};

return {
  ...lead,
  slack_error_message: errorMessage,
  _metadata: {
    processing_stage: 'calendly_slack_error_handled',
    severity: 'low',
    error_message: errorMessage,
    failed_node: 'Slack Calendly Notify',
  },
};
"""

PREPARE_CALENDLY_AUDIT_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const matched = safeNodeJson('Match Lead By Email') ?? {};
const updateError = safeNodeJson('Handle Update Meeting Error');

let auditEvent = matched.audit_event || 'calendly_updated';
if (updateError?.sheets_update_failed) {
  auditEvent = updateError.audit_event || 'calendly_update_failed';
}

return {
  lead_id: matched.lead_id || '',
  correlation_id: matched.correlation_id || '',
  audit_event: auditEvent,
  previous_meeting_status: matched.previous_meeting_status || '',
  meeting_status: matched.meeting_status || '',
  updated_at: matched.updated_at || new Date().toISOString(),
  _metadata: { processing_stage: 'calendly_audit_prepared' },
};
"""

VERIFY_SLACK_SIGNATURE_JS = r"""
const crypto = require('crypto');

const item = $input.item;
const json = item.json || {};
const headers = json.headers || {};
const body = json.body ?? json;
const signingSecret = $env.SLACK_SIGNING_SECRET || '';
const skipTimestampCheck = String($env.SLACK_SKIP_TIMESTAMP_CHECK || '').toLowerCase() === 'true';
const maxAgeSeconds = parseInt($env.SLACK_SIGNATURE_MAX_AGE_SECONDS || '300', 10);

const signatureHeader =
  headers['x-slack-signature'] ||
  headers['X-Slack-Signature'] ||
  '';
const timestampHeader =
  headers['x-slack-request-timestamp'] ||
  headers['X-Slack-Request-Timestamp'] ||
  '';

function readRawBody() {
  if (json.rawBody) return { rawBody: json.rawBody, raw_body_source: 'json.rawBody' };

  const binary = item.binary?.data;
  if (binary?.data) {
    return {
      rawBody: Buffer.from(binary.data, binary.encoding || 'base64').toString('utf8'),
      raw_body_source: 'binary.data',
    };
  }

  if (typeof body === 'string') {
    return { rawBody: body, raw_body_source: 'body_string' };
  }

  if (body && body.payload != null) {
    return {
      rawBody:
        'payload=' +
        encodeURIComponent(
          typeof body.payload === 'string' ? body.payload : JSON.stringify(body.payload),
        ),
      raw_body_source: 'payload_reencoded',
    };
  }

  return {
    rawBody: JSON.stringify(body || {}),
    raw_body_source: 'json_stringified',
  };
}

function computeSignature(secret, timestamp, payload) {
  const sigBasestring = `v0:${timestamp}:${payload}`;
  return (
    'v0=' + crypto.createHmac('sha256', secret).update(sigBasestring).digest('hex')
  );
}

function signaturesMatch(signature, expected) {
  try {
    return (
      signature.length === expected.length &&
      crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))
    );
  } catch {
    return false;
  }
}

function verifySlackSignature(secret, signature, timestamp, payload) {
  if (!secret) {
    return { valid: true, skipped: true, reason: 'verification_skipped' };
  }
  if (!signature || !timestamp) {
    return { valid: false, skipped: false, reason: 'missing_signature' };
  }

  const requestTs = parseInt(timestamp, 10);
  const now = Math.floor(Date.now() / 1000);
  const ageSeconds = Number.isFinite(requestTs) ? Math.abs(now - requestTs) : Number.MAX_SAFE_INTEGER;
  const timestampFresh =
    skipTimestampCheck ||
    (Number.isFinite(requestTs) && ageSeconds <= (Number.isFinite(maxAgeSeconds) ? maxAgeSeconds : 300));

  const expectedSignature = computeSignature(secret, timestamp, payload);
  const signatureMatch = signaturesMatch(signatureHeader, expectedSignature);

  if (!timestampFresh) {
    return {
      valid: false,
      skipped: false,
      reason: signatureMatch ? 'timestamp_expired' : 'timestamp_expired_invalid_signature',
      signature_match: signatureMatch,
      age_seconds: ageSeconds,
    };
  }

  return {
    valid: signatureMatch,
    skipped: false,
    reason: signatureMatch ? 'ok' : 'invalid_signature',
    signature_match: signatureMatch,
    age_seconds: ageSeconds,
  };
}

const { rawBody, raw_body_source } = readRawBody();
const result = verifySlackSignature(
  signingSecret,
  signatureHeader,
  timestampHeader,
  rawBody,
);

return {
  headers,
  body,
  rawBody,
  raw_body_source,
  signature_valid: result.valid,
  signature_skipped: result.skipped || false,
  signature_error: result.reason,
  signature_match: result.signature_match ?? null,
  signature_age_seconds: result.age_seconds ?? null,
  _metadata: {
    processing_stage: result.valid ? 'slack_signature_verified' : 'slack_signature_failed',
    severity: result.valid ? 'info' : 'medium',
  },
};
"""

PARSE_SLACK_PAYLOAD_JS = r"""
const verified = $input.item.json || {};
const body = verified.body || {};

let payload;
try {
  const rawPayload = body.payload ?? verified.payload;
  if (!rawPayload) throw new Error('missing_payload');
  payload = typeof rawPayload === 'string' ? JSON.parse(rawPayload) : rawPayload;
} catch (error) {
  return {
    ...verified,
    parse_error: true,
    parse_error_message: error.message || 'payload_parse_failed',
    _metadata: { processing_stage: 'slack_payload_parse_failed', severity: 'medium' },
  };
}

const action = (payload.actions && payload.actions[0]) || {};
const user = payload.user || {};

let actionValue = {};
try {
  actionValue = JSON.parse(action.value || '{}');
} catch {
  actionValue = { lead_id: action.value || '' };
}

const slackUserId = user.id || '';
const slackUserName = user.username || user.name || slackUserId;
const adminList = ($env.SLACK_ADMIN_USERS || '')
  .split(',')
  .map((entry) => entry.trim())
  .filter(Boolean);
const adminAllowed = adminList.length === 0 || adminList.includes(slackUserId);

return {
  ...verified,
  parse_error: false,
  action_id: action.action_id || '',
  lead_id: actionValue.lead_id || '',
  correlation_id: actionValue.correlation_id || '',
  slack_user_id: slackUserId,
  slack_user_name: slackUserName,
  response_url: payload.response_url || '',
  admin_allowed: adminAllowed,
  channel_id: payload.channel?.id || '',
  message_ts: payload.message?.ts || payload.container?.message_ts || '',
  _metadata: { processing_stage: 'slack_payload_parsed' },
};
"""

SET_UNAUTHORIZED_REPLY_JS = r"""
const item = $input.item.json || {};

return {
  ...item,
  skip_update: true,
  slack_response_type: 'ephemeral',
  slack_reply: 'You are not authorized to perform this action.',
  audit_event: 'slack_action_unauthorized',
  _metadata: { processing_stage: 'slack_action_unauthorized' },
};
"""

RESOLVE_LEAD_ACTION_JS = r"""
const item = $input.item.json || {};
const now = new Date().toISOString();
const actionId = item.action_id || '';

const actionMap = {
  assign_lead: {
    review_status: 'approved',
    recommended_action: 'crm_sync',
    lead_stage: 'sql',
    owner_id: item.slack_user_id,
    reviewer: item.slack_user_id,
    audit_event: 'slack_action_assign',
    slack_reply: `Lead assigned to <@${item.slack_user_id}>`,
  },
  mark_junk: {
    review_status: 'rejected',
    recommended_action: 'reject',
    lead_stage: 'junk',
    audit_event: 'slack_action_junk',
    slack_reply: `Lead marked as junk by <@${item.slack_user_id}>`,
  },
  nurture_lead: {
    review_status: 'review_later',
    recommended_action: 'notify_only',
    lead_stage: 'nurture',
    audit_event: 'slack_action_nurture',
    slack_reply: `Lead moved to nurture by <@${item.slack_user_id}>`,
  },
};

const action = actionMap[actionId];
if (!action) {
  return {
    ...item,
    unknown_action: true,
    skip_update: true,
    audit_event: 'slack_action_unknown',
    updated_at: now,
    _metadata: { processing_stage: 'slack_unknown_action' },
  };
}

return {
  ...item,
  unknown_action: false,
  skip_update: false,
  review_notes: `Slack action ${actionId} by ${item.slack_user_name || item.slack_user_id}`,
  reviewed_at: now,
  updated_at: now,
  ...action,
  _metadata: { processing_stage: 'slack_action_resolved' },
};
"""

MATCH_LEAD_BY_ID_JS = r"""
// Must runOnceForAllItems: Sheets returns one item per row; forEachItem would
// fan-out and can break $('Resolve Lead Action') / .all() pairing → false "Lead not found".
const action = $('Resolve Lead Action').first()?.json || {};
const leadId = String(action.lead_id || '').trim();

function rowsFrom(name) {
  try {
    return $(name).all().map((row) => row.json).filter((row) => row && row.lead_id);
  } catch {
    return [];
  }
}

let existingRows = [];
try {
  existingRows = $input.all().map((row) => row.json).filter((row) => row && row.lead_id);
} catch {
  existingRows = [];
}
if (!existingRows.length) {
  existingRows = rowsFrom('Read All Leads For Slack');
}

const lead = existingRows.find(
  (row) => String(row.lead_id || '').trim() === leadId,
);

if (!lead) {
  return {
    ...action,
    lead_found: false,
    skip_update: true,
    audit_event: 'slack_action_lead_not_found',
    sheets_row_count: existingRows.length,
    _metadata: {
      processing_stage: 'slack_lead_not_found',
      lookup_lead_id: leadId,
      sheets_row_count: existingRows.length,
    },
  };
}

const now = action.updated_at || new Date().toISOString();
const merged = {
  review_status: action.review_status || lead.review_status,
  recommended_action: action.recommended_action || lead.recommended_action,
  lead_stage: action.lead_stage || lead.lead_stage,
  owner_id: action.owner_id || lead.owner_id || '',
  reviewer: action.reviewer || lead.reviewer || '',
  review_notes: action.review_notes || lead.review_notes || '',
  reviewed_at: now,
  updated_at: now,
};

return {
  ...action,
  ...merged,
  lead_found: true,
  skip_update: false,
  contact_name: lead.contact_name || '',
  contact_email: lead.contact_email || '',
  company_name: lead.company_name || '',
  score: lead.score ?? '',
  correlation_id: action.correlation_id || lead.correlation_id || '',
  previous_review_status: lead.review_status || '',
  previous_lead_stage: lead.lead_stage || '',
  previous_owner_id: lead.owner_id || lead.reviewer || '',
  already_assigned:
    action.action_id === 'assign_lead' &&
    String(lead.review_status || '').toLowerCase() === 'approved' &&
    !!(lead.owner_id || lead.reviewer),
  _metadata: { processing_stage: 'slack_lead_matched' },
};
"""

HANDLE_SLACK_READ_ERROR_JS = error_message_prelude("Unknown Read All Leads For Slack error") + r"""
const action = $('Resolve Lead Action').first()?.json ?? {};

return {
  ...action,
  lead_found: false,
  skip_update: true,
  read_error_message: errorMessage,
  slack_response_type: 'ephemeral',
  slack_reply: 'Could not load leads. Please retry.',
  audit_event: 'slack_action_read_failed',
  _metadata: {
    processing_stage: 'slack_read_failed',
    severity: 'medium',
    error_message: errorMessage,
    failed_node: 'Read All Leads For Slack',
  },
};
"""

HANDLE_UPDATE_REVIEW_ERROR_JS = error_message_prelude("Unknown Update Lead Review error") + r"""
const lead = $('Match Lead By ID').first()?.json ?? {};

return {
  ...lead,
  sheets_update_failed: true,
  sheets_error_message: errorMessage,
  slack_response_type: 'ephemeral',
  slack_reply: 'Action failed, please retry.',
  audit_event: 'slack_action_update_failed',
  _metadata: {
    processing_stage: 'slack_update_failed',
    severity: 'high',
    error_message: errorMessage,
    failed_node: 'Update Lead Review',
  },
};
"""

SLACK_ACTION_UI_HELPERS_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

function mergeSlackContext(incoming) {
  const context =
    safeNodeJson('Match Lead By ID') ??
    safeNodeJson('Handle Update Review Error') ??
    safeNodeJson('Handle Slack Read Error') ??
    safeNodeJson('Resolve Lead Action') ??
    safeNodeJson('Set Unauthorized Reply') ??
    safeNodeJson('Parse Slack Payload') ??
    {};

  return {
    ...context,
    ...incoming,
    response_url: incoming.response_url || context.response_url || '',
    channel_id: incoming.channel_id || context.channel_id || '',
    message_ts: incoming.message_ts || context.message_ts || '',
    slack_user_id: incoming.slack_user_id || context.slack_user_id || '',
    slack_user_name: incoming.slack_user_name || context.slack_user_name || '',
    lead_id: incoming.lead_id || context.lead_id || '',
    correlation_id: incoming.correlation_id || context.correlation_id || '',
    action_id: incoming.action_id || context.action_id || '',
    audit_event: incoming.audit_event || context.audit_event || 'slack_action',
    contact_name: incoming.contact_name || context.contact_name || '',
    contact_email: incoming.contact_email || context.contact_email || '',
    company_name: incoming.company_name || context.company_name || '',
    score: incoming.score ?? context.score ?? '',
    previous_review_status:
      context.previous_review_status || incoming.previous_review_status || '',
    previous_lead_stage: context.previous_lead_stage || incoming.previous_lead_stage || '',
    previous_owner_id: context.previous_owner_id || incoming.previous_owner_id || '',
    review_status: incoming.review_status || context.review_status || '',
    lead_stage: incoming.lead_stage || context.lead_stage || '',
    already_assigned: incoming.already_assigned ?? context.already_assigned ?? false,
    lead_found: incoming.lead_found ?? context.lead_found,
    sheets_update_failed:
      incoming.sheets_update_failed ?? context.sheets_update_failed ?? false,
    sheets_error_message:
      incoming.sheets_error_message || context.sheets_error_message || '',
    read_error_message: incoming.read_error_message || context.read_error_message || '',
  };
}

function escapeMrkdwn(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function leadHeadline(ctx) {
  const name = escapeMrkdwn(ctx.contact_name || 'Unknown lead');
  const company = escapeMrkdwn(ctx.company_name || 'N/A');
  const email = escapeMrkdwn(ctx.contact_email || 'N/A');
  const score =
    ctx.score !== undefined && ctx.score !== null && ctx.score !== ''
      ? ` · Score ${ctx.score}`
      : '';
  return `*${name}* @ ${company}${score}\n📧 ${email}`;
}

function leadFooter(ctx) {
  const leadRef = ctx.lead_id ? `\`${String(ctx.lead_id).slice(0, 8)}…\`` : 'N/A';
  const corr = ctx.correlation_id ? `\`${ctx.correlation_id}\`` : 'N/A';
  return `Lead ${leadRef} · Correlation ${corr}`;
}

const ACTION_META = {
  assign_lead: {
    processing: 'Assigning',
    success: 'Assigned',
    done: 'Already assigned',
    fail: 'Assign failed',
  },
  mark_junk: {
    processing: 'Marking as junk',
    success: 'Marked as junk',
    done: 'Already marked junk',
    fail: 'Junk update failed',
  },
  nurture_lead: {
    processing: 'Moving to nurture',
    success: 'Moved to nurture',
    done: 'Already in nurture',
    fail: 'Nurture update failed',
  },
};

function metaFor(actionId) {
  return (
    ACTION_META[actionId] || {
      processing: 'Processing',
      success: 'Completed',
      done: 'Already updated',
      fail: 'Action failed',
    }
  );
}

function buildProcessingBlocks(ctx) {
  const meta = metaFor(ctx.action_id);
  return [
    {
      type: 'section',
      text: {
        type: 'mrkdwn',
        text:
          `⏳ *${meta.processing}* — ${leadHeadline(ctx)}\n` +
          `👤 by <@${ctx.slack_user_id}> · please wait…`,
      },
    },
    {
      type: 'context',
      elements: [{ type: 'mrkdwn', text: leadFooter(ctx) }],
    },
  ];
}

function buildFinalBlocks(ctx) {
  const meta = metaFor(ctx.action_id);
  const unauthorized = ctx.audit_event === 'slack_action_unauthorized';
  const notFound =
    ctx.audit_event === 'slack_action_lead_not_found' || ctx.lead_found === false;
  const unknown = ctx.audit_event === 'slack_action_unknown';
  const failure = ctx.sheets_update_failed || !!ctx.read_error_message;

  if (unauthorized) {
    return [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: '🚫 *Not authorized*\nYou cannot perform this action.',
        },
      },
    ];
  }

  if (notFound) {
    return [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `❌ *Lead not found*\n${leadFooter(ctx)}`,
        },
      },
    ];
  }

  if (unknown) {
    return [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `❌ *Unknown action*\n\`${escapeMrkdwn(ctx.action_id || 'missing')}\``,
        },
      },
    ];
  }

  if (failure) {
    const detail = escapeMrkdwn(
      ctx.sheets_error_message || ctx.read_error_message || 'Please retry or check Sheets.',
    );
    return [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `❌ *${meta.fail}*\n${leadHeadline(ctx)}\n_${detail}_`,
        },
      },
      {
        type: 'context',
        elements: [{ type: 'mrkdwn', text: leadFooter(ctx) }],
      },
    ];
  }

  if (ctx.already_assigned && ctx.action_id === 'assign_lead') {
    const owner = ctx.previous_owner_id ? `<@${ctx.previous_owner_id}>` : 'someone';
    return [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `ℹ️ *${meta.done}*\n${leadHeadline(ctx)}\n👤 Owner: ${owner}`,
        },
      },
      {
        type: 'context',
        elements: [
          {
            type: 'mrkdwn',
            text: `${leadFooter(ctx)} · buttons removed · no duplicate update`,
          },
        ],
      },
    ];
  }

  let detail = '';
  if (ctx.action_id === 'assign_lead') {
    detail = `\n👤 Owner: <@${ctx.slack_user_id}>`;
  } else if (ctx.action_id === 'mark_junk') {
    detail = '\n📋 Stage: `junk` · Review: `rejected`';
  } else if (ctx.action_id === 'nurture_lead') {
    detail = '\n📋 Stage: `nurture` · Review: `review_later`';
  }

  return [
    {
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: `✅ *${meta.success}*\n${leadHeadline(ctx)}${detail}`,
      },
    },
    {
      type: 'context',
      elements: [{ type: 'mrkdwn', text: `${leadFooter(ctx)} · updated · buttons removed` }],
    },
  ];
}

function buildSlackMessageBody(ctx, blocks, fallbackText) {
  return {
    replace_original: true,
    blocks,
    text: fallbackText,
  };
}
"""

PREPARE_SLACK_ACK_JS = SLACK_ACTION_UI_HELPERS_JS + r"""
const merged = mergeSlackContext($input.item.json || {});
const blocks = buildProcessingBlocks(merged);
const meta = metaFor(merged.action_id);

return {
  ...merged,
  has_slack_message_target: !!(merged.channel_id && merged.message_ts),
  has_response_url: !!merged.response_url,
  slack_message_body: buildSlackMessageBody(
    merged,
    blocks,
    `${meta.processing} ${merged.contact_name || 'lead'}…`,
  ),
  _metadata: { processing_stage: 'slack_ack_prepared' },
};
"""

PREPARE_SLACK_RESPONSE_BODY_JS = SLACK_ACTION_UI_HELPERS_JS + r"""
const merged = mergeSlackContext($input.item.json || {});
const blocks = buildFinalBlocks(merged);
const meta = metaFor(merged.action_id);
const isFailure =
  merged.audit_event === 'slack_action_unauthorized' ||
  merged.audit_event === 'slack_action_lead_not_found' ||
  merged.audit_event === 'slack_action_unknown' ||
  merged.sheets_update_failed ||
  !!merged.read_error_message;
const fallbackPrefix = isFailure ? meta.fail : merged.already_assigned ? meta.done : meta.success;

return {
  ...merged,
  has_slack_message_target: !!(merged.channel_id && merged.message_ts),
  has_response_url: !!merged.response_url,
  slack_message_body: buildSlackMessageBody(
    merged,
    blocks,
    `${fallbackPrefix}: ${merged.contact_name || 'lead'} @ ${merged.company_name || 'N/A'}`,
  ),
  _metadata: { processing_stage: 'slack_final_response_prepared' },
};
"""

LOG_SLACK_RESPONSE_ERROR_JS = error_message_prelude("Unknown Post Slack Response error") + r"""
const lead =
  $('Prepare Slack Response Body').first()?.json ??
  $('Match Lead By ID').first()?.json ??
  $('Resolve Lead Action').first()?.json ??
  {};

return {
  ...lead,
  slack_response_error_message: errorMessage,
  _metadata: {
    processing_stage: 'slack_response_error_handled',
    severity: 'low',
    error_message: errorMessage,
    failed_node: 'Slack Update Final',
  },
};
"""

PREPARE_SLACK_ACTION_AUDIT_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const responseContext = safeNodeJson('Prepare Slack Response Body') ?? {};
const matched =
  safeNodeJson('Match Lead By ID') ??
  safeNodeJson('Handle Update Review Error') ??
  safeNodeJson('Handle Slack Read Error') ??
  safeNodeJson('Set Unauthorized Reply') ??
  safeNodeJson('Resolve Lead Action') ??
  {};
const updateError = safeNodeJson('Handle Update Review Error');

let auditEvent =
  responseContext.audit_event || matched.audit_event || 'slack_action';
if (updateError?.sheets_update_failed) {
  auditEvent = updateError.audit_event || 'slack_action_update_failed';
}

return {
  lead_id: responseContext.lead_id || matched.lead_id || '',
  correlation_id: responseContext.correlation_id || matched.correlation_id || '',
  audit_event: auditEvent,
  previous_review_status:
    responseContext.previous_review_status || matched.previous_review_status || '',
  new_review_status: responseContext.review_status || matched.review_status || '',
  previous_lead_stage:
    responseContext.previous_lead_stage || matched.previous_lead_stage || '',
  new_lead_stage: responseContext.lead_stage || matched.lead_stage || '',
  slack_user_id: responseContext.slack_user_id || matched.slack_user_id || '',
  updated_at:
    responseContext.updated_at || matched.updated_at || new Date().toISOString(),
  _metadata: { processing_stage: 'slack_action_audit_prepared' },
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

ATTACH_HUNTER_DATA_JS = r"""
const lead = $('Domain Enrichment').item.json;
const resp = $input.item.json || {};
const hasError = $input.item.error;
const errorObj = hasError || {};
const errorMessage =
  errorObj.message ||
  errorObj.description ||
  (typeof errorObj === 'string' ? errorObj : null) ||
  '';
const co = resp.data;

let companyRegion = '';
if (co?.location) {
  if (typeof co.location === 'string') companyRegion = co.location;
  else {
    const parts = [co.location.city, co.location.state, co.location.country].filter(Boolean);
    companyRegion = parts.join(', ');
  }
}

const hasData = !hasError && co && (co.name || co.category?.industry);
const external = hasData
  ? JSON.stringify({
      source: 'hunter',
      name: co.name,
      domain: co.domain,
      industry: co.category?.industry || co.category?.sector || '',
      company_size: co.metrics?.employees || '',
      company_region: companyRegion,
      description: co.description || '',
      location: co.location || '',
      founded: co.foundedYear,
      tags: co.tags || [],
    })
  : '';

return {
  ...lead,
  external_enrichment: external,
  company_region: companyRegion,
  hunter_error_message: hasError ? String(errorMessage || 'Hunter Company Lookup failed') : '',
  _metadata: {
    ...(lead._metadata || {}),
    processing_stage: hasError
      ? 'hunter_enrichment_failed'
      : hasData
        ? 'hunter_company_enriched'
        : 'hunter_skipped',
    ...(hasError
      ? { severity: 'low', error_message: errorMessage, failed_node: 'Hunter Company Lookup' }
      : {}),
  },
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

HANDLE_AI_ENRICH_FAILURE_JS = error_message_prelude("Unknown HTTP Enrich Lead error") + r"""
const lead = $('Domain Enrichment').item.json;
return {
  ...lead,
  content_summary: (lead.raw_content || '').slice(0, 300),
  enrichment_status: 'failed',
  enrichment_summary: 'LLM enrichment failed; using raw content fallback',
  processing_status: 'enriched',
  enrichment_error_message: errorMessage,
  _metadata: {
    processing_stage: 'enrichment_fallback',
    severity: 'medium',
    error_message: errorMessage,
    failed_node: 'HTTP Enrich Lead',
  },
};
"""

MERGE_SCORING_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const lead =
  safeNodeJson('Merge Enrichment Result') ??
  safeNodeJson('Handle Enrichment Failure') ??
  safeNodeJson('Domain Enrichment') ??
  {};
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

CHECK_SALES_MEMO_ELIGIBLE_JS = r"""
const item = $input.item.json;
const config = item.global_config || {};
const minScore = Number(config.sales_memo_min_score ?? 80);
const score = Number(item.score || 0);
const action = item.recommended_action || '';
const eligible = score >= minScore && action !== 'reject';
return {
  ...item,
  sales_memo_eligible: eligible,
  _metadata: { processing_stage: eligible ? 'sales_memo_gate_pass' : 'sales_memo_gate_skip' },
};
"""

MERGE_SALES_MEMO_JS = r"""
const lead = $('Check Sales Memo Eligible').item.json;
const ai = $input.item.json;
return {
  ...lead,
  sales_memo: JSON.stringify(ai),
  sales_memo_status: 'complete',
  updated_at: new Date().toISOString(),
  _metadata: { processing_stage: 'sales_memo_merged' },
};
"""

SKIP_SALES_MEMO_JS = r"""
const item = $input.item.json;
return {
  ...item,
  sales_memo: '',
  sales_memo_status: 'skipped_low_score',
  updated_at: new Date().toISOString(),
  _metadata: { processing_stage: 'sales_memo_skipped' },
};
"""

HANDLE_SALES_MEMO_FAILURE_JS = error_message_prelude("Unknown HTTP Sales Memo error") + r"""
const lead = $('Check Sales Memo Eligible').item.json;
const fallbackMemo = {
  company_background: [],
  talking_points: [],
  pain_hypotheses: [],
  recommended_opener: (lead.content_summary || 'Review lead summary before outreach.').slice(0, 300),
  fallback_used: true,
};
return {
  ...lead,
  sales_memo: JSON.stringify(fallbackMemo),
  sales_memo_status: 'failed',
  sales_memo_error_message: errorMessage,
  updated_at: new Date().toISOString(),
  _metadata: {
    processing_stage: 'sales_memo_fallback',
    severity: 'medium',
    error_message: errorMessage,
    failed_node: 'HTTP Sales Memo',
  },
};
"""

HANDLE_AI_SCORE_FAILURE_JS = error_message_prelude("Unknown HTTP Score Lead error") + r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const lead =
  safeNodeJson('Merge Enrichment Result') ??
  safeNodeJson('Handle Enrichment Failure') ??
  safeNodeJson('Domain Enrichment') ??
  {};
return {
  ...lead,
  score: 0,
  score_reasoning: 'AI scoring failed',
  confidence: 'low',
  recommended_action: 'manual_review',
  routing_decision: 'fallback_manual_review',
  fallback_used: true,
  sales_memo: '',
  sales_memo_status: 'skipped_low_score',
  processing_status: 'scoring',
  scoring_error_message: errorMessage,
  _metadata: {
    processing_stage: 'scoring_fallback',
    severity: 'high',
    error_message: errorMessage,
    failed_node: 'HTTP Score Lead',
  },
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

MERGE_MANUAL_REVIEW_JS = r"""
const lead = $('Apply Review Rules').item.json;
const ai = $input.item.json || {};
const explanation = ai.review_explanation || '';
const questions = Array.isArray(ai.suggested_questions) ? ai.suggested_questions.join('; ') : '';
const risks = Array.isArray(ai.risk_flags) ? ai.risk_flags.join(', ') : '';
const notes = [
  explanation,
  questions ? `Questions: ${questions}` : '',
  risks ? `Risks: ${risks}` : '',
].filter(Boolean).join('\n');

return {
  ...lead,
  review_notes: notes,
  _metadata: { processing_stage: 'manual_review_merged' },
};
"""

SKIP_MANUAL_REVIEW_JS = r"""
const lead = $('Apply Review Rules').item.json;
return { ...lead, _metadata: { processing_stage: 'manual_review_skipped' } };
"""

CHECK_ERROR_ALERT_ENABLED_JS = r"""
const mode = ($('Read config_main').all().find(r => r.json.key === 'mode') || {}).json?.value || 'test';
const rules = $('Read config_notifications').all().map(r => r.json);
const rule = rules.find(r => r.event_type === 'error_alert');
const enabled = rule && (rule.enabled === true || rule.enabled === 'true');
return {
  ...$('Extract Error Details').item.json,
  should_alert_slack: String(mode).toLowerCase() === 'production' && enabled,
};
"""

VERIFY_TALLY_SIGNATURE_JS = r"""
const crypto = require('crypto');
const item = $input.item;
const json = item.json || {};
const headers = json.headers || {};
const secret = $env.TALLY_WEBHOOK_SIGNING_KEY || '';

const sigHeader =
  headers['tally-signature'] ||
  headers['Tally-Signature'] ||
  '';

const rawBody =
  json.rawBody ||
  (typeof json.body === 'string' ? json.body : JSON.stringify(json.body ?? json));

function verify(secret, header, payload) {
  // Empty env key: skip verification (dev/demo only). Calendly Intake uses the same pattern.
  if (!secret) return { valid: true, skipped: true, reason: 'verification_skipped' };
  if (!header) return { valid: false, reason: 'missing_signature' };

  const calc = crypto.createHmac('sha256', secret).update(payload).digest('base64');
  if (header === calc) return { valid: true };

  const parts = {};
  for (const part of String(header).split(',')) {
    const eq = part.indexOf('=');
    if (eq > -1) parts[part.slice(0, eq).trim()] = part.slice(eq + 1).trim();
  }
  if (parts.t && parts.v1) {
    const base = `t=${parts.t}.${payload}`;
    const calc2 = crypto.createHmac('sha256', secret).update(base).digest('hex');
    if (calc2 === parts.v1) return { valid: true };
  }
  return { valid: false, reason: 'signature_mismatch' };
}

const result = verify(secret, sigHeader, rawBody);
return { ...json, tally_signature_valid: result.valid, tally_verify: result };
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
const skipNotification = item.skip_notification === true || item.trigger_source === 'slack_action';
return {
  ...item,
  crm_gate_passed: canSync,
  crm_status: canSync ? 'pending' : (mode === 'production' ? 'skipped_gate' : 'skipped_test_mode'),
  skip_notification: skipNotification,
  _metadata: { processing_stage: 'crm_gate' },
};
"""

CHECK_FIRST_TOUCH_ELIGIBLE_JS = r"""
const item = $input.item.json;
const config = item.global_config || {};
const mode = String(config.mode || 'test').toLowerCase();
const minScore = Number(config.first_touch_min_score ?? config.sales_memo_min_score ?? 80);
const score = Number(item.score || 0);
const action = item.recommended_action || '';
const domainType = item.domain_type || '';
const existingStatus = item.first_touch_status || '';
const crmStatus = item.crm_status || '';
const reviewStatus = item.review_status || '';
const triggerSource = item.trigger_source || '';

const notificationRules = config.notification_rules || [];
const firstTouchRule = notificationRules.find((r) => r.event_type === 'first_touch_email');
const enabled = firstTouchRule && (firstTouchRule.enabled === true || firstTouchRule.enabled === 'true');
const channels = String((firstTouchRule && firstTouchRule.channels) || 'email').split(',').map(s => s.trim()).filter(Boolean);
const emailChannelEnabled = channels.includes('email');

const baseEligible =
  mode === 'production' &&
  enabled && emailChannelEnabled &&
  crmStatus === 'synced' &&
  action === 'crm_sync' &&
  score >= minScore &&
  domainType !== 'personal' &&
  !!item.crm_contact_id;

const shouldDraft =
  baseEligible &&
  !['draft_pending_review', 'approved_to_send', 'sent'].includes(existingStatus);

const shouldSendAfterApproval =
  baseEligible &&
  triggerSource === 'slack_action' &&
  reviewStatus === 'approved' &&
  existingStatus === 'draft_pending_review';

let first_touch_phase = 'skip';
let skipReason = '';

if (mode !== 'production') skipReason = 'test_mode';
else if (!enabled || !emailChannelEnabled) skipReason = 'disabled';
else if (crmStatus !== 'synced') skipReason = 'crm_not_synced';
else if (action !== 'crm_sync') skipReason = 'action_not_crm_sync';
else if (score < minScore) skipReason = 'low_score';
else if (domainType === 'personal') skipReason = 'personal_email';
else if (existingStatus === 'sent') skipReason = 'already_sent';
else if (!item.crm_contact_id) skipReason = 'no_contact_id';
else if (shouldSendAfterApproval) first_touch_phase = 'send';
else if (shouldDraft) first_touch_phase = 'draft';
else if (existingStatus === 'draft_pending_review') skipReason = 'awaiting_human_review';
else skipReason = 'not_eligible';

return {
  ...item,
  first_touch_phase,
  first_touch_eligible: first_touch_phase !== 'skip',
  first_touch_skip_reason: skipReason,
  first_touch_min_score: minScore,
  first_touch_sender_name: config.first_touch_sender_name || 'Your Team',
  _metadata: { processing_stage: first_touch_phase === 'skip' ? 'first_touch_gate_skip' : `first_touch_${first_touch_phase}` },
};
"""

MERGE_OUTBOUND_EMAIL_JS = r"""
const lead = $('Check First Touch Eligible').item.json;
const ai = $input.item.json;
return {
  ...lead,
  outbound_email_subject: ai.subject || '',
  outbound_email_body: ai.body || '',
  outbound_email_personalization_notes: ai.personalization_notes || '',
  outbound_email_fallback_used: ai.fallback_used === true,
  _metadata: { processing_stage: 'outbound_email_drafted' },
};
"""

HANDLE_OUTBOUND_EMAIL_FAILURE_JS = error_message_prelude("Unknown Outbound Email LLM error") + r"""
const lead = $('Check First Touch Eligible').item.json;
const config = lead.global_config || {};
const company = lead.company_name || 'your team';
const firstName = (lead.contact_name || '').split(' ')[0] || 'there';
let opener = lead.content_summary || 'I noticed your recent inquiry and wanted to reach out.';

try {
  const memo = typeof lead.sales_memo === 'string' ? JSON.parse(lead.sales_memo || '{}') : (lead.sales_memo || {});
  if (memo.recommended_opener) opener = memo.recommended_opener;
} catch {}

const calendlyUrl = config.calendly_url || '';
const cta = calendlyUrl
  ? `\n\nWould you be open to a quick chat? ${calendlyUrl}`
  : '\n\nWould you be open to a quick reply?';
const body = `Hi ${firstName},\n\n${opener}\n\nI'd love to learn more about what ${company} is working on and share how we might help.${cta}\n\nBest regards`;

return {
  ...lead,
  outbound_email_subject: `Quick note for ${company}`.slice(0, 60),
  outbound_email_body: body,
  outbound_email_personalization_notes: 'Fallback draft after LLM failure',
  outbound_email_fallback_used: true,
  outbound_email_error_message: errorMessage,
  _metadata: {
    processing_stage: 'outbound_email_fallback',
    severity: 'medium',
    error_message: errorMessage,
    failed_node: 'HTTP Outbound Email',
  },
};
"""

MARK_FIRST_TOUCH_SENT_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

// HubSpot Log Outbound Email returns the engagement object — do NOT spread it as the lead.
const hs = $input.item.json || {};
const lead =
  safeNodeJson('Load Draft From Lead') ||
  safeNodeJson('Check First Touch Eligible') ||
  {};
const now = new Date().toISOString();
const engagementId =
  hs.id ||
  (hs.properties && (hs.properties.hs_object_id || hs.properties.hs_object_id?.value)) ||
  '';

return {
  ...lead,
  first_touch_status: 'approved_to_send',
  first_touch_channel: 'email',
  first_touch_at: now,
  first_touch_error: '',
  hubspot_email_engagement_id: engagementId != null && engagementId !== '' ? String(engagementId) : '',
  _metadata: { processing_stage: 'first_touch_approved_to_send' },
};
"""

MARK_DRAFT_PENDING_REVIEW_JS = r"""
const lead = $input.item.json;
const now = new Date().toISOString();
return {
  ...lead,
  first_touch_status: 'draft_pending_review',
  first_touch_channel: 'email',
  first_touch_at: now,
  first_touch_error: '',
  outbound_email_subject: lead.outbound_email_subject || '',
  outbound_email_body: lead.outbound_email_body || '',
  _metadata: { processing_stage: 'first_touch_draft_pending_review' },
};
"""

LOAD_DRAFT_FROM_LEAD_JS = r"""
const item = $input.item.json;
return {
  ...item,
  outbound_email_subject: item.outbound_email_subject || '',
  outbound_email_body: item.outbound_email_body || '',
  _metadata: { processing_stage: 'first_touch_send_loaded_draft' },
};
"""

SKIP_FIRST_TOUCH_JS = r"""
const lead = $('Check First Touch Eligible').item.json;
const skipReason = lead.first_touch_skip_reason || 'unknown';
const statusMap = {
  test_mode: 'skipped_test_mode',
  disabled: 'skipped_disabled',
  crm_not_synced: 'skipped_no_crm',
  pending_review: 'skipped_pending_review',
  action_not_crm_sync: 'skipped_action',
  low_score: 'skipped_low_score',
  personal_email: 'skipped_personal',
  already_sent: 'skipped_already_sent',
  no_contact_id: 'skipped_no_crm',
  awaiting_human_review: 'draft_pending_review',
};
return {
  ...lead,
  first_touch_status: statusMap[skipReason] || 'skipped',
  first_touch_channel: '',
  first_touch_at: '',
  first_touch_error: '',
  _metadata: { processing_stage: 'first_touch_skipped' },
};
"""

HANDLE_FIRST_TOUCH_SEND_FAILURE_JS = error_message_prelude("Unknown HubSpot Outbound Email error") + r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const lead =
  safeNodeJson('Merge Outbound Email') ||
  safeNodeJson('Handle Outbound Email Failure') ||
  safeNodeJson('Check First Touch Eligible') ||
  {};
return {
  ...lead,
  first_touch_status: 'failed',
  first_touch_channel: 'email',
  first_touch_at: new Date().toISOString(),
  first_touch_error: errorMessage,
  _metadata: {
    processing_stage: 'first_touch_failed',
    severity: 'high',
    error_message: errorMessage,
    failed_node: 'HubSpot Log Outbound Email',
  },
};
"""

LOG_FIRST_TOUCH_SLACK_ALERT_JS = error_message_prelude("Unknown First Touch Slack Alert error") + r"""
const lead = $('Handle First Touch Send Failure').item.json;
return {
  ...lead,
  first_touch_slack_alert_failed: true,
  first_touch_slack_error_message: errorMessage,
  _metadata: {
    processing_stage: 'first_touch_slack_alert_failed',
    severity: 'low',
    error_message: errorMessage,
    failed_node: 'Slack First Touch Alert',
  },
};
"""

PREPARE_FIRST_TOUCH_AUDIT_JS = r"""
const item = $input.item.json;
const status = item.first_touch_status || 'unknown';
const auditByStatus = {
  sent: 'first_touch_email_sent',
  failed: 'first_touch_email_failed',
  skipped_test_mode: 'first_touch_email_skipped_test',
  skipped_disabled: 'first_touch_email_disabled',
  skipped_no_crm: 'first_touch_email_skipped_no_crm',
  skipped_pending_review: 'first_touch_email_skipped_review',
  skipped_action: 'first_touch_email_skipped_action',
  skipped_low_score: 'first_touch_email_skipped_low_score',
  skipped_personal: 'first_touch_email_skipped_personal',
  skipped_already_sent: 'first_touch_email_skipped_duplicate',
  skipped: 'first_touch_email_skipped',
  draft_pending_review: 'first_touch_email_draft_pending',
  approved_to_send: 'first_touch_email_approved',
};
return {
  ...item,
  audit_event: auditByStatus[status] || 'first_touch_email_unknown',
  first_touch_status: status,
  first_touch_channel: item.first_touch_channel || '',
  first_touch_at: item.first_touch_at || '',
  first_touch_error: item.first_touch_error || '',
  outbound_email_subject: item.outbound_email_subject || '',
  updated_at: item.updated_at || item.first_touch_at || new Date().toISOString(),
  _metadata: { processing_stage: 'first_touch_audit_prepared' },
};
"""

PREPARE_SLACK_CRM_PAYLOAD_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

function rowsFrom(name) {
  const wrap = safeNodeJson(name) || {};
  return (wrap.rows || []).filter(Boolean);
}

const matched = safeNodeJson('Match Lead By ID') || {};
let leadRows = [];
try {
  leadRows = $('Read All Leads For Slack').all().map((row) => row.json).filter((row) => row.lead_id);
} catch {
  leadRows = [];
}
const lead = leadRows.find((row) => String(row.lead_id || '').trim() === String(matched.lead_id || '').trim()) || matched;

const mainRows = rowsFrom('Normalize config_main For CRM');
const notificationRows = rowsFrom('Normalize config_notifications For CRM');

const configMap = {};
for (const row of mainRows) {
  if (row.key) configMap[row.key] = row.value;
}

const actionId = matched.action_id || '';
const reviewStatus = matched.review_status || lead.review_status || '';
const recommendedAction = matched.recommended_action || lead.recommended_action || '';

// Must mirror Enrichment's global_config shape enough for CRM Gate + First Touch
// (mode alone → first_touch_email rule missing → phase=skip / disabled).
const global_config = {
  mode: String(configMap.mode || 'test').toLowerCase(),
  first_touch_min_score: parseInt(
    configMap.first_touch_min_score || configMap.sales_memo_min_score || configMap.score_threshold_high || '80',
    10,
  ),
  first_touch_sender_name: configMap.first_touch_sender_name || 'Your Team',
  calendly_url: configMap.calendly_url || '',
  notification_rules: notificationRows.filter((r) => r.event_type),
};

return {
  lead_id: lead.lead_id,
  correlation_id: matched.correlation_id || lead.correlation_id || '',
  contact_email: (lead.contact_email || '').toLowerCase().trim(),
  contact_name: lead.contact_name || '',
  contact_role: lead.contact_role || '',
  company_name: lead.company_name || '',
  company_domain: lead.company_domain || '',
  domain_type: lead.domain_type || '',
  score: lead.score,
  score_reasoning: lead.score_reasoning || '',
  outbound_email_subject: lead.outbound_email_subject || '',
  outbound_email_body: lead.outbound_email_body || '',
  first_touch_status: lead.first_touch_status || '',
  notification_status: lead.notification_status || '',
  crm_status: lead.crm_status != null && lead.crm_status !== '' ? String(lead.crm_status) : '',
  crm_contact_id:
    lead.crm_contact_id != null && lead.crm_contact_id !== ''
      ? String(lead.crm_contact_id)
      : '',
  review_status: reviewStatus,
  recommended_action: recommendedAction,
  routing_decision: lead.routing_decision || `slack_action_${actionId}`,
  processing_status:
    matched.lead_stage === 'sql' ? 'completed' : (lead.processing_status || 'review_pending'),
  global_config,
  confidence: lead.confidence,
  industry: lead.industry || '',
  company_size: lead.company_size || '',
  content_summary: lead.content_summary || '',
  intent_signals: lead.intent_signals || '',
  enrichment_summary: lead.enrichment_summary || '',
  enrichment_status: lead.enrichment_status || '',
  sales_memo: lead.sales_memo || '',
  sales_memo_status: lead.sales_memo_status || '',
  source_type: lead.source_type || '',
  source_name: lead.source_name || '',
  company_region: lead.company_region || '',
  skip_notification: true,
  trigger_source: 'slack_action',
  slack_action_id: actionId,
  _metadata: { processing_stage: 'slack_crm_payload_ready' },
};
"""

NOTIFICATION_PAYLOAD_JS = r"""
const item = $input.item.json;
const mode = (item.global_config || {}).mode || 'test';
const score = Number(item.score || 0);

function displayValue(value) {
  if (value == null || value === '') return 'N/A';
  return String(value);
}

function escapeMrkdwn(text) {
  return String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function truncate(text, maxLen) {
  const value = String(text || '');
  if (value.length <= maxLen) return value;
  return value.slice(0, maxLen - 1) + '…';
}

function formatIntentSignals(raw) {
  try {
    const signals = typeof raw === 'string' ? JSON.parse(raw || '[]') : (raw || []);
    if (Array.isArray(signals) && signals.length) return signals.join(', ');
  } catch {}
  return 'N/A';
}

function formatSalesMemo(raw, status) {
  if (status === 'skipped_low_score') return 'Skipped (score below threshold)';
  if (!raw || raw === '') return 'N/A';
  try {
    const memo = typeof raw === 'string' ? JSON.parse(raw) : raw;
    const lines = ['--- AI Sales Memo ---'];
    if (Array.isArray(memo.company_background) && memo.company_background.length) {
      lines.push('Background: ' + memo.company_background.join('; '));
    }
    if (Array.isArray(memo.talking_points) && memo.talking_points.length) {
      lines.push('Talking points: ' + memo.talking_points.join('; '));
    }
    if (Array.isArray(memo.pain_hypotheses) && memo.pain_hypotheses.length) {
      lines.push('Pain hypotheses: ' + memo.pain_hypotheses.join('; '));
    }
    if (memo.recommended_opener) {
      lines.push('Opener: ' + memo.recommended_opener);
    }
    if (lines.length > 1) return lines.join('\n');
  } catch {}
  return displayValue(raw);
}

function quoteMrkdwn(text, maxLen) {
  const body = truncate(text, maxLen);
  return body.split('\n').map((line) => '>' + line).join('\n');
}

function headerEmoji(eventType, score) {
  if (eventType === 'review_required') return '⚠️';
  if (eventType === 'low_score') return '🔴';
  if (score >= 80) return '🟢';
  return '🔵';
}

function buildSalesMemoBlocks(raw, status) {
  const blocks = [];
  if (status === 'skipped_low_score') {
    blocks.push({
      type: 'section',
      text: { type: 'mrkdwn', text: '🤖 *AI Sales Memo*\n_Skipped (score below threshold)_' },
    });
    return blocks;
  }
  if (!raw || raw === '') {
    blocks.push({
      type: 'section',
      text: { type: 'mrkdwn', text: '🤖 *AI Sales Memo*\n_N/A_' },
    });
    return blocks;
  }

  try {
    const memo = typeof raw === 'string' ? JSON.parse(raw) : raw;
    blocks.push({
      type: 'section',
      text: { type: 'mrkdwn', text: '🤖 *AI Sales Memo*' },
    });

    function bulletSection(title, items, maxItems = 2) {
      if (!Array.isArray(items) || !items.length) return;
      const shown = items.slice(0, maxItems);
      const lines = shown.map((bullet) => '• ' + escapeMrkdwn(bullet));
      if (items.length > maxItems) {
        lines.push('_…+' + (items.length - maxItems) + ' more_');
      }
      blocks.push({
        type: 'section',
        text: { type: 'mrkdwn', text: '*' + title + '*\n' + lines.join('\n') },
      });
    }

    bulletSection('Background', memo.company_background);
    bulletSection('Talking points', memo.talking_points);
    bulletSection('Pain hypotheses', memo.pain_hypotheses);

    if (memo.recommended_opener) {
      blocks.push({
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: '*💬 Recommended opener*\n' + quoteMrkdwn(escapeMrkdwn(memo.recommended_opener), 350),
        },
      });
    }
  } catch {
    blocks.push({
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: '🤖 *AI Sales Memo*\n' + escapeMrkdwn(truncate(displayValue(raw), 300)),
      },
    });
  }
  return blocks;
}

function buildSlackBlocks(ctx) {
  const actionValue = truncate(JSON.stringify({
    lead_id: ctx.lead_id,
    correlation_id: ctx.correlation_id,
  }), 2000);

  const blocks = [
    {
      type: 'header',
      text: {
        type: 'plain_text',
        text: truncate(
          `${headerEmoji(ctx.event_type, ctx.score)} Score ${ctx.score} · ${ctx.headerLabel}`,
          150,
        ),
        emoji: true,
      },
    },
    {
      type: 'section',
      fields: [
        { type: 'mrkdwn', text: '👤 *Name*\n' + escapeMrkdwn(ctx.contactName) },
        { type: 'mrkdwn', text: '📧 *Email*\n' + escapeMrkdwn(ctx.contactEmail) },
        { type: 'mrkdwn', text: '🏢 *Company*\n' + escapeMrkdwn(ctx.companyName) },
        { type: 'mrkdwn', text: '📊 *Source*\n' + escapeMrkdwn(ctx.sourceDisplay) },
      ],
    },
    { type: 'divider' },
    {
      type: 'section',
      fields: [
        { type: 'mrkdwn', text: '🏭 *Industry*\n' + escapeMrkdwn(ctx.industry) },
        { type: 'mrkdwn', text: '📏 *Size*\n' + escapeMrkdwn(ctx.companySize) },
        { type: 'mrkdwn', text: '🌍 *Region*\n' + escapeMrkdwn(ctx.companyRegion) },
        { type: 'mrkdwn', text: '🎯 *Signals*\n' + escapeMrkdwn(truncate(ctx.intentSignalsDisplay, 120)) },
      ],
    },
  ];

  if (ctx.contentSummary && ctx.contentSummary !== 'N/A') {
    blocks.push({
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: '📝 *Intent summary*\n' + quoteMrkdwn(escapeMrkdwn(ctx.contentSummary), 380),
      },
    });
  }

  if (ctx.enrichmentSummary && ctx.enrichmentSummary !== 'N/A') {
    blocks.push({
      type: 'context',
      elements: [{
        type: 'mrkdwn',
        text: '🔍 _' + escapeMrkdwn(truncate(ctx.enrichmentSummary, 200)) + '_',
      }],
    });
  }

  blocks.push({ type: 'divider' });
  blocks.push(...buildSalesMemoBlocks(ctx.salesMemoRaw, ctx.salesMemoStatus));

  blocks.push({
    type: 'actions',
    block_id: 'lead_actions_' + String(ctx.lead_id || 'unknown').slice(0, 20),
    elements: [
      {
        type: 'button',
        text: { type: 'plain_text', text: 'Assign', emoji: true },
        action_id: 'assign_lead',
        value: actionValue,
        style: 'primary',
      },
      {
        type: 'button',
        text: { type: 'plain_text', text: 'Mark Junk', emoji: true },
        action_id: 'mark_junk',
        value: actionValue,
        style: 'danger',
      },
      {
        type: 'button',
        text: { type: 'plain_text', text: 'Nurture', emoji: true },
        action_id: 'nurture_lead',
        value: actionValue,
      },
    ],
  });

  if (ctx.calendlyUrl) {
    blocks.push({
      type: 'context',
      elements: [{
        type: 'mrkdwn',
        text: '📅 <' + ctx.calendlyUrl + '|Book a meeting>',
      }],
    });
  }

  blocks.push({
    type: 'context',
    elements: [{
      type: 'mrkdwn',
      text: 'Correlation: `' + escapeMrkdwn(ctx.correlationId) + '` · Action: `' + escapeMrkdwn(ctx.recommendedAction) + '`',
    }],
  });

  return { blocks };
}

const industry = displayValue(item.industry);
const companySize = displayValue(item.company_size);
const companyRegion = displayValue(item.company_region);
const contentSummary = displayValue(item.content_summary);
const intentSignalsDisplay = formatIntentSignals(item.intent_signals);
const enrichmentSummary = displayValue(item.enrichment_summary);
const salesMemoBlock = formatSalesMemo(item.sales_memo, item.sales_memo_status);
const sourceDisplay = [displayValue(item.source_type), displayValue(item.source_name)]
  .filter((value) => value !== 'N/A')
  .join(' / ') || 'N/A';
const calendlyUrl = (item.global_config || {}).calendly_url || '';

let event_type = 'high_score_lead';
if (item.review_status === 'pending_review') event_type = 'review_required';
if (item.recommended_action === 'reject') event_type = 'low_score';

let headerLabel = 'New high-score lead';
if (event_type === 'review_required') headerLabel = 'Review required';
if (event_type === 'low_score') headerLabel = 'Low-score lead';

const headline = `${item.company_name || 'Unknown'} — ${item.contact_name || ''} (${item.contact_email}) — Score: ${score}`;
const profileBlock = [
  '--- Lead Profile ---',
  `Industry: ${industry}`,
  `Size: ${companySize}`,
  `Region: ${companyRegion}`,
  `Summary: ${contentSummary}`,
  `Signals: ${intentSignalsDisplay}`,
  `Enrichment: ${enrichmentSummary}`,
  salesMemoBlock,
].join('\n');

const fallbackMessage = [
  event_type === 'review_required' ? 'Lead needs manual review' : 'New high-score B2B lead',
  headline,
  profileBlock,
  `Action: ${displayValue(item.recommended_action)}`,
  `Correlation: ${displayValue(item.correlation_id)}`,
  calendlyUrl ? `Book: ${calendlyUrl}` : '',
].filter(Boolean).join('\n');

let slack_blocks = { blocks: [] };
let slack_blocks_valid = false;
let slack_blocks_degraded = false;

try {
  slack_blocks = buildSlackBlocks({
    lead_id: item.lead_id,
    correlation_id: item.correlation_id,
    correlationId: displayValue(item.correlation_id),
    recommendedAction: displayValue(item.recommended_action),
    contactName: displayValue(item.contact_name),
    contactEmail: displayValue(item.contact_email),
    companyName: displayValue(item.company_name),
    sourceDisplay,
    score,
    event_type,
    headerLabel,
    industry,
    companySize,
    companyRegion,
    contentSummary,
    intentSignalsDisplay,
    enrichmentSummary,
    salesMemoRaw: item.sales_memo,
    salesMemoStatus: item.sales_memo_status,
    calendlyUrl,
  });
  slack_blocks_valid = Array.isArray(slack_blocks.blocks) && slack_blocks.blocks.length > 0;
} catch (error) {
  slack_blocks_degraded = true;
  slack_blocks_valid = false;
}

const payload = {
  event_type,
  severity: event_type === 'review_required' ? 'warning' : 'info',
  title: event_type === 'review_required' ? 'Lead needs manual review' : 'New high-score B2B lead',
  message: fallbackMessage,
  lead_id: item.lead_id,
  correlation_id: item.correlation_id,
  channels: ['slack'],
  slack_blocks,
  slack_blocks_valid,
  slack_blocks_degraded,
  metadata: {
    score,
    company_name: item.company_name,
    recommended_action: item.recommended_action,
    calendly_url: calendlyUrl,
    industry,
    company_size: companySize,
    company_region: companyRegion,
    content_summary: contentSummary,
    intent_signals: intentSignalsDisplay,
    enrichment_summary: enrichmentSummary,
    sales_memo_status: item.sales_memo_status || '',
    source_type: displayValue(item.source_type),
    source_name: displayValue(item.source_name),
  },
  notification_mode: mode,
  _metadata: { processing_stage: 'notification_enrichment_attached' },
};
const skipNotification = item.skip_notification === true;

const rules = (item.global_config || {}).notification_rules || [];
const eventType =
  item.review_status === 'pending_review' ? 'review_required' : 'high_score_lead';
const rule = rules.find((r) => r.event_type === eventType);
const ruleEnabled = rule && (rule.enabled === true || rule.enabled === 'true');

const shouldSendSlack =
  mode === 'production' &&
  !skipNotification &&
  item.recommended_action !== 'reject' &&
  ruleEnabled;
return {
  ...item,
  skip_notification: skipNotification,
  should_send_slack: shouldSendSlack,
  notification: payload,
};
"""

SKIP_NOTIFICATION_TEST_JS = r"""
const item = $input.item.json;
const mode = String((item.global_config || {}).mode || 'test').toLowerCase();
const isReject = item.recommended_action === 'reject';
const skipResend = item.skip_notification === true;
const prior = item.notification_status || '';

let notification_status;
let processing_stage;

// Assign / post-assign re-entry: do not pretend we are in test mode, and keep prior "sent".
if (skipResend) {
  notification_status = prior === 'sent' ? 'sent' : (prior || 'skipped_no_resend');
  processing_stage = 'notification_skipped_slack_action';
} else if (mode !== 'production') {
  notification_status = 'skipped_test_mode';
  processing_stage = 'notification_skipped_test';
} else if (isReject) {
  notification_status = 'skipped';
  processing_stage = 'notification_skipped_reject';
} else {
  notification_status = 'skipped';
  processing_stage = 'notification_skipped';
}

return {
  ...item,
  notification_status,
  _metadata: { processing_stage },
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

LOAD_DAILY_CONFIG_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

function loadWrapper(normalizeName, handleName, table) {
  const ok = safeNodeJson(normalizeName);
  if (ok) return ok;
  const err = safeNodeJson(handleName);
  if (err) return err;
  return {
    config_table: table,
    rows: [],
    load_failed: true,
    load_error_message: 'Config wrapper not executed',
  };
}

const mainWrap = loadWrapper('Normalize config_main', 'Handle config_main Read Error', 'config_main');
const notificationWrap = loadWrapper(
  'Normalize config_notifications',
  'Handle config_notifications Read Error',
  'config_notifications',
);

const mainRows = (mainWrap.rows || []).filter(r => r.key);
const notificationRows = (notificationWrap.rows || []).filter(r => r.event_type);

const kv = {};
for (const row of mainRows) {
  if (row.key) kv[row.key] = row.value;
}

const dailyRule = notificationRows.find(r => r.event_type === 'daily_summary') || {};
const dailyEnabled = dailyRule.enabled === true || dailyRule.enabled === 'true';

const failedTables = [mainWrap, notificationWrap]
  .filter(w => w.load_failed)
  .map(w => w.config_table);

return {
  mode: (kv.mode || 'test').toLowerCase(),
  score_threshold_high: parseInt(kv.score_threshold_high || '80', 10),
  daily_summary_enabled: dailyEnabled,
  config_load_failed: failedTables.length > 0,
  config_failed_tables: failedTables,
  _metadata: { processing_stage: 'daily_config_loaded' },
};
"""

# Aggregates yesterday UTC 00:00–24:00 (not "today so far"). Sets daily_gate_passed for Slack.
DAILY_SUMMARY_JS = r"""
function safeNodeAll(name) {
  try {
    return $(name).all().map(i => i.json);
  } catch {
    return [];
  }
}

const config = $('Load Daily Config').first()?.json || {};
const leads = safeNodeAll('Read Leads For Summary').filter(r => r.lead_id);
const errors = safeNodeAll('Read Errors For Summary');
const yesterday = new Date();
yesterday.setUTCDate(yesterday.getUTCDate() - 1);
const reportDate = yesterday.toISOString().slice(0, 10);
const threshold = Number(config.score_threshold_high || 80);

const dayLeads = leads.filter(l => (l.created_at || '').startsWith(reportDate));
const highScore = dayLeads.filter(l => Number(l.score || 0) >= threshold);
const crmSynced = dayLeads.filter(l => l.crm_status === 'synced');
const notified = dayLeads.filter(l => l.notification_status === 'sent');
const reviewPending = dayLeads.filter(l => l.review_status === 'pending_review');
const reviewApproved = dayLeads.filter(l => l.review_status === 'approved');

const errorTypes = {};
for (const e of errors.filter(e => (e.timestamp || '').startsWith(reportDate))) {
  const key = (e.message || 'unknown').slice(0, 40);
  errorTypes[key] = (errorTypes[key] || 0) + 1;
}

const dailyEnabled = config.daily_summary_enabled === true;
const mode = (config.mode || 'test').toLowerCase();

return {
  date: reportDate,
  new_leads: dayLeads.length,
  high_score_leads: highScore.length,
  crm_success_rate: dayLeads.length ? (crmSynced.length / dayLeads.length * 100).toFixed(1) + '%' : 'N/A',
  slack_success_count: notified.length,
  review_pending: reviewPending.length,
  review_approved: reviewApproved.length,
  error_count: Object.values(errorTypes).reduce((a,b)=>a+b,0),
  error_types: errorTypes,
  score_threshold_high: threshold,
  mode,
  daily_summary_enabled: dailyEnabled,
  daily_gate_passed: mode === 'production' && dailyEnabled,
  _metadata: { processing_stage: 'daily_summary_built' },
};
"""

SKIP_DAILY_SLACK_JS = r"""
const summary = $input.item.json;
return {
  ...summary,
  slack_skipped: true,
  _metadata: { processing_stage: 'daily_slack_skipped_test_or_disabled' },
};
"""

LOAD_WEEKLY_CONFIG_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

function loadWrapper(normalizeName, handleName, table) {
  const ok = safeNodeJson(normalizeName);
  if (ok) return ok;
  const err = safeNodeJson(handleName);
  if (err) return err;
  return {
    config_table: table,
    rows: [],
    load_failed: true,
    load_error_message: 'Config wrapper not executed',
  };
}

const mainWrap = loadWrapper('Normalize config_main', 'Handle config_main Read Error', 'config_main');
const notificationWrap = loadWrapper(
  'Normalize config_notifications',
  'Handle config_notifications Read Error',
  'config_notifications',
);

const mainRows = (mainWrap.rows || []).filter(r => r.key);
const notificationRows = (notificationWrap.rows || []).filter(r => r.event_type);

const kv = {};
for (const row of mainRows) {
  if (row.key) kv[row.key] = row.value;
}

const weeklyRule = notificationRows.find(r => r.event_type === 'weekly_summary') || {};
const weeklyEnabled = weeklyRule.enabled === true || weeklyRule.enabled === 'true';

const failedTables = [mainWrap, notificationWrap]
  .filter(w => w.load_failed)
  .map(w => w.config_table);

return {
  mode: (kv.mode || 'test').toLowerCase(),
  score_threshold_high: parseInt(kv.score_threshold_high || '80', 10),
  weekly_summary_enabled: weeklyEnabled,
  config_load_failed: failedTables.length > 0,
  config_failed_tables: failedTables,
  _metadata: { processing_stage: 'weekly_config_loaded' },
};
"""

BUILD_WEEKLY_METRICS_JS = r"""
function safeNodeAll(name) {
  try {
    return $(name).all().map(i => i.json);
  } catch {
    return [];
  }
}

const config = $('Load Weekly Config').first()?.json || {};
const leads = safeNodeAll('Read Leads For Weekly').filter(r => r.lead_id);
const errors = safeNodeAll('Read Errors For Weekly');
const priorRows = safeNodeAll('Read Prior Weekly Metrics').filter(r => r.week_start);

const now = new Date();
const day = now.getUTCDay();
const diffToMonday = (day + 6) % 7;
const weekStart = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - diffToMonday));
const weekEnd = new Date(now);

const weekStartStr = weekStart.toISOString().slice(0, 10);
const weekEndStr = weekEnd.toISOString().slice(0, 10);

const inWeek = (ts) => {
  if (!ts) return false;
  const d = new Date(ts);
  return d >= weekStart && d <= weekEnd;
};

const threshold = Number(config.score_threshold_high || 80);
const weekLeads = leads.filter(l => inWeek(l.created_at));
const scores = weekLeads.map(l => Number(l.score || 0)).filter(n => !Number.isNaN(n));
const highScore = weekLeads.filter(l => Number(l.score || 0) >= threshold);
const crmSynced = weekLeads.filter(l => l.crm_status === 'synced');
const notified = weekLeads.filter(l => l.notification_status === 'sent');
const reviewPending = weekLeads.filter(l => l.review_status === 'pending_review');
const reviewApproved = weekLeads.filter(l => l.review_status === 'approved');
const reviewRejected = weekLeads.filter(l => l.review_status === 'rejected');
const meetingsBooked = weekLeads.filter(l => l.meeting_status === 'booked');
const firstTouchSent = weekLeads.filter(l => l.first_touch_status === 'sent');

const avgScore = scores.length
  ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1)
  : 'N/A';

const crmSyncRate = weekLeads.length
  ? (crmSynced.length / weekLeads.length * 100).toFixed(1) + '%'
  : 'N/A';

const bookingRate = highScore.length
  ? (meetingsBooked.length / highScore.length * 100).toFixed(1) + '%'
  : 'N/A';

const errorTypes = {};
for (const e of errors.filter(e => inWeek(e.timestamp))) {
  const key = (e.message || 'unknown').slice(0, 40);
  errorTypes[key] = (errorTypes[key] || 0) + 1;
}

const groupCount = (rows, field) => {
  const out = {};
  for (const row of rows) {
    const key = (row[field] || 'unknown').toString().trim() || 'unknown';
    out[key] = (out[key] || 0) + 1;
  }
  return out;
};

const leadsBySource = groupCount(weekLeads, 'source_type');
const leadsByIndustry = groupCount(weekLeads, 'industry');
const leadsByStage = groupCount(weekLeads, 'lead_stage');

const funnel = {
  intake: weekLeads.length,
  enriched: weekLeads.filter(l => l.enrichment_status === 'complete').length,
  scored: weekLeads.filter(l => Number(l.score || 0) > 0).length,
  crm_synced: crmSynced.length,
  booked: meetingsBooked.length,
};

const priorWeekStart = new Date(weekStart);
priorWeekStart.setUTCDate(priorWeekStart.getUTCDate() - 7);
const priorWeekStartStr = priorWeekStart.toISOString().slice(0, 10);
const priorRow = priorRows
  .filter(r => r.week_start === priorWeekStartStr)
  .sort((a, b) => (b.generated_at || '').localeCompare(a.generated_at || ''))[0];

let priorWeekMetrics = {};
if (priorRow) {
  try {
    priorWeekMetrics = priorRow.metrics_json ? JSON.parse(priorRow.metrics_json) : { ...priorRow };
  } catch {
    priorWeekMetrics = { ...priorRow };
  }
}

const wowDelta = (key) => {
  if (!priorRow) return null;
  const current = Number(weekLeads.length && key === 'new_leads' ? weekLeads.length : 0);
  const map = {
    new_leads: weekLeads.length,
    high_score_leads: highScore.length,
    meetings_booked: meetingsBooked.length,
    slack_sent_count: notified.length,
    error_count: Object.values(errorTypes).reduce((a, b) => a + b, 0),
  };
  const c = Number(map[key] ?? 0);
  const p = Number(priorRow[key] ?? priorWeekMetrics[key] ?? 0);
  if (p === 0) return c > 0 ? 100 : 0;
  return Math.round(((c - p) / p) * 100);
};

const correlationId = 'weekly-' + weekStartStr + '-' + Math.random().toString(36).slice(2, 10);
const generatedAt = now.toISOString();

const metricsJson = {
  week_start: weekStartStr,
  week_end: weekEndStr,
  generated_at: generatedAt,
  new_leads: weekLeads.length,
  high_score_leads: highScore.length,
  avg_score: avgScore,
  crm_sync_rate: crmSyncRate,
  slack_sent_count: notified.length,
  review_pending: reviewPending.length,
  review_approved: reviewApproved.length,
  review_rejected: reviewRejected.length,
  meetings_booked: meetingsBooked.length,
  booking_rate: bookingRate,
  first_touch_sent: firstTouchSent.length,
  error_count: Object.values(errorTypes).reduce((a, b) => a + b, 0),
  error_types: errorTypes,
  leads_by_source: leadsBySource,
  leads_by_industry: leadsByIndustry,
  leads_by_lead_stage: leadsByStage,
  funnel,
  score_threshold_high: threshold,
  wow_delta: {
    new_leads: wowDelta('new_leads'),
    high_score_leads: wowDelta('high_score_leads'),
    meetings_booked: wowDelta('meetings_booked'),
    slack_sent_count: wowDelta('slack_sent_count'),
    error_count: wowDelta('error_count'),
  },
};

return {
  ...metricsJson,
  metrics_json: metricsJson,
  prior_week_metrics: priorWeekMetrics,
  prior_week_start: priorWeekStartStr,
  mode: config.mode || 'test',
  weekly_summary_enabled: config.weekly_summary_enabled === true,
  weekly_gate_passed:
    (config.mode || 'test') === 'production' && config.weekly_summary_enabled === true,
  correlation_id: correlationId,
  source_breakdown_json: JSON.stringify(leadsBySource),
  _metadata: { processing_stage: 'weekly_metrics_built' },
};
"""

HANDLE_WEEKLY_READ_ERROR_JS = error_message_prelude("Unknown Weekly Summary read error") + r"""

function safeNodeAll(name) {
  try {
    return $(name).all().map(i => i.json);
  } catch {
    return [];
  }
}

const leads = safeNodeAll('Read Leads For Weekly').filter(r => r.lead_id);
const now = new Date();
const day = now.getUTCDay();
const diffToMonday = (day + 6) % 7;
const weekStart = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - diffToMonday));
const weekStartStr = weekStart.toISOString().slice(0, 10);
const weekEndStr = now.toISOString().slice(0, 10);

const inWeek = (ts) => {
  if (!ts) return false;
  const d = new Date(ts);
  return d >= weekStart && d <= now;
};

const weekLeads = leads.filter(l => inWeek(l.created_at));
const correlationId = 'weekly-' + weekStartStr + '-' + Math.random().toString(36).slice(2, 10);

const metricsJson = {
  week_start: weekStartStr,
  week_end: weekEndStr,
  generated_at: now.toISOString(),
  new_leads: weekLeads.length,
  high_score_leads: weekLeads.filter(l => Number(l.score || 0) >= 80).length,
  avg_score: 'N/A',
  crm_sync_rate: weekLeads.length ? 'partial' : 'N/A',
  slack_sent_count: weekLeads.filter(l => l.notification_status === 'sent').length,
  review_pending: weekLeads.filter(l => l.review_status === 'pending_review').length,
  review_approved: weekLeads.filter(l => l.review_status === 'approved').length,
  review_rejected: weekLeads.filter(l => l.review_status === 'rejected').length,
  meetings_booked: weekLeads.filter(l => l.meeting_status === 'booked').length,
  booking_rate: 'N/A',
  first_touch_sent: weekLeads.filter(l => l.first_touch_status === 'sent').length,
  error_count: 0,
  error_types: {},
  leads_by_source: {},
  leads_by_industry: {},
  leads_by_lead_stage: {},
  funnel: { intake: weekLeads.length, enriched: 0, scored: 0, crm_synced: 0, booked: 0 },
};

return {
  ...metricsJson,
  metrics_json: metricsJson,
  prior_week_metrics: {},
  prior_week_start: '',
  mode: 'test',
  weekly_summary_enabled: false,
  weekly_gate_passed: false,
  correlation_id: correlationId,
  source_breakdown_json: '{}',
  _weekly_degraded: true,
  weekly_read_error_message: errorMessage,
  _metadata: {
    processing_stage: 'weekly_summary_read_failed',
    severity: 'medium',
    error_message: errorMessage,
    failed_node: 'Read Leads/Errors/Prior Weekly Metrics',
  },
};
"""

HANDLE_WEEKLY_AI_FAILURE_JS = error_message_prelude("Unknown HTTP Weekly Insights error") + r"""
const metrics = $('Build Weekly Metrics').first()?.json || $('Handle Weekly Read Error').first()?.json || {};

const summary =
  'Week ' + (metrics.week_start || '') + '–' + (metrics.week_end || '') + ': ' +
  (metrics.new_leads || 0) + ' new leads, ' +
  (metrics.high_score_leads || 0) + ' high-score, ' +
  (metrics.meetings_booked || 0) + ' meetings booked. Metrics-only summary (AI unavailable).';

const recommendations = [];
if ((metrics.high_score_leads || 0) > (metrics.meetings_booked || 0)) {
  recommendations.push('Follow up on high-score leads without bookings');
}
if ((metrics.review_pending || 0) > 0) {
  recommendations.push('Clear pending manual reviews');
}

return {
  executive_summary: summary,
  key_trends: [],
  recommendations,
  anomalies: (metrics.error_count || 0) > 5 ? ['Elevated error count: ' + metrics.error_count] : [],
  fallback_used: true,
  weekly_ai_error_message: errorMessage,
  _metadata: {
    processing_stage: 'weekly_ai_failed',
    severity: 'low',
    error_message: errorMessage,
    failed_node: 'HTTP Weekly Insights',
  },
};
"""

MERGE_WEEKLY_REPORT_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const metrics = safeNodeJson('Build Weekly Metrics') || safeNodeJson('Handle Weekly Read Error') || {};
const aiOk = safeNodeJson('HTTP Weekly Insights');
const aiFail = safeNodeJson('Handle Weekly AI Failure');

let insights = aiOk;
if (!insights || insights.executive_summary === undefined) {
  insights = aiFail || {
    executive_summary: 'AI insights unavailable',
    key_trends: [],
    recommendations: [],
    anomalies: [],
    fallback_used: true,
  };
}

const formatList = (items) => (items || []).map(i => '• ' + i).join('\n') || '—';
const formatWow = (delta) => {
  if (delta === null || delta === undefined) return '';
  const sign = delta > 0 ? '+' : '';
  return ' (' + sign + delta + '% WoW)';
};

const wow = metrics.wow_delta || {};
const sourceLines = Object.entries(metrics.leads_by_source || {})
  .map(([k, v]) => '- ' + k + ': ' + v)
  .join('\n') || '—';

const slackText =
  '📈 CRM Weekly Summary (' + metrics.week_start + ' – ' + metrics.week_end + ')\n\n' +
  'New leads: ' + metrics.new_leads + formatWow(wow.new_leads) + '\n' +
  'High score: ' + metrics.high_score_leads + formatWow(wow.high_score_leads) + '\n' +
  'Avg score: ' + metrics.avg_score + '\n' +
  'CRM sync rate: ' + metrics.crm_sync_rate + '\n' +
  'Meetings booked: ' + metrics.meetings_booked + ' (rate: ' + metrics.booking_rate + ')' + formatWow(wow.meetings_booked) + '\n' +
  'Slack sent: ' + metrics.slack_sent_count + '\n' +
  'Review pending / approved / rejected: ' + metrics.review_pending + ' / ' + metrics.review_approved + ' / ' + metrics.review_rejected + '\n' +
  'Errors: ' + metrics.error_count + '\n\n' +
  'By source:\n' + sourceLines + '\n\n' +
  'Funnel: intake ' + (metrics.funnel?.intake || 0) +
  ' → enriched ' + (metrics.funnel?.enriched || 0) +
  ' → scored ' + (metrics.funnel?.scored || 0) +
  ' → CRM ' + (metrics.funnel?.crm_synced || 0) +
  ' → booked ' + (metrics.funnel?.booked || 0) + '\n\n' +
  'AI Summary:\n' + (insights.executive_summary || '—') + '\n\n' +
  'Key trends:\n' + formatList(insights.key_trends) + '\n\n' +
  'Recommendations:\n' + formatList(insights.recommendations);

return {
  ...metrics,
  executive_summary: insights.executive_summary || '',
  key_trends: insights.key_trends || [],
  recommendations: insights.recommendations || [],
  anomalies: insights.anomalies || [],
  fallback_used: insights.fallback_used === true,
  ai_summary: insights.executive_summary || '',
  slack_text: slackText,
  _metadata: { processing_stage: 'weekly_report_merged' },
};
"""

LOG_SLACK_WEEKLY_ERROR_JS = error_message_prelude("Unknown Slack Weekly Report error") + r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const report = safeNodeJson('Merge Weekly Report') || safeNodeJson('Skip Weekly Slack') || {};
return {
  ...report,
  error_type: 'slack_weekly_failed',
  slack_error_message: errorMessage,
  _metadata: { processing_stage: 'slack_weekly_error_handled', severity: 'low', error_message: errorMessage },
};
"""

RESTORE_WEEKLY_REPORT_AFTER_SLACK_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const report = safeNodeJson('Merge Weekly Report') || {};
return {
  ...report,
  slack_sent: true,
  _metadata: { processing_stage: 'weekly_slack_sent' },
};
"""

SKIP_WEEKLY_SLACK_JS = r"""
const report = $input.item.json;
return {
  ...report,
  slack_skipped: true,
  _metadata: { processing_stage: 'weekly_slack_skipped_test_or_disabled' },
};
"""

HANDLE_APPEND_WEEKLY_METRICS_ERROR_JS = error_message_prelude("Unknown Append Weekly Metrics error") + r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

const report =
  safeNodeJson('Restore Weekly Report After Slack') ||
  safeNodeJson('Log Slack Weekly Error') ||
  safeNodeJson('Skip Weekly Slack') ||
  safeNodeJson('Merge Weekly Report') ||
  {};

return {
  ...report,
  weekly_metrics_append_failed: true,
  sheets_error_message: errorMessage,
  _metadata: {
    processing_stage: 'weekly_metrics_append_failed',
    severity: 'medium',
    error_message: errorMessage,
    failed_node: 'Append Weekly Metrics',
  },
};
"""

LOAD_BOOKING_CONFIG_JS = r"""
function safeNodeJson(name) {
  try {
    return $(name).first()?.json;
  } catch {
    return undefined;
  }
}

function loadWrapper(normalizeName, handleName, table) {
  const ok = safeNodeJson(normalizeName);
  if (ok) return ok;
  const err = safeNodeJson(handleName);
  if (err) return err;
  return {
    config_table: table,
    rows: [],
    load_failed: true,
    load_error_message: 'Config wrapper not executed',
  };
}

const mainWrap = loadWrapper('Normalize config_main', 'Handle config_main Read Error', 'config_main');
const notificationWrap = loadWrapper(
  'Normalize config_notifications',
  'Handle config_notifications Read Error',
  'config_notifications',
);

const mainRows = (mainWrap.rows || []).filter(r => r.key);
const notificationRows = (notificationWrap.rows || []).filter(r => r.event_type);

const kv = {};
for (const row of mainRows) {
  if (row.key) kv[row.key] = row.value;
}

const bookingRule =
  notificationRows.find(r => r.event_type === 'booking_reminder') || {};
const reminderEnabled =
  bookingRule.enabled === true || bookingRule.enabled === 'true';

const failedTables = [mainWrap, notificationWrap]
  .filter(w => w.load_failed)
  .map(w => w.config_table);

return {
  mode: (kv.mode || 'test').toLowerCase(),
  score_threshold_high: parseInt(kv.score_threshold_high || '80', 10),
  booking_reminder_hours: parseInt(kv.booking_reminder_hours || '24', 10),
  calendly_url: kv.calendly_url || '',
  booking_reminder_enabled: reminderEnabled,
  booking_reminder_channels: String(bookingRule.channels || 'slack')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean),
  booking_reminder_template_key: bookingRule.template_key || 'booking',
  config_load_failed: failedTables.length > 0,
  failed_tables: failedTables.join(','),
  _metadata: {
    processing_stage: failedTables.length
      ? 'booking_reminder_config_degraded'
      : 'booking_reminder_config_loaded',
  },
};
"""

FILTER_DUE_BOOKING_REMINDERS_JS = r"""
const leads = $('Read Leads For Reminder')
  .all()
  .map(i => i.json)
  .filter(r => r.lead_id);
const config = $('Load Booking Config').first()?.json ?? {};

const scoreMin = Number(config.score_threshold_high || 80);
const hours = Number(config.booking_reminder_hours || 24);
const cutoff = Date.now() - hours * 60 * 60 * 1000;

function reminderAlreadySent(value) {
  if (value === true || value === 'true' || value === 'TRUE' || value === '1') return true;
  return false;
}

const dueLeads = leads.filter(l => {
  const score = Number(l.score || 0);
  if (score < scoreMin) return false;
  const status = String(l.meeting_status || '').toLowerCase();
  if (status !== 'not_booked') return false;
  if (reminderAlreadySent(l.booking_reminder_sent)) return false;
  const created = Date.parse(l.created_at || '');
  if (!created || Number.isNaN(created) || created > cutoff) return false;
  return true;
});

return {
  ...config,
  due_leads: dueLeads,
  due_count: dueLeads.length,
  has_due_reminders: dueLeads.length > 0,
  _metadata: { processing_stage: 'booking_reminders_filtered' },
};
"""

EXPAND_DUE_BOOKING_LEADS_JS = r"""
const filtered = $('Filter Due Booking Reminders').first()?.json ?? {};
const dueLeads = filtered.due_leads || [];

return dueLeads.map(lead => ({
  json: {
    ...lead,
    mode: filtered.mode,
    calendly_url: filtered.calendly_url,
    booking_reminder_enabled: filtered.booking_reminder_enabled,
    booking_reminder_channels: filtered.booking_reminder_channels,
    booking_reminder_template_key: filtered.booking_reminder_template_key,
    score_threshold_high: filtered.score_threshold_high,
    booking_reminder_hours: filtered.booking_reminder_hours,
  },
}));
"""

BUILD_BOOKING_REMINDER_TEXT_JS = r"""
const item = $input.item.json;
const mode = String(item.mode || 'test').toLowerCase();
const channels = item.booking_reminder_channels || ['slack'];
const enabled = item.booking_reminder_enabled === true || item.booking_reminder_enabled === 'true';
const gatePassed = mode === 'production' && enabled && channels.includes('slack');

const name = item.contact_name || 'Unknown';
const email = item.contact_email || '';
const score = item.score != null && item.score !== '' ? item.score : 'N/A';
const createdAt = item.created_at || 'N/A';
const calendlyUrl = item.calendly_url || '';
const bookLine = calendlyUrl ? `Book: ${calendlyUrl}` : 'Book: (no Calendly URL configured)';

return {
  ...item,
  reminder_gate_passed: gatePassed,
  slack_text: [
    '⏰ Booking reminder — high-score lead has not booked',
    `Lead: ${name} (${email})`,
    `Score: ${score}`,
    `Created: ${createdAt}`,
    bookLine,
    `Correlation: ${item.correlation_id || 'N/A'}`,
  ].join('\n'),
  _metadata: { processing_stage: 'booking_reminder_prepared' },
};
"""

MARK_BOOKING_REMINDER_SENT_JS = r"""
const lead = $('Build Booking Reminder Text').item.json;
const now = new Date().toISOString();
return {
  ...lead,
  booking_reminder_sent: true,
  booking_reminder_at: now,
  reminder_status: 'sent',
  updated_at: now,
  _metadata: { processing_stage: 'booking_reminder_sent' },
};
"""

SKIP_BOOKING_REMINDER_JS = r"""
const lead = $('Build Booking Reminder Text').item.json;
const mode = String(lead.mode || 'test').toLowerCase();
const enabled = lead.booking_reminder_enabled === true || lead.booking_reminder_enabled === 'true';
let skipReason = 'disabled';
if (!enabled) skipReason = 'disabled';
else if (mode !== 'production') skipReason = 'test_mode';
else skipReason = 'channel_not_slack';

return {
  ...lead,
  reminder_status: skipReason === 'test_mode' ? 'skipped_test_mode' : 'skipped_disabled',
  skip_reason: skipReason,
  _metadata: { processing_stage: 'booking_reminder_skipped' },
};
"""

LOG_SLACK_BOOKING_REMINDER_ERROR_JS = error_message_prelude("Unknown Slack Booking Reminder error") + r"""
const lead = $('Build Booking Reminder Text').item.json;
return {
  ...lead,
  reminder_status: 'failed',
  slack_error_message: errorMessage,
  _metadata: {
    processing_stage: 'booking_reminder_slack_failed',
    severity: 'low',
    error_message: errorMessage,
    failed_node: 'Slack Booking Reminder',
  },
};
"""

PREPARE_BOOKING_REMINDER_AUDIT_JS = r"""
const item = $input.item.json;
const status = item.reminder_status || 'unknown';
const auditByStatus = {
  sent: 'booking_reminder',
  failed: 'booking_reminder_failed',
  skipped_test_mode: 'booking_reminder_skipped_test',
  skipped_disabled: 'booking_reminder_disabled',
};
return {
  lead_id: item.lead_id || '',
  correlation_id: item.correlation_id || '',
  audit_event: auditByStatus[status] || 'booking_reminder_unknown',
  reminder_status: status,
  booking_reminder_sent: item.booking_reminder_sent === true,
  booking_reminder_at: item.booking_reminder_at || '',
  slack_error_message: item.slack_error_message || '',
  skip_reason: item.skip_reason || '',
  updated_at: item.updated_at || new Date().toISOString(),
  _metadata: { processing_stage: 'booking_reminder_audit_prepared' },
};
"""

HANDLE_BOOKING_READ_ERROR_JS = error_message_prelude("Unknown Read Leads For Reminder error") + r"""
return {
  read_failed: true,
  read_error_message: errorMessage,
  due_count: 0,
  has_due_reminders: false,
  _metadata: {
    processing_stage: 'booking_reminder_read_failed',
    severity: 'medium',
    error_message: errorMessage,
    failed_node: 'Read Leads For Reminder',
  },
};
"""

HANDLE_UPDATE_REMINDER_ERROR_JS = error_message_prelude("Unknown Update Lead Reminder Status error") + r"""
const audit = $('Prepare Booking Reminder Audit').item.json;
return {
  ...audit,
  sheets_update_failed: true,
  sheets_error_message: errorMessage,
  audit_event: 'booking_reminder_update_failed',
  _metadata: {
    processing_stage: 'booking_reminder_update_failed',
    severity: 'high',
    error_message: errorMessage,
    failed_node: 'Update Lead Reminder Status',
  },
};
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
        code_node("Handle error_logs Write Failure", HANDLE_ERROR_LOGS_WRITE_FAILURE_JS, [440, 200]),
        sheets_read("Read config_main", [660, 0], "config_main", retry=True),
        sheets_read("Read config_notifications", [880, 0], "config_notifications", retry=True),
        code_node("Check Error Alert Enabled", CHECK_ERROR_ALERT_ENABLED_JS, [1100, 0], mode="runOnceForAllItems"),
        if_bool_node("Should Alert Slack?", [1320, 0], "={{ $json.should_alert_slack }}"),
        slack_node(
            "Slack Error Alert",
            [1540, 0],
            "=🚨 CRM Workflow Error\nWorkflow: {{ $('Extract Error Details').item.json.workflow }}\nNode: {{ $('Extract Error Details').item.json.node }}\nMessage: {{ $('Extract Error Details').item.json.message }}\nCorrelation: {{ $('Extract Error Details').item.json.correlation_id }}",
        ),
        code_node("Log Slack Error", LOG_SLACK_ERROR_JS, [1760, 120]),
        noop("No Operation, do nothing", [1540, 200]),
    ]
    conn = {}
    connect(conn, "Error Trigger", "Extract Error Details")
    connect(conn, "Extract Error Details", "Write error_logs")
    connect_error(conn, "Write error_logs", "Handle error_logs Write Failure")
    connect(conn, "Write error_logs", "Read config_main")
    connect(conn, "Handle error_logs Write Failure", "Read config_main")
    connect(conn, "Read config_main", "Read config_notifications")
    connect(conn, "Read config_notifications", "Check Error Alert Enabled")
    connect(conn, "Check Error Alert Enabled", "Should Alert Slack?")
    connect(conn, "Should Alert Slack?", "Slack Error Alert", src_output=0)
    connect(conn, "Should Alert Slack?", "No Operation, do nothing", src_output=1)
    connect_error(conn, "Slack Error Alert", "Log Slack Error")
    save_workflow("B2B Lead Error Handler.json", "B2B Lead Error Handler", nodes, conn)


def build_intake() -> None:
    # Tally must use responseMode=responseNode whenever a Respond to Webhook node
    # exists (same pattern as Calendly / Slack Actions). Success path responds 200
    # immediately after signature check so the HTTP client is not held through Sheets/LLM.
    nodes = [
        webhook_node(
            "Tally Webhook",
            [0, 64],
            "tally-lead",
            http_method="POST",
            response_mode="responseNode",
            raw_body=True,
        ),
        webhook_node("Google Forms Webhook", [0, 256], "google-forms-lead"),
        code_node("Verify Tally Signature", VERIFY_TALLY_SIGNATURE_JS, [224, 64]),
        if_bool_node("Tally Validation Passed?", [448, 64], "={{ $json.tally_signature_valid }}"),
        respond_to_webhook_node(
            "Respond 401",
            [672, -176],
            response_code=401,
            response_body='={{ { "ok": false, "error": "invalid_signature" } }}',
        ),
        respond_to_webhook_node(
            "Respond 200",
            [672, -32],
            response_code=200,
            response_body='={{ { "ok": true } }}',
        ),
        code_node("Normalize Tally Payload", NORMALIZE_TALLY_JS, [896, 64]),
        code_node("Normalize Google Forms Payload", NORMALIZE_GFORMS_JS, [224, 256]),
        code_node("Generate Lead IDs", GENERATE_IDS_JS, [448, 160]),
        code_node("Validate Lead", VALIDATE_LEAD_JS, [672, 160]),
        if_node("Validation Passed?", [896, 160], "={{ $json.validation_passed }}", "true"),
        sheets_read("Read All Leads", [1120, 64], "leads", always_output_data=True, retry=True),
        code_node("Handle Read Leads Error", HANDLE_READ_LEADS_ERROR_JS, [1344, 160]),
        code_node("Dedup Lead", DEDUP_LEAD_JS, [1344, -32], mode="runOnceForAllItems"),
        if_bool_node("Is Update?", [1568, 64], "={{ $json.is_update }}"),
        sheets_update("Update Lead", [1792, 0], "leads", "lead_id", {
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
        }, retry=True),
        code_node("Handle Update Lead Error", HANDLE_UPDATE_LEAD_ERROR_JS, [2016, 0]),
        sheets_append("Append Lead", [1792, 192], "leads", {
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
            "meeting_status": "not_booked",
            "processing_status": "={{ $json.processing_status }}",
            "created_at": "={{ $json.created_at }}",
            "updated_at": "={{ $json.updated_at }}",
        }, retry=True),
        code_node("Handle Append Lead Error", HANDLE_APPEND_LEAD_ERROR_JS, [2016, 256]),
        set_node("Normalize Lead", [2240, 64]),
        sheets_append("Write Audit Log", [2464, 64], "audit_logs", {
            "lead_id": "={{ $json.lead_id }}",
            "correlation_id": "={{ $json.correlation_id }}",
            "event": "={{ ($json.is_update === true || $json.is_update === 'true') ? 'lead_updated' : (($json.is_update === false || $json.is_update === 'false') ? 'lead_created' : ($json.created_at ? 'lead_created' : 'lead_updated')) }}",
            "new_value": "={{ $json.processing_status }}",
            "workflow": "B2B Lead Intake",
            "timestamp": "={{ $json.updated_at }}",
        }, retry=True),
        code_node("Handle Audit Log Error", HANDLE_AUDIT_LOG_ERROR_JS, [2688, 144]),
        code_node("Pass Lead To Enrichment", PASS_LEAD_TO_ENRICHMENT_JS, [2912, 64]),
        execute_workflow(
            "Execute Enrichment Scoring",
            [3136, 64],
            "B2B Lead Enrichment Scoring",
            inputs=INTAKE_TO_ENRICHMENT_INPUTS,
        ),
        noop("Validation Failed End", [1120, 256]),
    ]
    conn = {}
    connect(conn, "Tally Webhook", "Verify Tally Signature")
    connect(conn, "Verify Tally Signature", "Tally Validation Passed?")
    connect(conn, "Tally Validation Passed?", "Respond 200", src_output=0)
    connect(conn, "Tally Validation Passed?", "Respond 401", src_output=1)
    connect(conn, "Respond 200", "Normalize Tally Payload")
    connect(conn, "Google Forms Webhook", "Normalize Google Forms Payload")
    connect(conn, "Normalize Tally Payload", "Generate Lead IDs")
    connect(conn, "Normalize Google Forms Payload", "Generate Lead IDs")
    connect(conn, "Generate Lead IDs", "Validate Lead")
    connect(conn, "Validate Lead", "Validation Passed?")
    connect(conn, "Validation Passed?", "Read All Leads", src_output=0)
    connect(conn, "Read All Leads", "Dedup Lead")
    connect_error(conn, "Read All Leads", "Handle Read Leads Error")
    connect(conn, "Handle Read Leads Error", "Is Update?")
    connect(conn, "Dedup Lead", "Is Update?")
    connect(conn, "Is Update?", "Update Lead", src_output=0)
    connect(conn, "Is Update?", "Append Lead", src_output=1)
    connect(conn, "Update Lead", "Normalize Lead")
    connect_error(conn, "Update Lead", "Handle Update Lead Error")
    connect(conn, "Handle Update Lead Error", "Normalize Lead")
    connect(conn, "Append Lead", "Normalize Lead")
    connect_error(conn, "Append Lead", "Handle Append Lead Error")
    connect(conn, "Handle Append Lead Error", "Normalize Lead")
    connect(conn, "Normalize Lead", "Write Audit Log")
    connect(conn, "Write Audit Log", "Pass Lead To Enrichment")
    connect_error(conn, "Write Audit Log", "Handle Audit Log Error")
    connect(conn, "Handle Audit Log Error", "Pass Lead To Enrichment")
    connect(conn, "Pass Lead To Enrichment", "Execute Enrichment Scoring")
    connect(conn, "Validation Passed?", "Validation Failed End", src_output=1)
    save_workflow("B2B Lead Intake.json", "B2B Lead Intake", nodes, conn, error_workflow="B2B Lead Error Handler")


def build_enrichment_scoring() -> None:
    config_nodes: list[dict] = [
        {
            "parameters": {"workflowInputs": {"values": ENRICHMENT_WORKFLOW_INPUTS}},
            "type": "n8n-nodes-base.executeWorkflowTrigger",
            "typeVersion": 1.1,
            "position": [0, 200],
            "id": nid("trigger"),
            "name": "When Executed by Another Workflow",
        },
        code_node("Hold Lead", HOLD_LEAD_JS, [220, 200]),
    ]
    x = 440
    for table, read_name in CONFIG_TABLES:
        short = read_name.replace("Read ", "")
        max_tries = 3 if short == "config_routing" else None
        config_nodes.append(sheets_read(read_name, [x, 200], table, retry=True, max_tries=max_tries))
        config_nodes.append(
            code_node(
                f"Normalize {short}",
                normalize_config_js(table),
                [x + 112, 120],
                mode="runOnceForAllItems",
            )
        )
        config_nodes.append(
            code_node(
                f"Handle {short} Error",
                handle_config_read_error_js(table, read_name),
                [x + 112, 320],
            )
        )
        x += 336

    config_nodes.extend([
        code_node("Build Global Config", BUILD_GLOBAL_CONFIG_JS, [x, 200]),
        code_node("Domain Enrichment", DOMAIN_ENRICHMENT_JS, [1100, 200]),
        if_node("Is Corporate Domain?", [1210, 200], "={{ $json.domain_type }}", "corporate", strict=True),
        http_get_request_node(
            "Hunter Company Lookup",
            [1320, 80],
            "https://api.hunter.io/v2/companies/find",
            [
                {"name": "domain", "value": "={{ $json.company_domain }}"},
                {"name": "api_key", "value": "={{ $env.HUNTER_API_KEY }}"},
            ],
        ),
        code_node("Attach Hunter Data", ATTACH_HUNTER_DATA_JS, [1430, 80]),
        http_request_node("HTTP Enrich Lead", [1540, 200], "POST", "http://crm_python_ai:8001/enrich", [
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
        code_node("Merge Enrichment Result", MERGE_ENRICHMENT_JS, [1760, 200]),
        code_node("Handle Enrichment Failure", HANDLE_AI_ENRICH_FAILURE_JS, [1760, 400]),
        http_request_node("HTTP Score Lead", [1980, 200], "POST", "http://crm_python_ai:8001/score", [
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
        code_node("Merge Scoring Result", MERGE_SCORING_JS, [2200, 200]),
        code_node("Handle Scoring Failure", HANDLE_AI_SCORE_FAILURE_JS, [2200, 400]),
        code_node("Check Sales Memo Eligible", CHECK_SALES_MEMO_ELIGIBLE_JS, [2420, 200]),
        if_bool_node("Sales Memo Eligible?", [2640, 200], "={{ $json.sales_memo_eligible }}"),
        http_request_node("HTTP Sales Memo", [2860, 100], "POST", "http://crm_python_ai:8001/sales-memo", [
            {"name": "lead_id", "value": "={{ $json.lead_id }}"},
            {"name": "correlation_id", "value": "={{ $json.correlation_id }}"},
            {"name": "source_type", "value": "={{ $json.source_type }}"},
            {"name": "source_name", "value": "={{ $json.source_name }}"},
            {"name": "contact_name", "value": "={{ $json.contact_name }}"},
            {"name": "contact_email", "value": "={{ $json.contact_email }}"},
            {"name": "contact_role", "value": "={{ $json.contact_role }}"},
            {"name": "company_name", "value": "={{ $json.company_name }}"},
            {"name": "company_domain", "value": "={{ $json.company_domain }}"},
            {"name": "industry", "value": "={{ $json.industry }}"},
            {"name": "company_size", "value": "={{ $json.company_size }}"},
            {"name": "content_summary", "value": "={{ $json.content_summary }}"},
            {"name": "intent_signals", "value": "={{ typeof $json.intent_signals === 'string' ? JSON.parse($json.intent_signals || '[]') : ($json.intent_signals || []) }}"},
            {"name": "enrichment_summary", "value": "={{ $json.enrichment_summary }}"},
            {"name": "score", "value": "={{ $json.score }}"},
            {"name": "score_reasoning", "value": "={{ $json.score_reasoning }}"},
            {"name": "recommended_action", "value": "={{ $json.recommended_action }}"},
        ]),
        code_node("Merge Sales Memo", MERGE_SALES_MEMO_JS, [3080, 100]),
        code_node("Handle Sales Memo Failure", HANDLE_SALES_MEMO_FAILURE_JS, [3080, 280]),
        code_node("Skip Sales Memo", SKIP_SALES_MEMO_JS, [2860, 300]),
        code_node("Apply Review Rules", APPLY_REVIEW_RULES_JS, [3300, 200]),
        if_node("Needs Manual Review AI?", [3520, 200], "={{ $json.review_status }}", "pending_review", strict=True),
        http_json_request_node(
            "HTTP Manual Review",
            [3740, 320],
            "POST",
            "http://crm_python_ai:8001/manual-review",
            '={\n'
            '  "lead_id": "={{ $json.lead_id }}",\n'
            '  "correlation_id": "={{ $json.correlation_id }}",\n'
            '  "contact_name": "={{ $json.contact_name }}",\n'
            '  "contact_role": "={{ $json.contact_role }}",\n'
            '  "contact_email": "={{ $json.contact_email }}",\n'
            '  "company_name": "={{ $json.company_name }}",\n'
            '  "company_domain": "={{ $json.company_domain }}",\n'
            '  "score": "={{ Number($json.score || 0) }}",\n'
            '  "score_reasoning": "={{ $json.score_reasoning }}",\n'
            '  "enrichment_status": "={{ $json.enrichment_status }}",\n'
            '  "review_triggers": "={{ $json.review_triggers }}"\n'
            '}',
        ),
        code_node("Merge Manual Review", MERGE_MANUAL_REVIEW_JS, [3960, 320]),
        code_node("Skip Manual Review", SKIP_MANUAL_REVIEW_JS, [3740, 480]),
        code_node("Apply Routing Rules", APPLY_ROUTING_RULES_JS, [4180, 200]),
        sheets_update("Update Lead Scores", [3740, 200], "leads", "lead_id", {
            "lead_id": "={{ $json.lead_id }}",
            "content_summary": "={{ $json.content_summary }}",
            "industry": "={{ $json.industry }}",
            "company_size": "={{ $json.company_size }}",
            "domain_type": "={{ $json.domain_type }}",
            "intent_signals": "={{ $json.intent_signals }}",
            "enrichment_status": "={{ $json.enrichment_status }}",
            "enrichment_summary": "={{ $json.enrichment_summary }}",
            "score": "={{ $json.score }}",
            "score_reasoning": "={{ $json.score_reasoning }}",
            "confidence": "={{ $json.confidence }}",
            "recommended_action": "={{ $json.recommended_action }}",
            "routing_decision": "={{ $json.routing_decision }}",
            "fallback_used": "={{ $json.fallback_used }}",
            "sales_memo": "={{ $json.sales_memo }}",
            "sales_memo_status": "={{ $json.sales_memo_status }}",
            "review_status": "={{ $json.review_status }}",
            "review_notes": "={{ $json.review_notes || '' }}",
            "company_region": "={{ $json.company_region || '' }}",
            "processing_status": "={{ $json.processing_status }}",
            "updated_at": "={{ $json.updated_at }}",
        }),
        code_node("Handle Sheets Score Error", HANDLE_SHEETS_SCORE_ERROR_JS, [3740, 400]),
        code_node("Normalize Enriched Lead", NORMALIZE_ENRICHED_LEAD_JS, [3960, 200]),
        execute_workflow(
            "Execute CRM Sync",
            [4180, 200],
            "B2B Lead CRM Sync Notification",
            inputs=ENRICHMENT_TO_CRM_INPUTS,
        ),
    ])
    nodes = config_nodes

    conn = {}
    connect(conn, "When Executed by Another Workflow", "Hold Lead")
    connect(conn, "Hold Lead", "Read config_main")
    read_names = [read_name for _, read_name in CONFIG_TABLES]
    for i, (table, read_name) in enumerate(CONFIG_TABLES):
        short = read_name.replace("Read ", "")
        norm_name = f"Normalize {short}"
        handle_name = f"Handle {short} Error"
        next_node = read_names[i + 1] if i + 1 < len(read_names) else "Build Global Config"
        connect(conn, read_name, norm_name)
        connect_error(conn, read_name, handle_name)
        connect(conn, norm_name, next_node)
        connect(conn, handle_name, next_node)
    connect(conn, "Build Global Config", "Domain Enrichment")
    connect(conn, "Domain Enrichment", "Is Corporate Domain?")
    connect(conn, "Is Corporate Domain?", "Hunter Company Lookup", src_output=0)
    connect(conn, "Is Corporate Domain?", "HTTP Enrich Lead", src_output=1)
    connect(conn, "Hunter Company Lookup", "Attach Hunter Data", src_output=0)
    connect_error(conn, "Hunter Company Lookup", "Attach Hunter Data")
    connect(conn, "Attach Hunter Data", "HTTP Enrich Lead")
    connect(conn, "HTTP Enrich Lead", "Merge Enrichment Result", src_output=0)
    connect_error(conn, "HTTP Enrich Lead", "Handle Enrichment Failure")
    connect(conn, "Handle Enrichment Failure", "HTTP Score Lead")
    connect(conn, "Merge Enrichment Result", "HTTP Score Lead")
    connect(conn, "HTTP Score Lead", "Merge Scoring Result", src_output=0)
    connect_error(conn, "HTTP Score Lead", "Handle Scoring Failure")
    connect(conn, "Handle Scoring Failure", "Apply Review Rules")
    connect(conn, "Merge Scoring Result", "Check Sales Memo Eligible")
    connect(conn, "Check Sales Memo Eligible", "Sales Memo Eligible?")
    connect(conn, "Sales Memo Eligible?", "HTTP Sales Memo", src_output=0)
    connect(conn, "Sales Memo Eligible?", "Skip Sales Memo", src_output=1)
    connect(conn, "HTTP Sales Memo", "Merge Sales Memo", src_output=0)
    connect_error(conn, "HTTP Sales Memo", "Handle Sales Memo Failure")
    connect(conn, "Merge Sales Memo", "Apply Review Rules")
    connect(conn, "Handle Sales Memo Failure", "Apply Review Rules")
    connect(conn, "Skip Sales Memo", "Apply Review Rules")
    connect(conn, "Apply Review Rules", "Needs Manual Review AI?")
    connect(conn, "Needs Manual Review AI?", "HTTP Manual Review", src_output=0)
    connect(conn, "Needs Manual Review AI?", "Apply Routing Rules", src_output=1)
    connect(conn, "HTTP Manual Review", "Merge Manual Review", src_output=0)
    connect_error(conn, "HTTP Manual Review", "Skip Manual Review")
    connect(conn, "Merge Manual Review", "Apply Routing Rules")
    connect(conn, "Skip Manual Review", "Apply Routing Rules")
    connect(conn, "Apply Routing Rules", "Update Lead Scores")
    connect(conn, "Update Lead Scores", "Normalize Enriched Lead")
    connect_error(conn, "Update Lead Scores", "Handle Sheets Score Error")
    connect(conn, "Handle Sheets Score Error", "Normalize Enriched Lead")
    connect(conn, "Normalize Enriched Lead", "Execute CRM Sync")
    save_workflow("B2B Lead Enrichment Scoring.json", "B2B Lead Enrichment Scoring", nodes, conn, error_workflow="B2B Lead Error Handler")


def build_crm_sync_notification() -> None:
    nodes = [
        {
            "parameters": {"workflowInputs": {"values": CRM_WORKFLOW_INPUTS}},
            "type": "n8n-nodes-base.executeWorkflowTrigger",
            "typeVersion": 1.1,
            "position": [0, 200],
            "id": nid("trigger"),
            "name": "When Executed by Another Workflow",
        },
        code_node("CRM Gate", CRM_GATE_JS, [220, 200]),
        if_bool_node("Should Sync CRM?", [440, 200], "={{ $json.crm_gate_passed }}"),
        hubspot_upsert_node("HubSpot Upsert Contact", [660, 100]),
        code_node("Handle HubSpot Failure", HANDLE_HUBSPOT_FAILURE_JS, [880, 260]),
        code_node("Mark CRM Synced", MARK_CRM_SYNCED_JS, [880, 100]),
        code_node("Skip CRM Test Mode", "return { ...$input.item.json, crm_status: 'skipped_test_mode', _metadata: { processing_stage: 'crm_skipped' } };", [660, 300]),
        set_node("Normalize CRM Result", [1100, 200]),
        code_node("Check First Touch Eligible", CHECK_FIRST_TOUCH_ELIGIBLE_JS, [1320, 200]),
        if_string_or_node(
            "First Touch Eligible?",
            [1540, 200],
            "={{ $json.first_touch_phase }}",
            ["draft", "send"],
        ),
        if_node("Draft or Send?", [1760, 80], "={{ $json.first_touch_phase }}", "draft", strict=True),
        http_request_node("HTTP Outbound Email", [1980, 80], "POST", "http://crm_python_ai:8001/outbound-email", [
            {"name": "lead_id", "value": "={{ $json.lead_id }}"},
            {"name": "correlation_id", "value": "={{ $json.correlation_id }}"},
            {"name": "source_type", "value": "={{ $json.source_type }}"},
            {"name": "source_name", "value": "={{ $json.source_name }}"},
            {"name": "contact_name", "value": "={{ $json.contact_name }}"},
            {"name": "contact_email", "value": "={{ $json.contact_email }}"},
            {"name": "contact_role", "value": "={{ $json.contact_role }}"},
            {"name": "company_name", "value": "={{ $json.company_name }}"},
            {"name": "company_domain", "value": "={{ $json.company_domain }}"},
            {"name": "industry", "value": "={{ $json.industry }}"},
            {"name": "company_size", "value": "={{ $json.company_size }}"},
            {"name": "content_summary", "value": "={{ $json.content_summary }}"},
            {"name": "intent_signals", "value": "={{ typeof $json.intent_signals === 'string' ? JSON.parse($json.intent_signals || '[]') : ($json.intent_signals || []) }}"},
            {"name": "enrichment_summary", "value": "={{ $json.enrichment_summary }}"},
            {"name": "score", "value": "={{ $json.score }}"},
            {"name": "score_reasoning", "value": "={{ $json.score_reasoning }}"},
            {"name": "recommended_action", "value": "={{ $json.recommended_action }}"},
            {"name": "sales_memo", "value": "={{ $json.sales_memo }}"},
            {"name": "sender_name", "value": "={{ $json.first_touch_sender_name }}"},
            {"name": "calendly_url", "value": "={{ ($json.global_config || {}).calendly_url || '' }}"},
        ]),
        code_node("Merge Outbound Email", MERGE_OUTBOUND_EMAIL_JS, [2200, 80]),
        code_node("Handle Outbound Email Failure", HANDLE_OUTBOUND_EMAIL_FAILURE_JS, [1980, 280]),
        code_node("Mark Draft Pending Review", MARK_DRAFT_PENDING_REVIEW_JS, [2420, 80]),
        code_node("Load Draft From Lead", LOAD_DRAFT_FROM_LEAD_JS, [1980, 480]),
        hubspot_crm_email_node("HubSpot Log Outbound Email", [2200, 480]),
        code_node("Mark First Touch Sent", MARK_FIRST_TOUCH_SENT_JS, [2420, 480]),
        code_node("Handle First Touch Send Failure", HANDLE_FIRST_TOUCH_SEND_FAILURE_JS, [2200, 280]),
        if_bool_node(
            "Should Alert First Touch?",
            [2420, 280],
            "={{ $json.first_touch_status === 'failed' && (($json.global_config || {}).mode === 'production') }}",
        ),
        slack_node(
            "Slack First Touch Alert",
            [2640, 280],
            "=🚨 First-touch email failed\nLead: {{ $json.contact_name }} ({{ $json.contact_email }})\nScore: {{ $json.score }}\nError: {{ $json.first_touch_error }}\nCorrelation: {{ $json.correlation_id }}",
        ),
        code_node("Log First Touch Slack Alert Error", LOG_FIRST_TOUCH_SLACK_ALERT_JS, [2860, 280]),
        code_node("Skip First Touch", SKIP_FIRST_TOUCH_JS, [1760, 400]),
        code_node("Build Notification Payload", NOTIFICATION_PAYLOAD_JS, [2860, 200]),
        if_bool_node(
            "Should Notify?",
            [3080, 200],
            "={{ $json.should_send_slack }}",
        ),
        if_bool_node("Use Slack Blocks?", [3300, 100], "={{ $json.notification.slack_blocks_valid }}"),
        slack_blocks_node("Slack Notify", [3520, 0]),
        slack_node(
            "Slack Notify Text",
            [3520, 200],
            "=📋 {{ $json.notification.title }}\n{{ $json.notification.message }}\nAction: {{ $json.notification.metadata.recommended_action }}\nScore: {{ $json.notification.metadata.score }}\nCorrelation: {{ $json.correlation_id }}\n{{ $json.notification.metadata.calendly_url ? 'Book: ' + $json.notification.metadata.calendly_url : '' }}",
        ),
        code_node("Mark Notification Sent", "return { ...($('Build Notification Payload').item.json), notification_status: 'sent', _metadata: { processing_stage: 'notification_sent' } };", [3740, 100]),
        code_node("Skip Notification Test", SKIP_NOTIFICATION_TEST_JS, [3300, 300]),
        code_node("Log Slack Notify Error", LOG_SLACK_NOTIFY_ERROR_JS, [3740, 260]),
        set_node("Normalize Notification Result", [3960, 200]),
        code_node("Prepare First Touch Audit", PREPARE_FIRST_TOUCH_AUDIT_JS, [4180, 200]),
        sheets_append("Write First Touch Audit", [4400, 200], "audit_logs", {
            "lead_id": "={{ $json.lead_id }}",
            "correlation_id": "={{ $json.correlation_id }}",
            "event": "={{ $json.audit_event }}",
            "new_value": "={{ $json.first_touch_status }}",
            "workflow": "B2B Lead CRM Sync Notification",
            "timestamp": "={{ $json.updated_at || new Date().toISOString() }}",
        }, retry=True),
        sheets_update("Update Final Status", [4620, 200], "leads", "lead_id", {
            "lead_id": "={{ $json.lead_id }}",
            "crm_status": "={{ $json.crm_status }}",
            "crm_contact_id": "={{ $json.crm_contact_id || '' }}",
            "notification_status": "={{ $json.notification_status || 'pending' }}",
            "first_touch_status": "={{ $json.first_touch_status || '' }}",
            "first_touch_channel": "={{ $json.first_touch_channel || '' }}",
            "first_touch_at": "={{ $json.first_touch_at || '' }}",
            "first_touch_error": "={{ $json.first_touch_error || '' }}",
            "outbound_email_subject": "={{ $json.outbound_email_subject || '' }}",
            "outbound_email_body": "={{ $json.outbound_email_body || '' }}",
            "processing_status": "={{ $json.processing_status || 'completed' }}",
            "updated_at": "={{ new Date().toISOString() }}",
        }, retry=True),
        code_node("Handle Final Status Error", HANDLE_FINAL_STATUS_ERROR_JS, [4620, 400]),
        noop("Final Status Write Failed End", [4840, 400]),
    ]
    conn = {}
    connect(conn, "When Executed by Another Workflow", "CRM Gate")
    connect(conn, "CRM Gate", "Should Sync CRM?")
    connect(conn, "Should Sync CRM?", "HubSpot Upsert Contact", src_output=0)
    connect(conn, "Should Sync CRM?", "Skip CRM Test Mode", src_output=1)
    connect(conn, "HubSpot Upsert Contact", "Mark CRM Synced", src_output=0)
    connect_error(conn, "HubSpot Upsert Contact", "Handle HubSpot Failure")
    connect(conn, "Mark CRM Synced", "Normalize CRM Result")
    connect(conn, "Handle HubSpot Failure", "Normalize CRM Result")
    connect(conn, "Skip CRM Test Mode", "Normalize CRM Result")
    connect(conn, "Normalize CRM Result", "Check First Touch Eligible")
    connect(conn, "Check First Touch Eligible", "First Touch Eligible?")
    connect(conn, "First Touch Eligible?", "Draft or Send?", src_output=0)
    connect(conn, "First Touch Eligible?", "Skip First Touch", src_output=1)
    connect(conn, "Draft or Send?", "HTTP Outbound Email", src_output=0)
    connect(conn, "Draft or Send?", "Load Draft From Lead", src_output=1)
    connect(conn, "HTTP Outbound Email", "Merge Outbound Email", src_output=0)
    connect_error(conn, "HTTP Outbound Email", "Handle Outbound Email Failure")
    connect(conn, "Merge Outbound Email", "Mark Draft Pending Review")
    connect(conn, "Handle Outbound Email Failure", "Mark Draft Pending Review")
    connect(conn, "Mark Draft Pending Review", "Build Notification Payload")
    connect(conn, "Load Draft From Lead", "HubSpot Log Outbound Email")
    connect(conn, "HubSpot Log Outbound Email", "Mark First Touch Sent", src_output=0)
    connect_error(conn, "HubSpot Log Outbound Email", "Handle First Touch Send Failure")
    connect(conn, "Mark First Touch Sent", "Build Notification Payload")
    connect(conn, "Handle First Touch Send Failure", "Should Alert First Touch?")
    connect(conn, "Should Alert First Touch?", "Slack First Touch Alert", src_output=0)
    connect(conn, "Should Alert First Touch?", "Build Notification Payload", src_output=1)
    connect(conn, "Slack First Touch Alert", "Build Notification Payload", src_output=0)
    connect_error(conn, "Slack First Touch Alert", "Log First Touch Slack Alert Error")
    connect(conn, "Log First Touch Slack Alert Error", "Build Notification Payload")
    connect(conn, "Skip First Touch", "Build Notification Payload")
    connect(conn, "Build Notification Payload", "Should Notify?")
    connect(conn, "Should Notify?", "Use Slack Blocks?", src_output=0)
    connect(conn, "Should Notify?", "Skip Notification Test", src_output=1)
    connect(conn, "Use Slack Blocks?", "Slack Notify", src_output=0)
    connect(conn, "Use Slack Blocks?", "Slack Notify Text", src_output=1)
    connect(conn, "Slack Notify", "Mark Notification Sent", src_output=0)
    connect(conn, "Slack Notify Text", "Mark Notification Sent", src_output=0)
    connect_error(conn, "Slack Notify", "Log Slack Notify Error")
    connect_error(conn, "Slack Notify Text", "Log Slack Notify Error")
    connect(conn, "Mark Notification Sent", "Normalize Notification Result")
    connect(conn, "Skip Notification Test", "Normalize Notification Result")
    connect(conn, "Log Slack Notify Error", "Normalize Notification Result")
    connect(conn, "Normalize Notification Result", "Update Final Status")
    connect(conn, "Update Final Status", "Prepare First Touch Audit")
    connect(conn, "Prepare First Touch Audit", "Write First Touch Audit")
    connect_error(conn, "Update Final Status", "Handle Final Status Error")
    connect(conn, "Handle Final Status Error", "Final Status Write Failed End")
    save_workflow("B2B Lead CRM Sync Notification.json", "B2B Lead CRM Sync Notification", nodes, conn, error_workflow="B2B Lead Error Handler")


def build_daily_summary() -> None:
    """Daily 09:00 digest for yesterday UTC; Slack only if production + daily_summary.enabled."""
    nodes = [
        {
            "parameters": {"rule": {"interval": [{"field": "days", "triggerAtHour": 9}]}},
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [0, 200],
            "id": nid("schedule"),
            "name": "Daily 9am",
        },
        sheets_read("Read Leads For Summary", [220, 200], "leads", always_output_data=True),
        sheets_read("Read Errors For Summary", [440, 200], "error_logs", always_output_data=True),
        code_node("Handle Summary Read Error", HANDLE_SUMMARY_READ_ERROR_JS, [440, 400]),
        sheets_read("Read config_main", [660, 200], "config_main", retry=True),
        code_node(
            "Normalize config_main",
            normalize_config_js("config_main"),
            [660, 360],
            mode="runOnceForAllItems",
        ),
        code_node(
            "Handle config_main Read Error",
            handle_config_read_error_js("config_main", "Read config_main"),
            [660, 520],
        ),
        sheets_read("Read config_notifications", [880, 200], "config_notifications", retry=True),
        code_node(
            "Normalize config_notifications",
            normalize_config_js("config_notifications"),
            [880, 360],
            mode="runOnceForAllItems",
        ),
        code_node(
            "Handle config_notifications Read Error",
            handle_config_read_error_js("config_notifications", "Read config_notifications"),
            [880, 520],
        ),
        code_node("Load Daily Config", LOAD_DAILY_CONFIG_JS, [1100, 200], mode="runOnceForAllItems"),
        code_node("Build Daily Summary", DAILY_SUMMARY_JS, [1320, 200], mode="runOnceForAllItems"),
        if_bool_node("Should Send Daily?", [1540, 200], "={{ $json.daily_gate_passed }}"),
        slack_node(
            "Slack Daily Report",
            [1760, 120],
            "=📊 CRM Daily Summary ({{ $json.date }})\nNew leads: {{ $json.new_leads }}\nHigh score: {{ $json.high_score_leads }}\nCRM success rate: {{ $json.crm_success_rate }}\nSlack sent: {{ $json.slack_success_count }}\nReview pending: {{ $json.review_pending }}\nErrors: {{ $json.error_count }}",
        ),
        code_node("Skip Daily Slack", SKIP_DAILY_SLACK_JS, [1760, 320]),
        code_node("Log Slack Summary Error", LOG_SLACK_SUMMARY_ERROR_JS, [1980, 240]),
        noop("Daily Summary End", [1980, 120]),
    ]
    conn = {}
    connect(conn, "Daily 9am", "Read Leads For Summary")
    connect(conn, "Read Leads For Summary", "Read Errors For Summary")
    connect_error(conn, "Read Leads For Summary", "Handle Summary Read Error")
    connect(conn, "Read Errors For Summary", "Read config_main")
    connect_error(conn, "Read Errors For Summary", "Handle Summary Read Error")
    connect(conn, "Read config_main", "Normalize config_main")
    connect_error(conn, "Read config_main", "Handle config_main Read Error")
    connect(conn, "Normalize config_main", "Read config_notifications")
    connect(conn, "Handle config_main Read Error", "Read config_notifications")
    connect(conn, "Read config_notifications", "Normalize config_notifications")
    connect_error(conn, "Read config_notifications", "Handle config_notifications Read Error")
    connect(conn, "Normalize config_notifications", "Load Daily Config")
    connect(conn, "Handle config_notifications Read Error", "Load Daily Config")
    connect(conn, "Load Daily Config", "Build Daily Summary")
    connect(conn, "Build Daily Summary", "Should Send Daily?")
    connect(conn, "Handle Summary Read Error", "Should Send Daily?")
    connect(conn, "Should Send Daily?", "Slack Daily Report", src_output=0)
    connect(conn, "Should Send Daily?", "Skip Daily Slack", src_output=1)
    connect(conn, "Slack Daily Report", "Daily Summary End")
    connect_error(conn, "Slack Daily Report", "Log Slack Summary Error")
    connect(conn, "Log Slack Summary Error", "Daily Summary End")
    connect(conn, "Skip Daily Slack", "Daily Summary End")
    save_workflow("B2B Lead Daily Summary.json", "B2B Lead Daily Summary", nodes, conn, error_workflow="B2B Lead Error Handler")


def build_weekly_summary() -> None:
    """Friday 17:00 weekly metrics + /weekly-insights; always Append weekly_metrics; Slack gated."""
    nodes = [
        {
            "parameters": {
                "rule": {
                    "interval": [{"field": "weeks", "triggerAtDay": [5], "triggerAtHour": 17}],
                }
            },
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [0, 200],
            "id": nid("schedule"),
            "name": "Friday 5pm",
        },
        sheets_read("Read Leads For Weekly", [220, 200], "leads", always_output_data=True),
        sheets_read("Read Errors For Weekly", [440, 200], "error_logs", always_output_data=True),
        sheets_read("Read Prior Weekly Metrics", [660, 200], "weekly_metrics", always_output_data=True),
        sheets_read("Read config_main", [880, 200], "config_main", retry=True),
        code_node(
            "Normalize config_main",
            normalize_config_js("config_main"),
            [880, 360],
            mode="runOnceForAllItems",
        ),
        code_node(
            "Handle config_main Read Error",
            handle_config_read_error_js("config_main", "Read config_main"),
            [880, 520],
        ),
        sheets_read("Read config_notifications", [1100, 200], "config_notifications", retry=True),
        code_node(
            "Normalize config_notifications",
            normalize_config_js("config_notifications"),
            [1100, 360],
            mode="runOnceForAllItems",
        ),
        code_node(
            "Handle config_notifications Read Error",
            handle_config_read_error_js("config_notifications", "Read config_notifications"),
            [1100, 520],
        ),
        code_node("Load Weekly Config", LOAD_WEEKLY_CONFIG_JS, [1320, 200], mode="runOnceForAllItems"),
        code_node("Handle Weekly Read Error", HANDLE_WEEKLY_READ_ERROR_JS, [440, 400]),
        code_node("Build Weekly Metrics", BUILD_WEEKLY_METRICS_JS, [1540, 200], mode="runOnceForAllItems"),
        http_json_post_node(
            "HTTP Weekly Insights",
            [1760, 200],
            "http://crm_python_ai:8001/weekly-insights",
            "={{ JSON.stringify({ week_start: $json.week_start, week_end: $json.week_end, correlation_id: $json.correlation_id, metrics: $json.metrics_json, prior_week_metrics: $json.prior_week_metrics || {} }) }}",
            correlation_id_header=True,
        ),
        code_node("Handle Weekly AI Failure", HANDLE_WEEKLY_AI_FAILURE_JS, [1760, 400]),
        code_node("Merge Weekly Report", MERGE_WEEKLY_REPORT_JS, [1980, 200], mode="runOnceForAllItems"),
        if_bool_node("Should Send Weekly?", [2200, 200], "={{ $json.weekly_gate_passed }}"),
        slack_node("Slack Weekly Report", [2420, 120], "={{ $json.slack_text }}"),
        code_node("Skip Weekly Slack", SKIP_WEEKLY_SLACK_JS, [2420, 320]),
        code_node("Log Slack Weekly Error", LOG_SLACK_WEEKLY_ERROR_JS, [2640, 240]),
        code_node(
            "Restore Weekly Report After Slack",
            RESTORE_WEEKLY_REPORT_AFTER_SLACK_JS,
            [2640, 40],
        ),
        sheets_append("Append Weekly Metrics", [2860, 120], "weekly_metrics", {
            "week_start": "={{ $json.week_start }}",
            "week_end": "={{ $json.week_end }}",
            "generated_at": "={{ $json.generated_at || new Date().toISOString() }}",
            "new_leads": "={{ $json.new_leads }}",
            "high_score_leads": "={{ $json.high_score_leads }}",
            "avg_score": "={{ $json.avg_score }}",
            "crm_sync_rate": "={{ $json.crm_sync_rate }}",
            "slack_sent_count": "={{ $json.slack_sent_count }}",
            "review_pending": "={{ $json.review_pending }}",
            "review_approved": "={{ $json.review_approved }}",
            "meetings_booked": "={{ $json.meetings_booked }}",
            "first_touch_sent": "={{ $json.first_touch_sent }}",
            "error_count": "={{ $json.error_count }}",
            "source_breakdown_json": "={{ $json.source_breakdown_json }}",
            "metrics_json": "={{ JSON.stringify($json.metrics_json || {}) }}",
            "ai_summary": "={{ $json.ai_summary }}",
            "fallback_used": "={{ $json.fallback_used }}",
            "correlation_id": "={{ $json.correlation_id }}",
        }, retry=True),
        code_node(
            "Handle Append Weekly Metrics Error",
            HANDLE_APPEND_WEEKLY_METRICS_ERROR_JS,
            [2860, 280],
        ),
        noop("Weekly Summary End", [3080, 200]),
    ]
    conn = {}
    connect(conn, "Friday 5pm", "Read Leads For Weekly")
    connect(conn, "Read Leads For Weekly", "Read Errors For Weekly")
    connect_error(conn, "Read Leads For Weekly", "Handle Weekly Read Error")
    connect(conn, "Read Errors For Weekly", "Read Prior Weekly Metrics")
    connect_error(conn, "Read Errors For Weekly", "Handle Weekly Read Error")
    connect(conn, "Read Prior Weekly Metrics", "Read config_main")
    connect_error(conn, "Read Prior Weekly Metrics", "Handle Weekly Read Error")
    connect(conn, "Read config_main", "Normalize config_main")
    connect_error(conn, "Read config_main", "Handle config_main Read Error")
    connect(conn, "Normalize config_main", "Read config_notifications")
    connect(conn, "Handle config_main Read Error", "Read config_notifications")
    connect(conn, "Read config_notifications", "Normalize config_notifications")
    connect_error(conn, "Read config_notifications", "Handle config_notifications Read Error")
    connect(conn, "Normalize config_notifications", "Load Weekly Config")
    connect(conn, "Handle config_notifications Read Error", "Load Weekly Config")
    connect(conn, "Load Weekly Config", "Build Weekly Metrics")
    connect(conn, "Handle Weekly Read Error", "HTTP Weekly Insights")
    connect(conn, "Build Weekly Metrics", "HTTP Weekly Insights")
    connect(conn, "HTTP Weekly Insights", "Merge Weekly Report", src_output=0)
    connect_error(conn, "HTTP Weekly Insights", "Handle Weekly AI Failure")
    connect(conn, "Handle Weekly AI Failure", "Merge Weekly Report")
    connect(conn, "Merge Weekly Report", "Should Send Weekly?")
    connect(conn, "Should Send Weekly?", "Slack Weekly Report", src_output=0)
    connect(conn, "Should Send Weekly?", "Skip Weekly Slack", src_output=1)
    connect(conn, "Slack Weekly Report", "Restore Weekly Report After Slack", src_output=0)
    connect_error(conn, "Slack Weekly Report", "Log Slack Weekly Error")
    connect(conn, "Restore Weekly Report After Slack", "Append Weekly Metrics")
    connect(conn, "Log Slack Weekly Error", "Append Weekly Metrics")
    connect(conn, "Skip Weekly Slack", "Append Weekly Metrics")
    connect(conn, "Append Weekly Metrics", "Weekly Summary End")
    connect_error(conn, "Append Weekly Metrics", "Handle Append Weekly Metrics Error")
    connect(conn, "Handle Append Weekly Metrics Error", "Weekly Summary End")
    save_workflow(
        "B2B Lead Weekly Summary.json",
        "B2B Lead Weekly Summary",
        nodes,
        conn,
        error_workflow="B2B Lead Error Handler",
    )


def build_booking_followup() -> None:
    nodes = [
        {
            "parameters": {"rule": {"interval": [{"field": "days", "triggerAtHour": 10}]}},
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [0, 200],
            "id": nid("schedule"),
            "name": "Daily 10am",
        },
        sheets_read("Read Leads For Reminder", [220, 200], "leads", always_output_data=True, retry=True),
        sheets_read("Read config_main", [440, 200], "config_main", retry=True),
        code_node(
            "Normalize config_main",
            normalize_config_js("config_main"),
            [440, 360],
            mode="runOnceForAllItems",
        ),
        code_node(
            "Handle config_main Read Error",
            handle_config_read_error_js("config_main", "Read config_main"),
            [440, 520],
        ),
        sheets_read("Read config_notifications", [660, 200], "config_notifications", retry=True),
        code_node(
            "Normalize config_notifications",
            normalize_config_js("config_notifications"),
            [660, 360],
            mode="runOnceForAllItems",
        ),
        code_node(
            "Handle config_notifications Read Error",
            handle_config_read_error_js("config_notifications", "Read config_notifications"),
            [660, 520],
        ),
        code_node("Load Booking Config", LOAD_BOOKING_CONFIG_JS, [880, 200], mode="runOnceForAllItems"),
        code_node("Handle Booking Read Error", HANDLE_BOOKING_READ_ERROR_JS, [220, 400]),
        code_node(
            "Filter Due Booking Reminders",
            FILTER_DUE_BOOKING_REMINDERS_JS,
            [1100, 200],
            mode="runOnceForAllItems",
        ),
        if_bool_node("Has Due Reminders?", [1320, 200], "={{ $json.has_due_reminders }}"),
        code_node("Expand Due Leads", EXPAND_DUE_BOOKING_LEADS_JS, [1540, 120], mode="runOnceForAllItems"),
        code_node("Build Booking Reminder Text", BUILD_BOOKING_REMINDER_TEXT_JS, [1760, 120]),
        if_bool_node("Should Send Reminder?", [1980, 120], "={{ $json.reminder_gate_passed }}"),
        slack_node("Slack Booking Reminder", [2200, 0], "={{ $json.slack_text }}"),
        code_node("Mark Reminder Sent", MARK_BOOKING_REMINDER_SENT_JS, [2420, 0]),
        code_node("Skip Reminder", SKIP_BOOKING_REMINDER_JS, [2200, 240]),
        code_node("Log Slack Reminder Error", LOG_SLACK_BOOKING_REMINDER_ERROR_JS, [2420, 160]),
        code_node("Prepare Booking Reminder Audit", PREPARE_BOOKING_REMINDER_AUDIT_JS, [2640, 120]),
        if_bool_node("Should Update Lead?", [2860, 120], "={{ $json.booking_reminder_sent }}"),
        sheets_update("Update Lead Reminder Status", [3080, 0], "leads", "lead_id", {
            "lead_id": "={{ $json.lead_id }}",
            "booking_reminder_sent": "={{ true }}",
            "booking_reminder_at": "={{ $json.booking_reminder_at }}",
            "updated_at": "={{ $json.updated_at }}",
        }, retry=True),
        code_node("Handle Update Reminder Error", HANDLE_UPDATE_REMINDER_ERROR_JS, [3300, 0]),
        sheets_append("Write Booking Reminder Audit", [3300, 200], "audit_logs", {
            "lead_id": "={{ $json.lead_id }}",
            "correlation_id": "={{ $json.correlation_id }}",
            "event": "={{ $json.audit_event }}",
            "new_value": "={{ $json.reminder_status }}",
            "workflow": "B2B Lead Booking Follow-up",
            "timestamp": "={{ $json.updated_at || new Date().toISOString() }}",
        }, retry=True),
        sheets_append("Write Reminder Read Error Log", [440, 400], "error_logs", {
            "workflow": "B2B Lead Booking Follow-up",
            "execution_id": "={{ $execution.id }}",
            "node": "Read Leads For Reminder",
            "message": "={{ $json.read_error_message }}",
            "stack": "",
            "correlation_id": "",
            "retry_suggestion": "retry_sheets_read",
            "timestamp": "={{ new Date().toISOString() }}",
        }),
        noop("Booking Follow-up End", [3520, 200]),
        noop("No Due Reminders End", [1540, 320]),
        noop("Booking Follow-up Failed End", [660, 400]),
    ]
    conn = {}
    connect(conn, "Daily 10am", "Read Leads For Reminder")
    connect(conn, "Read Leads For Reminder", "Read config_main")
    connect_error(conn, "Read Leads For Reminder", "Handle Booking Read Error")
    connect(conn, "Read config_main", "Normalize config_main")
    connect_error(conn, "Read config_main", "Handle config_main Read Error")
    connect(conn, "Normalize config_main", "Read config_notifications")
    connect(conn, "Handle config_main Read Error", "Read config_notifications")
    connect(conn, "Read config_notifications", "Normalize config_notifications")
    connect_error(conn, "Read config_notifications", "Handle config_notifications Read Error")
    connect(conn, "Normalize config_notifications", "Load Booking Config")
    connect(conn, "Handle config_notifications Read Error", "Load Booking Config")
    connect(conn, "Load Booking Config", "Filter Due Booking Reminders")
    connect(conn, "Filter Due Booking Reminders", "Has Due Reminders?")
    connect(conn, "Has Due Reminders?", "Expand Due Leads", src_output=0)
    connect(conn, "Has Due Reminders?", "No Due Reminders End", src_output=1)
    connect(conn, "Expand Due Leads", "Build Booking Reminder Text")
    connect(conn, "Build Booking Reminder Text", "Should Send Reminder?")
    connect(conn, "Should Send Reminder?", "Slack Booking Reminder", src_output=0)
    connect(conn, "Should Send Reminder?", "Skip Reminder", src_output=1)
    connect(conn, "Slack Booking Reminder", "Mark Reminder Sent", src_output=0)
    connect_error(conn, "Slack Booking Reminder", "Log Slack Reminder Error")
    connect(conn, "Mark Reminder Sent", "Prepare Booking Reminder Audit")
    connect(conn, "Skip Reminder", "Prepare Booking Reminder Audit")
    connect(conn, "Log Slack Reminder Error", "Prepare Booking Reminder Audit")
    connect(conn, "Prepare Booking Reminder Audit", "Should Update Lead?")
    connect(conn, "Should Update Lead?", "Update Lead Reminder Status", src_output=0)
    connect(conn, "Should Update Lead?", "Write Booking Reminder Audit", src_output=1)
    connect(conn, "Update Lead Reminder Status", "Write Booking Reminder Audit", src_output=0)
    connect_error(conn, "Update Lead Reminder Status", "Handle Update Reminder Error")
    connect(conn, "Handle Update Reminder Error", "Write Booking Reminder Audit")
    connect(conn, "Write Booking Reminder Audit", "Booking Follow-up End")
    connect(conn, "No Due Reminders End", "Booking Follow-up End")
    connect(conn, "Handle Booking Read Error", "Write Reminder Read Error Log")
    connect(conn, "Write Reminder Read Error Log", "Booking Follow-up Failed End")
    save_workflow(
        "B2B Lead Booking Follow-up.json",
        "B2B Lead Booking Follow-up",
        nodes,
        conn,
        error_workflow="B2B Lead Error Handler",
    )


def build_calendly_webhook() -> None:
    nodes = [
        webhook_node(
            "Calendly Webhook",
            [0, 200],
            "calendly",
            http_method="POST",
            response_mode="responseNode",
            raw_body=True,
        ),
        code_node("Verify Calendly Signature", VERIFY_CALENDLY_SIGNATURE_JS, [220, 200]),
        if_bool_node("Signature Valid?", [440, 200], "={{ $json.signature_valid }}"),
        sheets_append("Write Invalid Signature Audit", [660, 400], "audit_logs", {
            "lead_id": "",
            "correlation_id": "",
            "event": "calendly_signature_invalid",
            "new_value": "={{ $json.signature_error }}",
            "workflow": "B2B Lead Calendly Webhook",
            "timestamp": "={{ new Date().toISOString() }}",
        }),
        respond_to_webhook_node(
            "Respond 401",
            [880, 400],
            response_code=401,
            response_body='={{ { "ok": false, "error": $json.signature_error || "invalid_signature" } }}',
        ),
        code_node("Normalize Calendly Payload", NORMALIZE_CALENDLY_JS, [660, 200]),
        sheets_read("Read All Leads", [880, 200], "leads", always_output_data=True, retry=True),
        code_node(
            "Match Lead By Email",
            MATCH_LEAD_BY_EMAIL_JS,
            [1100, 200],
            mode="runOnceForAllItems",
        ),
        code_node("Handle Calendly Read Error", HANDLE_CALENDLY_READ_ERROR_JS, [880, 400]),
        if_bool_node("Lead Found?", [1320, 200], "={{ $json.lead_found }}"),
        sheets_update("Update Lead Meeting", [1540, 120], "leads", "lead_id", {
            "lead_id": "={{ $json.lead_id }}",
            "meeting_status": "={{ $json.meeting_status }}",
            "meeting_time": "={{ $json.meeting_time }}",
            "calendly_event_uri": "={{ $json.calendly_event_uri }}",
            "calendly_invitee_email": "={{ $json.calendly_invitee_email }}",
            "updated_at": "={{ $json.updated_at }}",
        }, retry=True),
        code_node("Handle Update Meeting Error", HANDLE_UPDATE_MEETING_ERROR_JS, [1760, 120]),
        sheets_append("Write Calendly Update Error Log", [1980, 240], "error_logs", {
            "workflow": "B2B Lead Calendly Webhook",
            "execution_id": "={{ $execution.id }}",
            "node": "Update Lead Meeting",
            "message": "={{ $json.sheets_error_message }}",
            "stack": "",
            "correlation_id": "={{ $json.correlation_id }}",
            "retry_suggestion": "retry_sheets_update",
            "timestamp": "={{ new Date().toISOString() }}",
        }),
        code_node(
            "Build Calendly Slack Text",
            BUILD_CALENDLY_SLACK_TEXT_JS,
            [1760, 0],
            mode="runOnceForAllItems",
        ),
        slack_node(
            "Slack Calendly Notify",
            [1980, 0],
            "={{ $json.slack_text }}",
        ),
        code_node("Log Calendly Slack Error", LOG_CALENDLY_SLACK_ERROR_JS, [2200, 120]),
        code_node("Prepare Calendly Audit", PREPARE_CALENDLY_AUDIT_JS, [2200, 0]),
        sheets_append("Write Calendly Audit Log", [2420, 0], "audit_logs", {
            "lead_id": "={{ $json.lead_id }}",
            "correlation_id": "={{ $json.correlation_id }}",
            "event": "={{ $json.audit_event }}",
            "old_value": "={{ $json.previous_meeting_status || '' }}",
            "new_value": "={{ $json.meeting_status }}",
            "workflow": "B2B Lead Calendly Webhook",
            "timestamp": "={{ $json.updated_at || new Date().toISOString() }}",
        }, retry=True),
        sheets_append("Write Unmatched Audit Log", [1540, 320], "audit_logs", {
            "lead_id": "",
            "correlation_id": "={{ $json.correlation_id }}",
            "event": "={{ $json.audit_event || 'calendly_unmatched' }}",
            "new_value": "={{ $json.invitee_email || $json.calendly_invitee_email || '' }}",
            "workflow": "B2B Lead Calendly Webhook",
            "timestamp": "={{ $json.updated_at || new Date().toISOString() }}",
        }),
        respond_to_webhook_node("Respond 200", [2640, 200]),
        noop("Calendly Webhook End", [2860, 200]),
    ]
    conn = {}
    connect(conn, "Calendly Webhook", "Verify Calendly Signature")
    connect(conn, "Verify Calendly Signature", "Signature Valid?")
    connect(conn, "Signature Valid?", "Normalize Calendly Payload", src_output=0)
    connect(conn, "Signature Valid?", "Write Invalid Signature Audit", src_output=1)
    connect(conn, "Write Invalid Signature Audit", "Respond 401")
    connect(conn, "Normalize Calendly Payload", "Read All Leads")
    connect(conn, "Read All Leads", "Match Lead By Email")
    connect_error(conn, "Read All Leads", "Handle Calendly Read Error")
    connect(conn, "Handle Calendly Read Error", "Write Unmatched Audit Log")
    connect(conn, "Match Lead By Email", "Lead Found?")
    connect(conn, "Lead Found?", "Update Lead Meeting", src_output=0)
    connect(conn, "Lead Found?", "Write Unmatched Audit Log", src_output=1)
    connect(conn, "Update Lead Meeting", "Build Calendly Slack Text")
    connect_error(conn, "Update Lead Meeting", "Handle Update Meeting Error")
    connect(conn, "Handle Update Meeting Error", "Write Calendly Update Error Log")
    connect(conn, "Write Calendly Update Error Log", "Prepare Calendly Audit")
    connect(conn, "Build Calendly Slack Text", "Slack Calendly Notify")
    connect(conn, "Slack Calendly Notify", "Prepare Calendly Audit")
    connect_error(conn, "Slack Calendly Notify", "Log Calendly Slack Error")
    connect(conn, "Log Calendly Slack Error", "Prepare Calendly Audit")
    connect(conn, "Prepare Calendly Audit", "Write Calendly Audit Log")
    connect(conn, "Write Calendly Audit Log", "Respond 200")
    connect(conn, "Write Unmatched Audit Log", "Respond 200")
    connect(conn, "Respond 200", "Calendly Webhook End")
    save_workflow(
        "B2B Lead Calendly Webhook.json",
        "B2B Lead Calendly Webhook",
        nodes,
        conn,
        error_workflow="B2B Lead Error Handler",
    )


def build_slack_actions() -> None:
    nodes = [
        webhook_node(
            "Slack Interactions Webhook",
            [0, 200],
            "slack-interactions",
            http_method="POST",
            response_mode="responseNode",
            raw_body=True,
        ),
        code_node("Verify Slack Signature", VERIFY_SLACK_SIGNATURE_JS, [220, 200]),
        if_bool_node("Signature Valid?", [440, 200], "={{ $json.signature_valid }}"),
        sheets_append("Write Invalid Signature Audit", [660, 400], "audit_logs", {
            "lead_id": "",
            "correlation_id": "",
            "event": "slack_action_signature_invalid",
            "new_value": "={{ $json.signature_error }}",
            "workflow": "B2B Lead Slack Actions",
            "timestamp": "={{ new Date().toISOString() }}",
        }),
        respond_to_webhook_node(
            "Respond 401",
            [880, 400],
            response_code=401,
            response_body='={{ { "ok": false, "error": $json.signature_error || "invalid_signature" } }}',
        ),
        code_node("Parse Slack Payload", PARSE_SLACK_PAYLOAD_JS, [660, 200]),
        if_bool_node("Parse OK?", [880, 200], "={{ !$json.parse_error }}"),
        sheets_append("Write Parse Error Audit", [1100, 400], "audit_logs", {
            "lead_id": "",
            "correlation_id": "",
            "event": "slack_action_parse_failed",
            "new_value": "={{ $json.parse_error_message || 'payload_parse_failed' }}",
            "workflow": "B2B Lead Slack Actions",
            "timestamp": "={{ new Date().toISOString() }}",
        }),
        respond_to_webhook_node(
            "Respond 400",
            [1320, 400],
            response_code=400,
            response_body='={{ { "ok": false, "error": $json.parse_error_message || "invalid_payload" } }}',
        ),
        respond_to_webhook_node("Respond 200 Ack", [1100, 0]),
        if_bool_node("Admin Allowed?", [1320, 200], "={{ $json.admin_allowed }}"),
        code_node("Set Unauthorized Reply", SET_UNAUTHORIZED_REPLY_JS, [1320, 400]),
        code_node("Resolve Lead Action", RESOLVE_LEAD_ACTION_JS, [1320, 200]),
        if_bool_node("Known Action?", [1540, 200], "={{ !$json.unknown_action }}"),
        sheets_read("Read All Leads For Slack", [1760, 120], "leads", always_output_data=True, retry=True),
        code_node(
            "Match Lead By ID",
            MATCH_LEAD_BY_ID_JS,
            [1980, 120],
            mode="runOnceForAllItems",
        ),
        code_node("Handle Slack Read Error", HANDLE_SLACK_READ_ERROR_JS, [1760, 320]),
        if_bool_node("Lead Found?", [2200, 120], "={{ $json.lead_found }}"),
        if_bool_node(
            "Already Assigned?",
            [2420, 120],
            "={{ $json.action_id === 'assign_lead' && $json.already_assigned }}",
        ),
        code_node("Prepare Slack Ack", PREPARE_SLACK_ACK_JS, [2640, 0]),
        slack_update_blocks_node("Slack Update Ack", [2860, 0]),
        sheets_update("Update Lead Review", [3080, 0], "leads", "lead_id", {
            "lead_id": "={{ $('Match Lead By ID').first().json.lead_id }}",
            "review_status": "={{ $('Match Lead By ID').first().json.review_status }}",
            "recommended_action": "={{ $('Match Lead By ID').first().json.recommended_action }}",
            "lead_stage": "={{ $('Match Lead By ID').first().json.lead_stage }}",
            "owner_id": "={{ $('Match Lead By ID').first().json.owner_id }}",
            "reviewer": "={{ $('Match Lead By ID').first().json.reviewer }}",
            "review_notes": "={{ $('Match Lead By ID').first().json.review_notes }}",
            "reviewed_at": "={{ $('Match Lead By ID').first().json.reviewed_at }}",
            "updated_at": "={{ $('Match Lead By ID').first().json.updated_at }}",
        }, retry=True),
        code_node("Handle Update Review Error", HANDLE_UPDATE_REVIEW_ERROR_JS, [3300, 200]),
        if_bool_node(
            "Should Trigger CRM?",
            [3520, 0],
            "={{ ['assign_lead', 'nurture_lead'].includes($('Match Lead By ID').first().json.action_id) }}",
        ),
        sheets_read("Read config_main For CRM", [3740, -80], "config_main", retry=True),
        code_node(
            "Normalize config_main For CRM",
            normalize_config_js("config_main"),
            [3960, -120],
            mode="runOnceForAllItems",
        ),
        sheets_read("Read config_notifications For CRM", [3960, -40], "config_notifications", retry=True),
        code_node(
            "Normalize config_notifications For CRM",
            normalize_config_js("config_notifications"),
            [4180, -40],
            mode="runOnceForAllItems",
        ),
        code_node("Prepare Slack CRM Payload", PREPARE_SLACK_CRM_PAYLOAD_JS, [4400, -80]),
        execute_workflow(
            "Execute Post-Assign CRM Sync",
            [4620, -80],
            "B2B Lead CRM Sync Notification",
            inputs=SLACK_TO_CRM_INPUTS,
            on_error="continueRegularOutput",
        ),
        sheets_append("Write Slack Update Error Log", [3520, 200], "error_logs", {
            "workflow": "B2B Lead Slack Actions",
            "execution_id": "={{ $execution.id }}",
            "node": "Update Lead Review",
            "message": "={{ $json.sheets_error_message }}",
            "stack": "",
            "correlation_id": "={{ $json.correlation_id }}",
            "retry_suggestion": "retry_sheets_update",
            "timestamp": "={{ new Date().toISOString() }}",
        }),
        code_node("Prepare Slack Response Body", PREPARE_SLACK_RESPONSE_BODY_JS, [4840, 200]),
        if_bool_node(
            "Can Update Slack Message?",
            [5060, 200],
            "={{ $json.has_slack_message_target }}",
        ),
        slack_update_blocks_node("Slack Update Final", [5280, 120]),
        http_json_post_node(
            "Post Slack Final Fallback",
            [5280, 320],
            "={{ $json.response_url }}",
            "={{ $json.slack_message_body }}",
        ),
        code_node("Log Slack Response Error", LOG_SLACK_RESPONSE_ERROR_JS, [5500, 320]),
        code_node("Prepare Slack Action Audit", PREPARE_SLACK_ACTION_AUDIT_JS, [5500, 200]),
        sheets_append("Write Slack Action Audit Log", [5720, 200], "audit_logs", {
            "lead_id": "={{ $json.lead_id }}",
            "correlation_id": "={{ $json.correlation_id }}",
            "event": "={{ $json.audit_event }}",
            "old_value": "={{ ($json.previous_review_status || '') + '/' + ($json.previous_lead_stage || '') }}",
            "new_value": "={{ ($json.new_review_status || '') + '/' + ($json.new_lead_stage || '') + ' by ' + ($json.slack_user_id || '') }}",
            "workflow": "B2B Lead Slack Actions",
            "timestamp": "={{ $json.updated_at || new Date().toISOString() }}",
        }, retry=True),
        noop("Slack Actions End", [5940, 200]),
    ]
    conn = {}
    connect(conn, "Slack Interactions Webhook", "Verify Slack Signature")
    connect(conn, "Verify Slack Signature", "Signature Valid?")
    connect(conn, "Signature Valid?", "Parse Slack Payload", src_output=0)
    connect(conn, "Signature Valid?", "Write Invalid Signature Audit", src_output=1)
    connect(conn, "Write Invalid Signature Audit", "Respond 401")
    connect(conn, "Parse Slack Payload", "Parse OK?")
    connect(conn, "Parse OK?", "Respond 200 Ack", src_output=0)
    connect(conn, "Respond 200 Ack", "Admin Allowed?")
    connect(conn, "Parse OK?", "Write Parse Error Audit", src_output=1)
    connect(conn, "Write Parse Error Audit", "Respond 400")
    connect(conn, "Admin Allowed?", "Resolve Lead Action", src_output=0)
    connect(conn, "Admin Allowed?", "Set Unauthorized Reply", src_output=1)
    connect(conn, "Set Unauthorized Reply", "Prepare Slack Response Body")
    connect(conn, "Resolve Lead Action", "Known Action?")
    connect(conn, "Known Action?", "Read All Leads For Slack", src_output=0)
    connect(conn, "Known Action?", "Prepare Slack Response Body", src_output=1)
    connect(conn, "Read All Leads For Slack", "Match Lead By ID")
    connect_error(conn, "Read All Leads For Slack", "Handle Slack Read Error")
    connect(conn, "Handle Slack Read Error", "Prepare Slack Response Body")
    connect(conn, "Match Lead By ID", "Lead Found?")
    connect(conn, "Lead Found?", "Already Assigned?", src_output=0)
    connect(conn, "Lead Found?", "Prepare Slack Response Body", src_output=1)
    connect(conn, "Already Assigned?", "Prepare Slack Response Body", src_output=0)
    connect(conn, "Already Assigned?", "Prepare Slack Ack", src_output=1)
    connect(conn, "Prepare Slack Ack", "Slack Update Ack")
    connect(conn, "Slack Update Ack", "Update Lead Review")
    connect_error(conn, "Slack Update Ack", "Update Lead Review")
    connect(conn, "Update Lead Review", "Should Trigger CRM?")
    connect_error(conn, "Update Lead Review", "Handle Update Review Error")
    connect(conn, "Should Trigger CRM?", "Read config_main For CRM", src_output=0)
    connect(conn, "Should Trigger CRM?", "Prepare Slack Response Body", src_output=1)
    connect(conn, "Read config_main For CRM", "Normalize config_main For CRM")
    connect_error(conn, "Read config_main For CRM", "Normalize config_main For CRM")
    connect(conn, "Normalize config_main For CRM", "Read config_notifications For CRM")
    connect(conn, "Read config_notifications For CRM", "Normalize config_notifications For CRM")
    connect_error(conn, "Read config_notifications For CRM", "Normalize config_notifications For CRM")
    connect(conn, "Normalize config_notifications For CRM", "Prepare Slack CRM Payload")
    connect(conn, "Prepare Slack CRM Payload", "Execute Post-Assign CRM Sync")
    connect(conn, "Execute Post-Assign CRM Sync", "Prepare Slack Response Body")
    connect_error(conn, "Execute Post-Assign CRM Sync", "Prepare Slack Response Body")
    connect(conn, "Handle Update Review Error", "Write Slack Update Error Log")
    connect(conn, "Write Slack Update Error Log", "Prepare Slack Response Body")
    connect(conn, "Prepare Slack Response Body", "Can Update Slack Message?")
    connect(conn, "Can Update Slack Message?", "Slack Update Final", src_output=0)
    connect(conn, "Can Update Slack Message?", "Post Slack Final Fallback", src_output=1)
    connect(conn, "Slack Update Final", "Prepare Slack Action Audit")
    connect_error(conn, "Slack Update Final", "Log Slack Response Error")
    connect(conn, "Post Slack Final Fallback", "Prepare Slack Action Audit")
    connect_error(conn, "Post Slack Final Fallback", "Log Slack Response Error")
    connect(conn, "Log Slack Response Error", "Prepare Slack Action Audit")
    connect(conn, "Prepare Slack Action Audit", "Write Slack Action Audit Log")
    connect(conn, "Write Slack Action Audit Log", "Slack Actions End")
    save_workflow(
        "B2B Lead Slack Actions.json",
        "B2B Lead Slack Actions",
        nodes,
        conn,
        error_workflow="B2B Lead Error Handler",
    )


def main() -> None:
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    build_error_handler()
    build_intake()
    build_enrichment_scoring()
    build_crm_sync_notification()
    build_daily_summary()
    build_weekly_summary()
    build_booking_followup()
    build_calendly_webhook()
    build_slack_actions()


if __name__ == "__main__":
    main()

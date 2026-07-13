#!/usr/bin/env python3
"""Sync n8n UI exports from workflows/workflows-new/ into canonical workflows/*.json.

Applies repo hygiene (credential placeholders, errorWorkflow name, active=false)
and fixes known regressions from raw exports before writing.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / "workflows"
EXPORT_DIR = WORKFLOWS_DIR / "workflows-new"
ERROR_WORKFLOW_NAME = "B2B Lead Error Handler"

PLACEHOLDER_CREDS = {
    "googleSheetsOAuth2Api": {"id": "GOOGLE_SHEETS_CREDENTIAL_ID", "name": "Google Sheets account"},
    "hubspotOAuth2Api": {"id": "HUBSPOT_CREDENTIAL_ID", "name": "HubSpot account"},
    "slackOAuth2Api": {"id": "SLACK_CREDENTIAL_ID", "name": "Slack account"},
}

EXECUTE_TARGETS = {
    "Execute Enrichment Scoring": "B2B Lead Enrichment Scoring",
    "Execute CRM Sync": "B2B Lead CRM Sync Notification",
    "Execute Post-Assign CRM Sync": "B2B Lead CRM Sync Notification",
}

REMOVE_NODE_NAMES = {"Final Status Write Failed End1"}

ATTACH_HUNTER_DATA_JS = """const lead = $('Domain Enrichment').item.json;
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
};"""

MARK_DRAFT_PENDING_REVIEW_JS = """const lead = $input.item.json;
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
};"""

CODE_NODE_EACH_ITEM = {
    "Attach Hunter Data",
    "Check Sales Memo Eligible",
    "Merge Sales Memo",
    "Skip Sales Memo",
    "Handle Sales Memo Failure",
    "Skip Manual Review",
    "Prepare Slack Ack",
    "Mark Draft Pending Review",
    "Normalize Enriched Lead",
}

NORMALIZE_ENRICHED_LEAD_FIELD_DEFAULTS = {
    "industry": "lead.industry ?? ''",
    "company_size": "lead.company_size ?? ''",
    "content_summary": "lead.content_summary ?? ''",
    "intent_signals": "lead.intent_signals ?? ''",
    "enrichment_summary": "lead.enrichment_summary ?? ''",
    "enrichment_status": "lead.enrichment_status ?? ''",
}


def normalize_credentials(node: dict) -> None:
    creds = node.get("credentials")
    if not creds:
        return
    if "googleSheetsOAuth2Api" in creds:
        node["credentials"] = {"googleSheetsOAuth2Api": PLACEHOLDER_CREDS["googleSheetsOAuth2Api"]}
    elif "hubspotAppToken" in creds or "hubspotOAuth2Api" in creds:
        node["credentials"] = {"hubspotOAuth2Api": PLACEHOLDER_CREDS["hubspotOAuth2Api"]}
    elif "slackApi" in creds or "slackOAuth2Api" in creds:
        node["credentials"] = {"slackOAuth2Api": PLACEHOLDER_CREDS["slackOAuth2Api"]}


def normalize_hubspot_upsert(node: dict) -> None:
    if node.get("name") != "HubSpot Upsert Contact":
        return
    params = node.setdefault("parameters", {})
    params.setdefault("resource", "contact")
    params.setdefault("operation", "upsert")
    params.setdefault("email", "={{ $json.contact_email }}")
    params.setdefault(
        "additionalFields",
        {
            "firstName": "={{ ($json.contact_name || '').split(' ')[0] }}",
            "lastName": "={{ ($json.contact_name || '').split(' ').slice(1).join(' ') }}",
            "companyName": "={{ $json.company_name }}",
            "jobTitle": "={{ $json.contact_role }}",
        },
    )
    node["credentials"] = {"hubspotOAuth2Api": PLACEHOLDER_CREDS["hubspotOAuth2Api"]}
    node["retryOnFail"] = True
    node["maxTries"] = 3
    node["waitBetweenTries"] = 5000
    node["onError"] = "continueErrorOutput"


def normalize_execute_workflow(node: dict) -> None:
    name = node.get("name")
    if name not in EXECUTE_TARGETS:
        return
    params = node.setdefault("parameters", {})
    params["workflowId"] = {"__rl": True, "mode": "name", "value": EXECUTE_TARGETS[name]}


def fix_parse_slack_payload(node: dict) -> None:
    if node.get("name") != "Parse Slack Payload":
        return
    js = node.get("parameters", {}).get("jsCode", "")
    if "payload.container?.message_ts" in js:
        return
    js = js.replace(
        "message_ts: payload.message?.ts || '',",
        "message_ts: payload.message?.ts || payload.container?.message_ts || '',",
    )
    node["parameters"]["jsCode"] = js


def fix_attach_hunter_data(node: dict) -> None:
    if node.get("name") != "Attach Hunter Data":
        return
    node.setdefault("parameters", {})["jsCode"] = ATTACH_HUNTER_DATA_JS


def fix_normalize_enriched_lead(node: dict) -> None:
    if node.get("name") != "Normalize Enriched Lead":
        return
    js = node.get("parameters", {}).get("jsCode", "")
    for field, expr in NORMALIZE_ENRICHED_LEAD_FIELD_DEFAULTS.items():
        bare = f"{field}: lead.{field},"
        fixed = f"{field}: {expr},"
        if bare in js and fixed not in js:
            js = js.replace(bare, fixed)
    node["parameters"]["jsCode"] = js


def fix_mark_draft_pending_review(node: dict) -> None:
    if node.get("name") != "Mark Draft Pending Review":
        return
    node.setdefault("parameters", {})["jsCode"] = MARK_DRAFT_PENDING_REVIEW_JS
    node["parameters"]["mode"] = "runOnceForEachItem"


def fix_code_node_mode(node: dict) -> None:
    name = node.get("name")
    if name not in CODE_NODE_EACH_ITEM:
        return
    node.setdefault("parameters", {})["mode"] = "runOnceForEachItem"


def fix_tally_webhook_raw_body(node: dict) -> None:
    if node.get("name") != "Tally Webhook":
        return
    node.setdefault("parameters", {}).setdefault("options", {})["rawBody"] = True


def fix_calendly_webhook_raw_body(node: dict) -> None:
    if node.get("name") != "Calendly Webhook":
        return
    node.setdefault("parameters", {}).setdefault("options", {})["rawBody"] = True


def remove_duplicate_nodes(workflow: dict) -> None:
    nodes = workflow.get("nodes", [])
    workflow["nodes"] = [n for n in nodes if n.get("name") not in REMOVE_NODE_NAMES]

    connections = workflow.get("connections", {})
    end_name = "Final Status Write Failed End"
    for src, conn in list(connections.items()):
        if src in REMOVE_NODE_NAMES:
            del connections[src]
            continue
        for branch in conn.get("main", []):
            for edge in branch:
                if edge.get("node") in REMOVE_NODE_NAMES:
                    edge["node"] = end_name
    workflow["connections"] = connections


def merge_settings(new_settings: dict, old_settings: dict, workflow_name: str) -> dict:
    merged = copy.deepcopy(new_settings)
    if workflow_name == ERROR_WORKFLOW_NAME:
        merged.pop("errorWorkflow", None)
    else:
        merged["errorWorkflow"] = ERROR_WORKFLOW_NAME
    merged["callerPolicy"] = old_settings.get("callerPolicy", merged.get("callerPolicy", "workflowsFromSameOwner"))
    merged.pop("binaryMode", None)
    merged.pop("availableInMCP", None)
    merged.pop("timeSavedMode", None)
    return merged


def sanitize_workflow(workflow: dict, old_workflow: dict) -> dict:
    workflow = copy.deepcopy(workflow)
    workflow_name = workflow.get("name", "")
    workflow["settings"] = merge_settings(
        workflow.get("settings", {}),
        old_workflow.get("settings", {}),
        workflow_name,
    )
    workflow["active"] = False
    workflow.pop("pinData", None)
    meta = workflow.get("meta") or {}
    meta["templateCredsSetupCompleted"] = False
    workflow["meta"] = meta

    remove_duplicate_nodes(workflow)

    for node in workflow.get("nodes", []):
        normalize_credentials(node)
        normalize_execute_workflow(node)
        normalize_hubspot_upsert(node)
        fix_parse_slack_payload(node)
        fix_attach_hunter_data(node)
        fix_normalize_enriched_lead(node)
        fix_mark_draft_pending_review(node)
        fix_code_node_mode(node)
        fix_tally_webhook_raw_body(node)
        fix_calendly_webhook_raw_body(node)

    if not workflow.get("tags"):
        workflow["tags"] = [{"name": "crm-workflow"}]

    return workflow


def sync_file(export_name: str) -> None:
    export_path = EXPORT_DIR / export_name
    target_path = WORKFLOWS_DIR / export_name
    if not export_path.exists():
        raise FileNotFoundError(export_path)

    exported = json.loads(export_path.read_text(encoding="utf-8"))
    old_workflow = json.loads(target_path.read_text(encoding="utf-8")) if target_path.exists() else {}
    workflow = sanitize_workflow(exported, old_workflow)
    target_path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    print(f"Synced {target_path.name}")


def main() -> None:
    if not EXPORT_DIR.is_dir():
        raise SystemExit(f"Missing export directory: {EXPORT_DIR}")

    for export_path in sorted(EXPORT_DIR.glob("*.json")):
        sync_file(export_path.name)

    print(f"Done. Source: {EXPORT_DIR}")


if __name__ == "__main__":
    main()

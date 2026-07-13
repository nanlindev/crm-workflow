#!/usr/bin/env python3
"""Patch New.json config section → serial wrapper pattern, write Enrichment workflow."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW_PATH = ROOT / "workflows" / "New.json"
OUT_PATH = ROOT / "workflows" / "B2B Lead Enrichment Scoring.json"

ERROR_PRELUDE = """const item = $input.item;
const errJson = item.json || {};
const errorObj = item.error || errJson.error || {};
const errorMessage =
  errorObj.message ||
  errorObj.description ||
  errJson.message ||
  errJson.description ||
  (typeof errJson.error === 'string' ? errJson.error : null) ||
  '{default_msg}';
"""


def nid() -> str:
    return str(uuid.uuid4())


def normalize_config_js(table: str) -> str:
    return f"""const rows = $input.all().map(i => i.json).filter(r => r && !r.config_table);
return {{
  config_table: '{table}',
  rows,
  load_failed: false,
  load_error_message: '',
}};
"""


def handle_config_error_js(table: str, read_node: str) -> str:
    default_msg = f"Unknown {read_node} error"
    prelude = ERROR_PRELUDE.replace("{default_msg}", default_msg)
    return (
        prelude
        + f"""
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
    )


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

HOLD_LEAD_JS = "return $input.item.json;"

CONFIG_CHAIN = [
    ("config_main", "Read config_main"),
    ("config_routing", "Read config_routing"),
    ("config_notifications", "Read config_notifications"),
    ("config_review", "Read config_review"),
]

REMOVE_NODES = {
    "Merge Config 1",
    "Merge Config 2",
    "Merge Config 3",
    "Handle Config Load Error",
}


def code_node(name: str, js: str, position: list[int], *, mode: str = "runOnceForEachItem") -> dict:
    return {
        "parameters": {"mode": mode, "jsCode": js},
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": position,
        "id": nid(),
        "name": name,
    }


def patch_workflow(data: dict) -> dict:
    wf = deepcopy(data)
    wf["name"] = "B2B Lead Enrichment Scoring"

    # Keep trigger + downstream enrichment nodes; drop old config merge/handler.
    kept_nodes = [n for n in wf["nodes"] if n["name"] not in REMOVE_NODES]
    by_name = {n["name"]: n for n in kept_nodes}

    trigger = by_name["When Executed by Another Workflow"]
    base_x, base_y = trigger["position"]

    # Hold Lead right after trigger.
    hold_lead = code_node("Hold Lead", HOLD_LEAD_JS, [base_x + 224, base_y])
    new_nodes = [hold_lead]

    x = base_x + 448
    read_nodes: list[str] = []
    for table, read_name in CONFIG_CHAIN:
        read_node = by_name[read_name]
        read_node["position"] = [x, base_y]
        read_node["alwaysOutputData"] = True
        if read_node.get("credentials", {}).get("googleSheetsOAuth2Api"):
            read_node["credentials"]["googleSheetsOAuth2Api"]["id"] = "GOOGLE_SHEETS_CREDENTIAL_ID"
            read_node["credentials"]["googleSheetsOAuth2Api"]["name"] = "Google Sheets account"
        read_nodes.append(read_name)

        norm_name = f"Normalize {read_name.replace('Read ', '')}"
        handle_name = f"Handle {read_name.replace('Read ', '')} Error"
        new_nodes.append(
            code_node(norm_name, normalize_config_js(table), [x + 112, base_y - 80], mode="runOnceForAllItems")
        )
        new_nodes.append(
            code_node(handle_name, handle_config_error_js(table, read_name), [x + 112, base_y + 80])
        )
        x += 336

    build_node = by_name["Build Global Config"]
    build_node["position"] = [x, base_y]
    build_node["parameters"]["jsCode"] = BUILD_GLOBAL_CONFIG_JS

    # Replace sheets creds on Update Lead Scores
    for node in kept_nodes:
        cred = node.get("credentials", {}).get("googleSheetsOAuth2Api")
        if cred:
            cred["id"] = "GOOGLE_SHEETS_CREDENTIAL_ID"
            cred["name"] = "Google Sheets account"

    wf["nodes"] = kept_nodes + new_nodes

    conn: dict = {}
    conn["When Executed by Another Workflow"] = {"main": [[{"node": "Hold Lead", "type": "main", "index": 0}]]}
    conn["Hold Lead"] = {"main": [[{"node": "Read config_main", "type": "main", "index": 0}]]}

    for i, (table, read_name) in enumerate(CONFIG_CHAIN):
        short = read_name.replace("Read ", "")
        norm_name = f"Normalize {short}"
        handle_name = f"Handle {short} Error"
        next_read = read_nodes[i + 1] if i + 1 < len(read_nodes) else "Build Global Config"

        conn[read_name] = {
            "main": [
                [{"node": norm_name, "type": "main", "index": 0}],
                [{"node": handle_name, "type": "main", "index": 0}],
            ]
        }
        conn[norm_name] = {"main": [[{"node": next_read, "type": "main", "index": 0}]]}
        conn[handle_name] = {"main": [[{"node": next_read, "type": "main", "index": 0}]]}

    # Preserve all non-config connections from original file.
    old_conn = data["connections"]
    for key, value in old_conn.items():
        if key in REMOVE_NODES or key.startswith("Merge Config"):
            continue
        if key in {
            "When Executed by Another Workflow",
            "Read config_main",
            "Read config_routing",
            "Read config_notifications",
            "Read config_review",
            "Build Global Config",
            "Handle Config Load Error",
        }:
            continue
        conn[key] = value

    conn["Build Global Config"] = {"main": [[{"node": "Domain Enrichment", "type": "main", "index": 0}]]}

    wf["connections"] = conn
    wf["pinData"] = {}
    settings = wf.get("settings", {})
    settings["executionOrder"] = settings.get("executionOrder", "v1")
    settings["errorWorkflow"] = "B2B Lead Error Handler"
    wf["settings"] = settings
    wf["meta"] = {"templateCredsSetupCompleted": False}
    return wf


def main() -> None:
    data = json.loads(NEW_PATH.read_text(encoding="utf-8"))
    patched = patch_workflow(data)
    OUT_PATH.write_text(json.dumps(patched, indent=2), encoding="utf-8")
    print(f"Patched {NEW_PATH.name} → {OUT_PATH}")


if __name__ == "__main__":
    main()

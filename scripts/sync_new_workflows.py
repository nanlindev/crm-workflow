#!/usr/bin/env python3
"""One-shot sync: apply UI-tuned *_New.json workflows into canonical repo exports."""

from __future__ import annotations

import copy
import json
from pathlib import Path

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / "workflows"

PAIRS: list[tuple[str, str, str | None]] = [
    ("Intake_New.json", "B2B Lead Intake.json", "B2B Lead Enrichment Scoring"),
    ("Enrichment_Scoring_New.json", "B2B Lead Enrichment Scoring.json", "B2B Lead CRM Sync Notification"),
    ("Notification_New.json", "B2B Lead CRM Sync Notification.json", None),
]

PLACEHOLDER_CREDS = {
    "googleSheetsOAuth2Api": {"id": "GOOGLE_SHEETS_CREDENTIAL_ID", "name": "Google Sheets account"},
    "hubspotOAuth2Api": {"id": "HUBSPOT_CREDENTIAL_ID", "name": "HubSpot account"},
    "slackOAuth2Api": {"id": "SLACK_CREDENTIAL_ID", "name": "Slack account"},
}

EXECUTE_NODES: dict[str, str] = {
    "Execute Enrichment Scoring": "B2B Lead Enrichment Scoring",
    "Execute CRM Sync": "B2B Lead CRM Sync Notification",
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


def normalize_hubspot_node(node: dict) -> None:
    if node.get("name") != "HubSpot Upsert Contact":
        return
    node["parameters"] = {
        "resource": "contact",
        "operation": "upsert",
        "email": "={{ $json.contact_email }}",
        "additionalFields": {
            "firstName": "={{ ($json.contact_name || '').split(' ')[0] }}",
            "lastName": "={{ ($json.contact_name || '').split(' ').slice(1).join(' ') }}",
            "companyName": "={{ $json.company_name }}",
            "jobTitle": "={{ $json.contact_role }}",
        },
    }
    node["credentials"] = {"hubspotOAuth2Api": PLACEHOLDER_CREDS["hubspotOAuth2Api"]}
    node["retryOnFail"] = True
    node["maxTries"] = 3
    node["waitBetweenTries"] = 5000
    node["onError"] = "continueErrorOutput"


def normalize_execute_workflow(node: dict) -> None:
    name = node.get("name")
    if name not in EXECUTE_NODES:
        return
    target = EXECUTE_NODES[name]
    params = node.setdefault("parameters", {})
    params["workflowId"] = {"__rl": True, "mode": "name", "value": target}
    # workflowInputs mapping preserved from New export


def merge_settings(new_settings: dict, old_settings: dict) -> dict:
    merged = copy.deepcopy(new_settings)
    if "errorWorkflow" in old_settings:
        merged["errorWorkflow"] = old_settings["errorWorkflow"]
    if "callerPolicy" in old_settings:
        merged["callerPolicy"] = old_settings["callerPolicy"]
    return merged


def sync_pair(new_name: str, target_name: str) -> None:
    new_path = WORKFLOWS_DIR / new_name
    target_path = WORKFLOWS_DIR / target_name
    old_path = target_path

    workflow = json.loads(new_path.read_text(encoding="utf-8"))
    old_workflow = json.loads(old_path.read_text(encoding="utf-8")) if old_path.exists() else {}

    workflow["settings"] = merge_settings(workflow.get("settings", {}), old_workflow.get("settings", {}))

    for node in workflow.get("nodes", []):
        normalize_credentials(node)
        normalize_execute_workflow(node)
        if target_name == "B2B Lead CRM Sync Notification.json":
            normalize_hubspot_node(node)

    target_path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    print(f"Wrote {target_path}")


def main() -> None:
    for new_name, target_name, _ in PAIRS:
        sync_pair(new_name, target_name)

    for new_name, _, _ in PAIRS:
        path = WORKFLOWS_DIR / new_name
        path.unlink()
        print(f"Removed {path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Post demo pre-seed leads to the Tally webhook, then print Sheets backdate hints.

Usage:
  python3 scripts/seed_demo_leads.py --url https://YOUR_N8N_HOST/webhook/tally-lead
  python3 scripts/seed_demo_leads.py --url ... --dry-run
  python3 scripts/seed_demo_leads.py --url ... --delay 12

After enrichment finishes, backdate rows in Google Sheets per printed instructions
(so Daily / Booking Follow-up look populated). Leave the live hero lead for Scenario A.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = ROOT / "scripts" / "demo_seed_leads.json"


def utc_day_offset(days: int, hour: int, minute: int, second: int = 0) -> str:
    base = datetime.now(timezone.utc) - timedelta(days=days)
    dt = base.replace(hour=hour, minute=minute, second=second, microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_created_at(token: str) -> str | None:
    if not token or token == "keep":
        return None
    # YESTERDAY_UTC_10:15:00Z / TWO_DAYS_AGO_UTC_09:00:00Z
    if token.startswith("YESTERDAY_UTC_"):
        hm = token.removeprefix("YESTERDAY_UTC_").rstrip("Z")
        h, m, s = (int(x) for x in hm.split(":"))
        return utc_day_offset(1, h, m, s)
    if token.startswith("TWO_DAYS_AGO_UTC_"):
        hm = token.removeprefix("TWO_DAYS_AGO_UTC_").rstrip("Z")
        h, m, s = (int(x) for x in hm.split(":"))
        return utc_day_offset(2, h, m, s)
    return token


def build_payload(fields: dict[str, str]) -> dict:
    return {
        "eventType": "FORM_RESPONSE",
        "data": {
            "formName": "B2B Contact Demo Seed",
            "formUrl": "https://tally.so/r/demo-seed",
            "fields": [{"label": k, "value": v} for k, v in fields.items()],
        },
    }


def post_json(url: str, payload: dict, timeout: float = 60.0) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, body


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed demo leads via Tally webhook")
    parser.add_argument("--url", required=True, help="n8n Tally webhook URL (.../webhook/tally-lead)")
    parser.add_argument("--file", type=Path, default=DEFAULT_JSON, help="Seed JSON path")
    parser.add_argument("--delay", type=float, default=15.0, help="Seconds between posts")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads only")
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Optional seed ids to include (default: all)",
    )
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"Missing seed file: {args.file}", file=sys.stderr)
        return 1

    doc = json.loads(args.file.read_text(encoding="utf-8"))
    leads = doc.get("leads") or []
    if args.only:
        wanted = set(args.only)
        leads = [L for L in leads if L.get("id") in wanted]

    if not leads:
        print("No leads to send.", file=sys.stderr)
        return 1

    print(f"Seeding {len(leads)} leads → {args.url}")
    print(f"Delay between posts: {args.delay}s\n")

    results: list[dict] = []
    for i, lead in enumerate(leads):
        lid = lead.get("id", f"lead-{i}")
        fields = lead.get("fields") or {}
        payload = build_payload(fields)
        email = fields.get("Email", "")

        print(f"[{i + 1}/{len(leads)}] {lid}  {email}")
        if args.dry_run:
            print(json.dumps(payload, ensure_ascii=False, indent=2)[:400], "...\n")
            status, body = 0, "(dry-run)"
        else:
            status, body = post_json(args.url, payload)
            snippet = body.replace("\n", " ")[:160]
            print(f"  → HTTP {status}  {snippet}")
            if i < len(leads) - 1 and args.delay > 0:
                time.sleep(args.delay)

        after = lead.get("sheets_after") or {}
        created = resolve_created_at(str(after.get("created_at", "keep")))
        results.append(
            {
                "id": lid,
                "email": email,
                "purpose": lead.get("purpose"),
                "http": status,
                "set_created_at": created,
                "meeting_status": after.get("meeting_status"),
                "booking_reminder_sent": after.get("booking_reminder_sent"),
                "note": after.get("note", ""),
            }
        )

    print("\n" + "=" * 72)
    print("NEXT: wait until enrichment/CRM finishes for each row, then edit Sheets.")
    print("=" * 72)
    print(
        f"{'email':<42} {'set created_at (UTC)':<24} extra"
    )
    print("-" * 72)
    for r in results:
        extra_parts = []
        if r.get("meeting_status"):
            extra_parts.append(f"meeting_status={r['meeting_status']}")
        if r.get("booking_reminder_sent") is not None and r.get("booking_reminder_sent") != "":
            extra_parts.append(f"booking_reminder_sent={r['booking_reminder_sent']!r}")
        elif r.get("meeting_status") == "not_booked":
            extra_parts.append("clear booking_reminder_sent")
        extra = "; ".join(extra_parts) if extra_parts else (r.get("note") or "")
        ca = r["set_created_at"] or "(keep)"
        print(f"{r['email']:<42} {ca:<24} {extra}")

    hero = doc.get("live_hero_do_not_seed") or {}
    if hero:
        hf = hero.get("fields") or {}
        print("\nLive Scenario A (do NOT seed now):")
        print(f"  {hf.get('Name')} <{hf.get('Email')}> — submit while recording.")

    print(
        "\nTips:\n"
        "  • Prefer mode=test while seeding if you want less Slack noise;\n"
        "    switch to production only for the recorded run.\n"
        "  • Daily window = yesterday UTC date prefix on created_at.\n"
        "  • Booking Follow-up needs high score + not_booked + age > booking_reminder_hours.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

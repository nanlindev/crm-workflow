#!/usr/bin/env python3
"""Offline Slack signature check: python3 scripts/verify_slack_sig_test.py <raw_body_file>"""

from __future__ import annotations

import hashlib
import hmac
import sys
import time

SECRET = b"66a15e6597708279ec464870e3d71ae1"  # from platform-n8n/.env for local debug only
TS = "1783656990"
EXPECTED = "v0=89d60fdf3ea0002e3247514886820708d3aba4fdcea07b59ec1c668ebe53a144"


def sign(secret: bytes, timestamp: str, raw_body: str) -> str:
    basestring = f"v0:{timestamp}:{raw_body}"
    digest = hmac.new(secret, basestring.encode(), hashlib.sha256).hexdigest()
    return f"v0={digest}"


def main() -> None:
    raw_body = sys.stdin.read() if len(sys.argv) < 2 else open(sys.argv[1], encoding="utf-8").read()
    computed = sign(SECRET, TS, raw_body)
    now = int(time.time())
    age = abs(now - int(TS))
    print("timestamp age (seconds):", age)
    print("expected: ", EXPECTED)
    print("computed: ", computed)
    print("match:    ", computed == EXPECTED)


if __name__ == "__main__":
    main()

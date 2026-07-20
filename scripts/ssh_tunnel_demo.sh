#!/usr/bin/env bash
# SSH tunnels for local Loom/OBS capture of remote n8n + OBS UIs.
# Usage:
#   REMOTE_HOST=user@your-server ./scripts/ssh_tunnel_demo.sh
# Optional env overrides:
#   N8N_LOCAL_PORT=5678 JAEGER_LOCAL_PORT=16686 LANGFUSE_LOCAL_PORT=3000
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-}"
if [[ -z "$REMOTE_HOST" ]]; then
  echo "Set REMOTE_HOST=user@host (or Host alias from ~/.ssh/config)" >&2
  exit 1
fi

N8N_LOCAL_PORT="${N8N_LOCAL_PORT:-5678}"
JAEGER_LOCAL_PORT="${JAEGER_LOCAL_PORT:-16686}"
LANGFUSE_LOCAL_PORT="${LANGFUSE_LOCAL_PORT:-3000}"

# Remote container/host ports — adjust if your deploy maps differently.
N8N_REMOTE_PORT="${N8N_REMOTE_PORT:-5678}"
JAEGER_REMOTE_PORT="${JAEGER_REMOTE_PORT:-16686}"
LANGFUSE_REMOTE_PORT="${LANGFUSE_REMOTE_PORT:-3000}"

echo "Tunneling:"
echo "  n8n      http://127.0.0.1:${N8N_LOCAL_PORT}"
echo "  Jaeger   http://127.0.0.1:${JAEGER_LOCAL_PORT}"
echo "  Langfuse http://127.0.0.1:${LANGFUSE_LOCAL_PORT}"
echo "Ctrl+C to stop."

exec ssh -N \
  -L "${N8N_LOCAL_PORT}:127.0.0.1:${N8N_REMOTE_PORT}" \
  -L "${JAEGER_LOCAL_PORT}:127.0.0.1:${JAEGER_REMOTE_PORT}" \
  -L "${LANGFUSE_LOCAL_PORT}:127.0.0.1:${LANGFUSE_REMOTE_PORT}" \
  "$REMOTE_HOST"

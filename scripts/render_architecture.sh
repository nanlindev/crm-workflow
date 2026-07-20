#!/usr/bin/env bash
# Render assets/architecture.svg → assets/architecture.png via Chromium headless.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SVG="$ROOT/assets/architecture.svg"
OUT="$ROOT/assets/architecture.png"
HTML="$ROOT/assets/.architecture_render.html"

if [[ ! -f "$SVG" ]]; then
  echo "Missing $SVG" >&2
  exit 1
fi

CHROME=""
for c in chromium google-chrome google-chrome-stable chromium-browser; do
  if command -v "$c" >/dev/null 2>&1; then
    CHROME="$c"
    break
  fi
done
if [[ -z "$CHROME" ]]; then
  echo "Need chromium/chrome to rasterize SVG" >&2
  exit 1
fi

{
  echo '<!DOCTYPE html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#f8fafc;}</style></head><body>'
  cat "$SVG"
  echo '</body></html>'
} >"$HTML"

"$CHROME" --headless --disable-gpu --no-sandbox --virtual-time-budget=5000 \
  --window-size=1400,780 \
  --screenshot="$OUT" \
  "file://$HTML" >/dev/null 2>&1 || true

rm -f "$HTML"

if [[ -f "$OUT" ]]; then
  echo "Wrote $OUT ($(wc -c <"$OUT") bytes)"
else
  echo "Render failed" >&2
  exit 1
fi

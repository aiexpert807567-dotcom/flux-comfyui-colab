#!/usr/bin/env bash
# Start ComfyUI in the background (localhost only) and optionally open a Cloudflare quick tunnel.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
[ -f "$COMFY_DIR/main.py" ] || die "ComfyUI not installed. Run: bash colab/setup_colab.sh"

LOG="$WORKDIR/comfyui.log"; TLOG="$WORKDIR/cloudflared.log"
pkill -f "main.py --listen 127.0.0.1 --port $COMFY_PORT" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 1

FLAGS="$(python3 "$ROOT/scripts/detect_gpu.py" --flags --no-write || true)"
log "Starting ComfyUI on 127.0.0.1:$COMFY_PORT  flags: ${FLAGS:-(none)}"
cd "$COMFY_DIR"
# shellcheck disable=SC2086
nohup python3 main.py --listen 127.0.0.1 --port "$COMFY_PORT" \
  --output-directory "$OUTPUT_DIR" \
  --extra-model-paths-config "$COMFY_DIR/extra_model_paths.yaml" $FLAGS > "$LOG" 2>&1 &

for i in $(seq 1 120); do
  if curl -fs "http://127.0.0.1:$COMFY_PORT/system_stats" >/dev/null 2>&1; then READY=1; break; fi
  sleep 2
done
[ "${READY:-0}" = "1" ] || { tail -n 40 "$LOG"; die "ComfyUI did not come up in 4 min. Log: $LOG"; }
log "ComfyUI is running (local). Log: $LOG"

if [ "$TUNNEL" = "cloudflared" ]; then
  CF="$WORKDIR/cloudflared"
  [ -x "$CF" ] || { curl -fsSL -o "$CF" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x "$CF"; }
  nohup "$CF" tunnel --no-autoupdate --url "http://127.0.0.1:$COMFY_PORT" > "$TLOG" 2>&1 &
  URL=""
  for i in $(seq 1 30); do
    URL="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$TLOG" | head -n1 || true)"
    [ -n "$URL" ] && break; sleep 2
  done
  echo
  if [ -n "$URL" ]; then
    echo "=============================================================="
    echo " ComfyUI URL:  $URL"
    echo " WARNING: anyone with this link has FULL control of this ComfyUI"
    echo " (no password). Do not share it. Stop the runtime when done."
    echo "=============================================================="
  else
    echo "Tunnel URL not found; see $TLOG. Use the notebook's headless 'Generate' cell, or TUNNEL=none."
  fi
else
  echo "TUNNEL=none: ComfyUI only on localhost:$COMFY_PORT inside the runtime (use scripts/run_workflow.py)."
fi

# Sourced by the other scripts. Resolves paths + config. Do not run directly.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
set -a
[ -f "$ROOT/config/local.env" ] && . "$ROOT/config/local.env"
. "$ROOT/config/project.env"
set +a

WORKDIR="${WORKDIR:-/content}"; [ -d "$WORKDIR" ] || WORKDIR="$HOME"
COMFY_DIR="${COMFY_DIR:-$WORKDIR/ComfyUI}"

if [ "${PERSIST}" = "drive" ]; then
  if [ -d /content/drive/MyDrive ]; then
    MODELS_DIR="${MODELS_DIR:-$DRIVE_ROOT/models}"
    OUTPUT_DIR="${OUTPUT_DIR:-$DRIVE_ROOT/outputs}"
    mkdir -p "$MODELS_DIR" "$OUTPUT_DIR"
  else
    echo "WARN: PERSIST=drive but Google Drive is not mounted (run the 'Mount Drive' notebook cell). Using temporary storage." >&2
    PERSIST=none
  fi
fi
MODELS_DIR="${MODELS_DIR:-$COMFY_DIR/models}"
OUTPUT_DIR="${OUTPUT_DIR:-$COMFY_DIR/output}"
export ROOT WORKDIR COMFY_DIR MODELS_DIR OUTPUT_DIR PERSIST COMFY_PORT COMFYUI_REF FLUX_VARIANT WITH_UPSCALER

log() { printf '\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
die() { printf '\033[1;31m[ERROR]\033[0m %s\n' "$*" >&2; exit 1; }

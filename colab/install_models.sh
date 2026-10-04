#!/usr/bin/env bash
# Download models for the detected GPU. Extra args pass through, e.g.:
#   bash colab/install_models.sh --with-upscaler
#   bash colab/install_models.sh --only flux2_klein_4b_base_fp8
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
ARGS=("$@")
[ "${WITH_UPSCALER:-0}" = "1" ] && ARGS+=("--with-upscaler")
log "Models directory: $MODELS_DIR (persist=$PERSIST)"
python3 "$ROOT/scripts/download_models.py" "${ARGS[@]}" || die "Model download failed. See docs/TROUBLESHOOTING.md."

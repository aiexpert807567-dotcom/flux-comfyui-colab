#!/usr/bin/env bash
# ONE-COMMAND SETUP: GPU check -> ComfyUI (pinned) -> deps -> models -> health check -> start server.
#   bash colab/setup_colab.sh            # everything
#   NO_START=1 bash colab/setup_colab.sh # skip starting the server
# Safe to re-run after a disconnect: existing ComfyUI/models are reused.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

log "1/7 GPU detection"
command -v nvidia-smi >/dev/null || die "No NVIDIA GPU. Colab: Runtime > Change runtime type > select a GPU, reconnect, re-run."
python3 "$ROOT/scripts/detect_gpu.py" || die "GPU not sufficient for FLUX.2 klein 4B (see message above)."

log "2/7 Storage: persist=$PERSIST  models=$MODELS_DIR  outputs=$OUTPUT_DIR"
mkdir -p "$MODELS_DIR"/{diffusion_models,text_encoders,vae,upscale_models} "$OUTPUT_DIR"

log "3/7 ComfyUI $COMFYUI_REF -> $COMFY_DIR"
if [ -d "$COMFY_DIR/.git" ]; then
  git -C "$COMFY_DIR" fetch --tags --quiet
else
  git clone --quiet "$COMFYUI_REPO" "$COMFY_DIR"
fi
git -C "$COMFY_DIR" checkout --quiet "$COMFYUI_REF" || die "Cannot check out COMFYUI_REF=$COMFYUI_REF"

log "4/7 Python dependencies (keeping Colab's preinstalled PyTorch)"
REQ_TMP="$(mktemp)"
grep -viE '^\s*(torch|torchvision|torchaudio)\s*($|[<>=!~;#])' "$COMFY_DIR/requirements.txt" > "$REQ_TMP"
python3 -m pip install -q -r "$REQ_TMP" requests safetensors \
  || die "pip install failed (dependency conflict). See docs/TROUBLESHOOTING.md 'dependency conflict'."
rm -f "$REQ_TMP"

log "5/7 Model path config"
cat > "$COMFY_DIR/extra_model_paths.yaml" <<YAML
flux_colab:
  base_path: $MODELS_DIR
  diffusion_models: diffusion_models/
  text_encoders: text_encoders/
  vae: vae/
  upscale_models: upscale_models/
YAML

log "6/7 Models"
bash "$ROOT/colab/install_models.sh"

log "7/7 Health check"
python3 "$ROOT/scripts/check_environment.py" || die "Health check failed; fix the items marked FAIL."

if [ "${NO_START:-0}" = "1" ]; then
  log "Setup finished. Start later with: bash colab/start_comfyui.sh"
else
  bash "$ROOT/colab/start_comfyui.sh"
fi

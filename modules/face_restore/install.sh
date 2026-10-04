#!/usr/bin/env bash
# OPTIONAL, separate from the core install. Face restoration (GFPGAN v1.4) for YOUR OWN or consented images.
# Installs the community ComfyUI node "facerestore_cf" + the GFPGAN weights. Nothing else depends on this.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../../colab/_common.sh"
[ -d "$COMFY_DIR/custom_nodes" ] || die "Run colab/setup_colab.sh first."
echo "Face restoration is for restoring your own photos, consenting subjects, testing, and synthetic characters."
echo "Do not use it to impersonate or deceive people or to process images of people without consent."
git clone --depth 1 https://github.com/mav-rik/facerestore_cf "$COMFY_DIR/custom_nodes/facerestore_cf" 2>/dev/null || \
  git -C "$COMFY_DIR/custom_nodes/facerestore_cf" pull --quiet
python3 -m pip install -q -r "$COMFY_DIR/custom_nodes/facerestore_cf/requirements.txt" || echo "WARN: node requirements failed; see docs/TROUBLESHOOTING.md (custom-node errors)."
mkdir -p "$MODELS_DIR/facerestore_models"
[ -s "$MODELS_DIR/facerestore_models/GFPGANv1.4.pth" ] || \
  curl -fL -o "$MODELS_DIR/facerestore_models/GFPGANv1.4.pth" https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth
grep -q facerestore_models "$COMFY_DIR/extra_model_paths.yaml" || echo "  facerestore_models: facerestore_models/" >> "$COMFY_DIR/extra_model_paths.yaml"
echo "Done. Restart ComfyUI (bash colab/start_comfyui.sh). Add 'FaceRestoreModelLoader' + 'FaceRestoreCFWithModel' nodes after your decode step."

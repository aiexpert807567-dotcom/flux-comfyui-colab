#!/usr/bin/env bash
# Print GPU report + chosen profile. Exit 2 if no GPU.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
command -v nvidia-smi >/dev/null || die "nvidia-smi not found: no NVIDIA GPU. Colab: Runtime > Change runtime type > select a GPU, then reconnect."
python3 "$ROOT/scripts/detect_gpu.py"

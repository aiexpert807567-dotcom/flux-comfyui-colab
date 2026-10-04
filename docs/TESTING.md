# Test plan

| # | Action (Colab) | Expected | If it fails |
|---|---|---|---|
| 1 | `!python scripts/check_environment.py` | ends `SYSTEM READY` | read the `[FAIL]` lines; TROUBLESHOOTING |
| 2 | `!bash colab/start_comfyui.sh` then `!curl -s localhost:8188/system_stats` | JSON with your GPU; URL printed | `tail -50 /content/comfyui.log` |
| 3 | `!python scripts/run_workflow.py workflows/flux_basic.json --check` | `Workflow validation OK` | node/model names listed in the error |
| 4 | `!python scripts/run_workflow.py workflows/flux_basic.json --prompt "a red fox in snow" --seed 1` | PNG in `outputs/` in ~5-60 s (first run slower: model load) | OOM / black image sections |
| 5 | Upload an image; run `flux_image_to_image.json --image X --denoise 0.5` | image resembling X, restyled | check upload path, denoise |
| 6 | Look in `/content/ComfyUI/output` (or Drive `outputs/`) | same PNG files present | `$OUTPUT_DIR` in setup log |
| 7 | Runtime > Disconnect and delete runtime; reconnect; run cells 2-4 | setup finishes; temporary mode re-downloads, Drive mode prints `already installed` | see Drive / disk sections |
| 8 | Set `PERSIST="drive"`, run, generate, then repeat test 7 | second setup skips all downloads | mount cell, quota |

# flux-comfyui-colab

Reproducible **FLUX.2 [klein] 4B + ComfyUI** on a **Google Colab GPU**, managed from GitHub.

```
GitHub repo (scripts/config/workflows only) -> Colab GPU -> detect GPU/VRAM -> ComfyUI (pinned) -> FLUX.2 klein 4B -> workflows -> images
```
GitHub Codespaces is only for editing/committing. **All GPU inference runs in Colab.**

## Why this model
FLUX.2 [klein] 4B: **Apache-2.0** (commercial OK), 4-step distilled, ~8-13 GB VRAM, supports generation + editing, native in ComfyUI. Alternatives (documented, not default): klein 4B *base* (negative prompts, 30+ steps), FLUX.1 [schnell] (Apache, 12B, heavier), klein 9B / FLUX.2 dev (**non-commercial**, 24+ GB). GPU selection is automatic: >=20 GB + bf16 hardware -> bf16 file; 12-20 GB or T4 -> fp8 file; 6-12 GB -> fp8 + `--lowvram`; <6 GB -> clear error. Downloads ~16 GB (DiT 7.3 or 3.9 GB, text encoder 8 GB, VAE 0.35 GB).
Files come from Hugging Face (Comfy-Org repackaged / Black Forest Labs). No HF token is required for the Apache models; set `HF_TOKEN` only if a download returns 401/403.

## Quick start
**GITHUB CODESPACES COMMAND** (once)
```bash
bash bootstrap.sh aiexpert807567-dotcom   # already done if you used it
git add -A && git commit -m "flux-comfyui-colab" && git push
```
**GOOGLE COLAB**: open `colab/flux_comfyui.ipynb` from GitHub (Colab > File > Open notebook > GitHub), choose a GPU runtime, run cells 1-5.
**Or in a Colab terminal:** `git clone https://github.com/aiexpert807567-dotcom/flux-comfyui-colab && cd flux-comfyui-colab && bash colab/setup_colab.sh`
**COMFYUI ACTION:** open the printed URL, or just run the headless test cell for your first image.

## Layout
| Path | Purpose |
|---|---|
| `colab/` | `setup_colab.sh` (one command), `start_comfyui.sh`, `detect_gpu.sh`, `install_models.sh`, `_common.sh`, notebook |
| `scripts/` | `detect_gpu.py`, `download_models.py`, `check_environment.py`, `run_workflow.py` |
| `workflows/` | API-format ComfyUI workflows: basic, image-to-image, upscale |
| `config/` | `project.env` (switches), `models.json` (central model registry) |
| `modules/face_restore/` | optional, isolated face restoration |
| `docs/` | COLAB, WORKFLOWS (+performance), SECURITY, LICENSES, TESTING, TROUBLESHOOTING |

Models, outputs and secrets are git-ignored. Models live in `/content/ComfyUI/models` (temporary) or `MyDrive/flux-comfyui/models` (`PERSIST="drive"`).

## Know the uncertainties
Colab images, ComfyUI nodes (`EmptyFlux2LatentImage`, CLIP type `flux2`), and Hugging Face paths change. ComfyUI is pinned (`COMFYUI_REF` in `config/project.env`, default v0.35.0); `run_workflow.py --check` validates node/model names against your running server; mirrors and a fallback model URL are in `config/models.json`. T4 fp16 numerics for Flux.2 are the least certain part: see TROUBLESHOOTING "Black images". Use is your responsibility: no deceptive or non-consensual imagery (docs/LICENSES.md).

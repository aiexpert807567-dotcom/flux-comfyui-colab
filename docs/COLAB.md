# Colab guide (from zero)

**What Colab is:** a free/paid Jupyter notebook running on a temporary Google VM. You get a GPU for a few hours; when the runtime disconnects or is recycled, **everything on its disk is deleted** (ComfyUI, models, images). Your GitHub repo and (optionally) Google Drive survive.

**Two modes**
| Mode | Setting | Models live in | After disconnect |
|---|---|---|---|
| A: temporary | `PERSIST="none"` | `/content/ComfyUI/models` | re-download ~16 GB (5-15 min) |
| B: Drive | `PERSIST="drive"` | `MyDrive/flux-comfyui/models` | models reused instantly (needs ~16 GB free Drive) |

Drive mode needs the notebook's mount cell (Colab only allows mounting from the notebook UI). If Drive isn't mounted the scripts fall back to mode A with a warning.

**Steps**
1. Open https://colab.research.google.com > File > Open notebook > GitHub tab > your repo > `colab/flux_comfyui.ipynb`.
2. Runtime > Change runtime type > pick a GPU (T4 free; L4/A100 if available to you).
3. (Optional) Left sidebar key icon > add secret `HF_TOKEN` (only needed if a download says 401/403) and `GITHUB_TOKEN` (only for a private repo). Toggle "Notebook access" on.
4. Run cells 1-4. Cell 4 = the single setup command. Open the printed URL.
5. Run cell 5 to verify with a headless test image.

Terminal alternative (Colab Pro has a terminal): `git clone https://github.com/<you>/flux-comfyui-colab && cd flux-comfyui-colab && bash colab/setup_colab.sh`.

**Where files are:** models `$MODELS_DIR`; generated images `$OUTPUT_DIR` (default `/content/ComfyUI/output`, Drive in mode B); ComfyUI log `/content/comfyui.log`; copies from `run_workflow.py` in `./outputs/`. **Download anything you want to keep from temporary mode** (Files panel > right-click > Download).

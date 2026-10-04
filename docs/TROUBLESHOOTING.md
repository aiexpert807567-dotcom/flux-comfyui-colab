# Troubleshooting (run these in Colab cells with a leading `!`, or in a terminal)

**No GPU / "nvidia-smi not found"** - Runtime > Change runtime type > GPU, Save, reconnect, re-run setup.

**CUDA out of memory** -
```
FLUX_VARIANT=fp8 bash colab/start_comfyui.sh                  # smaller model file
python scripts/run_workflow.py workflows/flux_basic.json --width 768 --height 768
nvidia-smi                                                      # something else holding VRAM? Runtime > Restart session
```
Below 12 GB VRAM the setup already adds `--lowvram` automatically.
Close other notebooks using the GPU. Keep batch size 1.

**Model not found / wrong directory / dropdown empty**
```
python scripts/check_environment.py
find /content -name "flux-2-klein*" -o -name "qwen_3_4b*" -o -name "flux2-vae*" 2>/dev/null
cat /content/ComfyUI/extra_model_paths.yaml
bash colab/install_models.sh && bash colab/start_comfyui.sh   # restart so ComfyUI rescans
```
Expected: `diffusion_models/flux-2-klein-4b[-fp8].safetensors`, `text_encoders/qwen_3_4b.safetensors`, `vae/flux2-vae.safetensors` under `$MODELS_DIR`.

**Failed / 401 / 403 Hugging Face download** - Add Colab secret `HF_TOKEN` (Notebook access on), accept the licence on the model page if it is gated, re-run `bash colab/install_models.sh`. Partial files resume automatically. 404 = URL moved: edit `config/models.json` (urls list) with the new link from the model's "Files" tab.
```
rm -f $MODELS_DIR/*/*.part && bash colab/install_models.sh
```

**Insufficient disk space** - `df -h /content`. Core needs ~16 GB. Use Drive mode (`PERSIST="drive"`) or `rm -rf /content/sample_data ~/.cache/pip`; `pip cache purge`.

**Dependency conflict / pip errors**
```
python3 -m pip install -r /content/ComfyUI/requirements.txt 2>&1 | tail -30
python3 -m pip check
```
Setup intentionally keeps Colab's PyTorch. If ComfyUI says PyTorch is too old (<2.7), choose a newer Colab runtime image or `pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126` then restart the session.

**Python version mismatch** - `python3 --version` (3.10+ required, Colab ships 3.11/3.12). Don't install other Pythons.

**CUDA / PyTorch mismatch** - `python3 -c "import torch;print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"` must print True. If False after a pip change, Runtime > Restart session; if still False, Disconnect and delete runtime, then re-run (never `pip install torch` over Colab's build unless told above).

**Black / noisy / NaN images on T4** - T4 lacks bf16; fp16 compute may overflow. Try:
```
cd /content/ComfyUI && python3 main.py --listen 127.0.0.1 --port 8188 --force-fp32 --lowvram ...   # slow but safe
```
or use an L4/A100 runtime. (Uncertain across ComfyUI versions: this is the first thing to test on T4.)

**Custom-node errors** - Core install uses none. For the optional module: `tail -50 /content/comfyui.log`; `cd /content/ComfyUI/custom_nodes/<node> && python3 -m pip install -r requirements.txt`; or `rm -rf` that node folder and restart.

**Workflow validation: "class does not exist" / "not one of"** - ComfyUI too old for FLUX.2 nodes: `COMFYUI_REF=master bash colab/setup_colab.sh`. Or the dropdown value differs: open the node and pick the file.

**Colab disconnect** - Reconnect, run notebook cells 2-4 again (Drive mode: models are reused). `tail -f /content/comfyui.log` for logs. Download images before leaving temporary mode.

**Google Drive mount issues** - Mount only works from a notebook cell: `from google.colab import drive; drive.mount('/content/drive', force_remount=True)`. Then `ls /content/drive/MyDrive`. Check Drive quota (needs ~16 GB).

**Tunnel / interface not loading** - `cat /content/cloudflared.log | tail -20`; `curl -s localhost:8188/system_stats`. If local works but URL doesn't: `bash colab/start_comfyui.sh` for a new URL. Wait 10-20 s after it appears. Fallback: `TUNNEL=none` and use `scripts/run_workflow.py`.

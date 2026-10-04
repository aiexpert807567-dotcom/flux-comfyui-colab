# Workflows, performance, usage

Workflows are **API-format JSON** (what `run_workflow.py` queues). ComfyUI's UI can load them: drag the .json onto the canvas (download it from the repo/Colab Files panel). If your frontend refuses, use `run_workflow.py` or ComfyUI > Browse Templates > "Flux.2 Klein 4B" (official, UI-format).
Run `python scripts/run_workflow.py <file> --check` to validate every node class and model name against the running ComfyUI before generating.

## flux_basic.json (text -> image)
UNETLoader (`flux-2-klein-4b[-fp8].safetensors`) + CLIPLoader (`qwen_3_4b.safetensors`, type `flux2`) + VAELoader (`flux2-vae.safetensors`) -> CLIPTextEncode (POSITIVE / NEGATIVE) -> EmptyFlux2LatentImage -> KSampler (euler, simple, 4 steps, cfg 1.0) -> VAEDecode -> SaveImage.
- The default model is **step-distilled**: 4 steps, cfg 1.0. At cfg 1.0 the **negative prompt has no effect**. For real negative prompts use the base model: `bash colab/install_models.sh --only flux2_klein_4b_base_fp8`, pick it in the UNET node, set steps 30, cfg 4.
- `run_workflow.py` auto-selects bf16/fp8 file for your GPU.

## flux_image_to_image.json
LoadImage -> ImageScale (1024x1024, center crop) -> VAEEncode -> KSampler (`denoise`) -> VAEDecode -> SaveImage.
- Upload: via script `--image path`, or in the UI click the LoadImage node's upload button (files land in `ComfyUI/input/`).
- **denoise**: 0.2-0.4 = keeps layout/colors, subtle restyle; 0.5-0.65 = keeps composition, changes style/details (default 0.6); 0.8-1.0 = mostly new image.
- Preserve composition: low denoise, prompt describes the *existing* scene; match width/height to the source aspect ratio.
- Stronger change: raise denoise, raise steps (8-12) so enough steps remain after the denoise cut.
- For instruction-style editing ("make the sky orange") use ComfyUI's official Klein *Image Edit* template instead; it uses reference-latent conditioning that this simple img2img does not.

## flux_upscale.json (optional)
FLUX is the wrong tool for pure upscaling. Uses **Real-ESRGAN x4plus** (BSD-3, 64 MB) via UpscaleModelLoader + ImageUpscaleWithModel. 4x output; large inputs need VRAM (tile via "ImageUpscaleWithModel" is automatic in recent ComfyUI).

## Performance (what each option does)
| Setting | Effect | When used |
|---|---|---|
| fp8 weights file | halves DiT size (3.9 vs 7.3 GB), small quality loss | GPUs < 20 GB or without bf16 (T4) |
| bf16 | native half precision, best quality/speed | Ampere+ (cc>=8.0) with >=20 GB |
| `--lowvram` | offloads model parts to RAM; slower | VRAM < 12 GB |
| 4-step distilled model | ~10x fewer steps than base | default |
| Resolution | cost ~ pixels; 1024x1024 default; try 768 on small GPUs | OOM |
| Batch size | keep 1 on <=16 GB | OOM |
ComfyUI unloads the text encoder after encoding automatically (smart memory). I deliberately don't force attention flags: ComfyUI picks a sane default for the installed PyTorch.

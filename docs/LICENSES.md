# Licenses (verify on the official pages before relying on this; checked Oct 2026)

| Component | License | Commercial use | Notes / source |
|---|---|---|---|
| FLUX.2 [klein] **4B** (distilled, base, fp8) | Apache-2.0 | Yes | https://huggingface.co/black-forest-labs/FLUX.2-klein-4B . BFL asks deployers to use content filters/mitigations; Apache terms: keep notices, state changes |
| FLUX.2 [klein] 9B, FLUX.2 [dev] | FLUX Non-Commercial License | **No** (without separate BFL licence) | Not used. Gated on Hugging Face; Dev needs far more VRAM |
| FLUX.1 [schnell] | Apache-2.0 | Yes | Alternative (12B, heavier) |
| FLUX.1 [dev] | FLUX.1-dev Non-Commercial | No | Not used |
| FLUX.2 VAE | Apache-2.0 | Yes | https://github.com/black-forest-labs/flux2 |
| Qwen3-4B text encoder | Apache-2.0 | Yes | https://huggingface.co/Qwen/Qwen3-4B (ComfyUI-repackaged copy used) |
| ComfyUI | GPL-3.0 | Yes (copyleft applies to ComfyUI code you distribute) | https://github.com/Comfy-Org/ComfyUI |
| Real-ESRGAN x4plus | BSD-3-Clause | Yes | https://github.com/xinntao/Real-ESRGAN |
| GFPGAN v1.4 (optional) | Apache-2.0 | Yes | https://github.com/TencentARC/GFPGAN |
| cloudflared | Apache-2.0 | Yes | Cloudflare quick tunnels: see Cloudflare terms |
| This repo's scripts | MIT | Yes | LICENSE |

Model licences are not "do anything": you remain responsible for what you generate (laws on likeness, copyright, deceptive or non-consensual imagery apply regardless of licence). Third-party "repackaged" files (Comfy-Org) follow the upstream licence.

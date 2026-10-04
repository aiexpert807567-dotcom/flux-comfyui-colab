#!/usr/bin/env python3
"""Detect the NVIDIA GPU and choose a FLUX.2 [klein] 4B configuration.

Usage:
  python scripts/detect_gpu.py            # human-readable report + writes config/generated/profile.json
  python scripts/detect_gpu.py --json     # JSON only
  python scripts/detect_gpu.py --flags    # only the extra ComfyUI CLI flags
  python scripts/detect_gpu.py --variant  # only the chosen variant (bf16|fp8)
Exit code 2 if no usable GPU.
"""
import argparse, json, os, platform, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT / "config" / "generated" / "profile.json"

UNET_BY_VARIANT = {
    "bf16": "flux-2-klein-4b.safetensors",
    "fp8": "flux-2-klein-4b-fp8.safetensors",
}


def _smi(field):
    try:
        out = subprocess.check_output(
            ["nvidia-smi", f"--query-gpu={field}", "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL, timeout=20)
        return out.strip().splitlines()[0].strip()
    except Exception:
        return None


def detect():
    info = {
        "python": platform.python_version(),
        "gpu_name": _smi("name"),
        "vram_gb": None,
        "compute_capability": None,
        "driver": _smi("driver_version"),
        "torch": None, "torch_cuda": None, "cuda_available": False,
        "disk_free_gb": round(shutil.disk_usage(str(ROOT)).free / 1e9, 1),
    }
    mem = _smi("memory.total")
    if mem:
        try:
            info["vram_gb"] = round(float(mem) / 1024, 1)
        except ValueError:
            pass
    cc = _smi("compute_cap")
    if cc:
        try:
            info["compute_capability"] = float(cc)
        except ValueError:
            pass
    try:
        import torch
        info["torch"] = torch.__version__
        info["torch_cuda"] = torch.version.cuda
        info["cuda_available"] = bool(torch.cuda.is_available())
        if info["cuda_available"]:
            props = torch.cuda.get_device_properties(0)
            info["gpu_name"] = info["gpu_name"] or props.name
            info["vram_gb"] = info["vram_gb"] or round(props.total_memory / 1024**3, 1)
            if info["compute_capability"] is None:
                info["compute_capability"] = float(f"{props.major}.{props.minor}")
    except Exception:
        pass
    return info


def choose_profile(info, override="auto"):
    warnings = []
    vram, cc = info.get("vram_gb"), info.get("compute_capability") or 0.0
    if not info.get("gpu_name") or not vram:
        return {"supported": False, "variant": None, "unet_name": None, "comfy_flags": [],
                "warnings": ["No NVIDIA GPU detected. In Colab: Runtime > Change runtime type > pick a GPU, then reconnect."]}
    # bf16 needs hardware support (compute capability >= 8.0) and enough VRAM for the 7.3 GB DiT
    if vram >= 20 and cc >= 8.0:
        variant, flags = "bf16", []
    elif vram >= 12:
        variant, flags = "fp8", []
        if cc < 8.0:
            warnings.append(f"Compute capability {cc} has no native bf16: ComfyUI will compute in fp16. "
                            "If images come out black/noisy, see docs/TROUBLESHOOTING.md ('black image').")
    elif vram >= 6:
        variant, flags = "fp8", ["--lowvram"]
        warnings.append("Low VRAM: using --lowvram (slower, model parts offloaded to system RAM).")
    else:
        return {"supported": False, "variant": None, "unet_name": None, "comfy_flags": [],
                "warnings": [f"{vram} GB VRAM is below the ~6 GB practical minimum for FLUX.2 klein 4B (fp8)."]}
    if override in UNET_BY_VARIANT and override != variant:
        warnings.append(f"FLUX_VARIANT override: using '{override}' instead of auto-selected '{variant}'.")
        variant = override
    return {
        "supported": True, "variant": variant, "unet_name": UNET_BY_VARIANT[variant],
        "comfy_flags": flags, "warnings": warnings,
        # distilled klein: 4 steps, cfg 1.0 (negative prompt has no effect at cfg 1)
        "defaults": {"steps": 4, "cfg": 1.0, "sampler": "euler", "scheduler": "simple"},
    }


def build(override=None):
    override = override or os.environ.get("FLUX_VARIANT", "auto")
    info = detect()
    prof = choose_profile(info, override)
    return {**info, **prof}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--flags", action="store_true")
    ap.add_argument("--variant", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    p = build()
    if p.get("supported") and not a.no_write:
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROFILE_PATH.write_text(json.dumps(p, indent=2))
    if a.flags:
        print(" ".join(p["comfy_flags"]))
    elif a.variant:
        print(p["variant"] or "")
    elif a.json:
        print(json.dumps(p, indent=2))
    else:
        print("GPU detected:\n  %s\n" % (p["gpu_name"] or "NONE"))
        print("VRAM:\n  %s GB\n" % (p["vram_gb"] or "n/a"))
        print("Compute capability:\n  %s\n" % (p["compute_capability"] or "n/a"))
        print("CUDA available (PyTorch):\n  %s\n" % ("yes" if p["cuda_available"] else "no / torch not importable"))
        print("PyTorch:\n  %s (CUDA %s)\n" % (p["torch"], p["torch_cuda"]))
        print("Python:\n  %s\n" % p["python"])
        print("Disk free:\n  %s GB\n" % p["disk_free_gb"])
        if p["supported"]:
            print("Selected model variant:\n  %s  (%s)\n" % (p["variant"], p["unet_name"]))
            print("Extra ComfyUI flags:\n  %s\n" % (" ".join(p["comfy_flags"]) or "(none)"))
        for w in p["warnings"]:
            print("WARNING:", w)
    sys.exit(0 if p.get("supported") else 2)


if __name__ == "__main__":
    main()

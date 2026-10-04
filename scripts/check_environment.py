#!/usr/bin/env python3
"""Health check. Ends with SYSTEM READY / SYSTEM NOT READY. Exit 0 / 1.
  python scripts/check_environment.py            # static checks
  python scripts/check_environment.py --server   # also require the ComfyUI HTTP server to answer
"""
import argparse, importlib, json, os, platform, shutil, subprocess, sys, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent
fails, warns = [], []


def row(ok, label, detail="", fatal=True):
    tag = "PASS" if ok else ("FAIL" if fatal else "WARN")
    print(f"[{tag}] {label}: {detail}")
    if not ok:
        (fails if fatal else warns).append(f"{label}: {detail}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", action="store_true")
    a = ap.parse_args()

    comfy = Path(os.environ.get("COMFY_DIR", ROOT.parent / "ComfyUI"))
    models_dir = Path(os.environ.get("MODELS_DIR", comfy / "models"))
    port = os.environ.get("COMFY_PORT", "8188")

    v = sys.version_info
    row(v >= (3, 10), "Python", platform.python_version())

    prof = None
    try:
        from detect_gpu import build
        prof = build()
    except Exception as e:
        row(False, "GPU detection", str(e))
    if prof:
        row(bool(prof["gpu_name"]), "GPU", f"{prof['gpu_name']} / {prof['vram_gb']} GB / cc {prof['compute_capability']}")
        row(prof["cuda_available"], "CUDA available (torch)", str(prof["cuda_available"]))
        row(bool(prof["torch"]), "PyTorch", f"{prof['torch']} (CUDA {prof['torch_cuda']})")
        if prof["torch"]:
            try:
                major, minor = [int(x) for x in prof["torch"].split("+")[0].split(".")[:2]]
                row((major, minor) >= (2, 7), "PyTorch >= 2.7 (ComfyUI minimum)", prof["torch"])
            except Exception:
                pass
        row(prof.get("supported", False), "GPU profile", f"variant={prof.get('variant')} flags={prof.get('comfy_flags')}")
        for w in prof.get("warnings", []):
            print("       note:", w)

    free = shutil.disk_usage(str(models_dir if models_dir.exists() else ROOT)).free / 1e9
    row(free >= 5, "Disk free", f"{free:.1f} GB", fatal=True)

    row((comfy / "main.py").exists(), "ComfyUI installed", str(comfy))
    if (comfy / "main.py").exists():
        try:
            ref = subprocess.check_output(["git", "-C", str(comfy), "describe", "--tags", "--always"], text=True).strip()
            print(f"       ComfyUI version: {ref}")
        except Exception:
            pass

    for mod in ["requests", "safetensors", "PIL", "numpy", "aiohttp", "yaml"]:
        try:
            m = importlib.import_module(mod)
            row(True, f"import {mod}", getattr(m, "__version__", "ok"))
        except Exception as e:
            row(False, f"import {mod}", f"{e}  -> python3 -m pip install -r {comfy}/requirements.txt")

    if prof and prof.get("supported"):
        reg = json.loads((ROOT / "config" / "models.json").read_text())["models"]
        needed = [m for m in reg if m["group"] == "core" and m.get("variant", prof["variant"]) == prof["variant"]]
        for m in needed:
            p = models_dir / m["subdir"] / m["filename"]
            ok = p.exists() and p.stat().st_size >= m["min_bytes"]
            row(ok, f"model {m['filename']}", str(p) if ok else f"missing/incomplete at {p} -> bash colab/install_models.sh")
        for m in reg:
            if m["group"] == "upscaler":
                p = models_dir / m["subdir"] / m["filename"]
                row(p.exists(), f"(optional) {m['filename']}", "installed" if p.exists() else "not installed (WITH_UPSCALER=1 to add)", fatal=False)

    if a.server:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/system_stats", timeout=5) as r:
                row(r.status == 200, "ComfyUI server", f"answering on :{port}")
        except Exception as e:
            row(False, "ComfyUI server", f"not reachable on :{port} ({e}) -> bash colab/start_comfyui.sh")

    print()
    if fails:
        print("SYSTEM NOT READY")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("SYSTEM READY")
    for w in warns:
        print("  (warning)", w)


if __name__ == "__main__":
    main()

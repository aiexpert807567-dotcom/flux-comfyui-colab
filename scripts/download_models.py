#!/usr/bin/env python3
"""Robust model downloader driven by config/models.json.

  python scripts/download_models.py                 # core models for the detected GPU profile
  python scripts/download_models.py --with-upscaler # + RealESRGAN upscaler
  python scripts/download_models.py --only flux2_klein_4b_base_fp8
  python scripts/download_models.py --list

Env: MODELS_DIR (destination root), HF_TOKEN (optional; only sent to huggingface.co).
Features: skip if present, resume (.part), URL fallbacks, retries, size + safetensors-header validation,
disk-space pre-check, non-zero exit on any failure.
"""
import argparse, hashlib, json, os, shutil, struct, sys, time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "config" / "models.json"
RETRIES = 3

try:
    import requests
except ImportError:
    print("ERROR: 'requests' missing. Run: python3 -m pip install requests"); sys.exit(1)


def load_registry():
    return json.loads(REGISTRY.read_text())["models"]


def validate_file(path, entry):
    size = path.stat().st_size
    if size < entry["min_bytes"]:
        return False, f"too small ({size/1e9:.2f} GB < {entry['min_bytes']/1e9:.2f} GB)"
    if path.suffix == ".safetensors":
        try:
            with open(path, "rb") as f:
                n = struct.unpack("<Q", f.read(8))[0]
                if n <= 0 or n > 100_000_000:
                    return False, "invalid safetensors header length"
                json.loads(f.read(n))
        except Exception as e:
            return False, f"invalid safetensors header ({e})"
    if entry.get("sha256"):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 24), b""):
                h.update(chunk)
        if h.hexdigest().lower() != entry["sha256"].lower():
            return False, "sha256 mismatch"
    return True, "ok"


def stream(url, part, token):
    headers = {"User-Agent": "flux-comfyui-colab/1.0"}
    if token and urlparse(url).hostname and urlparse(url).hostname.endswith("huggingface.co"):
        headers["Authorization"] = f"Bearer {token}"
    resume = part.stat().st_size if part.exists() else 0
    if resume:
        headers["Range"] = f"bytes={resume}-"
    with requests.get(url, headers=headers, stream=True, timeout=(15, 60), allow_redirects=True) as r:
        if r.status_code in (401, 403):
            raise PermissionError(f"HTTP {r.status_code}: authentication/licence acceptance required. "
                                  "Set HF_TOKEN (Colab Secrets) and accept the model licence on its Hugging Face page.")
        if r.status_code == 404:
            raise FileNotFoundError("HTTP 404 (URL moved or removed)")
        if r.status_code == 416:  # range not satisfiable -> restart cleanly
            part.unlink(missing_ok=True)
            raise RuntimeError("resume offset rejected; restarting")
        r.raise_for_status()
        mode = "ab" if r.status_code == 206 else "wb"
        if r.status_code != 206:
            resume = 0
        total = resume + int(r.headers.get("Content-Length", 0))
        done, last_pct, t0 = resume, -1, time.time()
        with open(part, mode) as f:
            for chunk in r.iter_content(chunk_size=1 << 22):
                if not chunk:
                    continue
                f.write(chunk); done += len(chunk)
                if total:
                    pct = int(done * 100 / total)
                    if pct // 5 != last_pct // 5:
                        last_pct = pct
                        speed = (done - resume) / max(time.time() - t0, 1e-6) / 1e6
                        print(f"    {pct:3d}%  {done/1e9:5.2f}/{total/1e9:.2f} GB  {speed:6.1f} MB/s", flush=True)
        if total and part.stat().st_size != total:
            raise IOError(f"incomplete download ({part.stat().st_size} of {total} bytes)")


def install(entry, models_dir, token):
    dest = models_dir / entry["subdir"] / entry["filename"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        ok, why = validate_file(dest, entry)
        if ok:
            print(f"[OK] {entry['id']}: already installed -> {dest}")
            return True
        print(f"[!!] {entry['id']}: existing file invalid ({why}); re-downloading")
        dest.unlink()
    part = dest.with_name(dest.name + ".part")
    print(f"[..] {entry['id']}: downloading (~{entry['approx_gb']} GB, licence: {entry.get('license','?')})")
    for url in entry["urls"]:
        print(f"  source: {url}")
        for attempt in range(1, RETRIES + 1):
            try:
                stream(url, part, token)
                tmp_final = part.with_name(entry["filename"] + ".verify")
                part.rename(tmp_final)
                ok, why = validate_file(tmp_final, entry)
                if ok:
                    tmp_final.rename(dest)
                    print(f"[OK] {entry['id']}: installed -> {dest}")
                    return True
                print(f"    validation failed: {why}")
                tmp_final.unlink(missing_ok=True)
                break  # try next URL
            except (PermissionError, FileNotFoundError) as e:
                print(f"    {e}")
                break  # retrying won't help; next URL
            except Exception as e:
                print(f"    attempt {attempt}/{RETRIES} failed: {e}")
                time.sleep(3 * attempt)
    print(f"[FAIL] {entry['id']}: all sources failed. See docs/TROUBLESHOOTING.md (failed download).")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-upscaler", action="store_true")
    ap.add_argument("--only", action="append", help="install only this model id (repeatable)")
    ap.add_argument("--variant", choices=["bf16", "fp8"], help="override auto variant")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    models = load_registry()
    if a.list:
        for m in models:
            print(f"{m['id']:28s} group={m['group']:9s} {m['approx_gb']:>5} GB  {m['subdir']}/{m['filename']}")
        return 0

    models_dir = Path(os.environ.get("MODELS_DIR", ROOT.parent / "ComfyUI" / "models"))
    if a.only:
        wanted = [m for m in models if m["id"] in a.only]
        missing = set(a.only) - {m["id"] for m in wanted}
        if missing:
            print("Unknown model id(s):", ", ".join(missing)); return 1
    else:
        variant = a.variant
        if not variant:
            from detect_gpu import build
            p = build()
            if not p.get("supported"):
                print("ERROR:", "; ".join(p["warnings"])); return 2
            variant = p["variant"]
        print(f"Model variant: {variant}")
        groups = {"core"} | ({"upscaler"} if (a.with_upscaler or os.environ.get("WITH_UPSCALER") == "1") else set())
        wanted = [m for m in models if m["group"] in groups and m.get("variant", variant) == variant]

    models_dir.mkdir(parents=True, exist_ok=True)
    need = sum(m["approx_gb"] for m in wanted if not (models_dir / m["subdir"] / m["filename"]).exists())
    free = shutil.disk_usage(str(models_dir)).free / 1e9
    print(f"Destination: {models_dir}\nStill to download: ~{need:.1f} GB, free disk: {free:.1f} GB")
    if free < need + 2:
        print("ERROR: not enough disk space (need download size + 2 GB headroom)."); return 3

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    results = {m["id"]: install(m, models_dir, token) for m in wanted}
    bad = [k for k, v in results.items() if not v]
    print("\nSummary:", ", ".join(f"{k}={'OK' if v else 'FAILED'}" for k, v in results.items()))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

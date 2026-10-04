#!/usr/bin/env python3
"""Queue an API-format workflow on a running ComfyUI, wait, and save the results.

  python scripts/run_workflow.py workflows/flux_basic.json --prompt "a red fox in snow, photo" --seed 1
  python scripts/run_workflow.py workflows/flux_image_to_image.json --image my.png --denoise 0.55 --prompt "oil painting"
  python scripts/run_workflow.py workflows/flux_upscale.json --image my.png
  python scripts/run_workflow.py workflows/flux_basic.json --check      # only validate nodes/models, don't run

Nodes are patched by their _meta.title: POSITIVE, NEGATIVE, LATENT, SAMPLER, UNET, LOAD_IMAGE, RESIZE.
Uses only the Python standard library.
"""
import argparse, json, os, random, sys, time, urllib.parse, urllib.request, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "config" / "generated" / "profile.json"


def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def jget(url):
    return json.loads(http(url))


def by_title(wf, title):
    return [(k, v) for k, v in wf.items() if v.get("_meta", {}).get("title") == title]


def validate(wf, base):
    """Check every class_type exists and every combo value is currently selectable."""
    info = jget(f"{base}/object_info")
    problems = []
    for nid, node in wf.items():
        ct = node["class_type"]
        if ct not in info:
            problems.append(f"node {nid}: class '{ct}' does not exist in this ComfyUI (update ComfyUI / check COMFYUI_REF)")
            continue
        spec = {**info[ct]["input"].get("required", {}), **info[ct]["input"].get("optional", {})}
        for name, val in node["inputs"].items():
            if isinstance(val, list) or name not in spec:
                continue
            opts = spec[name][0]
            if isinstance(opts, list) and val not in opts:
                problems.append(f"node {nid} ({ct}).{name} = {val!r} is not one of: {opts[:12]}{'...' if len(opts) > 12 else ''}")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow")
    ap.add_argument("--server", default=f"127.0.0.1:{os.environ.get('COMFY_PORT', '8188')}")
    ap.add_argument("--prompt"); ap.add_argument("--negative")
    ap.add_argument("--seed", type=int); ap.add_argument("--steps", type=int); ap.add_argument("--cfg", type=float)
    ap.add_argument("--width", type=int); ap.add_argument("--height", type=int)
    ap.add_argument("--denoise", type=float)
    ap.add_argument("--image", help="local image file (uploaded to ComfyUI input/)")
    ap.add_argument("--out", default="outputs", help="local folder to copy results to")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    base = f"http://{a.server}"
    wf = json.loads(Path(a.workflow).read_text())

    # Select the model file matching the detected GPU profile (bf16 vs fp8)
    if PROFILE.exists():
        unet = json.loads(PROFILE.read_text()).get("unet_name")
        for _, n in by_title(wf, "UNET"):
            if unet:
                n["inputs"]["unet_name"] = unet
    for _, n in by_title(wf, "POSITIVE"):
        if a.prompt: n["inputs"]["text"] = a.prompt
    for _, n in by_title(wf, "NEGATIVE"):
        if a.negative is not None: n["inputs"]["text"] = a.negative
    for _, n in by_title(wf, "LATENT"):
        if a.width: n["inputs"]["width"] = a.width
        if a.height: n["inputs"]["height"] = a.height
    for _, n in by_title(wf, "RESIZE"):
        if a.width: n["inputs"]["width"] = a.width
        if a.height: n["inputs"]["height"] = a.height
    for _, n in by_title(wf, "SAMPLER"):
        n["inputs"]["seed"] = a.seed if a.seed is not None else random.randint(0, 2**32 - 1)
        if a.steps: n["inputs"]["steps"] = a.steps
        if a.cfg is not None: n["inputs"]["cfg"] = a.cfg
        if a.denoise is not None: n["inputs"]["denoise"] = a.denoise

    try:
        problems = validate(wf, base)
    except Exception as e:
        print(f"ERROR: cannot reach ComfyUI at {base} ({e}). Start it: bash colab/start_comfyui.sh"); return 1
    if problems:
        print("WORKFLOW VALIDATION FAILED:")
        for p in problems: print("  -", p)
        print("Fix: pick the right file in the node dropdown, or download missing models (bash colab/install_models.sh).")
        return 2
    print("Workflow validation OK (all nodes and model names exist).")
    if a.check:
        return 0

    if a.image:
        path = Path(a.image)
        boundary = uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{path.name}\"\r\n"
                "Content-Type: application/octet-stream\r\n\r\n").encode() + path.read_bytes() + \
               (f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{boundary}--\r\n").encode()
        res = json.loads(http(f"{base}/upload/image", body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}))
        for _, n in by_title(wf, "LOAD_IMAGE"):
            n["inputs"]["image"] = res["name"]
        print("Uploaded:", res["name"])

    resp = json.loads(http(f"{base}/prompt", json.dumps({"prompt": wf, "client_id": uuid.uuid4().hex}).encode(),
                           {"Content-Type": "application/json"}))
    pid = resp["prompt_id"]
    print("Queued:", pid)
    t0 = time.time()
    while True:
        h = jget(f"{base}/history/{pid}")
        if pid in h:
            entry = h[pid]
            if entry.get("status", {}).get("status_str") == "error":
                print("EXECUTION ERROR:", json.dumps(entry["status"].get("messages", [])[-1:], indent=1)[:2000])
                print("See docs/TROUBLESHOOTING.md (CUDA out of memory / model not found).")
                return 3
            break
        time.sleep(1)
        if time.time() - t0 > 1800:
            print("Timed out after 30 min"); return 4
    Path(a.out).mkdir(parents=True, exist_ok=True)
    saved = []
    for out in entry["outputs"].values():
        for im in out.get("images", []):
            q = urllib.parse.urlencode({"filename": im["filename"], "subfolder": im["subfolder"], "type": im["type"]})
            dst = Path(a.out) / im["filename"]
            dst.write_bytes(http(f"{base}/view?{q}"))
            saved.append(str(dst))
    print(f"Done in {time.time()-t0:.1f}s. Saved:")
    for s in saved: print("  ", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())

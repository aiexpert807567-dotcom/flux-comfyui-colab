# config/

| File | Purpose |
|------|---------|
| `project.env` | Defaults (ComfyUI version pin, storage mode, tunnel, variant). Env vars set before running a script override it. |
| `local.env` | YOUR overrides. Git-ignored. **Never put tokens here if you ever remove it from .gitignore.** |
| `models.json` | Central model registry (URLs, destination subfolder, size sanity floor, license). Add a model = add one JSON entry. |
| `generated/` | Created at runtime (GPU profile). Git-ignored. |

Secrets (Hugging Face token) go in **Colab Secrets** (key icon in the Colab sidebar, name `HF_TOKEN`), not in files.

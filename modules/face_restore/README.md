# Optional module: face restoration (separate from core)

- **What:** GFPGAN v1.4 restores/sharpens degraded faces (old photos, low-res portraits) via the community node `facerestore_cf`.
- **Install:** `bash modules/face_restore/install.sh` then restart ComfyUI. The core system never imports it.
- **GPU:** small model; runs on any Colab GPU that runs the core setup.
- **Licenses:** GFPGAN code Apache-2.0 (TencentARC/GFPGAN). `facerestore_cf` - check its repository license before commercial use. Do NOT swap in CodeFormer for commercial work without reading its licence (S-Lab, non-commercial).
- **Not included on purpose:** face *swapping* tools (e.g. FaceFusion). If you add them yourself, use only images of yourself, consenting people, or synthetic characters; never for impersonation, deception, or non-consensual content. Check each tool's licence and its model licences (some bundled models are research/non-commercial only).
- **Node names** come from the community node and can change; verify in ComfyUI's node search ("FaceRestore").

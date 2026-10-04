# Security

- ComfyUI binds to **127.0.0.1** (localhost inside the Colab VM): unreachable from the internet by itself.
- `TUNNEL=cloudflared` creates a **public, unauthenticated** `*.trycloudflare.com` URL pointing at it. The name is random and short-lived, but anyone who gets the link can queue jobs, read your outputs and use custom-node features. Don't post it, don't leave sessions running, never run a persistent public server. Prefer `TUNNEL=none` + `scripts/run_workflow.py` when you can.
- ComfyUI has no built-in login. Do not install untrusted custom nodes (they run arbitrary Python as you; in Colab that includes access to a mounted Drive).
- Never commit: Hugging Face / GitHub tokens, API keys, `.env`, Drive paths with personal data, generated images of people. Use Colab Secrets. `.gitignore` blocks `.env`, `*token*`, keys, model files and images.
- If a token leaks: revoke it at huggingface.co/settings/tokens or github.com/settings/tokens immediately; removing it from a later commit does not remove it from history.
- Drive mode gives the runtime access to your Drive: use a separate Google account if that concerns you.

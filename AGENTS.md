# Agent instructions

See `../AGENTS.md` for workspace-level conventions (git workflow, test/lint autonomy, readonly ops, writing voice, deploy knowledge). This file covers only what's specific to this repo.

---

# eco-spec-tracker / eco-jobs-tracker

FastAPI + Jinja2 + HTMX web app that lists every Eco player's jobs (professions/specialties) with `active / total` counts. Paired with a C# Eco server mod that exposes `/api/v1/skills`.

Deploy target: `eco-jobs-tracker.coilysiren.me` (k3s homelab, same rig as `backend` / `eco-mcp-app`).

## Deploy reference

This repo is the **canonical reference** for the current deploy shape - when other repos need to match a working baseline, eco-spec-tracker is what they copy from (commit `49f99e4`). The comprehensive writeup still lives in [`infrastructure/docs/k3s-deploy-notes.md`](../infrastructure/docs/k3s-deploy-notes.md). Read that first before touching any deploy config (Dockerfile, Makefile, `deploy/main.yml`, GHA workflow, or Tailscale/k3s secrets). When you resolve a new deploy pitfall, add it to that doc's §7 / §9.

## Project layout

Python side (the web app):
- `src/eco_spec_tracker/main.py` - FastAPI app. Routes: `/`, `/players`, `/healthz`, `/partials/*` (HTMX), `/api/v1/*` (JSON).
- `src/eco_spec_tracker/mock_data.py` - placeholder data matching the shape the mod returns. Bypassed once the real mod is wired.
- `src/eco_spec_tracker/templates/` - Jinja2 templates. `base.html` is the layout; `_*.html` are HTMX partials. Styling via Tailwind Play CDN (no build step).
- `src/eco_spec_tracker/static/` - empty for now; keep around for future self-hosted assets.

C# side (the mod):
- `mod/eco-jobs-tracker.sln` - one solution, two projects.
- `mod/src/EcoJobsTracker.csproj` + `.cs` - the real mod. References `Eco.ReferenceAssemblies`. Compiles to a DLL that drops into Eco's `Server/Mods/EcoJobsTracker/` directory.
- `mod/shell/EcoJobsTracker.Shell.csproj` + `.cs` - standalone ASP.NET Core harness. Same route (`GET /api/v1/skills`), same DTOs, canned data. Lets the Python tracker iterate against a real C# HTTP server on `localhost:5100` without booting Eco.
- `mod/src/Dtos.cs` - shared DTO record types; `<Compile Include>`-linked into the shell so responses match byte-for-byte.

Deploy rig (cloned from `coilysiren/backend` pattern):
- `Makefile`, `Dockerfile`, `config.yml`, `deploy/main.yml`, `.github/workflows/build-and-publish.yml`.

## Dev loop

- `make build-native` - `uv sync --group dev` (Python).
- `make run-native` - uvicorn on `:4100` with `--reload`. Edit any file under `src/` and the server restarts.
- `make run-shell` - C# shell harness on `:5100`, same API shape the real mod will serve.
- `make build-mod` - compile the real mod DLL for deployment onto an Eco server.
- `make build-docker` / `make deploy` - build/push image, roll out to k3s.
- `pre-commit install` - ruff + mypy on Python, `dotnet format` on C# mod sources.

## Data flow

```
Eco server ──[real mod, EcoJobsTracker.dll]──► GET /api/v1/skills
                                                     ▲
                              or locally            │
                                                     │
mod/shell (EcoJobsTracker.Shell) ───────────────────┘  (port 5100, mock data)

                FastAPI tracker (eco-jobs-tracker.coilysiren.me, port 4100 locally)
                    ├─ HTML UI (Jinja2 + HTMX + Tailwind)
                    └─ /api/v1/{professions,players}
```

Today the FastAPI server reads `mock_data.py` directly. Next step: add an `UPSTREAM_URL` env var so it pulls from either the shell harness or the real mod endpoint.

## Eco mod notes

The mod is a standard UserCode mod: `.cs` files dropped into the server's `Mods/UserCode/` directory are compiled at server boot (no prebuild step). It uses the public ModKit API (`Eco.ReferenceAssemblies` NuGet, same as `eco-mods-public`).

Reference for how mods are authored / packaged:
- Sibling repo `eco-mods-public` for UserCode layout and `Register.cs` convention.
- ModKit: https://github.com/StrangeLoopGames/EcoModKit.
- Eco modding docs: https://docs.play.eco/.

The community mod `eco-price-calculator` (mod.io) is a known example of a mod that adds HTTP API endpoints; its source isn't published but confirms the approach is standard.

**Do not copy any file from the user's local Eco source checkout into this repo.** Only the public ModKit API surface should appear here.

## Sibling repos

| Dir | Visibility | Purpose |
|---|---|---|
| `backend` | public | Canonical deploy template (k3s + GHCR + Tailscale + cert-manager). |
| `eco-mcp-app` | public | MCP server exposing Eco `/info` - same deploy rig. |
| `eco-mods` / `eco-mods-public` | private / public | C# mods for the Eco server. |
| `infrastructure` | public | k3s cluster config, Traefik, cert-manager. |
| `kai-server` | public | Homelab k3s box (`kai@kai-server`, Tailscale `100.69.164.66`). |

## Reaching the homelab

`tailscale up && ssh kai@kai-server` gets you into the k3s host. The GitHub Actions `deploy` job does the same thing (tailscale up → kubeconfig → `make .deploy`).

### Pushing the mod DLL

`coily eco mod push --src EcoJobsTracker.zip` is the canonical path. The zip must contain `Mods/EcoJobsTracker/EcoJobsTracker.dll` (plus sibling `.deps.json` / `.pdb` when present) so it extracts directly under `/home/kai/Steam/steamapps/common/EcoServer/`. Then `coily eco restart` loads it. See [`infrastructure/eco.md`](../infrastructure/eco.md) §4 for the zip convention and sequencing rules (especially: push the mod before the web app picks up `UPSTREAM_URL`, since `upstream.py` has no fallback on a dead endpoint).

Build with `make build-mod` (drops the three files in `mod/src/bin/Release/net10.0/`); zip from that directory with the `Mods/EcoJobsTracker/` prefix.

## Open questions

- API-key provisioning for the mod endpoint (once we move off mock data).
- Whether "active" means "online right now" or "logged in within N days" - currently a mock boolean.

---

## Post-push follow-up (auto-schedule)

Per the workspace "Default to proactive scheduling" rule: after pushing to `main`, schedule a wake-up to verify the build-publish-deploy job landed on kai-server. CI builds the docker image, pushes to ghcr.io, and rolls out a k8s deployment; total time is ~6-12 min.

- **Cadence**: 720s (12 min) after push.
- **Verify CI**: `coily gh run list --repo coilysiren/eco-spec-tracker --limit 1` should show `completed/success`. Re-schedule once at +300s if in progress; surface and stop on failure.
- **Verify rollout**: `coily kubectl --context=kai-server -n coilysiren-eco-spec-tracker rollout status deployment/coilysiren-eco-spec-tracker-app --timeout=2m`.
- **Skip** for docs-only pushes.

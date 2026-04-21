# eco-spec-tracker / eco-jobs-tracker

FastAPI + Jinja2 + HTMX web app that lists every Eco player's jobs (professions/specialties) with `active / total` counts. Paired with a C# Eco server mod that exposes `/api/v1/skills`.

Deploy target: `eco-jobs-tracker.coilysiren.me` (k3s homelab, same rig as `backend` / `eco-mcp-app`).

## Autonomy

- Commit directly to `main`. Do not open PRs unless asked.
- Run tests, linters, and builds without asking.
- Fix lint errors automatically.
- Readonly git + shell commands (`ls`, `grep`, `cat`, etc.) are always fine.
- `cd` into any `/Users/kai/projects/coilysiren` folder without asking.

## Project layout

- `src/eco_spec_tracker/main.py` — FastAPI app. Routes: `/`, `/players`, `/healthz`, `/partials/*` (HTMX), `/api/v1/*` (JSON).
- `src/eco_spec_tracker/mock_data.py` — placeholder data matching the shape the mod will return.
- `src/eco_spec_tracker/templates/` — Jinja2 templates. `base.html` is the layout; `_*.html` are HTMX partials.
- `src/eco_spec_tracker/static/app.css` — single stylesheet, dark theme, no build step.
- `mod/` — (TODO) C# UserCode mod source for Eco. Drops into `Eco/Server/Mods/UserCode/`; auto-compiled by the server's Roslyn compiler at boot. No csproj needed.
- `Makefile` / `Dockerfile` / `config.yml` / `deploy/main.yml` / `.github/workflows/build-and-publish.yml` — deploy rig cloned from `coilysiren/backend` pattern.

## Dev loop

- `make build-native` — `uv sync --group dev`.
- `make run-native` — uvicorn on `:4000` with `--reload`. Edit any file under `src/` and the server restarts.
- `make build-docker` / `make deploy` — build/push image, roll out to k3s.

## Data flow (target)

```
Eco server (C# mod, UserCode/Controllers/SkillsApiController.cs)
  └─ GET http://eco-server:3001/api/v1/skills   [API key auth]
       └─ FastAPI tracker (eco-jobs-tracker.coilysiren.me)
            ├─ HTML UI (Jinja2 + HTMX)
            └─ /api/v1/professions, /api/v1/players (JSON passthrough)
```

Mock mode (current) bypasses the mod entirely and serves `mock_data.py`.

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
| `eco-mcp-app` | public | MCP server exposing Eco `/info` — same deploy rig. |
| `eco-mods` / `eco-mods-public` | private / public | C# mods for the Eco server. |
| `infrastructure` | public | k3s cluster config, Traefik, cert-manager. |
| `kai-server` | public | Homelab k3s box (`kai@kai-server`, Tailscale `100.69.164.66`). |

## Open questions

- How does the compiled mod reach the running Eco server? (scp? volume mount? manual deploy?)
- API-key provisioning for the mod endpoint.
- Whether "active" means "online right now" or "logged in within N days" — currently a mock boolean.

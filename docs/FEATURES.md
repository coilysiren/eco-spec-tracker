# Features

Headline-feature inventory for `eco-jobs-tracker`. "What does this repo do," not file-level detail.

## Shape

Two processes: a C# Eco mod exposing a read-only HTTP endpoint of every player's learned specialties, and a FastAPI dashboard rendering a "who can make what" board.

## Web dashboard (FastAPI)

- **Live HTML dashboard at `eco-jobs-tracker.coilysiren.me`** - Stacked Professions, Specialties, Players sections. Tailwind CDN, no build step.
- **Drill-down pages** - `/professions`, `/specialties`, `/players` each render one section without the eco-card header.
- **Embedded live server-status card** - Homepage embeds the card from sibling `eco-mcp-app` (git dep), in lockstep with the MCP widget.
- **HTMX partials** - `/partials/eco-card` and `/partials/profession/{name}` serve fragments for in-page expansion.
- **JSON API mirror** - `/api/v1/professions`, `/api/v1/players`, `/api/v1/specialties` return same data, machine-readable.
- **Iframe embedding** - CSP `frame-ancestors` allows `coilysiren.me` to embed (eco-modding page on personal site).
- **Healthcheck** - `/healthz` returns `{"ok": true}` for k8s probes.
- **Mock-data fallback** - `UPSTREAM_URL` unset = canned data from `mock_data.py`, flagged via `using_mock_data` template global.
- **Upstream mod fetch** - `UPSTREAM_URL` set = `upstream.py` calls `/api/v1/skills` with `UPSTREAM_API_KEY` as `X-API-Key`, 5s timeout, no fallback on a dead endpoint.
- **Dev-only livereload** - `DEBUG`-gated `/ws/livereload` WebSocket + injected script. CSS swaps without full reload. Zero prod cost.
- **Sentry telemetry** - `SENTRY_DSN`-gated init. No-op when unset.

## C# Eco mod (`EcoJobsTracker.dll`)

- **`GET /api/v1/skills` endpoint** - ModKit UserCode mod, `[ApiController]` picked up by Eco's ASP.NET host.
- **Every player's learned specialties** - Iterates `UserManager.Users`, filters `Level > 0 && IsSpecialty`, returns name/level/max-level + online state.
- **Auth via Eco's admin-token middleware** - Same `X-API-Key` gate as the rest of `/api/v1/*`. No bespoke auth.
- **Dual-attribute DTOs** - Records carry `System.Text.Json` and `Newtonsoft.Json` camelCase attributes, serializing identically under either pipeline.
- **mod.io distribution** - Listing copy + zip-shape in `mod/modio.md`.

## Shell harness (`mod/shell/`)

- **Standalone ASP.NET mock on `:5100`** - Same route, same DTOs (`<Compile Include>`-linked), canned data. Iterate without booting Eco.

## Deploy and ops

- **Canonical deploy reference for the homelab** - Other `coilysiren/*` repos copy this Dockerfile, Makefile, `deploy/main.yml`, GHA pipeline.
- **k3s + ExternalSecrets** - Pulls `SENTRY_DSN` + `UPSTREAM_API_KEY` from AWS SSM via ClusterSecretStore.
- **Image publish** - Builds + pushes to `ghcr.io/coilysiren/eco-spec-tracker/...`, git-SHA tagged.
- **Tailscale + Traefik + cert-manager** - Inherited from `backend` template.
- **`coily eco mod push` path** - `make build-mod`, zip with `Mods/EcoJobsTracker/` prefix, push, `coily eco restart`.

## Dev-loop tooling

- **`make build-native` / `run-native`** - `uv sync --group dev`, uvicorn `--reload` on `:4100`.
- **`make run-shell`** - C# shell harness on `:5100`.
- **`make build-mod`** - Production mod DLL.
- **`make build-docker` / `deploy`** - Container build/push + k3s rollout.
- **Pre-commit** - ruff + mypy on Python, `dotnet format` on C#.
- **Smoke suite** - `tests/test_smoke.py`: every page, every JSON, eco-card partial (respx-stubbed `/info`), parser fixture.

## Naming-debt note

Public name is `eco-jobs-tracker`. Internals still use `eco-spec-tracker` (k8s, package, image, SSM, Sentry). Rename deferred. See README.

## See also

- [README.md](../README.md) - human-facing intro.
- [AGENTS.md](../AGENTS.md) - agent-facing operating rules.
- [.coily/coily.yaml](../.coily/coily.yaml) - allowlisted commands.

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilyco-flight-deck/agentic-os/issues/59).

# Agent instructions

Workspace conventions load globally via `~/.claude/CLAUDE.md` -> `agentic-os-kai/AGENTS.md`. This file covers only what is specific to this repo.

## Scope

FastAPI + Jinja2 + HTMX app listing every Eco player's jobs (professions/specialties) with `active / total` counts. Paired with a C# Eco mod exposing `/api/v1/skills`. Deploy: `eco-jobs-tracker.coilysiren.me` (k3s homelab).

## Project shape

Python web app:

- `src/eco_spec_tracker/main.py` - FastAPI app. Routes `/`, `/players`, `/healthz`, `/partials/*`, `/api/v1/*`.
- `src/eco_spec_tracker/mock_data.py` - placeholder matching the mod's shape.
- `src/eco_spec_tracker/templates/` - Jinja2 `base.html` + `_*.html` HTMX partials, Tailwind CDN.

C# mod (`mod/`):

- `eco-jobs-tracker.sln` - one solution, two projects.
- `src/` - the real mod, references `Eco.ReferenceAssemblies`, drops into `Server/Mods/EcoJobsTracker/`.
- `shell/` - standalone ASP.NET harness on `:5100`, same route, canned data.
- `src/Dtos.cs` - shared DTO records, `<Compile Include>`-linked into the shell.

Deploy rig (cloned from `coilysiren/backend`): `Makefile`, `Dockerfile`, `coily.yaml`, `deploy/main.yml`, GHA workflow.

## Repo boundaries

This repo is the canonical reference for the current deploy shape - other repos copy from here. Writeup: [`infrastructure/docs/k3s-deploy-notes.md`](../infrastructure/docs/k3s-deploy-notes.md). Read before touching Dockerfile, Makefile, `deploy/main.yml`, GHA, or Tailscale/k3s secrets.

## Commands

Route dev verbs through `coily`, which reads [.coily/coily.yaml](.coily/coily.yaml):

- `coily exec build-native` / `run-native` - uv sync, uvicorn `:4100` with reload.
- `coily exec run-shell` - C# harness on `:5100`.
- `coily exec build-mod` - compile the real mod DLL.
- `coily exec build-docker` / `publish` - build the image, push to GHCR.

GHA (`build-and-publish.yml`) runs tests and publishes the image on push to `main`. The k3s rollout is the Makefile `deploy` target (`publish` + apply + rollout), not a CI job. `UPSTREAM_URL` selects whether FastAPI reads `mock_data.py` or pulls from shell/mod.

## Validation

Run `coily exec precommit` (ruff + mypy + `dotnet format` + agentic-os checks) and `coily exec test` before pushing. Run tests, linters, and builds without asking. Fix failures. Never use `--no-verify`.

## Safety

Do not change `coily.yaml`'s `name` - it cascades into every k8s resource and the image tag. The mod uses only the public ModKit API (`Eco.ReferenceAssemblies` NuGet). Do not copy from any local Eco source checkout.

## Cross-repo contracts

The mod is the source of truth, this app the view. The homepage server-status card imports from sibling `eco-mcp-app` (git dep). Push the mod before the web app picks up `UPSTREAM_URL` - no fallback on a dead endpoint. See [`infrastructure/eco.md`](../infrastructure/eco.md) §4.

## Release

Push the mod DLL with `coily eco mod push --src EcoJobsTracker.zip` (zip must hold `Mods/EcoJobsTracker/EcoJobsTracker.dll` + sibling `.deps.json`/`.pdb`), then `coily eco restart`. mod.io listing copy: [`mod/modio.md`](mod/modio.md).

After pushing `main` (skip docs-only), schedule a 720s wake-up: verify CI via `coily gh run list --repo coilysiren/eco-jobs-tracker --limit 1` (re-schedule once at +300s if in progress), then rollout via `coily kubectl --context=kai-server -n coilysiren-eco-spec-tracker rollout status deployment/coilysiren-eco-spec-tracker-app`.

## Agent rules

Commit to main directly, push after each commit, no PRs unless asked.

## See also

- [README.md](README.md) - human-facing intro.
- [docs/FEATURES.md](docs/FEATURES.md) - inventory of what ships today.
- [.coily/coily.yaml](.coily/coily.yaml) - allowlisted commands.

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilyco-flight-deck/agentic-os/issues/59).

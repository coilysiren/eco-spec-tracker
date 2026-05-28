# mod.io publish notes

Source of truth for the mod.io listing fields. Keep in sync when the mod
behavior or distribution shape changes.

- **Game:** ECO (id `6`)
- **Type tag:** `Script` (matches DiscordLink, Eco Price Calculator, Eco Transport, Cost Calculator. Server-side mods that expose code or HTTP endpoints all use this single tag.)
- **Visibility:** Public
- **Maturity:** None
- **Logo:** `docs/logo-modio.png` (1600x900, cropped from the live dashboard's Professions grid)
- **Homepage URL:** <https://github.com/coilysiren/eco-jobs-tracker>
- **Live demo:** <https://eco-jobs-tracker.coilysiren.me/> (the FastAPI dashboard in this same repo, pointing at the maintainer's server)

## Name

`Eco Jobs Tracker`

(Mod assembly is `EcoJobsTracker`. Matches the live dashboard subdomain.)

## Summary (≤250 chars)

> Read-only admin endpoint that lists every player's learned professions and specialties. Authenticated with your Eco admin token. Pair with the live dashboard at eco-jobs-tracker.coilysiren.me or point any client at GET /api/v1/skills.

## Description (markdown)

```markdown
**Eco Jobs Tracker** adds a single read-only endpoint to your Eco server:

```
GET /api/v1/skills
```

It returns every player on the server and the specialties they've learned, in
a stable JSON shape suitable for dashboards, Discord bots, or spreadsheet
imports.

## What it's for

Eco's "who can make what" question is hard to answer without poking each
player's profile. This mod gives admins, traders, and tooling a structured
answer: every player, every profession, every specialty, with levels.

## Pair with the live dashboard

The companion FastAPI app at <https://eco-jobs-tracker.coilysiren.me/> renders
the same data into a browsable UI - professions, specialties, and a per-player
view, with live `active / total` counts. You can host your own copy from the
same repo, or point your own UI at the JSON.

![dashboard screenshot](https://raw.githubusercontent.com/coilysiren/eco-spec-tracker/main/docs/screenshot.png)

## Install

1. Download the latest `EcoJobsTracker.zip`.
2. Extract into your Eco server directory so the DLL lands at
   `Mods/EcoJobsTracker/EcoJobsTracker.dll`.
3. Restart the server. Eco's mod loader picks up the controller automatically.
4. Verify: `curl -H "X-API-Key: <your-admin-token>" http://<your-server>:3001/api/v1/skills`

## Auth

The endpoint sits under `/api/v1/*`, so Eco's existing admin-token middleware
guards it - the same `X-API-Key` header you'd use for any other admin route.
No separate config to set on the mod side.

## Compatibility

- Eco `0.13.0-beta-release-998` and newer (built against `Eco.ReferenceAssemblies 0.13.0-beta-release-998`).
- Linux and Windows dedicated servers both work.

## Source and license

- Repo: <https://github.com/coilysiren/eco-jobs-tracker>
- License: MIT
- Issues / feature requests: GitHub issues on the repo.

This is an unofficial fan tool. Eco is a trademark of Strange Loop Games;
this mod is not affiliated with Strange Loop Games.
```

## Distribution zip

Build:

```sh
make build-mod
cd mod/src/bin/Release/net10.0
zip -r ../../../../EcoJobsTracker-0.1.0.zip Mods/EcoJobsTracker/
```

Zip layout (mod.io extracts straight into the server root):

```
EcoJobsTracker-0.1.0.zip
└── Mods/
    └── EcoJobsTracker/
        ├── EcoJobsTracker.dll
        ├── EcoJobsTracker.deps.json
        └── EcoJobsTracker.pdb
```

(The repo's existing `make build-mod` drops the three files at
`mod/src/bin/Release/net10.0/`. Zip from there with the `Mods/EcoJobsTracker/`
prefix - same convention `coily eco mod push` already expects.)

## Version bumps

- `<Version>` in `mod/src/EcoJobsTracker.csproj` is the source of truth.
- Filename of the zip uploaded to mod.io must match (`EcoJobsTracker-X.Y.Z.zip`).
- Mod.io release notes go under "Add files" on the upload form, not in this
  doc.

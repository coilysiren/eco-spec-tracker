"""FastAPI app for eco-jobs-tracker.

Serves a Jinja2 + HTMX UI plus a JSON API. Currently backed by mock data;
will eventually call the Eco mod's `/api/v1/skills` endpoint.

The top of every HTML page embeds the live Eco server status card from
`eco-mcp-app` (sister repo, installed as a git dep). The card and its CSS
are imported directly — we ride the same rendering path so visuals stay
in lockstep with whatever eco-mcp-app ships.
"""

from __future__ import annotations

import re
from pathlib import Path

from eco_mcp_app import render_status_html, status_css
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from eco_spec_tracker import mock_data, upstream
from eco_spec_tracker.livereload import DEBUG, LIVERELOAD_SCRIPT
from eco_spec_tracker.livereload import router as livereload_router

# Allow coilysiren.me to embed this app in an iframe (eco-modding page).
# Modern browsers honor frame-ancestors and ignore X-Frame-Options when both
# are present — keep X-Frame-Options unset everywhere (app + ingress).
FRAME_ANCESTORS_CSP = "frame-ancestors 'self' https://www.coilysiren.me https://coilysiren.me"

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# eco-mcp-app's CSS spliced into our base template via a Jinja global.
# Read once at module import; the bytes are tiny.
TEMPLATES.env.globals["eco_mcp_css"] = status_css()
TEMPLATES.env.globals["livereload_script"] = LIVERELOAD_SCRIPT if DEBUG else ""

app = FastAPI(title="eco-jobs-tracker", version="0.1.0")


@app.middleware("http")
async def add_frame_ancestors_csp(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = FRAME_ANCESTORS_CSP
    return response


app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
if DEBUG:
    app.include_router(livereload_router)


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"ok": True})


# eco-mcp-app's card.html bakes in a "Try this card on another public Eco
# server" pill strip and a "© Kai Siren · view source" credits line. The
# try-others pills belong in eco-mcp-app's /preview UI, not a jobs tracker
# pinned to one server; the credits line duplicates our own outer footer.
# Strip both blocks out of the rendered card HTML.
_TRY_OTHERS_RE = re.compile(r'<div class="try-others">.*?</div>\s*</div>', flags=re.DOTALL)
_CREDITS_LINE_RE = re.compile(r'<div class="credits-line">.*?</div>', flags=re.DOTALL)


@app.get("/partials/eco-card", response_class=HTMLResponse)
async def partial_eco_card() -> HTMLResponse:
    """Live Eco server status card, rendered by eco-mcp-app."""
    html = await render_status_html()
    html = _TRY_OTHERS_RE.sub("", html)
    html = _CREDITS_LINE_RE.sub("", html)
    return HTMLResponse(html)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Homepage: live eco card + all three content sections stacked."""
    rows = await upstream.fetch_rows()
    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "stats": mock_data.profession_stats(rows),
            "specialties": mock_data.specialties(rows),
            "players": mock_data.players(rows),
        },
    )


@app.get("/professions", response_class=HTMLResponse)
async def professions_page(request: Request) -> HTMLResponse:
    """Just the Professions section, no eco card."""
    rows = await upstream.fetch_rows()
    return TEMPLATES.TemplateResponse(
        request, "professions.html", {"stats": mock_data.profession_stats(rows)}
    )


@app.get("/specialties", response_class=HTMLResponse)
async def specialties_page(request: Request) -> HTMLResponse:
    """Just the Specialties section, no eco card."""
    rows = await upstream.fetch_rows()
    return TEMPLATES.TemplateResponse(
        request, "specialties.html", {"specialties": mock_data.specialties(rows)}
    )


@app.get("/players", response_class=HTMLResponse)
async def players_page(request: Request) -> HTMLResponse:
    """Just the Players section, no eco card."""
    rows = await upstream.fetch_rows()
    return TEMPLATES.TemplateResponse(request, "players.html", {"players": mock_data.players(rows)})


@app.get("/partials/profession/{name}", response_class=HTMLResponse)
async def partial_profession_detail(request: Request, name: str) -> HTMLResponse:
    """HTMX partial: expand a profession to see its players."""
    rows = await upstream.fetch_rows()
    stats = {s.profession: s for s in mock_data.profession_stats(rows)}
    stat = stats.get(name)
    if stat is None:
        return HTMLResponse(f"<p>Unknown profession: {name}</p>", status_code=404)
    return TEMPLATES.TemplateResponse(request, "_profession_detail.html", {"stat": stat})


# --- JSON API (machine-readable mirror of the live data) ---


@app.get("/api/v1/professions")
async def api_professions() -> JSONResponse:
    rows = await upstream.fetch_rows()
    stats = mock_data.profession_stats(rows)
    return JSONResponse(
        [
            {"profession": s.profession, "active": s.active, "total": s.total, "players": s.players}
            for s in stats
        ]
    )


@app.get("/api/v1/players")
async def api_players() -> JSONResponse:
    rows = await upstream.fetch_rows()
    return JSONResponse(
        [
            {
                "name": p.name,
                "active": p.active,
                "specialties": [
                    {"specialty": s.specialty, "level": s.level, "active": s.active}
                    for s in p.specialties
                ],
            }
            for p in mock_data.players(rows)
        ]
    )


@app.get("/api/v1/specialties")
async def api_specialties() -> JSONResponse:
    rows = await upstream.fetch_rows()
    return JSONResponse(
        [
            {
                "specialty": s.name,
                "profession": s.profession,
                "active": s.active,
                "total": s.total,
                "holders": [
                    {"player": h.player, "level": h.level, "active": h.active} for h in s.holders
                ],
            }
            for s in mock_data.specialties(rows)
        ]
    )

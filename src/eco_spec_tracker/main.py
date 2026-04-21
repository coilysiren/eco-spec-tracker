"""FastAPI app for eco-jobs-tracker.

Serves a Jinja2 + HTMX UI plus a JSON API. Currently backed by mock data;
will eventually call the Eco mod's `/api/v1/skills` endpoint.

The top of every HTML page embeds the live Eco server status card from
`eco-mcp-app` (sister repo, installed as a git dep). The card and its CSS
are imported directly — we ride the same rendering path so visuals stay
in lockstep with whatever eco-mcp-app ships.
"""

from __future__ import annotations

from pathlib import Path

from eco_mcp_app import render_status_html, status_css
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from eco_spec_tracker import mock_data
from eco_spec_tracker.livereload import DEBUG, LIVERELOAD_SCRIPT
from eco_spec_tracker.livereload import router as livereload_router

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# eco-mcp-app's CSS spliced into our base template via a Jinja global.
# Read once at module import; the bytes are tiny.
TEMPLATES.env.globals["eco_mcp_css"] = status_css()
TEMPLATES.env.globals["livereload_script"] = LIVERELOAD_SCRIPT if DEBUG else ""

app = FastAPI(title="eco-jobs-tracker", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
if DEBUG:
    app.include_router(livereload_router)


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"ok": True})


@app.get("/partials/eco-card", response_class=HTMLResponse)
async def partial_eco_card() -> HTMLResponse:
    """Live Eco server status card, rendered by eco-mcp-app."""
    return HTMLResponse(await render_status_html())


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Homepage: live eco card + all three content sections stacked."""
    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {
            "stats": mock_data.profession_stats(),
            "specialties": mock_data.specialties(),
            "players": mock_data.players(),
            "total_players": len(mock_data.players()),
        },
    )


@app.get("/professions", response_class=HTMLResponse)
def professions_page(request: Request) -> HTMLResponse:
    """Just the Professions section, no eco card."""
    return TEMPLATES.TemplateResponse(
        request,
        "professions.html",
        {
            "stats": mock_data.profession_stats(),
            "total_players": len(mock_data.players()),
        },
    )


@app.get("/specialties", response_class=HTMLResponse)
def specialties_page(request: Request) -> HTMLResponse:
    """Just the Specialties section, no eco card."""
    return TEMPLATES.TemplateResponse(
        request, "specialties.html", {"specialties": mock_data.specialties()}
    )


@app.get("/players", response_class=HTMLResponse)
def players_page(request: Request) -> HTMLResponse:
    """Just the Players section, no eco card."""
    return TEMPLATES.TemplateResponse(request, "players.html", {"players": mock_data.players()})


@app.get("/partials/professions", response_class=HTMLResponse)
def partial_professions(request: Request) -> HTMLResponse:
    """HTMX partial: refreshable profession grid."""
    stats = mock_data.profession_stats()
    return TEMPLATES.TemplateResponse(request, "_professions.html", {"stats": stats})


@app.get("/partials/profession/{name}", response_class=HTMLResponse)
def partial_profession_detail(request: Request, name: str) -> HTMLResponse:
    """HTMX partial: expand a profession to see its players."""
    stats = {s.profession: s for s in mock_data.profession_stats()}
    stat = stats.get(name)
    if stat is None:
        return HTMLResponse(f"<p>Unknown profession: {name}</p>", status_code=404)
    return TEMPLATES.TemplateResponse(request, "_profession_detail.html", {"stat": stat})


# --- JSON API (machine-readable mirror of the mock data) ---


@app.get("/api/v1/professions")
def api_professions() -> JSONResponse:
    stats = mock_data.profession_stats()
    return JSONResponse(
        [
            {"profession": s.profession, "active": s.active, "total": s.total, "players": s.players}
            for s in stats
        ]
    )


@app.get("/api/v1/players")
def api_players() -> JSONResponse:
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
            for p in mock_data.players()
        ]
    )


@app.get("/api/v1/specialties")
def api_specialties() -> JSONResponse:
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
            for s in mock_data.specialties()
        ]
    )

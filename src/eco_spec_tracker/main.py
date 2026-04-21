"""FastAPI app for eco-jobs-tracker.

Serves a Jinja2 + HTMX UI plus a JSON API. Currently backed by mock data;
will eventually call the Eco mod's `/api/v1/skills` endpoint.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from eco_spec_tracker import mock_data

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="eco-jobs-tracker", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"ok": True})


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    stats = mock_data.profession_stats()
    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        {"stats": stats, "total_players": len(mock_data.players())},
    )


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


@app.get("/players", response_class=HTMLResponse)
def players_page(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(
        request, "players.html", {"players": mock_data.players()}
    )


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

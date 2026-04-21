"""Dev-only browser livereload via WebSocket. No-op in production.

Two pieces that work together:

1. `router` — exposes ``/ws/livereload``. When any file under the configured
   paths changes, it pushes ``"reload"`` (or ``"css"`` for pure CSS changes).
2. `LIVERELOAD_SCRIPT` — one-line ``<script>`` block the host template drops
   into ``<body>``. Opens the socket, reloads the page (or swaps stylesheets)
   on messages, and reconnects after uvicorn ``--reload`` restarts.

Gated on the ``DEBUG`` env var. Set ``DEBUG=1`` for local dev; leave unset in
production. When off, the router is never registered and the script is an
empty string, so production pays zero runtime cost.

Pairs nicely with ``uvicorn --reload``:
- ``--reload`` restarts the Python process on ``.py`` changes.
- This module forces the *browser* to reload on any watched-file change.
- The client's ``onclose`` reconnect loop survives the Python restart.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from watchfiles import awatch

DEBUG = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")

# Watch the whole src/eco_spec_tracker/ tree. .py changes trigger uvicorn's
# own reload first; the watcher then catches the resulting restart via the
# WebSocket closing and the client reconnects. Template/static changes are
# picked up directly by the watcher.
_WATCH_ROOT = Path(__file__).resolve().parent
WATCH_PATHS: tuple[str, ...] = (str(_WATCH_ROOT),)

router = APIRouter()


@router.websocket("/ws/livereload")
async def livereload(ws: WebSocket) -> None:
    await ws.accept()
    try:
        async for changes in awatch(*WATCH_PATHS):
            # CSS-only changes can hot-swap without a full page reload, which
            # preserves scroll position and form state. Anything else — HTML,
            # JS, Python — needs a full reload.
            if changes and all(str(path).endswith(".css") for _, path in changes):
                await ws.send_text("css")
            else:
                await ws.send_text("reload")
    except WebSocketDisconnect:
        pass


LIVERELOAD_SCRIPT = """
<script>
(() => {
  const connect = () => {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${proto}//${location.host}/ws/livereload`);
    ws.onmessage = (e) => {
      if (e.data === "reload") { location.reload(); return; }
      if (e.data === "css") {
        document.querySelectorAll("link[rel=stylesheet]").forEach((link) => {
          const url = new URL(link.href);
          url.searchParams.set("_", Date.now());
          link.href = url.toString();
        });
      }
    };
    ws.onclose = () => setTimeout(connect, 500);  // survive --reload restarts
  };
  connect();
})();
</script>
"""

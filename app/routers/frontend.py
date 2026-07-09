"""
Sirve el HTML de la SPA con cache-busting basado en mtime, para que los
navegadores siempre recojan la última versión de app.js/style.css tras un
cambio.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from ..config import STATIC_DIR

router = APIRouter(tags=["frontend"])


@router.get("/")
def index():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    for asset in ("app.js", "style.css"):
        asset_path = STATIC_DIR / asset
        if asset_path.is_file():
            version = int(asset_path.stat().st_mtime)
            html = html.replace(f"/static/{asset}", f"/static/{asset}?v={version}")
    return HTMLResponse(
        html,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/favicon.ico")
def favicon():
    return {}

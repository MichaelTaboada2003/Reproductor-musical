"""
Endpoints de canciones y letras:
  - GET  /api/canciones            → listado con flags (letra/karaoke cache)
  - POST /api/descargar            → descarga vía yt-dlp (audio_downloader)
  - GET  /api/letra/{stem}         → obtener texto de la letra
  - POST /api/letra/{stem}         → guardar/actualizar letra
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from audio_downloader import is_url, resolve_audio_source
from lyrics_sync import sync_cache_is_current

from ..config import CANCIONES_DIR
from ..utils import (
    find_song, list_songs, lyrics_path_for, obtener_duracion,
    sync_cache_path_for,
)

router = APIRouter(tags=["songs"])


def _has_playable_sync(song) -> bool:
    lyrics_path = lyrics_path_for(song.stem)
    cache_path = sync_cache_path_for(song.stem)
    if not lyrics_path.is_file() or not cache_path.is_file():
        return False
    try:
        import json

        data = json.loads(cache_path.read_text(encoding="utf-8"))
        return bool(
            sync_cache_is_current(data, str(song), str(lyrics_path))
            and data.get("quality", {}).get("playable")
        )
    except (OSError, ValueError, TypeError):
        return False


@router.get("/api/canciones")
def api_canciones():
    canciones = []
    for p in list_songs():
        canciones.append({
            "nombre": p.name,
            "stem": p.stem,
            "duracion": obtener_duracion(p),
            "tiene_letra": lyrics_path_for(p.stem).is_file(),
            "tiene_sync": _has_playable_sync(p),
        })
    return {"canciones": canciones}


class DescargaRequest(BaseModel):
    url: str
    nombre: Optional[str] = None


@router.post("/api/descargar")
def api_descargar(payload: DescargaRequest):
    if not is_url(payload.url):
        raise HTTPException(400, "La fuente debe ser una URL válida (YouTube, etc.)")
    try:
        resultado = resolve_audio_source(
            payload.url, output_dir=str(CANCIONES_DIR),
            filename=payload.nombre or None,
        )
        return {"status": "ok", "archivo": resultado.name}
    except Exception as e:
        # Los errores del recurso (DRM, video privado, edad, etc.) son 422:
        # el servidor entendió la petición pero el recurso remoto no está
        # disponible. Reservamos 500 para fallos internos reales.
        msg = str(e).lower()
        if any(k in msg for k in ("drm", "sign in", "age", "confirm", "protegido")):
            raise HTTPException(422, str(e))
        raise HTTPException(500, str(e))


@router.get("/api/letra/{stem}")
def api_obtener_letra(stem: str):
    path = lyrics_path_for(stem)
    if not path.is_file():
        return {"existe": False, "texto": ""}
    return {"existe": True, "texto": path.read_text(encoding="utf-8")}


class LetraRequest(BaseModel):
    texto: str


@router.post("/api/letra/{stem}")
def api_guardar_letra(stem: str, payload: LetraRequest):
    find_song(stem)  # 404 si no existe la canción
    path = lyrics_path_for(stem)
    path.write_text(payload.texto.strip() + "\n", encoding="utf-8")
    # Una palabra editada basta para desplazar toda la alineación posterior.
    cache_path = sync_cache_path_for(stem)
    cache_invalidada = cache_path.is_file()
    if cache_invalidada:
        cache_path.unlink()
    return {"status": "ok", "cache_invalidada": cache_invalidada}

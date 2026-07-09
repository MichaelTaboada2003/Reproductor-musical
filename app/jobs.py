"""
app.jobs
============
Gestor simple de tareas largas en background (sincronización, generación
de video). Cada job vive en un dict en memoria protegido por un Lock. Es
suficiente mientras la app corre en un solo proceso; si se escala a
múltiples workers habría que mover esto a Redis o similar.

Uso:
    from app.jobs import start_job, router as jobs_router

    def tarea(progress_cb):
        progress_cb("Preparando", 0)
        ...
        return {"resultado": ...}

    job_id = start_job(tarea)
"""

import threading
import uuid

from fastapi import APIRouter, HTTPException

_jobs: dict = {}
_jobs_lock = threading.Lock()


def start_job(fn) -> str:
    """Lanza `fn(progress_cb)` en un hilo. `progress_cb(phase: str, pct: float | None)`
    permite a la tarea reportar en qué fase está y (si se conoce) qué porcentaje
    lleva. Cuando pct es None, el frontend muestra una barra indeterminada.
    """
    job_id = uuid.uuid4().hex
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "running", "result": None, "error": None,
            "progress": {"phase": "En cola", "pct": None},
        }

    def progress_cb(phase: str, pct=None):
        pct_val = None
        if pct is not None:
            try:
                pct_val = max(0, min(100, float(pct)))
            except (TypeError, ValueError):
                pct_val = None
        with _jobs_lock:
            j = _jobs.get(job_id)
            if j is not None:
                j["progress"] = {"phase": phase, "pct": pct_val}

    def target():
        try:
            result = fn(progress_cb)
            with _jobs_lock:
                _jobs[job_id]["status"] = "done"
                _jobs[job_id]["result"] = result
                _jobs[job_id]["progress"] = {"phase": "Listo", "pct": 100}
        except Exception as e:
            with _jobs_lock:
                _jobs[job_id]["status"] = "error"
                _jobs[job_id]["error"] = str(e)

    threading.Thread(target=target, daemon=True).start()
    return job_id


router = APIRouter(tags=["jobs"])


@router.get("/api/job/{job_id}")
def api_job_status(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job no encontrado")
    return job

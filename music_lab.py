"""
music_lab.py
================
Lanzador de Music Lab. Ya no es un menú de terminal: toda la funcionalidad
(descargar canciones, escribir letras, sincronizar karaoke, generar videos
y reproducir música) vive ahora en una interfaz web servida por app.py.

Este script simplemente levanta el servidor FastAPI y abre la interfaz
en tu navegador por comodidad.

Uso:
    python music_lab.py
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
URL = "http://127.0.0.1:8000"


def main():
    print("Iniciando Music Lab en", URL)
    print("Presiona Ctrl+C para detener el servidor.")

    proceso = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BASE_DIR),
    )

    # Dar un momento al servidor antes de abrir el navegador.
    time.sleep(1.5)
    webbrowser.open(URL)

    try:
        proceso.wait()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
        proceso.terminate()


if __name__ == "__main__":
    main()

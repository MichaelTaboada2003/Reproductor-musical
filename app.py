from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
import yt_dlp
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configura la lista de orígenes permitidos
origins = [
    "http://127.0.0.1:5500",  # Tu front-end (puerto 5500 o donde estés sirviendo el HTML)
    "http://localhost:5500",  # Por si usas localhost en vez de 127.0.0.1
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/canciones", StaticFiles(directory="canciones"), name="canciones")


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/descargar_audio_mp3")
def descargar_audio_mp3(
    url: str = Query(..., description="URL"),
    nombre_salida: str = Query("%(title)s", description="Plantilla para el nombre del archivo de salida")
):
    ruta_archivo_salida = os.path.join("canciones", nombre_salida + ".%(ext)s")
    ydl_opts = {
        'format': 'bestaudio/best',          # Mejor formato de audio disponible
        'outtmpl': ruta_archivo_salida,        # Plantilla para el nombre del archivo
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',         # Convertir a MP3
            'preferredquality': '192',       # Bitrate de 192 kbps
        }],
    }

    # Ejecuta la descarga
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        # Retornamos un mensaje de éxito (o podrías retornar más datos según necesites)
        return {"status": "ok", "message": "Descarga y conversión completa"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    
@app.get("/lista_canciones")
def lista_canciones():
    archivos_mp3 = []
    for nombre in os.listdir("canciones"):
        archivos_mp3.append(nombre)   
    return {"canciones": archivos_mp3}




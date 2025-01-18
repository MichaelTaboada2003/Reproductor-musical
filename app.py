from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
import yt_dlp
import os
import subprocess
import json
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from yt_dlp import YoutubeDL

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

ARTISTAS = {
    "A New Kind Of Love.webm": "Frou frou",
    "Abba - Lay All Your Love On Me.mp3": "ABBA",
    "Absofacto - Dissolve.mp3": "Absofacto",
    "Impacto.webm": "Enjambre",
    "did i tell u that i miss u": "adore",
    
}


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/descargar_playlist_mp3")
def descargar_playlist_mp3(
    url: str = Query(..., description="URL de la playlist"),
    nombre_plantilla: str = Query("%(title)s", description="Plantilla para los nombres de los archivos")
):
    directorio_actual = os.getcwd()
    carpeta_canciones = os.path.join(directorio_actual, "canciones")
    os.makedirs(carpeta_canciones, exist_ok=True)

    ydl_opts_playlist = {
        'quiet': True,
        'extract_flat': True,  # No descargar, solo obtener los datos de la playlist
    }

    try:
        # Extraer información de la playlist
        with YoutubeDL(ydl_opts_playlist) as ydl:
            playlist_info = ydl.extract_info(url, download=False)
        
        if 'entries' not in playlist_info:
            return {"status": "error", "message": "No se encontraron canciones en la playlist"}
        
        canciones = playlist_info['entries']
        resultados = []

        # Descargar cada canción de la playlist
        for idx, cancion in enumerate(canciones, start=1):
            cancion_url = cancion.get('url')
            if not cancion_url:
                resultados.append({"status": "error", "message": f"URL no válida para la canción {idx}"})
                continue
            
            nombre_archivo = f"{nombre_plantilla.replace('%(title)s', cancion.get('title', f'cancion_{idx}'))}.mp3"
            ruta_salida = os.path.join(carpeta_canciones, nombre_archivo)
            
            ydl_opts_cancion = {
                'format': 'bestaudio/best',
                'outtmpl': ruta_salida,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
            }

            try:
                with YoutubeDL(ydl_opts_cancion) as ydl:
                    ydl.download([cancion_url])
                
                resultados.append({
                    "status": "ok",
                    "message": "Descargado con éxito",
                    "titulo": cancion.get('title'),
                    "ruta_archivo": ruta_salida
                })

            except Exception as e:
                resultados.append({
                    "status": "error",
                    "message": str(e),
                    "titulo": cancion.get('title', f"Cancion_{idx}")
                })

        return {
            "status": "finalizado",
            "total_canciones": len(canciones),
            "resultados": resultados
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


    
    
def obtener_duracion(ruta_archivo):
    try:
        comando = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "json", 
            ruta_archivo
        ]
        resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if resultado.returncode == 0:
            info = json.loads(resultado.stdout)
            duracion_segundos = float(info['format']['duration'])
            minutos = int(duracion_segundos // 60)
            segundos = int(duracion_segundos % 60)
            return f"{minutos}:{str(segundos).zfill(2)}"
        else:
            return "Desconocida"
    except Exception as e:
        return "Desconocida"
    
    
@app.get("/descargar_playlist")
def descargar_playlist(
    url: str = Query(..., description="URL de la playlist"),
    nombre_salida: str = Query("%(title)s", description="Plantilla para el nombre del archivo de salida")
):
    directorio_actual = os.getcwd()
    carpeta_canciones = os.path.join(directorio_actual, "canciones")
    os.makedirs(carpeta_canciones, exist_ok=True)
    
    ruta_completa = os.path.join(carpeta_canciones, nombre_salida + ".%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': ruta_completa,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
        },
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,  # Necesario para playlists
        'ignoreerrors': True,   # Continuar si un video falla
        'nocheckcertificate': True,
        'allow_unplayable_formats': True,
        'playlist': True,       # Habilitar soporte de playlist
        'yes_playlist': True    # Confirmar que queremos toda la playlist
    }

    try:
        canciones_descargadas: List[Dict] = []
        errores: List[Dict] = []

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Primero obtener información de la playlist
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:  # Es una playlist
                total_videos = len(info['entries'])
                
                # Descargar cada video de la playlist
                for index, entry in enumerate(info['entries'], 1):
                    if entry:
                        try:
                            # Descargar video individual
                            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            video_info = ydl.extract_info(video_url, download=True)
                            
                            canciones_descargadas.append({
                                "titulo": video_info.get('title', 'Desconocido'),
                                "numero": index,
                                "total": total_videos
                            })
                        except Exception as e:
                            errores.append({
                                "titulo": entry.get('title', 'Desconocido'),
                                "error": str(e),
                                "numero": index
                            })
                
                return {
                    "status": "ok",
                    "message": f"Proceso completado. {len(canciones_descargadas)} canciones descargadas.",
                    "canciones_descargadas": canciones_descargadas,
                    "errores": errores,
                    "directorio": carpeta_canciones,
                    "total_videos": total_videos
                }
            else:  # No es una playlist
                return {
                    "status": "error",
                    "message": "La URL proporcionada no es una playlist válida"
                }
                
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "directorio_buscado": carpeta_canciones
        }

@app.get("/lista_canciones")
def lista_canciones():
    archivos_webm = []
    for nombre in os.listdir("canciones"):
        ruta_archivo = os.path.join("canciones", nombre)
        if os.path.isfile(ruta_archivo) and (nombre.endswith(".webm") or nombre.endswith(".mp3")):
            duracion = obtener_duracion(ruta_archivo)
            artista = ARTISTAS.get(nombre, "Desconocido")  # Obtener el artista del diccionario
            archivos_webm.append({"nombre": nombre, "duracion": duracion, "artista": artista})
    return {"canciones": archivos_webm}
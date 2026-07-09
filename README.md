# Music Lab

Music Lab es una aplicación full-stack (FastAPI + Vanilla JS) que permite descargar audio, sincronizar letras automáticamente con Inteligencia Artificial y generar videos interactivos. 

Cuenta con una interfaz de usuario hiper-premium basada en "Glassmorphism", un visualizador de espectro de audio mediante la API Web Audio de HTML5, y tecnología de renderizado de video en backend.

## 🚀 Características Principales

*   **🎧 Reproductor Inmersivo:** Reproductor web interactivo con "Ambient Mode" (fondo reactivo al sonido) y visualizador de forma de onda.
*   **⬇️ Descarga Automática:** Descarga audio directo desde enlaces de YouTube (y otros).
*   **🎤 Karaoke Sincronizado por IA:** Utiliza **Whisper** (OpenAI) para escuchar el audio de la canción y alinear matemáticamente cada palabra de la letra escrita, detectando el milisegundo exacto en que se canta.
*   **🎬 Generador de Videos (TikTok/Reels):** Exporta fragmentos seleccionados a un video vertical (MP4) con **Kinetic Typography** (texto que reacciona e ilumina con la canción) y un analizador de espectro renderizado con NumPy FFT y MoviePy.

## 🛠️ Tecnologías

### Frontend
*   **Vanilla JS, HTML5 y CSS3**
*   **Web Audio API:** Para el analizador de espectro y orbe reactivo.
*   **Glassmorphism UI:** Diseño limpio, difuminado (blur) y minimalista.

### Backend
*   **Python 3 & FastAPI:** API y servidor web rápido y moderno.
*   **Whisper Timestamped:** Para la detección de palabras y alineación de voz (STT).
*   **MoviePy, PIL & NumPy:** Manipulación de video, dibujo (draw) en frames, y Transformada Rápida de Fourier (FFT) para el espectro de audio.
*   **Demucs (Opcional):** Para separar instrumentales de voces puras y sincronizar mejor el karaoke.

## ⚙️ Uso / Instalación

1.  **Clona este repositorio** y navega al directorio del proyecto.
2.  **Instala las dependencias** recomendadas en tu entorno virtual (se requiere `fastapi`, `uvicorn`, `whisper-timestamped`, `moviepy`, `numpy`, `Pillow`, etc.). También se necesita instalar **ffmpeg**.
3.  **Inicia el servidor backend:**
    ```bash
    uvicorn app:app --reload
    ```
4.  **Abre tu navegador** en `http://127.0.0.1:8000` para disfrutar de la experiencia Music Lab.

## 📁 Estructura del Proyecto

*   `app.py`: Servidor principal FastAPI y gestor de tareas en background.
*   `static/`: Contiene todo el código frontend (UI, estilos, lógica de navegador).
*   `tiktok_generator.py`: Motor de video que dibuja frames reactivos con PIL y los une en MoviePy.
*   `lyrics_sync.py`: Lógica principal de Whisper para alineación de letras.
*   `audio_downloader.py`: Utilidad para obtener y convertir fuentes de internet.

# Tech

## Stack

- **Language**: Python 3 (backend), vanilla JavaScript / HTML / CSS (frontend).
- **Web framework**: FastAPI, served by Uvicorn.
- **Frontend**: plain static files (no framework, no build step). `fetch` calls
  the JSON API on the same origin.

## Key libraries

- **yt-dlp** + **ffmpeg** — download audio from URLs and convert to MP3.
- **whisper-timestamped** — transcribe audio with per-word timestamps (Whisper).
- **demucs** — isolate vocals before transcription (run via `python -m demucs`).
- **auditok / silero** — VAD (voice activity detection) options for Whisper.
- **moviepy** + **Pillow (PIL)** + **numpy** — render the vertical lyric video.
- **rich** — used by the legacy terminal lyric viewer (`lyrics.py`).
- **ffprobe** — read audio duration (shelled out from `app.py`).

External binaries **ffmpeg** and **ffprobe** must be installed on the system.

## Common commands

Always work inside the virtual environment:

```bash
source venv/bin/activate
```

Run the app (starts Uvicorn and opens the browser):

```bash
python music_lab.py
```

Run the server directly (dev, with reload):

```bash
uvicorn app:app --reload
```

The app runs at `http://127.0.0.1:8000`.

### CLI tools (each module also runs standalone)

```bash
python audio_downloader.py "https://youtube.com/watch?v=..." -o canciones
python lyrics_sync.py letra.txt -a cancion.mp3 -l es -m small
python vocal_separator.py cancion.mp3
python tiktok_generator.py cancion.mp3 letra.txt -o salida.mp4 --start 30 --end 60
python lyrics.py letra.txt --audio cancion.mp3   # terminal karaoke view
```

## Notes / gotchas

- No dependency manifest (requirements.txt) exists yet. Dependencies live in
  `venv`. If you add a dependency, install it into the venv.
- Heavy operations (Demucs separation, Whisper transcription) are **cached**:
  `vocals/*.vocals.wav` for isolated vocals, `letras/*.sync.json` for alignment.
  The sync cache is invalidated when the config signature (model, vad,
  separate_vocals) or the lyrics file's mtime changes.
- Long-running work (sync, video) runs in **background threads** in `app.py`,
  tracked as jobs and polled via `GET /api/job/{job_id}`.
- Lyric timestamps are always **absolute** to the full audio, so exporting a
  fragment keeps the words in sync.
- Whisper defaults: language `es`, model `small`. Whisper runs on CPU.

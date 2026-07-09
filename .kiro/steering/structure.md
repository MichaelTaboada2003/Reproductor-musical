# Structure

## Layout

```
music-lab/
├── app.py                 # FastAPI backend: the JSON API + serves the web UI
├── music_lab.py           # Launcher: starts Uvicorn and opens the browser
├── audio_downloader.py    # Download audio from URLs (yt-dlp) -> MP3
├── lyrics_sync.py         # Core: align lyrics (.txt) to audio via Whisper
├── vocal_separator.py     # Isolate vocals with Demucs (cached)
├── tiktok_generator.py    # Render the vertical "terminal-style" lyric video
├── lyrics.py              # Legacy terminal karaoke viewer (rich)
├── static/                # Frontend (no build step)
│   ├── index.html         # Single-page UI with 5 views (sidebar navigation)
│   ├── app.js             # All UI logic + API calls
│   └── style.css
├── canciones/             # Downloaded MP3s (gitignored)
├── letras/                # <song>.txt lyrics + <song>.sync.json sync cache
├── vocals/                # <song>.vocals.wav isolated vocals cache (gitignored)
└── videos/                # Generated MP4s (gitignored)
```

## Architecture

- `app.py` is the single entry point for the running app. It exposes the API
  under `/api/*`, mounts static dirs (`/canciones`, `/videos`, `/static`), and
  serves `index.html` at `/`.
- The pipeline modules are designed to be usable **both** as libraries (imported
  by `app.py`) and as standalone CLI scripts (each has an `argparse` block).
- `lyrics_sync.align_lyrics_to_audio(...)` is the heart of the system: both the
  karaoke view and the video renderer consume its output so they always show the
  same thing at the same instant.

## Key conventions

- Songs are identified by their **stem** (filename without extension). A song,
  its lyrics, and its sync cache share the same stem:
  `canciones/<stem>.mp3`, `letras/<stem>.txt`, `letras/<stem>.sync.json`.
- Lyrics files: blank lines separate **stanzas**; each non-empty line is a line.
- The sync data structure is `{"stanzas": [[{text, start, end, words:[...]}]]}`.
  A `words` entry has `{text, start, end, synced}` where `synced` marks whether
  Whisper actually matched the word (reliable) vs. it was interpolated.
- Paths are resolved relative to each file's own directory (`BASE_DIR`), and
  audio paths are made absolute before processing, since Demucs may change the
  working directory.
- Frontend `app.js` is organized by view (Reproductor, Descargar, Letras,
  Karaoke, Video) with clear section banners; keep that structure when editing.

## Adding features

- New API endpoints go in `app.py`; keep long tasks in background jobs.
- New processing logic belongs in a focused module (like the existing ones),
  exposed as an importable function and, ideally, a CLI entry point.
- Frontend changes are edited directly in `static/` (no bundler).

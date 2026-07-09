# Product

Music Lab is a local web application for turning songs into synced-lyrics
("karaoke") experiences and vertical, TikTok/Reels-style lyric videos.

## Core features

- **Download**: fetch audio from a URL (YouTube and similar) and store it as MP3.
- **Lyrics**: view, write, and save the real lyrics of a song as plain text.
- **Karaoke sync**: align the saved lyrics to the audio using Whisper, so words
  light up in time with the music. Vocal isolation (Demucs) and voice activity
  detection (VAD) are used to get near-perfect timing and avoid the lyrics
  drifting over instrumental sections.
- **TikTok video**: render a vertical MP4 that mimics the terminal karaoke look
  (dark "terminal window", monospaced cyan text revealed word by word). Any
  segment (e.g. just the chorus) can be exported while keeping perfect sync.
- **Player**: browse and play the downloaded songs.

## How it runs

It is a single-user, run-it-on-your-own-machine tool. The user launches it
locally, a browser opens the interface, and all processing (download, vocal
separation, transcription, video render) happens on the local machine.

## Usage note

The tool is intended for audio the user has the rights to use. Downloading and
republishing copyrighted music without permission is the user's responsibility,
not the tool's.

## Conventions

- The interface and all user-facing text, comments, and docstrings are in
  **Spanish**. Keep new user-facing strings and code comments in Spanish to
  match the existing style.

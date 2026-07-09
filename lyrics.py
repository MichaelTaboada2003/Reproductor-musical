import time
import sys
import argparse
import subprocess
import shutil
from pathlib import Path

try:
    from rich.console import Console
    from rich.text import Text
    from rich.align import Align
    from rich.live import Live
    from rich.layout import Layout
    from rich.console import Group
except ImportError:
    print("Error: Por favor, instala la librería 'rich' para usar este script.")
    print("Activa el entorno virtual usando: source venv/bin/activate")
    sys.exit(1)

from lyrics_sync import align_lyrics_to_audio
from audio_downloader import resolve_audio_source

console = Console()


def _play_audio_background(audio_path: str):
    """Lanza la reproducción de audio en segundo plano (macOS: afplay)."""
    if not audio_path:
        return None
    if shutil.which("afplay") is None:
        console.print("[yellow]Aviso: 'afplay' no está disponible, se mostrará la letra sin sonido.[/]")
        return None
    return subprocess.Popen(
        ["afplay", audio_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _build_header(title, artist):
    panel_title = f"[bold yellow]🎵 {title}[/]" if title else "[bold yellow]🎵 Letra de la Canción[/]"
    panel_subtitle = f"[italic green]por {artist}[/]" if artist else ""
    return Group(
        Align.center(Text.from_markup(panel_title)),
        Align.center(Text.from_markup(panel_subtitle)) if artist else Text(""),
    )


def display_lyrics_synced(file_path: str, audio_path: str, title=None, artist=None,
                           language="es", model="base", force_sync=False):
    """
    Muestra la letra sincronizada con el tiempo REAL del audio.
    Usa lyrics_sync.align_lyrics_to_audio para obtener start/end por línea,
    y reproduce el audio en paralelo con afplay para que texto y sonido coincidan.
    """
    resolved_audio = resolve_audio_source(audio_path, output_dir=Path(file_path).parent)
    data = align_lyrics_to_audio(
        str(resolved_audio), file_path, language=language, model_name=model, force=force_sync
    )

    layout = Layout()
    layout.split(Layout(name="header", size=3), Layout(name="body"))
    layout["header"].update(_build_header(title, artist))

    player = _play_audio_background(str(resolved_audio))
    start_time = time.monotonic()

    try:
        with Live(console=console, refresh_per_second=30) as live:
            for stanza in data["stanzas"]:
                if not stanza:
                    continue
                max_len = max(len(l["text"]) for l in stanza)
                total_height = len(stanza) * 2 - 1

                stanza_start = stanza[0]["start"]
                # Esperar hasta que el audio llegue al inicio de la estrofa
                _wait_until(start_time, stanza_start)

                revealed = Text(justify="left")
                for i, line in enumerate(stanza):
                    if i > 0:
                        revealed.append("\n\n")
                    left_padding = " " * ((max_len - len(line["text"])) // 2)
                    revealed.append(left_padding)

                    words = line["words"] or [{"text": line["text"], "start": line["start"], "end": line["end"]}]
                    for w in words:
                        _wait_until(start_time, w["start"])
                        revealed.append(w["text"] + " ", style="bold cyan")
                        fixed_block = Align.center(revealed, vertical="middle", width=max_len, height=total_height)
                        layout["body"].update(Align.center(fixed_block))
                        live.update(layout)

                stanza_end = stanza[-1]["end"]
                _wait_until(start_time, stanza_end + 0.6)
    finally:
        if player and player.poll() is None:
            player.wait()


def _wait_until(start_time: float, target_seconds: float):
    now = time.monotonic() - start_time
    remaining = target_seconds - now
    if remaining > 0:
        time.sleep(remaining)


def display_lyrics_delay(file_path: str, title: str = None, artist: str = None, delay: float = 3.5):
    """Modo antiguo (sin audio): revela la letra con un delay fijo por línea."""
    path = Path(file_path)
    if not path.is_file():
        console.print(f"[red]Error: El archivo '{file_path}' no existe.[/red]")
        return

    with open(path, 'r', encoding='utf-8') as f:
        lyrics = f.read()

    if delay > 0:
        lines = lyrics.split('\n')

        layout = Layout()
        layout.split(Layout(name="header", size=3), Layout(name="body"))
        layout["header"].update(_build_header(title, artist))

        with Live(console=console, refresh_per_second=60) as live:
            stanzas = []
            current_stanza_lines = []
            for line in lines:
                line = line.strip()
                if line == "":
                    if current_stanza_lines:
                        stanzas.append(current_stanza_lines)
                        current_stanza_lines = []
                else:
                    current_stanza_lines.append(line)
            if current_stanza_lines:
                stanzas.append(current_stanza_lines)

            for stanza_lines in stanzas:
                if not stanza_lines:
                    continue

                max_len = max(len(l) for l in stanza_lines)
                total_height = len(stanza_lines) * 2 - 1

                current_stanza = Text(justify="left")

                for i, line in enumerate(stanza_lines):
                    if i > 0:
                        current_stanza.append("\n\n")

                    style = "bold cyan"
                    left_padding = " " * ((max_len - len(line)) // 2)
                    current_stanza.append(left_padding)

                    char_delay = (delay * 0.8) / len(line) if len(line) > 0 else 0
                    for char in line:
                        current_stanza.append(char, style=style)
                        fixed_block = Align.center(current_stanza, vertical="middle", width=max_len, height=total_height)
                        layout["body"].update(Align.center(fixed_block))
                        live.update(layout)
                        time.sleep(char_delay)

                    time.sleep(delay * 0.6)

                time.sleep(delay * 0.8)

            time.sleep(delay * 2)
    else:
        text = Text(justify="center")
        for line in lyrics.split('\n'):
            text.append(line.strip(), style="cyan")
            text.append("\n")

        console.print(Align.center(Text.from_markup(f"[bold yellow]🎵 {title or 'Letra de la Canción'}[/]")))
        if artist:
            console.print(Align.center(Text.from_markup(f"[italic green]por {artist}[/]")))
        console.print()
        console.print(Align.center(text))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Muestra letras de canciones de forma estética en la consola.")
    parser.add_argument("archivo", help="Ruta al archivo de texto con la letra de la canción.")
    parser.add_argument("-t", "--titulo", help="Título de la canción.", default="")
    parser.add_argument("-a", "--artista", help="Artista de la canción.", default="")
    parser.add_argument("--audio", help="Ruta local o URL (YouTube, etc.) del audio para sincronizar la letra con el tiempo real (recomendado).", default=None)
    parser.add_argument("-l", "--language", help="Idioma de la canción (para la transcripción con --audio).", default="es")
    parser.add_argument("-m", "--model", help="Modelo Whisper a usar (tiny, base, small...).", default="base")
    parser.add_argument("--force-sync", action="store_true", help="Fuerza re-transcripción aunque exista cache de sincronización.")
    parser.add_argument("-d", "--delay", type=float,
                         help="Retraso base por línea en segundos (solo se usa si NO se pasa --audio).",
                         default=3.5)

    args = parser.parse_args()

    if args.audio:
        display_lyrics_synced(
            args.archivo, args.audio, title=args.titulo, artist=args.artista,
            language=args.language, model=args.model, force_sync=args.force_sync,
        )
    else:
        display_lyrics_delay(args.archivo, args.titulo, args.artista, args.delay)

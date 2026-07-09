"""
vocal_separator.py
=====================
Aísla la pista de voz de una canción usando Demucs. Transcribir solo la voz
(en vez de la mezcla completa) reduce drásticamente las "alucinaciones" de
Whisper sobre secciones instrumentales y mejora mucho la precisión de los
tiempos, que es la clave para una sincronía casi perfecta del karaoke.

El resultado se cachea en vocals/<nombre>.vocals.wav para no volver a
separar la misma canción (Demucs es costoso en CPU).

Uso como librería:
    from vocal_separator import separate_vocals
    vocals_path = separate_vocals("canciones/cancion.mp3")
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VOCALS_DIR = BASE_DIR / "vocals"

DEFAULT_MODEL = "htdemucs"


def _cached_vocals_path(audio_path: Path) -> Path:
    return VOCALS_DIR / f"{audio_path.stem}.vocals.wav"


def separate_vocals(audio_path: str, model: str = DEFAULT_MODEL, force: bool = False) -> Path:
    """
    Separa la voz de `audio_path` y devuelve la ruta al .wav con solo la voz.
    Usa cache: si ya existe una separación más nueva que el audio original,
    la reutiliza.
    """
    audio_path = Path(audio_path)
    if not audio_path.is_file():
        raise FileNotFoundError(f"No existe el audio: {audio_path}")

    VOCALS_DIR.mkdir(parents=True, exist_ok=True)
    cached = _cached_vocals_path(audio_path)

    if cached.is_file() and not force:
        if cached.stat().st_mtime >= audio_path.stat().st_mtime:
            print(f"Usando voz aislada cacheada: {cached}")
            return cached

    print(f"Separando la voz con Demucs ('{model}'), esto puede tardar un poco...")
    with tempfile.TemporaryDirectory() as tmpdir:
        # --two-stems=vocals genera vocals.wav (voz) y no_vocals.wav (pista).
        cmd = [
            sys.executable, "-m", "demucs",
            "--two-stems=vocals",
            "-n", model,
            "-o", tmpdir,
            str(audio_path),
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                "Demucs falló al separar la voz.\n" + (result.stdout or "")[-1500:]
            )

        produced = Path(tmpdir) / model / audio_path.stem / "vocals.wav"
        if not produced.is_file():
            # Buscar por si el nombre de la subcarpeta difiere
            matches = list(Path(tmpdir).glob(f"{model}/*/vocals.wav"))
            if not matches:
                raise RuntimeError("Demucs terminó pero no se encontró el archivo de voz.")
            produced = matches[0]

        shutil.move(str(produced), str(cached))

    print(f"Voz aislada guardada en: {cached}")
    return cached


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aísla la voz de una canción con Demucs.")
    parser.add_argument("audio", help="Ruta al audio (mp3, wav, etc.)")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help="Modelo Demucs (htdemucs, htdemucs_ft, mdx_extra...)")
    parser.add_argument("--force", action="store_true", help="Fuerza re-separación aunque exista cache.")
    args = parser.parse_args()

    path = separate_vocals(args.audio, model=args.model, force=args.force)
    print(path)

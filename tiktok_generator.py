"""
tiktok_generator.py
=======================
Genera un video vertical (estilo TikTok/Reels) usando un diseño
premium con Glassmorphism, Kinetic Typography y un visualizador de 
espectro de audio real usando NumPy FFT.
"""

import argparse
from pathlib import Path
import numpy as np

from moviepy import VideoClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from lyrics_sync import align_lyrics_to_audio
from audio_downloader import resolve_audio_source

VIDEO_SIZE = (1080, 1920)
MARGIN_X = 80

# Colores Premium
COLOR_BG_TOP = (15, 20, 30)
COLOR_BG_BOTTOM = (5, 5, 10)
COLOR_TEXT_PRIMARY = (255, 255, 255)
COLOR_TEXT_SECONDARY = (150, 160, 170)
COLOR_ACCENT = (30, 215, 96) # Spotify green
COLOR_ACCENT_GLOW = (50, 255, 120)

_FONT_MONO_BOLD = ["Inter-Bold", "Arial-BoldMT", "Helvetica-Bold", "Menlo-Bold", "DejaVuSans-Bold"]
_FONT_MONO = ["Inter-Regular", "ArialMT", "Helvetica", "Menlo-Regular", "DejaVuSans"]

_FONT_CACHE = {}

def _load_font(candidates, size):
    key = (tuple(candidates), size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    font = None
    for name in candidates:
        try:
            font = ImageFont.truetype(name, size)
            break
        except IOError:
            continue
    if font is None:
        font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font

def _text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

def _fit_lyric_font(draw, stanza, max_width):
    longest = max((line["text"] for line in stanza), key=len, default="")
    for size in range(80, 30, -2):
        font = _load_font(_FONT_MONO_BOLD, size)
        if _text_width(draw, longest, font) <= max_width:
            return font, size
    return _load_font(_FONT_MONO_BOLD, 30), 30

def _active_stanza(stanzas, current_time):
    active = None
    for stanza in stanzas:
        if not stanza: continue
        if stanza[0]["start"] <= current_time + 0.2: # slight lookahead
            active = stanza
        else:
            break
    return active

def create_background():
    img = Image.new("RGB", VIDEO_SIZE)
    draw = ImageDraw.Draw(img)
    # Simple gradient
    for y in range(VIDEO_SIZE[1]):
        r = int(COLOR_BG_TOP[0] + (COLOR_BG_BOTTOM[0] - COLOR_BG_TOP[0]) * y / VIDEO_SIZE[1])
        g = int(COLOR_BG_TOP[1] + (COLOR_BG_BOTTOM[1] - COLOR_BG_TOP[1]) * y / VIDEO_SIZE[1])
        b = int(COLOR_BG_TOP[2] + (COLOR_BG_BOTTOM[2] - COLOR_BG_TOP[2]) * y / VIDEO_SIZE[1])
        draw.line([(0, y), (VIDEO_SIZE[0], y)], fill=(r, g, b))
    
    # Draw some abstract soft blobs
    draw.ellipse([-200, -200, 600, 600], fill=(30, 80, 100))
    draw.ellipse([500, 1200, 1400, 2100], fill=(10, 50, 40))
    return img.filter(ImageFilter.GaussianBlur(150))

def make_karaoke_frame(bg_img, stanzas, current_time, fonts, spectrum_bands, title=None, artist=None):
    width, height = VIDEO_SIZE
    # We use RGBA for drawing translucent elements
    overlay = Image.new("RGBA", VIDEO_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Draw Spectrum Visualizer at bottom
    num_bands = len(spectrum_bands)
    band_width = (width - 100) / num_bands
    max_band_h = 300
    for i, val in enumerate(spectrum_bands):
        h = min(val * max_band_h * 5, max_band_h) # scale intensity
        x1 = 50 + i * band_width
        y1 = height - 50 - h
        x2 = x1 + band_width * 0.8
        y2 = height - 50
        # Gradient color based on intensity and index
        color = (30 + int(200 * (i/num_bands)), 215, 96, 180)
        draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill=color)

    # 2. Draw Header
    y_header = 150
    if title:
        font_title = fonts["title"]
        w = _text_width(draw, title, font_title)
        draw.text(((width - w) / 2, y_header), title, font=font_title, fill=COLOR_TEXT_PRIMARY)
        y_header += font_title.size + 20
    if artist:
        font_artist = fonts["artist"]
        w = _text_width(draw, artist, font_artist)
        draw.text(((width - w) / 2, y_header), artist, font=font_artist, fill=COLOR_ACCENT)

    # 3. Draw Lyrics with Glassmorphism Card
    stanza = _active_stanza(stanzas, current_time)
    if stanza:
        font_lyric, lyric_size = _fit_lyric_font(draw, stanza, width - 2 * MARGIN_X)
        line_height = int(lyric_size * 1.5)
        block_height = len(stanza) * line_height
        y_cursor = (height - block_height) / 2

        # Draw Glass Card
        card_pad = 60
        card_box = [MARGIN_X - card_pad, y_cursor - card_pad, width - MARGIN_X + card_pad, y_cursor + block_height + card_pad]
        draw.rounded_rectangle(card_box, radius=30, fill=(20, 20, 20, 160), outline=(255, 255, 255, 30), width=2)

        space_w = _text_width(draw, " ", font_lyric)

        for line in stanza:
            full_text = line["text"]
            full_width = _text_width(draw, full_text, font_lyric)
            x = (width - full_width) / 2

            words = line["words"] or [{"text": full_text, "start": line["start"], "end": line["end"]}]
            for word in words:
                wtext = word["text"]
                w_width = _text_width(draw, wtext, font_lyric)
                
                # Kinetic Typography Logic
                is_past = current_time > word["end"]
                is_current = word["start"] <= current_time <= word["end"]
                
                if is_current:
                    # Current word: Bright white, slightly scaled (simulated by bold/glow)
                    draw.text((x, y_cursor), wtext, font=font_lyric, fill=(255, 255, 255, 255))
                elif is_past:
                    # Past word: dimmer
                    draw.text((x, y_cursor), wtext, font=font_lyric, fill=(255, 255, 255, 120))
                else:
                    # Future word: much dimmer
                    draw.text((x, y_cursor), wtext, font=font_lyric, fill=(255, 255, 255, 40))

                x += w_width + space_w
            y_cursor += line_height

    # Composite
    final_img = bg_img.copy()
    final_img.paste(overlay, (0, 0), overlay)
    return np.array(final_img)

def _build_fonts():
    return {
        "title": _load_font(_FONT_MONO_BOLD, 60),
        "artist": _load_font(_FONT_MONO, 40),
    }

def create_tiktok_video(audio_source, lyrics_path, output_path, language="es",
                         model="small", force_sync=False, start_time=None,
                         end_time=None, title=None, artist=None,
                         vad="auditok", separate_vocals=True):
    audio_path = resolve_audio_source(audio_source, output_dir=Path(lyrics_path).parent)
    data = align_lyrics_to_audio(
        str(audio_path), lyrics_path, language=language, model_name=model, force=force_sync,
        vad=vad, separate_vocals=separate_vocals,
    )
    stanzas = data["stanzas"]
    fonts = _build_fonts()
    bg_img = create_background()

    audio_clip = AudioFileClip(str(audio_path))
    full_duration = audio_clip.duration

    frag_start = max(0.0, start_time) if start_time is not None else 0.0
    frag_end = min(full_duration, end_time) if end_time is not None else full_duration
    if frag_end <= frag_start:
        raise ValueError("El fragmento seleccionado no es válido: el fin debe ser mayor que el inicio.")

    trimmed_audio = audio_clip.subclipped(frag_start, frag_end)
    duration = frag_end - frag_start

    print(f"Pre-procesando audio para el visualizador FFT...")
    # Extract audio array for FFT (mono)
    audio_array = trimmed_audio.to_soundarray(fps=22050)
    if audio_array.ndim == 2:
        audio_array = audio_array.mean(axis=1)

    def get_spectrum(t):
        idx = int((t - frag_start) * 22050)
        window_size = 1024
        window = audio_array[max(0, idx - window_size) : idx + window_size]
        if len(window) == 0:
            return np.zeros(32)
        window = window * np.hamming(len(window))
        fft = np.abs(np.fft.rfft(window))
        # downsample to 32 bands
        bands = np.array_split(fft, 32)
        return np.array([np.mean(b) for b in bands])

    print(f"Generando video premium ({frag_start:.1f}s - {frag_end:.1f}s de {full_duration:.1f}s totales)...")

    def make_frame(t):
        spectrum = get_spectrum(t + frag_start)
        return make_karaoke_frame(bg_img, stanzas, t + frag_start, fonts, spectrum, title=title, artist=artist)

    video_clip = VideoClip(make_frame, duration=duration)
    video_clip = video_clip.with_audio(trimmed_audio)

    print(f"Exportando {output_path}...")
    video_clip.write_videofile(str(output_path), fps=24, codec="libx264", audio_codec="aac")
    print("¡Video generado exitosamente!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador automático de TikToks Premium (Glassmorphism & FFT)")
    parser.add_argument("audio", help="Ruta local o URL (YouTube, etc.) del audio (mp3, wav)")
    parser.add_argument("letra", help="Ruta al archivo .txt con la letra real de la canción")
    parser.add_argument("-o", "--output", help="Ruta de salida del video mp4", default="tiktok_output.mp4")
    parser.add_argument("-l", "--language", help="Idioma (ej. en, es)", default="es")
    parser.add_argument("-m", "--model", help="Modelo Whisper a usar (tiny, base, small, medium...)", default="small")
    parser.add_argument("--force-sync", action="store_true", help="Fuerza re-transcripción aunque exista cache")
    parser.add_argument("--start", type=float, default=None, help="Segundo de inicio del fragmento a exportar")
    parser.add_argument("--end", type=float, default=None, help="Segundo de fin del fragmento a exportar")
    parser.add_argument("-t", "--titulo", default=None, help="Título a mostrar en el video")
    parser.add_argument("-a", "--artista", default=None, help="Artista a mostrar en el video")
    parser.add_argument("--vad", default="auditok", help="VAD: auditok, silero, o 'none' para desactivar.")
    parser.add_argument("--no-separacion", action="store_true", help="No aislar la voz con Demucs.")

    args = parser.parse_args()
    vad_arg = None if str(args.vad).lower() in ("none", "no", "off", "") else args.vad
    create_tiktok_video(
        args.audio, args.letra, args.output,
        language=args.language, model=args.model, force_sync=args.force_sync,
        start_time=args.start, end_time=args.end, title=args.titulo, artist=args.artista,
        vad=vad_arg, separate_vocals=not args.no_separacion,
    )

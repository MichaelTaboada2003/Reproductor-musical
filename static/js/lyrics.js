// ============================================================
// lyrics.js — vista "Letras": ver y editar la letra de una canción
// ============================================================

import { apiGet, apiPost, setStatus, refreshSongSelect } from "./api.js";

export const lyricsSongSelect = document.getElementById("lyricsSongSelect");
const lyricsTextarea = document.getElementById("lyricsTextarea");
const lyricsSaveBtn = document.getElementById("lyricsSaveBtn");
const lyricsStatus = document.getElementById("lyricsStatus");

export async function onLyricsSongChange() {
  const stem = lyricsSongSelect.value;
  if (!stem) return;
  try {
    const data = await apiGet(`/api/letra/${encodeURIComponent(stem)}`);
    lyricsTextarea.value = data.texto || "";
    setStatus(
      lyricsStatus,
      data.existe
        ? "Letra cargada."
        : "Esta canción todavía no tiene letra guardada."
    );
  } catch (e) {
    setStatus(lyricsStatus, `Error: ${e.message}`, "error");
  }
}

lyricsSongSelect.addEventListener("change", onLyricsSongChange);

lyricsSaveBtn.addEventListener("click", async () => {
  const stem = lyricsSongSelect.value;
  if (!stem) return;
  lyricsSaveBtn.disabled = true;
  try {
    await apiPost(`/api/letra/${encodeURIComponent(stem)}`, {
      texto: lyricsTextarea.value,
    });
    setStatus(lyricsStatus, "Letra guardada.", "ok");
    // Refrescar el select del estudio para que aparezca la marca · letra
    const { studioSongSelect } = await import("./studio.js");
    refreshSongSelect(studioSongSelect);
  } catch (e) {
    setStatus(lyricsStatus, `Error: ${e.message}`, "error");
  } finally {
    lyricsSaveBtn.disabled = false;
  }
});

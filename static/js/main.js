// ============================================================
// main.js — punto de entrada de la SPA. Importa todos los
//           módulos (los event listeners se registran al
//           importar cada módulo) y dispara el arranque.
// ============================================================

// 1. Inicializar el motor de karaoke con los nodos del DOM del reproductor.
//    Debe ir antes de que player.js registre sus listeners de audioPlayer.
import { init as initKaraoke } from "./karaoke.js";
import { audioPlayer } from "./player.js";

const karaokeStage = document.getElementById("karaokeStage");
const karaokeText = document.getElementById("karaokeText");
initKaraoke(audioPlayer, karaokeStage, karaokeText);

// 2. Módulos con efectos laterales (registran listeners al importar).
import "./player.js";
import "./lyrics.js";
import "./studio.js";
import "./discover.js";
import "./visualizer.js";

// 3. Descarga la lista de canciones inicial y renderiza la playlist.
import { cargarListaCanciones } from "./player.js";
cargarListaCanciones();

// 4. Activar la vista indicada por el hash (ej. /#view-spotify tras OAuth).
//    Se carga al final para que todos los módulos ya estén registrados.
import { activateFromHash } from "./nav.js";
activateFromHash();

// 5. Download form (no encaja en ningún módulo propio por su bajo volumen).
import { apiPost, setStatus } from "./api.js";

const downloadForm = document.getElementById("downloadForm");
const downloadStatus = document.getElementById("downloadStatus");
const downloadSubmit = document.getElementById("downloadSubmit");

downloadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = document.getElementById("downloadUrl").value.trim();
  const nombre = document.getElementById("downloadName").value.trim();
  if (!url) return;
  downloadSubmit.disabled = true;
  setStatus(downloadStatus, "Descargando... esto puede tardar un momento.");
  try {
    const data = await apiPost("/api/descargar", { url, nombre: nombre || null });
    setStatus(downloadStatus, `Descargado con éxito: ${data.archivo}`, "ok");
    downloadForm.reset();
    cargarListaCanciones();
  } catch (e) {
    setStatus(downloadStatus, `Error: ${e.message}`, "error");
  } finally {
    downloadSubmit.disabled = false;
  }
});

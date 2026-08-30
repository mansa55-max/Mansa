const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchResults = document.getElementById("search-results");
const uploadForm = document.getElementById("upload-form");
const videoInput = document.getElementById("video-input");
const uploadStatus = document.getElementById("upload-status");
const movieList = document.getElementById("movie-list");
const storyForm = document.getElementById("story-form");
const storyTitleInput = document.getElementById("story-title");
const storyTextInput = document.getElementById("story-text");
const storyImagesInput = document.getElementById("story-images");
const storyStatus = document.getElementById("story-status");
const storyList = document.getElementById("story-list");
const modal = document.getElementById("modal");
const modalBody = document.getElementById("modal-body");
const modalClose = document.getElementById("modal-close");

const STATUS_LABELS = {
  pending: "En attente...",
  extracting_audio: "Extraction de l'audio...",
  transcribing: "Transcription en cours...",
  summarizing: "Génération du résumé...",
  done: "Terminé",
  error: "Erreur",
};

const RECAP_STATUS_LABELS = {
  none: "",
  pending: "En attente...",
  narrating: "Génération de la narration audio...",
  assembling: "Montage de la vidéo...",
  done: "Terminé",
  error: "Erreur",
};

const STORY_STATUS_LABELS = {
  pending: "En attente...",
  narrating: "Génération de la narration audio...",
  assembling: "Montage de la vidéo...",
  done: "Terminé",
  error: "Erreur",
};

let pollTimer = null;
let openMovieId = null;
let openStoryId = null;

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = searchInput.value.trim();
  if (!query) return;
  searchResults.innerHTML = "<p class='hint'>Recherche...</p>";
  try {
    const results = await api(`/api/search?q=${encodeURIComponent(query)}`);
    if (!results.length) {
      searchResults.innerHTML = "<p class='empty'>Aucun résultat.</p>";
      return;
    }
    searchResults.innerHTML = "";
    for (const movie of results) {
      const div = document.createElement("div");
      div.className = "result-item";
      div.innerHTML = `
        ${movie.poster_url ? `<img src="${movie.poster_url}" alt="">` : ""}
        <div class="meta">
          <strong>${escapeHtml(movie.title)}</strong>
          <span>${movie.year || ""}</span>
        </div>
        <button type="button">Importer</button>
      `;
      div.querySelector("button").addEventListener("click", () => importFromSearch(movie.tmdb_id, div));
      searchResults.appendChild(div);
    }
  } catch (err) {
    searchResults.innerHTML = `<p class="error-message">${escapeHtml(err.message)}</p>`;
  }
});

async function importFromSearch(tmdbId, container) {
  const button = container.querySelector("button");
  button.disabled = true;
  button.textContent = "Import...";
  try {
    await api("/api/movies/import-from-search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tmdb_id: tmdbId }),
    });
    button.textContent = "Importé ✓";
    refreshAll();
  } catch (err) {
    button.disabled = false;
    button.textContent = "Réessayer";
    alert("Erreur d'import : " + err.message);
  }
}

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = videoInput.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append("file", file);
  uploadStatus.innerHTML = "<p class='hint'>Envoi du fichier...</p>";
  try {
    await api("/api/import/video", { method: "POST", body: formData });
    uploadStatus.innerHTML = "<p class='hint'>Import lancé, suis la progression ci-dessous.</p>";
    uploadForm.reset();
    refreshAll();
  } catch (err) {
    uploadStatus.innerHTML = `<p class="error-message">${escapeHtml(err.message)}</p>`;
  }
});

storyForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const files = storyImagesInput.files;
  if (!files.length) return;
  const formats = Array.from(document.querySelectorAll(".story-format:checked")).map((el) => el.value);
  if (!formats.length) {
    alert("Choisis au moins un format.");
    return;
  }
  const formData = new FormData();
  formData.append("title", storyTitleInput.value.trim() || "Histoire sans titre");
  formData.append("story", storyTextInput.value.trim());
  formData.append("formats", formats.join(","));
  for (const file of files) {
    formData.append("images", file);
  }
  storyStatus.innerHTML = "<p class='hint'>Envoi des images...</p>";
  try {
    await api("/api/story-videos", { method: "POST", body: formData });
    storyStatus.innerHTML = "<p class='hint'>Génération lancée, suis la progression ci-dessous.</p>";
    storyForm.reset();
    refreshAll();
  } catch (err) {
    storyStatus.innerHTML = `<p class="error-message">${escapeHtml(err.message)}</p>`;
  }
});

async function loadMovies() {
  try {
    const movies = await api("/api/movies");
    renderMovies(movies);
    if (openMovieId && movies.some((m) => m.id === openMovieId)) {
      await openMovie(openMovieId);
    }
    return movies.some(
      (m) => !["done", "error"].includes(m.job_status) || !["none", "done", "error"].includes(m.recap_status)
    );
  } catch (err) {
    movieList.innerHTML = `<p class="error-message">${escapeHtml(err.message)}</p>`;
    return false;
  }
}

async function loadStoryVideos() {
  try {
    const stories = await api("/api/story-videos");
    renderStoryVideos(stories);
    if (openStoryId && stories.some((s) => s.id === openStoryId)) {
      await openStory(openStoryId);
    }
    return stories.some((s) => !["done", "error"].includes(s.status));
  } catch (err) {
    storyList.innerHTML = `<p class="error-message">${escapeHtml(err.message)}</p>`;
    return false;
  }
}

async function refreshAll() {
  const [moviesWorking, storiesWorking] = await Promise.all([loadMovies(), loadStoryVideos()]);
  if (moviesWorking || storiesWorking) {
    ensurePolling();
  } else {
    stopPolling();
  }
}

function renderMovies(movies) {
  if (!movies.length) {
    movieList.innerHTML = "<p class='empty'>Aucun film importé pour le moment.</p>";
    return;
  }
  movieList.innerHTML = "";
  for (const movie of movies) {
    const card = document.createElement("div");
    card.className = "movie-card";
    const statusLabel = STATUS_LABELS[movie.job_status] || movie.job_status;
    const statusClass = movie.job_status === "error" ? "error" : movie.job_status === "done" ? "done" : "";
    const recapBadge = movie.recap_status === "done" ? '<span title="Vidéo résumé disponible">🎬</span>' : "";
    card.innerHTML = `
      ${movie.poster_url ? `<img src="${movie.poster_url}" alt="">` : `<div class="placeholder">🎞️</div>`}
      <div class="card-body">
        <h3>${escapeHtml(movie.title)} ${recapBadge}</h3>
        <div class="status ${statusClass}">${statusLabel}</div>
      </div>
    `;
    card.addEventListener("click", () => openMovie(movie.id));
    movieList.appendChild(card);
  }
}

function renderStoryVideos(stories) {
  if (!stories.length) {
    storyList.innerHTML = "<p class='empty'>Aucune vidéo générée pour le moment.</p>";
    return;
  }
  storyList.innerHTML = "";
  for (const story of stories) {
    const card = document.createElement("div");
    card.className = "movie-card";
    const statusLabel = STORY_STATUS_LABELS[story.status] || story.status;
    const statusClass = story.status === "error" ? "error" : story.status === "done" ? "done" : "";
    card.innerHTML = `
      <div class="placeholder">📽️</div>
      <div class="card-body">
        <h3>${escapeHtml(story.title)}</h3>
        <div class="status ${statusClass}">${statusLabel}</div>
      </div>
    `;
    card.addEventListener("click", () => openStory(story.id));
    storyList.appendChild(card);
  }
}

async function openMovie(id) {
  try {
    const movie = await api(`/api/movies/${id}`);
    openMovieId = id;
    openStoryId = null;
    modalBody.innerHTML = `
      <h2>${escapeHtml(movie.title)} ${movie.year ? `(${escapeHtml(movie.year)})` : ""}</h2>
      ${movie.poster_url ? `<img src="${movie.poster_url}" style="max-width:160px;border-radius:8px;margin-bottom:1rem;">` : ""}
      ${movie.genres && movie.genres.length ? `<p><em>${movie.genres.map(escapeHtml).join(", ")}</em></p>` : ""}
      ${movie.job_status !== "done" ? `<p class="hint">Statut : ${STATUS_LABELS[movie.job_status] || movie.job_status}</p>` : ""}
      ${movie.job_error ? `<p class="error-message">${escapeHtml(movie.job_error)}</p>` : ""}
      ${movie.summary ? `<h3>Résumé</h3><p>${escapeHtml(movie.summary)}</p>` : ""}
      ${movie.summary_source ? `<span class="summary-source">Source : ${movie.summary_source === "llm" ? "IA" : movie.summary_source === "extractive" ? "résumé automatique local" : movie.summary_source}</span>` : ""}
      ${movie.source === "video" && movie.job_status === "done" ? renderRecapSection(movie) : ""}
      <p><button type="button" id="delete-movie" style="margin-top:1.5rem;background:#402;color:#ff9c9c;">Supprimer</button></p>
    `;
    document.getElementById("delete-movie").addEventListener("click", async () => {
      if (!confirm("Supprimer ce film importé ?")) return;
      await api(`/api/movies/${id}`, { method: "DELETE" });
      closeModal();
      refreshAll();
    });
    const recapButton = document.getElementById("generate-recap");
    if (recapButton) {
      recapButton.addEventListener("click", () => {
        const formats = Array.from(document.querySelectorAll(".recap-format:checked")).map((el) => el.value);
        if (!formats.length) {
          alert("Choisis au moins un format.");
          return;
        }
        generateRecap(id, formats);
      });
    }
    modal.classList.remove("hidden");
  } catch (err) {
    alert("Erreur : " + err.message);
  }
}

function renderRecapSection(movie) {
  const status = movie.recap_status;
  let body;
  if (status === "none" || status === "error") {
    body = `
      ${status === "error" ? `<p class="error-message">${escapeHtml(movie.recap_error || "Erreur inconnue")}</p>` : ""}
      <label style="display:block;margin:0.4rem 0;"><input type="checkbox" class="recap-format" value="vertical" checked> Vertical 9:16 (TikTok / Shorts)</label>
      <label style="display:block;margin:0.4rem 0 0.8rem;"><input type="checkbox" class="recap-format" value="horizontal" checked> Horizontal 16:9 (YouTube)</label>
      <button type="button" id="generate-recap">Générer la vidéo résumé</button>
      <p class="hint">Extraits pris depuis ta vidéo importée + narration automatique du résumé. Assure-toi d'avoir les droits de republication avant de publier.</p>
    `;
  } else if (status === "done") {
    const videos = [];
    if (movie.recap_vertical_available) {
      videos.push(`
        <div>
          <p class="hint">Vertical (TikTok / Shorts)</p>
          <video controls style="max-width:220px;border-radius:8px;" src="/api/movies/${movie.id}/recap/vertical"></video><br>
          <a href="/api/movies/${movie.id}/recap/vertical" class="hint">Télécharger</a>
        </div>
      `);
    }
    if (movie.recap_horizontal_available) {
      videos.push(`
        <div>
          <p class="hint">Horizontal (YouTube)</p>
          <video controls style="max-width:320px;border-radius:8px;" src="/api/movies/${movie.id}/recap/horizontal"></video><br>
          <a href="/api/movies/${movie.id}/recap/horizontal" class="hint">Télécharger</a>
        </div>
      `);
    }
    body = `<div style="display:flex;gap:1.5rem;flex-wrap:wrap;margin-bottom:0.8rem;">${videos.join("")}</div>
      <label style="display:block;margin:0.4rem 0;"><input type="checkbox" class="recap-format" value="vertical" checked> Vertical 9:16</label>
      <label style="display:block;margin:0.4rem 0 0.8rem;"><input type="checkbox" class="recap-format" value="horizontal" checked> Horizontal 16:9</label>
      <button type="button" id="generate-recap">Régénérer</button>`;
  } else {
    body = `<p class="hint">${RECAP_STATUS_LABELS[status] || status}</p>`;
  }
  return `<h3 style="margin-top:1.5rem;">Vidéo résumé (TikTok / YouTube)</h3>${body}`;
}

async function generateRecap(id, formats) {
  try {
    await api(`/api/movies/${id}/recap`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ formats }),
    });
    await openMovie(id);
    ensurePolling();
  } catch (err) {
    alert("Erreur : " + err.message);
  }
}

async function openStory(id) {
  try {
    const story = await api(`/api/story-videos/${id}`);
    openStoryId = id;
    openMovieId = null;
    const videos = [];
    if (story.vertical_available) {
      videos.push(`
        <div>
          <p class="hint">Vertical (TikTok / Shorts)</p>
          <video controls style="max-width:220px;border-radius:8px;" src="/api/story-videos/${story.id}/video/vertical"></video><br>
          <a href="/api/story-videos/${story.id}/video/vertical" class="hint">Télécharger</a>
        </div>
      `);
    }
    if (story.horizontal_available) {
      videos.push(`
        <div>
          <p class="hint">Horizontal (YouTube)</p>
          <video controls style="max-width:320px;border-radius:8px;" src="/api/story-videos/${story.id}/video/horizontal"></video><br>
          <a href="/api/story-videos/${story.id}/video/horizontal" class="hint">Télécharger</a>
        </div>
      `);
    }
    modalBody.innerHTML = `
      <h2>${escapeHtml(story.title)}</h2>
      <p class="hint">${escapeHtml(story.story_text)}</p>
      ${story.status !== "done" ? `<p class="hint">Statut : ${STORY_STATUS_LABELS[story.status] || story.status}</p>` : ""}
      ${story.error ? `<p class="error-message">${escapeHtml(story.error)}</p>` : ""}
      ${videos.length ? `<div style="display:flex;gap:1.5rem;flex-wrap:wrap;margin:1rem 0;">${videos.join("")}</div>` : ""}
      <p><button type="button" id="delete-story" style="margin-top:0.5rem;background:#402;color:#ff9c9c;">Supprimer</button></p>
    `;
    document.getElementById("delete-story").addEventListener("click", async () => {
      if (!confirm("Supprimer cette vidéo générée ?")) return;
      await api(`/api/story-videos/${id}`, { method: "DELETE" });
      closeModal();
      refreshAll();
    });
    modal.classList.remove("hidden");
  } catch (err) {
    alert("Erreur : " + err.message);
  }
}

function closeModal() {
  modal.classList.add("hidden");
  modalBody.innerHTML = "";
  openMovieId = null;
  openStoryId = null;
}

modalClose.addEventListener("click", closeModal);
modal.addEventListener("click", (e) => {
  if (e.target === modal) closeModal();
});

function ensurePolling() {
  if (pollTimer) return;
  pollTimer = setInterval(refreshAll, 4000);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

refreshAll();

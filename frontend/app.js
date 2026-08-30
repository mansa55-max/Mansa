const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchResults = document.getElementById("search-results");
const uploadForm = document.getElementById("upload-form");
const videoInput = document.getElementById("video-input");
const uploadStatus = document.getElementById("upload-status");
const movieList = document.getElementById("movie-list");
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

let pollTimer = null;

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
    loadMovies();
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
    loadMovies();
    ensurePolling();
  } catch (err) {
    uploadStatus.innerHTML = `<p class="error-message">${escapeHtml(err.message)}</p>`;
  }
});

async function loadMovies() {
  try {
    const movies = await api("/api/movies");
    renderMovies(movies);
    if (movies.some((m) => !["done", "error"].includes(m.job_status))) {
      ensurePolling();
    } else {
      stopPolling();
    }
  } catch (err) {
    movieList.innerHTML = `<p class="error-message">${escapeHtml(err.message)}</p>`;
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
    card.innerHTML = `
      ${movie.poster_url ? `<img src="${movie.poster_url}" alt="">` : `<div class="placeholder">🎞️</div>`}
      <div class="card-body">
        <h3>${escapeHtml(movie.title)}</h3>
        <div class="status ${statusClass}">${statusLabel}</div>
      </div>
    `;
    card.addEventListener("click", () => openMovie(movie.id));
    movieList.appendChild(card);
  }
}

async function openMovie(id) {
  try {
    const movie = await api(`/api/movies/${id}`);
    modalBody.innerHTML = `
      <h2>${escapeHtml(movie.title)} ${movie.year ? `(${escapeHtml(movie.year)})` : ""}</h2>
      ${movie.poster_url ? `<img src="${movie.poster_url}" style="max-width:160px;border-radius:8px;margin-bottom:1rem;">` : ""}
      ${movie.genres && movie.genres.length ? `<p><em>${movie.genres.map(escapeHtml).join(", ")}</em></p>` : ""}
      ${movie.job_status !== "done" ? `<p class="hint">Statut : ${STATUS_LABELS[movie.job_status] || movie.job_status}</p>` : ""}
      ${movie.job_error ? `<p class="error-message">${escapeHtml(movie.job_error)}</p>` : ""}
      ${movie.summary ? `<h3>Résumé</h3><p>${escapeHtml(movie.summary)}</p>` : ""}
      ${movie.summary_source ? `<span class="summary-source">Source : ${movie.summary_source === "llm" ? "IA" : movie.summary_source === "extractive" ? "résumé automatique local" : movie.summary_source}</span>` : ""}
      <p><button type="button" id="delete-movie" style="margin-top:1.5rem;background:#402;color:#ff9c9c;">Supprimer</button></p>
    `;
    document.getElementById("delete-movie").addEventListener("click", async () => {
      if (!confirm("Supprimer ce film importé ?")) return;
      await api(`/api/movies/${id}`, { method: "DELETE" });
      closeModal();
      loadMovies();
    });
    modal.classList.remove("hidden");
  } catch (err) {
    alert("Erreur : " + err.message);
  }
}

function closeModal() {
  modal.classList.add("hidden");
  modalBody.innerHTML = "";
}

modalClose.addEventListener("click", closeModal);
modal.addEventListener("click", (e) => {
  if (e.target === modal) closeModal();
});

function ensurePolling() {
  if (pollTimer) return;
  pollTimer = setInterval(loadMovies, 4000);
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

loadMovies();

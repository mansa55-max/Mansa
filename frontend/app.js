const state = {
  avatars: [],
  voices: [],
  selectedAvatarId: null,
  pollTimers: new Map(),
};

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  let data = null;
  try {
    data = await res.json();
  } catch (_) {
    data = null;
  }
  if (!res.ok) {
    const detail = (data && data.detail) || `Erreur ${res.status}`;
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return data;
}

async function loadAvatars() {
  const statusEl = document.getElementById("avatar-status");
  const gridEl = document.getElementById("avatar-grid");
  statusEl.textContent = "Chargement des avatars...";
  gridEl.innerHTML = "";
  try {
    const avatars = await fetchJson("/api/options/avatars");
    state.avatars = avatars;
    if (!avatars.length) {
      statusEl.textContent = "Aucun avatar disponible.";
      return;
    }
    statusEl.textContent = "";
    renderAvatarGrid();
  } catch (err) {
    statusEl.textContent =
      err.status === 503
        ? "HeyGen n'est pas configuré (clé API manquante)."
        : `Impossible de charger les avatars : ${err.message}`;
    statusEl.classList.add("error-message");
  }
}

function renderAvatarGrid() {
  const gridEl = document.getElementById("avatar-grid");
  gridEl.innerHTML = state.avatars
    .map(
      (a) => `
      <div class="avatar-card${a.avatar_id === state.selectedAvatarId ? " selected" : ""}" data-id="${escapeHtml(a.avatar_id)}">
        <img src="${escapeHtml(a.preview_image_url || "")}" alt="${escapeHtml(a.name)}" loading="lazy" />
        <div class="avatar-name">${escapeHtml(a.name)}</div>
      </div>`
    )
    .join("");

  gridEl.querySelectorAll(".avatar-card").forEach((card) => {
    card.addEventListener("click", () => {
      state.selectedAvatarId = card.dataset.id;
      renderAvatarGrid();
    });
  });
}

async function loadVoices() {
  const selectEl = document.getElementById("voice-select");
  try {
    const voices = await fetchJson("/api/options/voices");
    state.voices = voices;
    if (!voices.length) {
      selectEl.innerHTML = '<option value="">Aucune voix disponible</option>';
      return;
    }
    selectEl.innerHTML = voices
      .map((v) => `<option value="${escapeHtml(v.voice_id)}">${escapeHtml(v.name)}${v.language ? ` (${escapeHtml(v.language)})` : ""}</option>`)
      .join("");
  } catch (err) {
    selectEl.innerHTML = '<option value="">Voix indisponibles</option>';
  }
}

function setupScriptGeneration() {
  const btn = document.getElementById("generate-script-btn");
  const statusEl = document.getElementById("generate-script-status");
  const scriptEl = document.getElementById("script-text");

  btn.addEventListener("click", async () => {
    const productName = document.getElementById("product-name").value.trim();
    const productDescription = document.getElementById("product-description").value.trim();
    if (!productName) {
      statusEl.textContent = "Indique le nom du produit d'abord.";
      statusEl.classList.add("error-message");
      return;
    }
    btn.disabled = true;
    statusEl.classList.remove("error-message");
    statusEl.textContent = "Génération du script en cours...";
    try {
      const result = await fetchJson("/api/generate-script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_name: productName, product_description: productDescription }),
      });
      scriptEl.value = result.script;
      updateCharCount();
      statusEl.textContent = "Script généré !";
    } catch (err) {
      statusEl.textContent =
        err.status === 503
          ? "La génération IA n'est pas configurée (clé API manquante)."
          : `Erreur : ${err.message}`;
      statusEl.classList.add("error-message");
    } finally {
      btn.disabled = false;
    }
  });
}

function updateCharCount() {
  const scriptEl = document.getElementById("script-text");
  document.getElementById("script-char-count").textContent = scriptEl.value.length;
}

function setupCreateAd() {
  const btn = document.getElementById("create-ad-btn");
  const statusEl = document.getElementById("create-ad-status");

  btn.addEventListener("click", async () => {
    const productName = document.getElementById("product-name").value.trim();
    const scriptText = document.getElementById("script-text").value.trim();
    const voiceId = document.getElementById("voice-select").value;
    const aspect = document.querySelector('input[name="aspect"]:checked').value;
    const captionsEnabled = document.getElementById("captions-enabled").checked;

    statusEl.classList.remove("error-message");

    if (!scriptText) {
      statusEl.textContent = "Le script est requis.";
      statusEl.classList.add("error-message");
      return;
    }
    if (!state.selectedAvatarId) {
      statusEl.textContent = "Choisis un avatar.";
      statusEl.classList.add("error-message");
      return;
    }
    if (!voiceId) {
      statusEl.textContent = "Choisis une voix.";
      statusEl.classList.add("error-message");
      return;
    }

    btn.disabled = true;
    statusEl.textContent = "Création de la pub...";
    try {
      const result = await fetchJson("/api/ads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_name: productName,
          script_text: scriptText,
          avatar_id: state.selectedAvatarId,
          voice_id: voiceId,
          aspect,
          captions_enabled: captionsEnabled,
        }),
      });
      statusEl.textContent = "Pub lancée, suis sa progression ci-dessous.";
      await loadAds();
      ensurePolling(result.id);
    } catch (err) {
      statusEl.textContent = `Erreur : ${err.message}`;
      statusEl.classList.add("error-message");
    } finally {
      btn.disabled = false;
    }
  });
}

const STATUS_LABELS = {
  pending: "En attente",
  generating: "Génération de l'avatar...",
  downloading: "Téléchargement...",
  captioning: "Ajout des sous-titres...",
  done: "Terminée",
  error: "Erreur",
};

function isActiveStatus(status) {
  return ["pending", "generating", "downloading", "captioning"].includes(status);
}

async function loadAds() {
  const listEl = document.getElementById("ads-list");
  try {
    const ads = await fetchJson("/api/ads");
    renderAds(ads);
    ads.forEach((ad) => {
      if (isActiveStatus(ad.status)) {
        ensurePolling(ad.id);
      }
    });
  } catch (err) {
    listEl.innerHTML = `<p class="empty error-message">Impossible de charger les pubs : ${escapeHtml(err.message)}</p>`;
  }
}

function renderAds(ads) {
  const listEl = document.getElementById("ads-list");
  if (!ads.length) {
    listEl.innerHTML = '<p class="empty">Aucune pub pour le moment.</p>';
    return;
  }
  listEl.innerHTML = ads
    .map(
      (ad) => `
      <div class="movie-card" data-id="${ad.id}">
        <div class="placeholder">${ad.status === "done" ? "🎬" : ad.status === "error" ? "⚠️" : "⏳"}</div>
        <div class="card-body">
          <h3>${escapeHtml(ad.product_name)}</h3>
          <div class="status ${escapeHtml(ad.status)}">${escapeHtml(STATUS_LABELS[ad.status] || ad.status)}</div>
        </div>
      </div>`
    )
    .join("");

  listEl.querySelectorAll(".movie-card").forEach((card) => {
    card.addEventListener("click", () => openAd(Number(card.dataset.id)));
  });
}

function ensurePolling(adId) {
  if (state.pollTimers.has(adId)) return;
  const timer = setInterval(async () => {
    try {
      const ad = await fetchJson(`/api/ads/${adId}`);
      if (!isActiveStatus(ad.status)) {
        stopPolling(adId);
      }
      await loadAds();
      const modal = document.getElementById("modal");
      if (!modal.classList.contains("hidden") && modal.dataset.adId === String(adId)) {
        renderModalBody(ad);
      }
    } catch (_) {
      stopPolling(adId);
    }
  }, 4000);
  state.pollTimers.set(adId, timer);
}

function stopPolling(adId) {
  const timer = state.pollTimers.get(adId);
  if (timer) {
    clearInterval(timer);
    state.pollTimers.delete(adId);
  }
}

async function openAd(adId) {
  const modal = document.getElementById("modal");
  modal.dataset.adId = String(adId);
  modal.classList.remove("hidden");
  document.getElementById("modal-body").innerHTML = "<p>Chargement...</p>";
  try {
    const ad = await fetchJson(`/api/ads/${adId}`);
    renderModalBody(ad);
  } catch (err) {
    document.getElementById("modal-body").innerHTML = `<p class="error-message">${escapeHtml(err.message)}</p>`;
  }
}

function renderModalBody(ad) {
  const body = document.getElementById("modal-body");
  let extra = "";
  if (ad.status === "done") {
    extra = `
      <video src="/api/ads/${ad.id}/video" controls style="width:100%;border-radius:8px;margin:0.75rem 0;"></video>
      <a href="/api/ads/${ad.id}/video" download style="display:inline-block;margin-bottom:0.75rem;">⬇️ Télécharger la vidéo</a>
    `;
  } else if (ad.status === "error") {
    extra = `<p class="error-message">${escapeHtml(ad.error || "Erreur inconnue")}</p>`;
  } else {
    extra = `<p class="hint">${escapeHtml(STATUS_LABELS[ad.status] || ad.status)}</p>`;
  }

  body.innerHTML = `
    <h2>${escapeHtml(ad.product_name)}</h2>
    <p class="status ${escapeHtml(ad.status)}">${escapeHtml(STATUS_LABELS[ad.status] || ad.status)}</p>
    ${extra}
    <p class="hint" style="white-space:pre-wrap;">${escapeHtml(ad.script_text)}</p>
    <button type="button" id="delete-ad-btn" style="background:var(--error);">🗑️ Supprimer</button>
  `;

  document.getElementById("delete-ad-btn").addEventListener("click", async () => {
    if (!confirm("Supprimer cette pub ?")) return;
    try {
      await fetch(`/api/ads/${ad.id}`, { method: "DELETE" });
      stopPolling(ad.id);
      closeModal();
      await loadAds();
    } catch (err) {
      alert(`Erreur lors de la suppression : ${err.message}`);
    }
  });
}

function closeModal() {
  const modal = document.getElementById("modal");
  modal.classList.add("hidden");
  delete modal.dataset.adId;
}

function setupModal() {
  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("modal").addEventListener("click", (e) => {
    if (e.target.id === "modal") closeModal();
  });
}

document.getElementById("script-text").addEventListener("input", updateCharCount);

setupScriptGeneration();
setupCreateAd();
setupModal();
loadAvatars();
loadVoices();
loadAds();

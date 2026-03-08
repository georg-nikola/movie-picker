(function () {
  "use strict";

  // ── DOM refs ──────────────────────────────────────────────────────────────
  const pickBtn       = document.getElementById("pickBtn");
  const cardInner     = document.getElementById("cardInner");
  const placeholder   = document.getElementById("placeholder");
  const result        = document.getElementById("result");
  const historySection = document.getElementById("historySection");
  const historyList   = document.getElementById("historyList");
  const btnText       = pickBtn.querySelector(".btn-text");

  // Auth bar
  const loginBtn      = document.getElementById("loginBtn");
  const logoutBtn     = document.getElementById("logoutBtn");
  const authUser      = document.getElementById("authUser");
  const browseBtn     = document.getElementById("browseBtn");

  // Watched
  const watchedBtn    = document.getElementById("watchedBtn");
  const watchedFilter = document.getElementById("watchedFilter");
  const filterCheckbox = document.getElementById("filterWatched");

  // Modal
  const authModal     = document.getElementById("authModal");
  const modalClose    = document.getElementById("modalClose");
  const modalTabs     = document.getElementById("modalTabs");
  const loginForm     = document.getElementById("loginForm");
  const registerForm  = document.getElementById("registerForm");

  // ── State ─────────────────────────────────────────────────────────────────
  let history     = [];
  let lastIndex   = -1;
  let currentTitle = "";

  let authToken   = localStorage.getItem("mp_token") || "";
  let authUsername   = localStorage.getItem("mp_username") || "";
  let watchedSet  = new Set();
  // ── API ───────────────────────────────────────────────────────────────────
  async function apiCall(method, path, body) {
    const opts = {
      method,
      headers: { "Content-Type": "application/json" },
    };
    if (authToken) opts.headers["Authorization"] = "Bearer " + authToken;
    if (body)      opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    const json = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(json.detail || "Request failed");
    return json;
  }

  async function fetchWatched() {
    if (!authToken) return;
    try {
      const data = await apiCall("GET", "/api/watched");
      watchedSet = new Set(data.watched);
      watchedFilter.classList.remove("hidden");
    } catch (e) {
      if (e.message.includes("401") || e.message === "Invalid token" || e.message === "User not found") {
        doLogout();
      }
    }
  }

  async function addWatched(title) {
    await apiCall("POST", "/api/watched", { movie_title: title });
    watchedSet.add(title);
  }

  async function removeWatched(title) {
    await apiCall("DELETE", "/api/watched/" + encodeURIComponent(title));
    watchedSet.delete(title);
  }

  // ── Auth helpers ──────────────────────────────────────────────────────────
  function updateAuthUI() {
    if (authToken) {
      loginBtn.classList.add("hidden");
      authUser.textContent = authUsername;
      authUser.classList.remove("hidden");
      logoutBtn.classList.remove("hidden");
    } else {
      loginBtn.classList.remove("hidden");
      authUser.classList.add("hidden");
      logoutBtn.classList.add("hidden");
      watchedFilter.classList.add("hidden");
      watchedBtn.classList.add("hidden");
    }
  }

  function doLogout() {
    authToken = "";
    authUsername = "";
    watchedSet = new Set();
    localStorage.removeItem("mp_token");
    localStorage.removeItem("mp_username");
    updateAuthUI();
    updateWatchedBtn();
  }

  function saveAuth(token, username) {
    authToken = token;
    authUsername = username;
    localStorage.setItem("mp_token", token);
    localStorage.setItem("mp_username", username);
    updateAuthUI();
    fetchWatched();
  }

  // ── Modal ─────────────────────────────────────────────────────────────────
  function openModal(tab) {
    authModal.classList.remove("hidden");
    showTab(tab || "login");
  }

  function closeModal() {
    authModal.classList.add("hidden");
    clearErrors();
  }

  function showTab(tab) {
    document.querySelectorAll(".modal-tab").forEach(function (t) {
      t.classList.toggle("active", t.dataset.tab === tab);
    });
    loginForm.classList.toggle("hidden", tab !== "login");
    registerForm.classList.toggle("hidden", tab !== "register");
  }

  function clearErrors() {
    ["loginError", "registerError"].forEach(function (id) {
      const el = document.getElementById(id);
      el.textContent = "";
      el.classList.add("hidden");
    });
  }

  function showError(id, msg) {
    const el = document.getElementById(id);
    el.textContent = msg;
    el.classList.remove("hidden");
  }

  // Modal tab switching
  modalTabs.addEventListener("click", function (e) {
    const tab = e.target.dataset.tab;
    if (tab) showTab(tab);
  });

  loginBtn.addEventListener("click", function () { openModal("login"); });
  logoutBtn.addEventListener("click", doLogout);
  modalClose.addEventListener("click", closeModal);
  authModal.addEventListener("click", function (e) {
    if (e.target === authModal) closeModal();
  });

  // Login submit
  loginForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    clearErrors();
    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;
    try {
      const data = await apiCall("POST", "/api/auth/login", { username, password });
      saveAuth(data.token, data.username);
      closeModal();
    } catch (err) {
      showError("loginError", err.message);
    }
  });

  // Register submit
  registerForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    clearErrors();
    const username = document.getElementById("registerUsername").value.trim();
    const password = document.getElementById("registerPassword").value;
    try {
      const data = await apiCall("POST", "/api/auth/register", { username, password });
      saveAuth(data.token, data.username);
      closeModal();
    } catch (err) {
      showError("registerError", err.message);
    }
  });

  // ── Watched button ────────────────────────────────────────────────────────
  function updateWatchedBtn() {
    if (!authToken || !currentTitle) {
      watchedBtn.classList.add("hidden");
      return;
    }
    watchedBtn.classList.remove("hidden");
    const isWatched = watchedSet.has(currentTitle);
    watchedBtn.querySelector(".watched-btn-text").textContent =
      isWatched ? "Watched" : "Mark as Watched";
    watchedBtn.classList.toggle("watched-btn-active", isWatched);
  }

  watchedBtn.addEventListener("click", async function () {
    if (!currentTitle) return;
    try {
      if (watchedSet.has(currentTitle)) {
        await removeWatched(currentTitle);
      } else {
        await addWatched(currentTitle);
      }
      updateWatchedBtn();
    } catch (e) {
      // silent fail
    }
  });

  // ── Movie picking ─────────────────────────────────────────────────────────
  function getAvailableMovies() {
    if (!authToken || !filterCheckbox.checked || watchedSet.size === 0) return MOVIES;
    const available = MOVIES.filter(function (m) { return !watchedSet.has(m); });
    return available.length > 0 ? available : MOVIES;
  }

  function getRandomMovie() {
    const pool = getAvailableMovies();
    let index;
    do {
      index = Math.floor(Math.random() * pool.length);
    } while (index === lastIndex && pool.length > 1);
    lastIndex = index;
    const title = pool[index];
    return { title: title, index: MOVIES.indexOf(title) + 1 };
  }

  function showMovie(movie) {
    currentTitle = movie.title;

    cardInner.classList.remove("shuffle");
    void cardInner.offsetWidth;
    cardInner.classList.add("shuffle");
    cardInner.classList.add("picked");

    placeholder.classList.add("hidden");
    result.classList.remove("hidden");

    void result.offsetWidth;

    document.getElementById("movieTitle").textContent = movie.title;
    document.getElementById("movieNumber").textContent = "#" + movie.index + " of " + MOVIES.length;

    btnText.textContent = "Pick Again";

    updateWatchedBtn();

    history.unshift(movie);
    if (history.length > 1) {
      renderHistory();
    }
  }

  function renderHistory() {
    const previous = history.slice(1, 6);
    if (previous.length === 0) return;

    historySection.classList.remove("hidden");
    historyList.innerHTML = "";

    previous.forEach(function (movie, i) {
      const item = document.createElement("div");
      item.className = "history-item";
      item.style.animationDelay = (i * 0.08) + "s";
      item.innerHTML =
        '<span class="history-num">#' + movie.index + '</span>' +
        '<span class="history-name">' + escapeHtml(movie.title) + '</span>';
      historyList.appendChild(item);
    });
  }

  function escapeHtml(text) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
  }

  pickBtn.addEventListener("click", function () {
    var movie = getRandomMovie();
    showMovie(movie);
  });

  document.addEventListener("keydown", function (e) {
    if (authModal.classList.contains("hidden")) {
      if (e.code === "Space" || e.code === "Enter") {
        if (e.target === document.body || e.target === pickBtn) {
          e.preventDefault();
          pickBtn.click();
        }
      }
    }
  });

  // ── Browser ───────────────────────────────────────────────────────────────
  const browserOverlay     = document.getElementById("browserOverlay");
  const browserClose       = document.getElementById("browserClose");
  const browserSearch      = document.getElementById("browserSearch");
  const browserSearchClear = document.getElementById("browserSearchClear");
  const browserSortGroup   = document.getElementById("browserSortGroup");
  const browserList        = document.getElementById("browserList");
  const browserResultsCount = document.getElementById("browserResultsCount");
  const browserWatchedCount = document.getElementById("browserWatchedCount");

  let browserSortOrder = "index"; // "index" | "alpha"
  let browserQuery     = "";
  let browserDebounce  = null;

  function openBrowser() {
    browserQuery = "";
    browserSearch.value = "";
    browserSearchClear.classList.add("hidden");
    browserResultsCount.classList.add("hidden");
    browserOverlay.classList.remove("hidden");
    renderBrowser();
    browserSearch.focus();
  }

  function closeBrowser() {
    browserOverlay.classList.add("hidden");
  }

  function getBrowserItems() {
    var q = browserQuery.trim().toLowerCase();
    var items = MOVIES.map(function (title, i) {
      return { title: title, index: i + 1, watched: watchedSet.has(title) };
    });
    if (q) {
      items = items.filter(function (m) { return m.title.toLowerCase().indexOf(q) !== -1; });
    }
    if (browserSortOrder === "alpha") {
      items = items.slice().sort(function (a, b) {
        return a.title.toLowerCase() < b.title.toLowerCase() ? -1 : 1;
      });
    }
    return items;
  }

  function renderBrowser() {
    var items = getBrowserItems();
    var watchedCount = watchedSet.size;

    browserWatchedCount.textContent = authToken
      ? watchedCount + " of " + MOVIES.length + " watched"
      : MOVIES.length + " films";

    if (browserQuery.trim()) {
      browserResultsCount.textContent = items.length + " result" + (items.length !== 1 ? "s" : "");
      browserResultsCount.classList.remove("hidden");
    } else {
      browserResultsCount.classList.add("hidden");
    }

    if (items.length === 0) {
      browserList.innerHTML = '<p class="browser-no-results">No films match your search.</p>';
      return;
    }

    var frag = document.createDocumentFragment();
    items.forEach(function (m) {
      var div = document.createElement("div");
      div.className = "browser-item" + (m.watched ? " watched" : "");
      div.dataset.title = m.title;
      div.innerHTML =
        '<span class="browser-item-check">&#10003;</span>' +
        '<span class="browser-item-index">#' + m.index + '</span>' +
        '<span class="browser-item-title">' + escapeHtml(m.title) + '</span>';
      frag.appendChild(div);
    });
    browserList.innerHTML = "";
    browserList.appendChild(frag);
  }

  // Toggle watched from browser list (event delegation)
  browserList.addEventListener("click", async function (e) {
    if (!authToken) return;
    var item = e.target.closest(".browser-item");
    if (!item) return;
    var title = item.dataset.title;
    try {
      if (watchedSet.has(title)) {
        await removeWatched(title);
        item.classList.remove("watched");
      } else {
        await addWatched(title);
        item.classList.add("watched");
      }
      // Update watched count in header and watched button if this is currentTitle
      browserWatchedCount.textContent = watchedSet.size + " of " + MOVIES.length + " watched";
      if (title === currentTitle) updateWatchedBtn();
    } catch (e) {
      // silent fail
    }
  });

  // Search input
  browserSearch.addEventListener("input", function () {
    browserQuery = browserSearch.value;
    browserSearchClear.classList.toggle("hidden", !browserQuery);
    clearTimeout(browserDebounce);
    browserDebounce = setTimeout(renderBrowser, 150);
  });

  browserSearchClear.addEventListener("click", function () {
    browserQuery = "";
    browserSearch.value = "";
    browserSearchClear.classList.add("hidden");
    browserResultsCount.classList.add("hidden");
    renderBrowser();
    browserSearch.focus();
  });

  // Sort buttons
  browserSortGroup.addEventListener("click", function (e) {
    var btn = e.target.closest(".browser-sort-btn");
    if (!btn) return;
    browserSortOrder = btn.dataset.sort;
    document.querySelectorAll(".browser-sort-btn").forEach(function (b) {
      b.classList.toggle("active", b.dataset.sort === browserSortOrder);
    });
    renderBrowser();
  });

  browserClose.addEventListener("click", closeBrowser);
  browserOverlay.addEventListener("click", function (e) {
    if (e.target === browserOverlay) closeBrowser();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !browserOverlay.classList.contains("hidden")) {
      closeBrowser();
    }
  });

  browseBtn.addEventListener("click", openBrowser);

  // ── Init ──────────────────────────────────────────────────────────────────
  updateAuthUI();
  if (authToken) fetchWatched();
})();

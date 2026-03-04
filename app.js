(function () {
  "use strict";

  const pickBtn = document.getElementById("pickBtn");
  const cardInner = document.getElementById("cardInner");
  const placeholder = document.getElementById("placeholder");
  const result = document.getElementById("result");
  const movieTitle = document.getElementById("movieTitle");
  const movieNumber = document.getElementById("movieNumber");
  const historySection = document.getElementById("historySection");
  const historyList = document.getElementById("historyList");
  const btnText = pickBtn.querySelector(".btn-text");

  let history = [];
  let lastIndex = -1;

  function getRandomMovie() {
    let index;
    // Avoid picking the same movie twice in a row
    do {
      index = Math.floor(Math.random() * MOVIES.length);
    } while (index === lastIndex && MOVIES.length > 1);
    lastIndex = index;
    return { title: MOVIES[index], index: index + 1 };
  }

  function showMovie(movie) {
    // Animate the card
    cardInner.classList.remove("shuffle");
    // Force reflow to restart animation
    void cardInner.offsetWidth;
    cardInner.classList.add("shuffle");
    cardInner.classList.add("picked");

    // Hide placeholder, show result
    placeholder.classList.add("hidden");
    result.classList.remove("hidden");

    // Reset animations on result children by re-rendering
    result.innerHTML = result.innerHTML;

    // Re-query after innerHTML reset
    const title = document.getElementById("movieTitle");
    const number = document.getElementById("movieNumber");

    title.textContent = movie.title;
    number.textContent = "#" + movie.index + " of " + MOVIES.length;

    // Update button text after first pick
    btnText.textContent = "Pick Again";

    // Add to history
    history.unshift(movie);
    if (history.length > 1) {
      renderHistory();
    }
  }

  function renderHistory() {
    // Only show previous picks (skip current)
    const previous = history.slice(1, 6); // Show last 5
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

  // Keyboard shortcut: Space or Enter to pick
  document.addEventListener("keydown", function (e) {
    if (e.code === "Space" || e.code === "Enter") {
      if (e.target === document.body || e.target === pickBtn) {
        e.preventDefault();
        pickBtn.click();
      }
    }
  });
})();

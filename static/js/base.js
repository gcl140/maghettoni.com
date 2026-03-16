// Search suggestions
document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.querySelector('input[name="q"]');
  const suggestionsBox = document.getElementById("searchSuggestions");

  if (searchInput && suggestionsBox) {
    let debounceTimer;

    searchInput.addEventListener("input", function (e) {
      clearTimeout(debounceTimer);
      const query = e.target.value.trim();

      if (query.length < 2) {
        suggestionsBox.classList.add("hidden");
        return;
      }

      debounceTimer = setTimeout(() => {
        fetch(`/dashboard/search/quick/?q=${encodeURIComponent(query)}`, {
          headers: { "X-Requested-With": "XMLHttpRequest" },
        })
          .then((r) => r.json())
          .then((data) => {
            suggestionsBox.innerHTML = "";
            if (!data.results || data.results.length === 0) {
              suggestionsBox.classList.add("hidden");
              return;
            }
            data.results.forEach((item) => {
              const div = document.createElement("div");
              div.className =
                "px-4 py-2 cursor-pointer hover:bg-gray-100 flex flex-col";
              div.innerHTML = `<span class="font-medium">${item.name}</span><span class="text-sm text-gray-500">${item.type} • ${item.detail}</span>`;
              div.addEventListener("click", () => {
                if (item.url && item.url !== "#")
                  window.location.href = item.url;
              });
              suggestionsBox.appendChild(div);
            });
            suggestionsBox.classList.remove("hidden");
          })
          .catch(() => suggestionsBox.classList.add("hidden"));
      }, 300);
    });

    document.addEventListener("click", function (e) {
      if (
        !searchInput.contains(e.target) &&
        !suggestionsBox.contains(e.target)
      ) {
        suggestionsBox.classList.add("hidden");
      }
    });

    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") suggestionsBox.classList.add("hidden");
    });
  }
});

// Sidebar, mobile nav, add menu, language switcher
(function () {
  "use strict";

  const body = document.getElementById("appBody");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sb-overlay");
  const desktopToggle = document.getElementById("desktopToggle");
  const mobileToggle = document.getElementById("mobileToggle");
  const addWrap = document.getElementById("addWrap");
  const addMenu = document.getElementById("addMenu");
  const addBtn = document.getElementById("addBtn");

  // ── Desktop: collapse / expand ──────────────────────────────
  const dtIcon = document.getElementById("dtIcon");

  function updateToggleIcon(collapsed) {
    if (!dtIcon) return;
    dtIcon.className = collapsed
      ? "fas fa-chevron-right text-xs"
      : "fas fa-chevron-left text-xs";
  }

  function setCollapsed(on) {
    body.classList.toggle("sb-collapsed", on);
    localStorage.setItem("sb_collapsed", on ? "1" : "0");
    updateToggleIcon(on);
  }

  requestAnimationFrame(function () {
    body.classList.remove("no-sb-transition");
  });

  if (window.innerWidth >= 1024) {
    var initCollapsed = localStorage.getItem("sb_collapsed") === "1";
    setCollapsed(initCollapsed);
  }

  desktopToggle &&
    desktopToggle.addEventListener("click", function () {
      setCollapsed(!body.classList.contains("sb-collapsed"));
    });

  // ── Mobile: show / hide ──────────────────────────────────────
  function openMobile() {
    sidebar.classList.add("mobile-open");
    overlay.classList.remove("hidden");
  }
  function closeMobile() {
    sidebar.classList.remove("mobile-open");
    overlay.classList.add("hidden");
  }

  mobileToggle && mobileToggle.addEventListener("click", openMobile);
  overlay && overlay.addEventListener("click", closeMobile);

  // ── Mobile search bar ────────────────────────────────────────
  const mobileSearchToggle = document.getElementById("mobileSearchToggle");
  const mobileSearchBar = document.getElementById("mobileSearchBar");
  const mobileSearchClose = document.getElementById("mobileSearchClose");
  const mobileSearchInput = document.getElementById("mobileSearchInput");

  mobileSearchToggle &&
    mobileSearchToggle.addEventListener("click", function () {
      mobileSearchBar.classList.toggle("hidden");
      if (!mobileSearchBar.classList.contains("hidden")) {
        mobileSearchInput && mobileSearchInput.focus();
      }
    });
  mobileSearchClose &&
    mobileSearchClose.addEventListener("click", function () {
      mobileSearchBar.classList.add("hidden");
    });

  window.addEventListener("resize", function () {
    if (window.innerWidth >= 1024) closeMobile();
  });

  // ── Add menu ─────────────────────────────────────────────────
  addBtn &&
    addBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      addMenu.classList.toggle("hidden");
    });
  document.addEventListener("click", function (e) {
    if (addWrap && !addWrap.contains(e.target)) {
      addMenu && addMenu.classList.add("hidden");
    }
  });

  // ── Language dropdown ─────────────────────────────────────────
  const langBtn = document.getElementById("langBtn");
  const langMenu = document.getElementById("langMenu");
  const langWrap = document.getElementById("langWrap");
  const langLabel = document.getElementById("langLabel");

  langBtn &&
    langBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      langMenu.classList.toggle("hidden");
    });
  document.addEventListener("click", function (e) {
    if (langWrap && !langWrap.contains(e.target))
      langMenu && langMenu.classList.add("hidden");
  });

  function getGTCookie() {
    const m = document.cookie.match(/(?:^|;)\s*googtrans=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : null;
  }

  function setGTCookie(val) {
    document.cookie = "googtrans=" + val + "; path=/";
    if (
      location.hostname !== "localhost" &&
      location.hostname !== "127.0.0.1"
    ) {
      document.cookie =
        "googtrans=" + val + "; domain=" + location.hostname + "; path=/";
      document.cookie =
        "googtrans=" + val + "; domain=." + location.hostname + "; path=/";
    }
  }

  function clearGTCookie() {
    var exp = "expires=Thu, 01 Jan 1970 00:00:00 UTC";
    document.cookie = "googtrans=; path=/; " + exp;
    if (
      location.hostname !== "localhost" &&
      location.hostname !== "127.0.0.1"
    ) {
      document.cookie =
        "googtrans=; domain=" + location.hostname + "; path=/; " + exp;
      document.cookie =
        "googtrans=; domain=." + location.hostname + "; path=/; " + exp;
    }
  }

  var savedLang = localStorage.getItem("mag-lang");
  var activeLang = savedLang || (getGTCookie() === "/en/sw" ? "sw" : "en");
  if (langLabel)
    langLabel.textContent = activeLang === "sw" ? "Kiswahili" : "English";
  document.querySelectorAll(".lang-opt").forEach(function (btn) {
    if (btn.dataset.lang === activeLang)
      btn.classList.add("bg-gray-100", "font-semibold");
  });

  window.switchLang = function (lang) {
    if (langMenu) {
      langMenu.classList.add("hidden");
    }

    localStorage.setItem("mag-lang", lang);
    if (lang === "sw") {
      setGTCookie("/en/sw");
    } else {
      clearGTCookie();
    }

    document.documentElement.lang = lang === "sw" ? "sw" : "en";
    if (langLabel) {
      langLabel.textContent = lang === "sw" ? "Kiswahili" : "English";
    }
    location.reload();
  };
})();

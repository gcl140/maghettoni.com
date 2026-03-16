/* Sidebar mobile toggle helpers */
window.tpCloseSidebar = function () {
  var sidebar = document.getElementById("tp-sidebar");
  var backdrop = document.getElementById("tp-sidebar-backdrop");
  if (sidebar) sidebar.classList.add("-translate-x-full");
  if (backdrop) backdrop.classList.add("hidden");
};
window.tpToggleSidebar = function () {
  var sidebar = document.getElementById("tp-sidebar");
  var backdrop = document.getElementById("tp-sidebar-backdrop");
  if (sidebar) sidebar.classList.toggle("-translate-x-full");
  if (backdrop) backdrop.classList.toggle("hidden");
};

(function () {
  var dialog = document.getElementById("tp-notif-dialog");
  var list = document.getElementById("tp-notif-list");
  var bell = document.getElementById("tp-bell-btn");
  if (!dialog || !bell || !list) {
    return;
  }

  var allItems = [];
  var currentPage = 1;
  var loading = false;

  function clearBellDot() {
    var dot = document.getElementById("tp-bell-dot");
    if (dot) {
      dot.remove();
    }
  }

  var colorMap = {
    info: "bg-blue-500/20 text-blue-400",
    success: "bg-green-500/20 text-green-400",
    warning: "bg-amber-500/20 text-amber-400",
    error: "bg-red-500/20 text-red-400",
  };

  var iconMap = {
    info: "fa-info-circle",
    success: "fa-check-circle",
    warning: "fa-exclamation-triangle",
    error: "fa-times-circle",
  };

  function itemHTML(item) {
    var dot = item.unread
      ? '<span class="flex-shrink-0 w-2 h-2 rounded-full bg-blue-400 mt-1.5"></span>'
      : "";
    var color = colorMap[item.notification_type] || colorMap.info;
    var icon = iconMap[item.notification_type] || iconMap.info;
    return (
      '<div class="flex items-start gap-3 p-3 rounded-lg ' +
      (item.unread ? "bg-brown-600/60" : "bg-brown-700/40") +
      '">' +
      '<div class="flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ' +
      color +
      '">' +
      '<i class="fas ' +
      icon +
      ' text-sm"></i>' +
      "</div>" +
      '<div class="min-w-0 flex-1">' +
      '<p class="text-sm font-medium text-white truncate">' +
      (item.title || "") +
      "</p>" +
      '<p class="text-xs text-brown-300 mt-0.5">' +
      (item.message || "") +
      "</p>" +
      '<p class="text-xs text-brown-500 mt-1">' +
      (item.created_at || "") +
      "</p>" +
      "</div>" +
      dot +
      "</div>"
    );
  }

  function renderAll(hasMore) {
    if (!allItems.length) {
      list.innerHTML =
        '<p class="text-sm text-brown-300 text-center py-6">No new notifications.</p>';
      return;
    }

    var html = allItems.map(itemHTML).join("");
    if (hasMore) {
      html +=
        '<button id="tp-notif-more" class="w-full mt-2 py-2 text-xs text-brown-300 hover:text-white transition-colors text-center">' +
        '<i class="fas fa-chevron-down mr-1"></i> Load more</button>';
    }

    list.innerHTML = html;
    var btn = document.getElementById("tp-notif-more");
    if (btn) {
      btn.addEventListener("click", loadMore);
    }
  }

  function fetchPage(page) {
    loading = true;
    return fetch("/tenant/api/notifications/?page=" + page)
      .then(function (resp) {
        return resp.json();
      })
      .finally(function () {
        loading = false;
      });
  }

  function loadMore() {
    if (loading) {
      return;
    }

    currentPage += 1;
    fetchPage(currentPage).then(function (data) {
      allItems = allItems.concat(data.items || []);
      renderAll(data.has_more);
    });
  }

  bell.addEventListener("click", function () {
    currentPage = 1;
    allItems = [];
    clearBellDot();
    list.innerHTML =
      '<p class="text-sm text-brown-300 text-center py-6"><i class="fas fa-spinner fa-spin mr-2"></i> Loading...</p>';
    dialog.showModal();

    fetchPage(1)
      .then(function (data) {
        allItems = data.items || [];
        if ((data.unread_count || 0) === 0) {
          clearBellDot();
        }
        renderAll(data.has_more);
      })
      .catch(function () {
        list.innerHTML =
          '<p class="text-sm text-red-400 text-center py-6">Error loading notifications.</p>';
      });
  });
})();

window.switchLang = function (lang) {
  localStorage.setItem("mag-lang", lang);

  var langMenu = document.getElementById("langMenu");
  if (langMenu) {
    langMenu.classList.add("hidden");
  }

  document.querySelectorAll(".lang-opt").forEach(function (btn) {
    btn.classList.toggle("font-semibold", btn.dataset.lang === lang);
  });

  if (lang === "en") {
    ["/", location.pathname].forEach(function (path) {
      document.cookie =
        "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=" + path + ";";
      document.cookie =
        "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=" +
        path +
        "; domain=." +
        location.hostname +
        ";";
    });
    window.location.reload();
    return;
  }

  document.cookie = "googtrans=/en/sw; path=/";
  document.cookie =
    "googtrans=/en/sw; domain=." + location.hostname + "; path=/";

  // Rely on cookie + reload so translation works even when goog-te-combo isn't ready yet.
  window.location.reload();
};

(function () {
  var isSwahili = document.cookie.split(";").some(function (cookie) {
    var c = cookie.trim();
    return c.startsWith("googtrans=") && c.includes("/sw");
  });

  if (isSwahili) {
    var label = document.getElementById("langLabel");
    if (label) {
      label.textContent = "Kiswahili";
    }
    document.querySelectorAll(".lang-opt").forEach(function (btn) {
      btn.classList.toggle("font-semibold", btn.dataset.lang === "sw");
    });
  }
})();

document.getElementById("langBtn")?.addEventListener("click", function (event) {
  event.stopPropagation();
  document.getElementById("langMenu")?.classList.toggle("hidden");
});

document.addEventListener("click", function () {
  document.getElementById("langMenu")?.classList.add("hidden");
});

(function () {
  var btn = document.getElementById("tp-collapse-btn");
  var icon = document.getElementById("tp-collapse-icon");
  if (!btn || !icon) {
    return;
  }

  function applyState(collapsed) {
    document.body.classList.toggle("tp-collapsed", collapsed);
    icon.style.transform = collapsed ? "rotate(180deg)" : "";
  }

  var style = document.createElement("style");
  style.textContent = "* { transition: none !important; }";
  document.head.appendChild(style);

  applyState(localStorage.getItem("tp-sidebar-collapsed") === "true");
  requestAnimationFrame(function () {
    document.head.removeChild(style);
  });

  btn.addEventListener("click", function () {
    var next = !document.body.classList.contains("tp-collapsed");
    localStorage.setItem("tp-sidebar-collapsed", String(next));
    applyState(next);
  });
})();

(function () {
  if (!window.Toastify) {
    return;
  }

  var toasts = document.querySelectorAll("#tp-toast-messages .tp-toast-item");
  if (!toasts.length) {
    return;
  }

  var colors = {
    success: "#16a34a",
    error: "#dc2626",
    warning: "#d97706",
    info: "#2563eb",
  };

  toasts.forEach(function (toast) {
    var text = toast.dataset.text || "";
    var level = toast.dataset.level || "info";
    var bg = colors[level] || colors.info;

    Toastify({
      text: text,
      duration: 4000,
      gravity: "top",
      position: "right",
      style: {
        background: bg,
        borderRadius: "10px",
        fontSize: "14px",
      },
    }).showToast();
  });
})();

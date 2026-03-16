(function () {
  const dialog = document.getElementById("notificationDialog");
  const list = document.getElementById("notif-list");
  const bell =
    document.getElementById("dashboardNotifBell") ||
    document.querySelector('[title="Notifications"]') ||
    document.querySelector('[title="Taarifa"]');
  if (!dialog || !list || !bell) return;

  const colorMap = {
    red: "bg-red-500/20 text-red-400",
    amber: "bg-amber-500/20 text-amber-400",
    blue: "bg-blue-500/20 text-blue-400",
  };

  let currentPage = 1;
  let allItems = [];
  let loading = false;

  function itemHTML(item) {
    const tag = item.url ? "a" : "div";
    const href = item.url ? `href="${item.url}"` : "";
    const dot = item.unread
      ? '<span class="flex-shrink-0 w-2 h-2 rounded-full bg-blue-400 mt-1.5"></span>'
      : "";
    return `
      <${tag} ${href} class="flex items-start gap-3 p-3 rounded-lg transition-colors ${item.unread ? "bg-brown-600/60 hover:bg-brown-600" : "bg-brown-700/40 hover:bg-brown-700/60"}">
        <div class="flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${colorMap[item.color] || colorMap.blue}">
          <i class="fas ${item.icon} text-sm"></i>
        </div>
        <div class="min-w-0 flex-1">
          <p class="text-sm font-medium text-white truncate">${item.title}</p>
          <p class="text-xs text-brown-300 mt-0.5">${item.message}</p>
          <p class="text-xs text-brown-500 mt-1">${item.created_at || ""}</p>
        </div>
        ${dot}
      </${tag}>
    `;
  }

  function renderAll(hasMore) {
    if (!allItems.length) {
      list.innerHTML =
        '<p class="text-sm text-brown-300 text-center py-6">Hakuna taarifa mpya.</p>';
      return;
    }
    let html = allItems.map(itemHTML).join("");
    if (hasMore) {
      html += `
        <button id="notif-load-more"
                class="w-full mt-2 py-2 text-xs text-brown-300 hover:text-white transition-colors text-center">
          <i class="fas fa-chevron-down mr-1"></i> Tazama Zaidi
        </button>`;
    }
    list.innerHTML = html;
    const btn = document.getElementById("notif-load-more");
    if (btn) btn.addEventListener("click", loadMore);
  }

  function fetchPage(page) {
    loading = true;
    return fetch(`/dashboard/api/v1/notifications/?page=${page}`)
      .then((r) => r.json())
      .finally(() => {
        loading = false;
      });
  }

  function loadMore() {
    if (loading) return;
    const btn = document.getElementById("notif-load-more");
    if (btn)
      btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Inapakia...';
    currentPage += 1;
    fetchPage(currentPage).then((data) => {
      allItems = allItems.concat(data.items);
      renderAll(data.has_more);
    });
  }

  bell.addEventListener("click", function () {
    currentPage = 1;
    allItems = [];
    list.innerHTML =
      '<p class="text-sm text-brown-300 text-center py-6"><i class="fas fa-spinner fa-spin mr-2"></i> Inapakia...</p>';
    dialog.showModal();

    fetchPage(1)
      .then((data) => {
        allItems = data.items;
        renderAll(data.has_more);
      })
      .catch(() => {
        list.innerHTML =
          '<p class="text-sm text-red-400 text-center py-6">Hitilafu. Jaribu tena.</p>';
      });
  });
})();

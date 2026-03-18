(function () {
  const dialog = document.getElementById("notificationDialog");
  const list = document.getElementById("notif-list");
  const bell =
    document.getElementById("dashboardNotifBell") ||
    document.querySelector('[title="Notifications"]') ||
    document.querySelector('[title="Taarifa"]');
  if (!dialog || !list || !bell) return;

  const colorMap = {
    red:   "background:#fee2e2;color:#ef4444",
    amber: "background:#fef3c7;color:#f59e0b",
    blue:  "background:#dbeafe;color:#3b82f6",
  };

  let currentPage = 1;
  let allItems = [];
  let loading = false;

  function itemHTML(item) {
    const tag = item.url ? "a" : "div";
    const href = item.url ? `href="${item.url}"` : "";
    const dot = item.unread
      ? '<span style="flex-shrink:0;width:8px;height:8px;border-radius:9999px;background:#f97316;margin-top:6px"></span>'
      : "";
    const itemStyle = item.unread
      ? "background:#fff7ed;border:1px solid #fed7aa"
      : "background:#f9fafb;border:1px solid #f3f4f6";
    const iconStyle = colorMap[item.color] || colorMap.blue;
    return `
      <${tag} ${href} style="display:flex;align-items:flex-start;gap:12px;padding:12px;border-radius:12px;${itemStyle};transition:background .15s">
        <div style="flex-shrink:0;width:32px;height:32px;border-radius:9999px;display:flex;align-items:center;justify-content:center;${iconStyle}">
          <i class="fas ${item.icon}" style="font-size:13px"></i>
        </div>
        <div style="min-width:0;flex:1">
          <p style="font-size:14px;font-weight:600;color:#1f2937;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${item.title}</p>
          <p style="font-size:12px;color:#6b7280;margin-top:2px">${item.message}</p>
          <p style="font-size:11px;color:#9ca3af;margin-top:4px">${item.created_at || ""}</p>
        </div>
        ${dot}
      </${tag}>
    `;
  }

  function renderAll(hasMore) {
    if (!allItems.length) {
      list.innerHTML =
        '<p class="text-sm text-gray-400 text-center py-8"><i class="fas fa-bell-slash block text-2xl mb-2 text-gray-300"></i>Hakuna taarifa mpya.</p>';
      return;
    }
    let html = allItems.map(itemHTML).join("");
    if (hasMore) {
      html += `
        <button id="notif-load-more"
                class="w-full mt-2 py-2 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors text-center">
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
      '<p class="text-sm text-gray-400 text-center py-6"><i class="fas fa-spinner fa-spin mr-2"></i> Inapakia...</p>';
    dialog.showModal();

    fetchPage(1)
      .then((data) => {
        allItems = data.items;
        renderAll(data.has_more);
      })
      .catch(() => {
        list.innerHTML =
          '<p class="text-sm text-red-500 text-center py-6"><i class="fas fa-exclamation-circle mr-1"></i> Hitilafu. Jaribu tena.</p>';
      });
  });
})();

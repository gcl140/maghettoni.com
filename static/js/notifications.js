(function () {
  const dialog = document.getElementById('notificationDialog');
  const list = document.getElementById('notif-list');
  const bell = document.querySelector('[title="Taarifa"]');
  if (!dialog || !bell) return;

  const colorMap = {
    red: 'bg-red-500/20 text-red-400',
    amber: 'bg-amber-500/20 text-amber-400',
    blue: 'bg-blue-500/20 text-blue-400',
  };

  function renderItems(items) {
    if (!items.length) {
      list.innerHTML = '<p class="text-sm text-brown-300 text-center py-6">Hakuna taarifa mpya.</p>';
      return;
    }
    list.innerHTML = items.map(item => `
      <a href="${item.url}" class="flex items-start gap-3 p-3 bg-brown-700/50 rounded-lg hover:bg-brown-700 transition-colors">
        <div class="flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${colorMap[item.color] || colorMap.blue}">
          <i class="fas ${item.icon} text-sm"></i>
        </div>
        <div class="min-w-0">
          <p class="text-sm font-medium text-white truncate">${item.title}</p>
          <p class="text-xs text-brown-300 mt-0.5">${item.message}</p>
        </div>
      </a>
    `).join('');
  }

  bell.addEventListener('click', function () {
    list.innerHTML = '<p class="text-sm text-brown-300 text-center py-6"><i class="fas fa-spinner fa-spin mr-2"></i> Inapakia...</p>';
    dialog.showModal();

    fetch('/dashboard/api/v1/notifications/')
      .then(r => r.json())
      .then(data => renderItems(data.items))
      .catch(() => {
        list.innerHTML = '<p class="text-sm text-red-400 text-center py-6">Hitilafu. Jaribu tena.</p>';
      });
  });
})();

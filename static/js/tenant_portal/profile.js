(function () {
  'use strict';

  function csrf() {
    return (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
  }

  document.querySelectorAll('.notif-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var tenancyId = btn.dataset.tenancyId;
      var label = btn.querySelector('.notif-label');
      var icon = btn.querySelector('i');

      fetch('/tenant-portal/tenancy/' + tenancyId + '/notifications/toggle/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrf(),
          'Content-Type': 'application/json',
        },
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.ok) return;
          var enabled = data.enabled;
          btn.dataset.enabled = enabled ? 'true' : 'false';
          if (enabled) {
            label.textContent = 'Reminders On';
            icon.className = 'fas fa-bell';
            btn.classList.remove('border-gray-200', 'bg-gray-50', 'text-gray-500', 'hover:bg-gray-100');
            btn.classList.add('border-green-200', 'bg-green-50', 'text-green-700', 'hover:bg-green-100');
          } else {
            label.textContent = 'Reminders Off';
            icon.className = 'fas fa-bell-slash';
            btn.classList.remove('border-green-200', 'bg-green-50', 'text-green-700', 'hover:bg-green-100');
            btn.classList.add('border-gray-200', 'bg-gray-50', 'text-gray-500', 'hover:bg-gray-100');
          }
        });
    });
  });
}());

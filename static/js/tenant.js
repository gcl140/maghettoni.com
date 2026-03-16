/* Tenant Portal — Dashboard JS */
(function () {
  'use strict';

  // ─── Greeting ────────────────────────────────────────────────────────────
  const greetingEl = document.getElementById('tp-greeting');
  if (greetingEl) {
    const hour = new Date().getHours();
    greetingEl.textContent =
      hour < 12 ? 'Good Morning 🌅' :
      hour < 17 ? 'Good Afternoon ☀️' :
                  'Good Evening 🌙';
  }

  // ─── Calendar ────────────────────────────────────────────────────────────
  const calEl   = document.getElementById('tp-calendar');
  const calLabel = document.getElementById('tp-cal-label');
  const prevBtn  = document.getElementById('tp-cal-prev');
  const nextBtn  = document.getElementById('tp-cal-next');

  if (!calEl) return;

  const MONTH_NAMES = [
    'January','February','March','April','May','June',
    'July','August','September','October','November','December'
  ];
  const DAY_NAMES = ['Ju','It','Ta','Ar','Al','Ij','Mo'];

  let viewYear  = new Date().getFullYear();
  let viewMonth = new Date().getMonth() + 1; // 1-based

  function renderCalendar(data) {
    const { year, month, days_in_month, due_day, payments_made, today } = data;

    // Build lookup: day → status
    const madeMap = {};
    payments_made.forEach(p => { madeMap[p.day] = p.status; });

    const firstDate  = new Date(year, month - 1, 1);
    const startWday  = firstDate.getDay(); // 0=Sun

    let html = '<div class="grid grid-cols-7 gap-px text-center mb-1">';
    DAY_NAMES.forEach(d => {
      html += `<div class="text-xs text-gray-400 font-medium py-1">${d}</div>`;
    });
    html += '</div><div class="grid grid-cols-7 gap-px text-center">';

    // Empty cells before month starts
    for (let i = 0; i < startWday; i++) {
      html += '<div class="py-1.5"></div>';
    }

    for (let d = 1; d <= days_in_month; d++) {
      const isToday   = d === today;
      const isDue     = d === due_day;
      const madeStatus = madeMap[d];
      const isPaid    = madeStatus === 'completed';
      const isPending = madeStatus === 'pending';

      let cls = 'py-1.5 text-xs rounded-lg transition-colors ';
      if (isToday && !isPaid && !isDue) {
        cls += 'bg-blue-500 text-white font-bold';
      } else if (isPaid) {
        cls += 'bg-green-100 text-green-700 font-semibold';
      } else if (isPending) {
        cls += 'bg-amber-100 text-amber-700 font-semibold';
      } else if (isDue) {
        cls += 'bg-amber-100 border border-amber-400 text-amber-800 font-bold';
      } else {
        cls += 'text-gray-700 hover:bg-gray-100';
      }

      const indicator = isPaid ? '✓' : (isDue && !isPaid ? '●' : '');
      html += `<div class="${cls}">${d}${indicator ? `<span class="block text-xs leading-none">${indicator}</span>` : ''}</div>`;
    }

    html += '</div>';
    calEl.innerHTML = html;
    calLabel.textContent = `${MONTH_NAMES[month - 1]} ${year}`;
  }

  function loadCalendar(year, month) {
    calEl.innerHTML = '<div class="text-center py-8 text-gray-400"><i class="fas fa-spinner fa-spin"></i></div>';
    fetch(`/tenant/api/calendar/?year=${year}&month=${month}`)
      .then(r => r.json())
      .then(renderCalendar)
      .catch(() => {
        calEl.innerHTML = '<p class="text-xs text-red-400 text-center py-6">Error. Please try again.</p>';
      });
  }

  prevBtn.addEventListener('click', () => {
    viewMonth--;
    if (viewMonth < 1) { viewMonth = 12; viewYear--; }
    loadCalendar(viewYear, viewMonth);
  });

  nextBtn.addEventListener('click', () => {
    viewMonth++;
    if (viewMonth > 12) { viewMonth = 1; viewYear++; }
    loadCalendar(viewYear, viewMonth);
  });

  // Initial load
  loadCalendar(viewYear, viewMonth);
})();

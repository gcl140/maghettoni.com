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
  const DAY_NAMES = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

  let viewYear  = new Date().getFullYear();
  let viewMonth = new Date().getMonth() + 1; // 1-based

  function renderCalendar(data) {
    const { year, month, days_in_month, due_day, payments_made, today, eligible_until_day } = data;

    // Build lookup: day → status
    const madeMap = {};
    payments_made.forEach(p => { madeMap[p.day] = p.status; });

    const firstDate  = new Date(year, month - 1, 1);
    const startWday  = firstDate.getDay(); // 0=Sun

    const gridStyle = 'display:grid;grid-template-columns:repeat(7,1fr);gap:2px;text-align:center;';
    let html = `<div style="${gridStyle}margin-bottom:4px;">`;
    DAY_NAMES.forEach(d => {
      html += `<div class="text-xs text-gray-400 font-medium py-1">${d}</div>`;
    });
    html += `</div><div style="${gridStyle}">`;

    // Empty cells before month starts
    for (let i = 0; i < startWday; i++) {
      html += '<div class="py-1.5"></div>';
    }

    for (let d = 1; d <= days_in_month; d++) {
      const isToday    = d === today;
      const isDue      = d === due_day;
      const isExpiry   = d === eligible_until_day;
      const madeStatus = madeMap[d];
      const isPaid     = madeStatus === 'completed';
      const isPending  = madeStatus === 'pending';

      let cls = 'py-1.5 text-xs rounded-lg transition-colors ';
      if (isToday && !isPaid && !isDue && !isExpiry) {
        cls += 'bg-blue-500 text-white font-bold';
      } else if (isPaid) {
        cls += 'bg-green-100 text-green-700 font-semibold';
      } else if (isPending) {
        cls += 'bg-amber-100 text-amber-700 font-semibold';
      } else if (isExpiry) {
        cls += 'bg-red-100 border border-red-400 text-red-700 font-bold';
      } else if (isDue) {
        cls += 'bg-amber-100 border border-amber-400 text-amber-800 font-bold';
      } else {
        cls += 'text-gray-700 hover:bg-gray-100';
      }

      const indicator = isPaid ? '✓' : isExpiry ? '⚑' : (isDue && !isPaid ? '●' : '');
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

// ─── Due Date Countdown ───────────────────────────────────────────────────
(function () {
  'use strict';

  var card = document.getElementById('due-card');
  if (!card) return;

  var tenancies = JSON.parse(card.dataset.tenancies);
  var idx = 0;
  var cdInterval = null;

  var elDays     = document.getElementById('cd-days');
  var elHours    = document.getElementById('cd-hours');
  var elMins     = document.getElementById('cd-mins');
  var elSecs     = document.getElementById('cd-secs');
  var elMoveIn   = document.getElementById('cd-move-in');
  var elDate     = document.getElementById('cd-due-date');
  var elRent     = document.getElementById('cd-rent');
  var elIconWrap = document.getElementById('due-icon-wrap');
  var elIcon     = document.getElementById('due-icon');
  var elLabel    = document.getElementById('due-tenancy-label');
  var elNav      = document.getElementById('due-nav');
  var elNavLabel = document.getElementById('due-nav-label');
  var elAll      = [elDays, elHours, elMins, elSecs];

  function cdColor(days) {
    return days === null || days === undefined ? '#4ade80'
      : days <= 3 ? '#f87171'
      : days <= 7 ? '#fbbf24'
      : '#4ade80';
  }
  function cdIconBg(days) {
    return days === null || days === undefined ? 'rgba(74,222,128,0.2)'
      : days <= 3 ? 'rgba(239,68,68,0.2)'
      : days <= 7 ? 'rgba(245,158,11,0.2)'
      : 'rgba(74,222,128,0.2)';
  }

  function renderCard(data) {
    var c = cdColor(data.days_until_due);
    elIconWrap.style.backgroundColor = cdIconBg(data.days_until_due);
    elIcon.style.color = c;
    elAll.forEach(function (el) { el.style.color = c; });

    elLabel.classList.remove('hidden');
    elLabel.textContent = data.property_name
      + (data.unit_number ? ' · Unit ' + data.unit_number : '')
      + (data.landlord ? ' · ' + data.landlord : '');

    if (tenancies.length > 1) {
      elNav.classList.remove('hidden');
      elNav.style.display = 'flex';
      elNavLabel.textContent = (idx + 1) + '/' + tenancies.length;
    }

    elMoveIn.textContent = data.move_in_date ? 'Moved in ' + data.move_in_date : '';
    elRent.textContent = data.monthly_rent
      ? 'TZS ' + Math.round(data.monthly_rent).toLocaleString()
      : '';

    if (!data.next_due_iso) {
      elAll.forEach(function (el) { el.textContent = '--'; });
      elDate.textContent = 'No payments recorded yet';
      return;
    }

    var target = new Date(data.next_due_iso + 'T23:59:59');
    var opts = { day: '2-digit', month: 'long', year: 'numeric' };
    elDate.textContent = 'Eligible until ' + new Date(data.next_due_iso + 'T00:00:00').toLocaleDateString('en-GB', opts);

    if (cdInterval) clearInterval(cdInterval);

    function tick() {
      var diff = target - new Date();
      if (diff <= 0) {
        elDays.textContent  = 'Pay';
        elHours.textContent = 'Now';
        elMins.textContent  = '!';
        elSecs.textContent  = '!';
        elAll.forEach(function (el) { el.style.color = '#f87171'; });
        clearInterval(cdInterval);
        return;
      }
      elDays.textContent  = String(Math.floor(diff / 86400000)).padStart(2, '0');
      elHours.textContent = String(Math.floor((diff % 86400000) / 3600000)).padStart(2, '0');
      elMins.textContent  = String(Math.floor((diff % 3600000) / 60000)).padStart(2, '0');
      elSecs.textContent  = String(Math.floor((diff % 60000) / 1000)).padStart(2, '0');
    }
    tick();
    cdInterval = setInterval(tick, 1000);
  }

  renderCard(tenancies[0]);

  if (tenancies.length > 1) {
    document.getElementById('due-prev').addEventListener('click', function () {
      idx = (idx - 1 + tenancies.length) % tenancies.length;
      renderCard(tenancies[idx]);
    });
    document.getElementById('due-next').addEventListener('click', function () {
      idx = (idx + 1) % tenancies.length;
      renderCard(tenancies[idx]);
    });
  }
}());

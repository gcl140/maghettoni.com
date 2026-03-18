document.addEventListener('DOMContentLoaded', function() {
    // Greeting based on time of day
    const hour = new Date().getHours();
    const greetingText = document.getElementById('greetingText');
    if (greetingText) {
        let greeting = 'Habari';
        if (hour < 12) greeting = 'Habari ya Asubuhi';
        else if (hour < 17) greeting = 'Habari ya Mchana';
        else greeting = 'Habari ya Jioni';
        greetingText.textContent = greeting;
    }
    
    // Update current date
    const currentDate = document.getElementById('currentDate');
    if (currentDate) {
        const now = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        currentDate.textContent = now.toLocaleDateString('sw-TZ', options);
    }
    
    // Revenue Chart
    const revenueChart = document.getElementById('revenueChart');
    if (revenueChart) {
        const labels = JSON.parse(revenueChart.dataset.labels);
        const data = JSON.parse(revenueChart.dataset.values);

        const ctx = revenueChart.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Mapato (TZS)',
                    data: data,
                    borderColor: '#603b2b',
                    backgroundColor: 'rgba(96, 59, 43, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'TZS ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'TZS ' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Add hover effects to all cards
    const cards = document.querySelectorAll('.hover-lift');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'transform 0.2s ease, box-shadow 0.2s ease';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Animate stats numbers on load
    const statsNumbers = document.querySelectorAll('.text-xl.font-bold');
    statsNumbers.forEach(number => {
        const originalValue = number.textContent;
        const target = parseInt(originalValue.replace(/,/g, ''));
        
        if (!isNaN(target) && target > 0) {
            number.textContent = '0';
            
            setTimeout(() => {
                let count = 0;
                const duration = 1500; // 1.5 seconds
                const increment = target / (duration / 16); // 60fps
                
                const timer = setInterval(() => {
                    count += increment;
                    if (count >= target) {
                        count = target;
                        clearInterval(timer);
                    }
                    number.textContent = Math.floor(count).toLocaleString();
                }, 16); // ~60fps
            }, 300); // Delay to allow page to load
        }
    });
    
    // Add click event to search bar for demo
    const searchInput = document.querySelector('input[placeholder="Tafuta..."]');
    if (searchInput) {
        searchInput.addEventListener('focus', function() {
            this.parentElement.classList.add('ring-2', 'ring-brown-300');
        });
        searchInput.addEventListener('blur', function() {
            this.parentElement.classList.remove('ring-2', 'ring-brown-300');
        });
    }
    
    // Add notification badge animation
    const notificationBtn = document.querySelector('button .fa-bell');
    const maint = document.getElementById('maintenanceStatus');
    if (maint) {
        const emergencyCount = JSON.parse(maint.dataset.values);
    } else { 
        var emergencyCount = 0; }
    if (notificationBtn && emergencyCount > 0) {
        setInterval(() => {
            const badge = notificationBtn.nextElementSibling;
            if (badge && badge.classList.contains('animate-pulse')) {
                badge.classList.toggle('animate-pulse');
                setTimeout(() => {
                    badge.classList.toggle('animate-pulse');
                }, 1000);
            }
        }, 3000);
    }
    
    // Initialize tooltips for chart
    if (revenueChart) {
        const tooltips = revenueChart.parentElement.querySelectorAll('.chart-tooltip');
        tooltips.forEach(tooltip => {
            tooltip.style.opacity = '0';
        });
    }
});

(function () {
  var calEl    = document.getElementById('ld-calendar');
  var calLabel = document.getElementById('ld-cal-label');
  var prevBtn  = document.getElementById('ld-cal-prev');
  var nextBtn  = document.getElementById('ld-cal-next');
  var modal    = document.getElementById('ld-cal-modal');
  if (!calEl) return;

  var MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  var DAYS   = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  var viewYear  = new Date().getFullYear();
  var viewMonth = new Date().getMonth() + 1;

  var STATUS_CFG = {
    completed: { bg: '#bbf7d0', color: '#166534', label: 'Paid' },
    pending:   { bg: '#fde68a', color: '#92400e', label: 'Pending' },
    overdue:   { bg: '#fecaca', color: '#991b1b', label: 'Overdue' },
    upcoming:  { bg: '#dbeafe', color: '#1e40af', label: 'Upcoming' },
    expiring:  { bg: '#fee2e2', color: '#991b1b', label: 'Lease Ends' }
  };

  function openModal(day, info) {
    document.getElementById('ld-cal-modal-title').textContent = MONTHS[viewMonth - 1] + ' ' + day + ', ' + viewYear;
    var total = info.items.length;
    document.getElementById('ld-cal-modal-sub').textContent = total + ' payment' + (total !== 1 ? 's' : '');
    document.getElementById('ld-cal-modal-body').innerHTML = info.items.map(function (item) {
      var cfg  = STATUS_CFG[item.status] || STATUS_CFG.pending;
      var amt  = item.amount != null ? 'TZS ' + Number(item.amount).toLocaleString('en-TZ', { maximumFractionDigits: 0 }) : '';
      var icon = item.status === 'completed' ? '✓' : item.status === 'overdue' ? '▲' : item.status === 'upcoming' ? '◷' : item.status === 'expiring' ? '⚑' : '•';
      return '<a href="/dashboard/payments/' + item.id + '/" style="display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:12px;background:#f9fafb;border:1px solid #f3f4f6;text-decoration:none;" onmouseover="this.style.background=\'#f3f4f6\'" onmouseout="this.style.background=\'#f9fafb\'">'
        + '<div style="width:36px;height:36px;border-radius:50%;background:' + cfg.bg + ';display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:14px;">' + icon + '</div>'
        + '<div style="flex:1;min-width:0;">'
        + '<p style="margin:0;font-size:13px;font-weight:600;color:#111827;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + item.tenant + '</p>'
        + '<p style="margin:2px 0 0;font-size:11px;color:#6b7280;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + item.property + '</p>'
        + '</div>'
        + '<div style="text-align:right;flex-shrink:0;">'
        + '<p style="margin:0;font-size:13px;font-weight:700;color:#111827;">' + amt + '</p>'
        + '<span style="display:inline-block;margin-top:2px;font-size:10px;font-weight:600;padding:2px 7px;border-radius:20px;background:' + cfg.bg + ';color:' + cfg.color + ';">' + cfg.label + '</span>'
        + '</div></a>';
    }).join('');
    modal.style.display = 'block';
  }

  function renderCalendar(data) {
    var year = data.year, month = data.month, days_in_month = data.days_in_month, today = data.today, days = data.days, expiring = data.expiring || {};
    var gs = 'display:grid;grid-template-columns:repeat(7,1fr);gap:2px;text-align:center;';
    var html = '<div style="' + gs + 'margin-bottom:4px;">';
    DAYS.forEach(function (d) { html += '<div style="color:#9ca3af;font-size:11px;padding:4px 0;">' + d + '</div>'; });
    html += '</div><div style="' + gs + '">';
    var startWday = new Date(year, month - 1, 1).getDay();
    for (var i = 0; i < startWday; i++) html += '<div></div>';
    for (var d = 1; d <= days_in_month; d++) {
      var info      = days[String(d)] || {};
      var expDay    = expiring[String(d)] || [];
      var isToday   = d === today;
      var hasOver   = (info.overdue   || 0) > 0;
      var hasPend   = (info.pending   || 0) > 0;
      var hasPaid   = (info.completed || 0) > 0;
      var hasUp     = (info.upcoming  || 0) > 0;
      var hasExpiry = expDay.length > 0;
      var hasItems  = (info.items || []).length > 0 || hasExpiry;
      var bg = 'color:#374151;', dot = '', extra = '';
      if (isToday && !hasOver && !hasPend && !hasPaid && !hasUp && !hasExpiry) {
        bg = 'background:#3b82f6;color:#fff;font-weight:700;';
      } else if (hasOver) {
        bg = 'background:#fecaca;color:#991b1b;font-weight:600;';
        dot = '<span style="display:block;font-size:8px;line-height:1.2;">▲' + info.overdue + '</span>';
      } else if (hasPend) {
        bg = 'background:#fde68a;color:#92400e;font-weight:600;';
        dot = '<span style="display:block;font-size:8px;line-height:1.2;">•' + info.pending + '</span>';
      } else if (hasPaid) {
        bg = 'background:#bbf7d0;color:#166534;font-weight:600;';
        dot = '<span style="display:block;font-size:8px;line-height:1.2;">✓' + info.completed + '</span>';
      } else if (hasUp) {
        bg = 'background:#dbeafe;color:#1e40af;font-weight:600;';
        dot = '<span style="display:block;font-size:8px;line-height:1.2;">◷' + info.upcoming + '</span>';
      } else if (hasExpiry) {
        bg = 'background:#fee2e2;color:#991b1b;font-weight:600;';
      }
      if (hasExpiry) {
        dot += '<span style="display:block;font-size:8px;line-height:1.2;color:#dc2626;">⚑' + expDay.length + '</span>';
      }
      if (hasItems) extra = 'cursor:pointer;outline:2px solid rgba(0,0,0,.08);';
      html += '<div data-cal-day="' + d + '" style="padding:4px 2px;border-radius:6px;' + bg + extra + '">' + d + dot + '</div>';
    }
    html += '</div>';
    calEl.innerHTML = html;
    calLabel.textContent = MONTHS[month - 1] + ' ' + year;
    calEl.querySelectorAll('[data-cal-day]').forEach(function (cell) {
      var day     = parseInt(cell.getAttribute('data-cal-day'));
      var info    = (data.days || {})[String(day)] || {};
      var expDay  = (data.expiring || {})[String(day)] || [];
      var items   = (info.items || []).slice();
      expDay.forEach(function (e) {
        items.push({ id: null, tenant: e.tenant, property: e.property, amount: null, status: 'expiring' });
      });
      if (items.length > 0) {
        cell.addEventListener('click', function () { openModal(day, { items: items }); });
      }
    });
  }

  function loadCalendar(year, month) {
    calEl.innerHTML = '<div style="text-align:center;padding:24px;color:#9ca3af;"><i class="fas fa-spinner fa-spin"></i></div>';
    fetch('/dashboard/api/v1/calendar/?year=' + year + '&month=' + month)
      .then(function (r) { return r.json(); })
      .then(renderCalendar)
      .catch(function () { calEl.innerHTML = '<p style="text-align:center;padding:16px;color:#f87171;font-size:12px;">Failed to load.</p>'; });
  }

  prevBtn.addEventListener('click', function () { viewMonth--; if (viewMonth < 1) { viewMonth = 12; viewYear--; } loadCalendar(viewYear, viewMonth); });
  nextBtn.addEventListener('click', function () { viewMonth++; if (viewMonth > 12) { viewMonth = 1; viewYear++; } loadCalendar(viewYear, viewMonth); });
  loadCalendar(viewYear, viewMonth);
})();
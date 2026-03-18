function markPaid() {
    var form = document.getElementById('mark-paid-form');
    if (!form) return;
    if (form.dataset.needsConfirmation === 'true') {
        showConfirm(form.dataset.confirmMsg, function () { form.submit(); });
    } else {
        form.submit();
    }
}

function toggleReminderMenu() {
    document.getElementById('reminder-menu').classList.toggle('hidden');
}

document.addEventListener('click', function (e) {
    var w = document.getElementById('reminder-wrapper');
    if (w && !w.contains(e.target)) {
        document.getElementById('reminder-menu').classList.add('hidden');
    }
});

function sendReminder(channel) {
    var wrapper = document.getElementById('reminder-wrapper');
    var paymentId = wrapper.dataset.paymentId;
    document.getElementById('reminder-menu').classList.add('hidden');
    var btn = wrapper.querySelector('button');
    var orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Sending...';
    fetch('/dashboard/api/v1/payments/' + paymentId + '/remind/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'channel=' + channel,
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.success) {
            btn.innerHTML = '<i class="fas fa-check mr-2"></i>Sent!';
            btn.classList.replace('bg-white', 'bg-green-50');
            setTimeout(function () { btn.innerHTML = orig; btn.classList.replace('bg-green-50', 'bg-white'); btn.disabled = false; }, 3000);
        } else {
            btn.innerHTML = '<i class="fas fa-times mr-2"></i>Failed';
            setTimeout(function () { btn.innerHTML = orig; btn.disabled = false; }, 3000);
        }
    })
    .catch(function () {
        btn.innerHTML = orig;
        btn.disabled = false;
    });
}

function sendDirectReminder(paymentId, btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Sending...';
    fetch(`/dashboard/api/v1/payments/${paymentId}/remind/`, {
        method: 'POST',
        headers: {'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''},
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            btn.innerHTML = '<i class="fas fa-check mr-2"></i>SMS Sent!';
            btn.classList.replace('bg-blue-600', 'bg-green-600');
            btn.classList.replace('hover:bg-blue-700', 'hover:bg-green-700');
        } else {
            btn.innerHTML = '<i class="fas fa-times mr-2"></i>Failed — retry';
            btn.classList.replace('bg-blue-600', 'bg-red-600');
            btn.classList.replace('hover:bg-blue-700', 'hover:bg-red-700');
            btn.disabled = false;
        }
    })
    .catch(() => {
        btn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>Send SMS Now';
        btn.disabled = false;
    });
}

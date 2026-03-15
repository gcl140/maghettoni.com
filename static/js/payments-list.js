function sendReminder(paymentId, btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Sending...';
    fetch(`/dashboard/api/v1/payments/${paymentId}/remind/`, {
        method: 'POST',
        headers: {'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)?.[1] || ''},
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            btn.innerHTML = '<i class="fas fa-check mr-2"></i>Sent!';
            btn.classList.replace('bg-blue-600', 'bg-green-600');
            btn.classList.replace('hover:bg-blue-700', 'hover:bg-green-700');
        } else {
            btn.innerHTML = '<i class="fas fa-times mr-2"></i>Failed' + (data.error ? `: ${data.error}` : '');
            btn.classList.replace('bg-blue-600', 'bg-red-600');
            btn.disabled = false;
        }
    })
    .catch(() => {
        btn.innerHTML = '<i class="fas fa-sms mr-2"></i>Remind';
        btn.disabled = false;
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const statusFilter = document.getElementById('statusFilter');
    const dateFilter   = document.getElementById('dateFilter');

    statusFilter && statusFilter.addEventListener('change', function () {
        const url = new URL(window.location.href);
        url.searchParams.set('status', this.value);
        window.location.href = url.toString();
    });

    dateFilter && dateFilter.addEventListener('change', function () {
        const url = new URL(window.location.href);
        url.searchParams.set('date', this.value);
        window.location.href = url.toString();
    });
});

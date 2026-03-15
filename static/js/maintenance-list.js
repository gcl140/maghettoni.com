function notifyTenant(requestId, btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Sending...';
    fetch(`/dashboard/api/v1/maintenance/${requestId}/notify/`, {
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
            btn.innerHTML = '<i class="fas fa-times mr-2"></i>Failed';
            btn.classList.replace('bg-blue-600', 'bg-red-600');
            btn.disabled = false;
        }
    })
    .catch(() => {
        btn.innerHTML = '<i class="fas fa-sms mr-2"></i>Notify';
        btn.disabled = false;
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const statusFilter   = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');

    statusFilter && statusFilter.addEventListener('change', function () {
        const url = new URL(window.location.href);
        url.searchParams.set('status', this.value);
        window.location.href = url.toString();
    });

    priorityFilter && priorityFilter.addEventListener('change', function () {
        const url = new URL(window.location.href);
        url.searchParams.set('priority', this.value);
        window.location.href = url.toString();
    });
});

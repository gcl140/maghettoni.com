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

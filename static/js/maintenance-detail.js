function markComplete() {
    if (confirm('Mark this maintenance request as completed?')) {
        document.querySelector('select[name="status"]').value = 'completed';
        document.querySelector('form').submit();
    }
}

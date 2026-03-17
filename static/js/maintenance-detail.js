function markComplete() {
  showConfirm('Mark this maintenance request as completed?', function () {
    document.querySelector('select[name="status"]').value = 'completed';
    document.querySelector('form').submit();
  });
}
